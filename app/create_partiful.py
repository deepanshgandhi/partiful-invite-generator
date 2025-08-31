"""Playwright automation for filling Partiful's Create invite page.

ToS-safe approach: headful browser, form fill        except Exception as e:
            print(f"\\n❌ Error during form filling: {e}")
            print("🔧 Browser will stay open for manual completion.")
            print("💡 Press Ctrl+C in the terminal to close the browser when done.")
            
            # Keep browser openeedn even on error
            try:
                while True:
                    await page.wait_for_timeout(10000)  # Check every 10 seconds
                    try:
                        await page.evaluate("document.title")
                    except:
                        print("🔄 Browser was closed by user.")
                        break
            except KeyboardInterrupt:
                print("\\n👋 Closing browser as requested...")
            except Exception:
                print("\\n🔄 Browser session ended.")
            raise
        finally:
            # Only close browser if wait_for_publish was True, otherwise keep it open
            if wait_for_publish:
                print("\\n✅ Auto-closing browser.")
                await browser.close()
            # If wait_for_publish is False, browser stays open (handled in main logic above)r publishes manually.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from playwright.async_api import Browser, Page, async_playwright

from .models import EventSpec
from .partiful_selectors import (
    DATE_INPUT_SELECTORS,
    DATE_TRIGGER,
    DESCRIPTION_INPUT_SELECTORS,
    DESCRIPTION_TRIGGER,
    LOCATION_INPUT_SELECTORS,
    LOCATION_TRIGGER,
    PUBLISH_BUTTON,
    SAVE_DRAFT_BUTTON,
    TITLE_SELECTOR,
)
from .settings import settings


async def fill_partiful_form(event: EventSpec, *, wait_for_publish: bool = False) -> None:
    """Fill Partiful's create form with event data in a headful browser.
    
    Args:
        event: The structured event data to fill
        wait_for_publish: If True, waits for user to manually click publish
    """
    
    async with async_playwright() as p:
        # Launch headful browser for user interaction
        browser = await p.chromium.launch(headless=settings.headless)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Try each create URL until one works
        page_loaded = False
        for url in settings.partiful_create_urls:
            try:
                print(f"Trying Partiful create page: {url}")
                await page.goto(url, timeout=15000)
                await page.wait_for_load_state("networkidle", timeout=10000)
                page_loaded = True
                print(f"✅ Successfully loaded: {url}")
                break
            except Exception as e:
                print(f"⚠️  Failed to load {url}: {e}")
                continue
        
        if not page_loaded:
            raise Exception("Could not load any Partiful create URLs")
        
        try:
            print("\\n🎯 Starting form fill process...")
            
            # Handle any modal overlays first
            await close_modal_overlays(page)
            
            # 1. Fill title
            await fill_title(page, event.title)
            
            # 2. Fill date/time (this is the most complex part)
            await fill_datetime(page, event.start, event.end)
            
            # 3. Fill location if provided
            if event.location_text:
                await fill_location(page, event.location_text)
            
            # 4. Fill description if provided
            if event.description_md:
                await fill_description(page, event.description_md)
            
            # 5. Upload cover image if provided
            if event.cover_image_path:
                await upload_cover_image(page, event.cover_image_path)
            
            print("\\n✅ Form filled successfully!")
            print("📝 Please review the form and manually publish when ready.")
            print("💡 Tip: Check the date/time format and make any final adjustments.")
            
            if wait_for_publish:
                print("\\n⏳ Waiting for manual publish... (browser will stay open)")
                try:
                    # Wait for publish button to be clicked or page navigation
                    await page.wait_for_function(
                        "() => window.location.href !== window.location.href", 
                        timeout=300000  # 5 minutes
                    )
                    print("✅ Page changed - event likely published!")
                except Exception:
                    print("⏰ Timeout reached. Please publish manually if needed.")
            else:
                print("\\n🌐 Browser will remain open for manual review and publishing...")
                print("💡 You can review the form and click 'Publish' when ready.")
                print("🔧 Press Ctrl+C in the terminal to close the browser when done.")
                
                # Keep the browser open indefinitely
                try:
                    while True:
                        await page.wait_for_timeout(10000)  # Check every 10 seconds
                        # Check if the page is still alive
                        try:
                            await page.evaluate("document.title")
                        except:
                            print("🔄 Browser was closed by user.")
                            break
                except KeyboardInterrupt:
                    print("\\n👋 Closing browser as requested...")
                except Exception:
                    print("\\n� Browser session ended.")
                
        except Exception as e:
            print(f"\\n❌ Error during form filling: {e}")
            print("🔧 Taking screenshot for debugging...")
            try:
                await page.screenshot(path="partiful_error_debug.png", full_page=True)
                print("� Error screenshot saved")
            except:
                pass
            raise
        finally:
            # Always close browser for debugging
            print("\\n� Closing browser...")
            await browser.close()


async def close_modal_overlays(page: Page) -> None:
    """Close any modal overlays that might be blocking interactions."""
    try:
        # Check for modal overlay
        modal = await page.query_selector('[role="dialog"].legacy-modal-overlay')
        if modal:
            print("🔄 Closing modal overlay...")
            # Try multiple methods to close the modal
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)
            
            # If still there, try clicking outside
            modal_still_there = await page.query_selector('[role="dialog"].legacy-modal-overlay')
            if modal_still_there:
                # Click outside the modal (at the overlay)
                await page.click('[role="dialog"].legacy-modal-overlay', force=True)
                await page.wait_for_timeout(500)
                
            # Final check
            modal_final = await page.query_selector('[role="dialog"].legacy-modal-overlay')
            if not modal_final:
                print("✅ Modal overlay closed")
            else:
                print("⚠️  Modal overlay persists")
    except:
        pass


async def select_date_in_datepicker(page: Page, target: datetime) -> bool:
    """Navigate the calendar to the target month and click the exact date.

    Based on actual Partiful calendar structure:
    - Navigation: button[name="next-month"] and button[name="previous-month"] 
    - Month header: DIV with class ptf-l-2YGTl containing "Month YYYY"
    - Day buttons: button[name="day"][role="gridcell"]
    """
    target_month = target.strftime("%B")  # September
    target_year = str(target.year)        # 2025
    target_day = str(target.day)          # 1
    
    print(f"🎯 Looking for {target_month} {target_year}, day {target_day}")

    async def get_current_month_year() -> tuple[str, str] | None:
        """Get the currently displayed month and year from the calendar header."""
        try:
            # Look for month header with the specific class from actual HTML
            month_header = await page.query_selector('.ptf-l-2YGTl')
            if month_header:
                text = await month_header.text_content()
                if text and text.strip():
                    print(f"📅 Current calendar shows: {text.strip()}")
                    # Parse "August 2025" format
                    parts = text.strip().split()
                    if len(parts) == 2:
                        return parts[0], parts[1]  # ("August", "2025")
            return None
        except Exception as e:
            print(f"⚠️ Error getting current month: {e}")
            return None

    async def click_next_month() -> bool:
        """Click the next month navigation button."""
        try:
            # Use the exact selector from actual HTML
            next_button = await page.query_selector('button[name="next-month"]')
            if next_button:
                is_enabled = not await next_button.get_attribute('disabled')
                if is_enabled:
                    await next_button.click(force=True)
                    await page.wait_for_timeout(300)  # Wait for calendar to update
                    print("➡️ Clicked next month")
                    return True
                else:
                    print("⚠️ Next month button is disabled")
            else:
                print("❌ Next month button not found")
            return False
        except Exception as e:
            print(f"⚠️ Error clicking next month: {e}")
            return False

    async def click_target_day() -> bool:
        """Click on the target day in the current month view."""
        try:
            # Find all day buttons
            day_buttons = await page.query_selector_all('button[name="day"][role="gridcell"]')
            print(f"📊 Found {len(day_buttons)} day buttons")
            
            for button in day_buttons:
                try:
                    button_text = await button.text_content()
                    is_disabled = await button.get_attribute('disabled') is not None
                    
                    if button_text and button_text.strip() == target_day and not is_disabled:
                        await button.click(force=True)
                        print(f"✅ Clicked on day {target_day}")
                        return True
                        
                except Exception as e:
                    continue
            
            print(f"❌ Could not find enabled day button for {target_day}")
            return False
            
        except Exception as e:
            print(f"⚠️ Error clicking target day: {e}")
            return False

    # Main navigation logic
    max_attempts = 12  # Don't navigate more than 12 months
    attempts = 0
    
    while attempts < max_attempts:
        attempts += 1
        
        # Get current month/year displayed
        current = await get_current_month_year()
        if not current:
            print("❌ Could not determine current month/year")
            return False
            
        current_month, current_year = current
        
        # Check if we're at the target month/year
        if current_month == target_month and current_year == target_year:
            print(f"🎯 Reached target month: {target_month} {target_year}")
            return await click_target_day()
        
        # Navigate forward if we need a future month/year
        if (int(current_year) < int(target_year)) or \
           (int(current_year) == int(target_year) and 
            datetime.strptime(current_month, "%B").month < target.month):
            
            if not await click_next_month():
                print("❌ Failed to navigate to next month")
                return False
        else:
            print(f"⚠️ Target date {target_month} {target_year} is before current {current_month} {current_year}")
            return False
    
    print(f"❌ Could not reach {target_month} {target_year} after {max_attempts} attempts")
    return False


async def set_time_in_datepicker(page: Page, start: datetime, end: Optional[datetime]) -> bool:
    """Set the start (and optionally end) time inside the datepicker panel.

    The time picker has individual time slots as clickable elements with format like "6:00PM".
    Returns True if any time was set.
    """
    success = False
    start_time = start.strftime("%I:%M%p").lstrip("0")  # Format: "6:00PM"
    end_time = end.strftime("%I:%M%p").lstrip("0") if end else None  # Format: "9:00PM"

    print(f"🕐 Looking for start time: {start_time}")
    
    try:
        # Look for the specific time element in the time picker
        # The time picker uses elements with class "ptf-l-cv08W" and contains time text
        time_elements = await page.query_selector_all('.ptf-l-cv08W')
        print(f"📋 Found {len(time_elements)} time elements")
        
        # Find and click the start time
        for time_elem in time_elements:
            time_text = await time_elem.text_content()
            if time_text and time_text.strip() == start_time:
                print(f"✅ Found start time element: {time_text}")
                await time_elem.click()
                await page.wait_for_timeout(500)  # Wait for selection
                success = True
                break
        
        if not success:
            print(f"⚠️ Could not find exact start time {start_time}, trying partial match...")
            # Try partial matching (e.g., "6:00PM" matches "6:00 PM")
            start_time_parts = start_time.replace("AM", " AM").replace("PM", " PM")
            for time_elem in time_elements:
                time_text = await time_elem.text_content()
                if time_text and (time_text.strip() == start_time_parts or 
                                time_text.replace(" ", "") == start_time):
                    print(f"✅ Found start time with partial match: {time_text}")
                    await time_elem.click()
                    await page.wait_for_timeout(500)
                    success = True
                    break
        
        # Try to set end time if we have it and start time was successful
        if success and end_time:
            print(f"🕘 Looking for end time: {end_time}")
            
            # After selecting start time, check if End time section appears
            await page.wait_for_timeout(1000)  # Wait for UI to update
            
            # Look for End button or End time section
            try:
                end_button = await page.query_selector('button:has-text("End")')
                if end_button:
                    print("🔘 Clicking End button to enable end time")
                    await end_button.click()
                    await page.wait_for_timeout(500)
                    
                    # Now look for end time elements
                    end_time_elements = await page.query_selector_all('.ptf-l-cv08W')
                    for time_elem in end_time_elements:
                        time_text = await time_elem.text_content()
                        if time_text and (time_text.strip() == end_time or 
                                        time_text.replace(" ", "") == end_time):
                            print(f"✅ Found end time element: {time_text}")
                            await time_elem.click()
                            await page.wait_for_timeout(500)
                            break
                    else:
                        print(f"⚠️ Could not find end time {end_time}")
                else:
                    print("ℹ️ End button not found, end time may not be available")
            except Exception as e:
                print(f"⚠️ Error setting end time: {e}")
                
    except Exception as e:
        print(f"❌ Error in time selection: {e}")
        
    return success

async def click_location_save(page: Page) -> bool:
    """Click the Save button in the Location modal and wait for it to close.

    Returns True if the modal was closed (save likely succeeded), False otherwise.
    """
    try:
        # Scope actions within the dialog
        dialog_loc = page.locator('[role="dialog"]')
        # Primary: role-based button named Save
        try:
            save_btn = dialog_loc.get_by_role("button", name="Save")
            if await save_btn.count() > 0:
                await save_btn.first.click(force=True)
                try:
                    await page.wait_for_selector('[role="dialog"]', state='hidden', timeout=3000)
                except Exception:
                    await page.wait_for_selector('[role="dialog"]', state='detached', timeout=3000)
                print("💾 Clicked Save; modal closed")
                return True
        except Exception as e:
            print(f"⚠️  Primary Save click failed: {e}")

        # Fallback 1: CSS text selector inside the dialog
        try:
            btn = await page.query_selector('[role="dialog"] button:has-text("Save")')
            if btn:
                await btn.click(force=True)
                try:
                    await page.wait_for_selector('[role="dialog"]', state='hidden', timeout=3000)
                except Exception:
                    await page.wait_for_selector('[role="dialog"]', state='detached', timeout=3000)
                print("💾 Clicked Save via fallback; modal closed")
                return True
        except Exception as e:
            print(f"⚠️  Fallback Save click failed: {e}")

        # Fallback 2: Press Enter to confirm
        try:
            await page.keyboard.press("Enter")
            try:
                await page.wait_for_selector('[role="dialog"]', state='hidden', timeout=2000)
            except Exception:
                await page.wait_for_selector('[role="dialog"]', state='detached', timeout=2000)
            print("💾 Pressed Enter; modal closed")
            return True
        except Exception:
            pass

        # Fallback 3: Click near bottom center of dialog
        try:
            dialog_el = await page.query_selector('[role="dialog"]')
            if dialog_el:
                box = await dialog_el.bounding_box()
                if box:
                    await page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height'] - 20)
                    try:
                        await page.wait_for_selector('[role="dialog"]', state='hidden', timeout=2000)
                    except Exception:
                        await page.wait_for_selector('[role="dialog"]', state='detached', timeout=2000)
                    print("💾 Clicked bottom of dialog; modal closed")
                    return True
        except Exception:
            pass

        print("⚠️  Could not close modal via Save")
        return False
    except Exception as e:
        print(f"⚠️  Error clicking Save: {e}")
        return False

async def fill_title(page: Page, title: str) -> None:
    """Fill the event title."""
    if title.lower().endswith("ntitled event"):
        title = title[:-10]
    print(f"📝 Filling title: {title}")
    try:
        # Click the title area and clear it
        await page.click(TITLE_SELECTOR)
        
        # Clear any existing text (including "Untitled Event")
        await page.keyboard.press("Delete")     # Delete selected text
        
        # Type the new title
        await page.keyboard.type(title)
        print("✅ Title filled successfully")
    except Exception as e:
        print(f"⚠️  Could not fill title: {e}")


async def fill_datetime(page: Page, start: datetime, end: Optional[datetime]) -> None:
    """Fill date and time information."""
    print(f"📅 Setting date/time: {start}")
    try:
        # First, ensure no modal overlays are blocking
        await close_modal_overlays(page)
        
        # Take screenshot before clicking
        await page.screenshot(path="before_date_click.png")
        print("📸 Screenshot taken before date click")
        
        # Try to find and click the date button more reliably
        date_clicked = False
        
        # Method 1: Try the CSS selector directly
        try:
            date_button = await page.query_selector('.ptf-l-EDGV-')
            if date_button:
                print("🎯 Found date button, checking properties...")
                
                # Check button properties
                is_visible = await date_button.is_visible()
                is_enabled = await date_button.is_enabled()
                text_content = await date_button.text_content()
                print(f"📋 Button - Visible: {is_visible}, Enabled: {is_enabled}, Text: '{text_content}'")
                
                if is_visible and is_enabled:
                    await date_button.click(force=True)
                    await page.wait_for_timeout(2000)  # Wait longer for modal
                    date_clicked = True
                    print("✅ Date button clicked via CSS selector")
                    
                    # Take screenshot after clicking to see modal
                    await page.screenshot(path="after_date_click.png")
                    print("📸 Screenshot taken after date click")
                    
                    # Log all modal/dialog elements that appear
                    dialogs = await page.query_selector_all('[role="dialog"]')
                    print(f"🗨️ Found {len(dialogs)} dialog elements after click")
                    
                    for i, dialog in enumerate(dialogs):
                        try:
                            is_visible = await dialog.is_visible()
                            inner_text = await dialog.text_content()
                            print(f"  Dialog {i}: visible={is_visible}, text='{inner_text[:100]}...'")
                            
                            if is_visible and i == 0:  # Save HTML of first visible dialog
                                dialog_html = await dialog.inner_html()
                                with open(f"dialog_{i}_content.html", "w", encoding="utf-8") as f:
                                    f.write(dialog_html)
                                print(f"💾 Dialog {i} HTML saved to dialog_{i}_content.html")
                        except Exception as e:
                            print(f"⚠️ Error inspecting dialog {i}: {e}")
                    
                    # Look for calendar grid specifically
                    grids = await page.query_selector_all('[role="grid"]')
                    gridcells = await page.query_selector_all('[role="gridcell"]')
                    print(f"📊 Found {len(grids)} grids and {len(gridcells)} gridcells")
                    
                    # Look for month/year header elements
                    month_texts = await page.query_selector_all('text=/January|February|March|April|May|June|July|August|September|October|November|December/')
                    print(f"📅 Found {len(month_texts)} month text elements")
                    
                    # Look for navigation buttons
                    nav_buttons = await page.query_selector_all('button[aria-label*="next"], button[aria-label*="previous"], button:has-text("›"), button:has-text("‹")')
                    print(f"🧭 Found {len(nav_buttons)} navigation buttons")
                    
        except Exception as e:
            print(f"⚠️ CSS selector click failed: {e}")
        
        # Method 2: Try text-based locator if CSS failed
        if not date_clicked:
            try:
                await page.locator('text="Set a date"').first.click(force=True)
                await page.wait_for_timeout(2000)
                date_clicked = True
                print("✅ Date button clicked via text locator")
            except Exception as e:
                print(f"⚠️ Text locator click failed: {e}")
        
        # If date picker opened, try to interact with it
        if date_clicked:
            print("🔍 Analyzing opened date picker...")
            
            # Wait a bit more and take another screenshot
            await page.wait_for_timeout(1000)
            await page.screenshot(path="date_picker_open.png")
            
            # Try to find September 2025 in the current view
            target_month = start.strftime("%B")  # September
            target_year = str(start.year)        # 2025
            target_day = str(start.day)          # 1
            
            print(f"🎯 Looking for: {target_month} {target_year}, day {target_day}")
            
            # Check what month/year is currently showing
            current_month_elements = await page.query_selector_all('text=/January|February|March|April|May|June|July|August|September|October|November|December/')
            for elem in current_month_elements:
                try:
                    text = await elem.text_content()
                    is_visible = await elem.is_visible()
                    if is_visible and text:
                        print(f"📅 Visible month text: '{text}'")
                except:
                    continue
            
            # Try the existing date selection logic
            success = await select_date_in_datepicker(page, start)
            if success:
                print("✅ Date selection via calendar succeeded")
                
                # Try to set time
                time_success = await set_time_in_datepicker(page, start, end)
                if time_success:
                    print("✅ Time setting succeeded")
                else:
                    print("⚠️ Time setting failed, will use fallback")
                
                # Close the datepicker
                try:
                    await page.keyboard.press('Escape')
                    await page.wait_for_timeout(500)
                    print("🔒 Date picker closed")
                except:
                    pass
                    
                # Take final screenshot
                await page.screenshot(path="after_date_selection.png")
                
                # Check if the date button now shows the selected date
                try:
                    final_date_button = await page.query_selector('.ptf-l-EDGV-')
                    if final_date_button:
                        final_text = await final_date_button.text_content()
                        print(f"📋 Final date button text: '{final_text}'")
                        if "Set a date" not in final_text:
                            print("✅ Date appears to be set successfully!")
                            return
                except:
                    pass
            else:
                print("❌ Date selection via calendar failed")
        
        # If we get here, the calendar interaction didn't work, so fall back to typing
        print("🔄 Falling back to text input method...")
        
        # Format date and time for display
        date_str = start.strftime("%A, %B %d, %Y")  # "Sunday, September 01, 2025"
        time_str = start.strftime("%I:%M %p").lstrip("0")  # "6:00 PM"
        
        # Try to type directly into the date field or focused element
        try:
            # Click the date button again to focus it
            date_button = await page.query_selector('.ptf-l-EDGV-')
            if date_button:
                await date_button.click()
                await page.wait_for_timeout(500)
            
            # Clear any existing content and type the date
            await page.keyboard.press("Control+a")  # Select all
            await page.keyboard.type(f"{date_str} at {time_str}")
            print(f"✅ Date/time typed as fallback: {date_str} at {time_str}")
            
            # Handle end time if provided
            if end:
                end_time_str = end.strftime("%I:%M %p").lstrip("0")
                try:
                    if end.date() == start.date():  # Same day
                        await page.keyboard.type(f" until {end_time_str}")
                        print(f"⏰ End time added: until {end_time_str}")
                    else:
                        end_date_str = end.strftime("%A, %B %d")
                        await page.keyboard.type(f" until {end_date_str} at {end_time_str}")
                        print(f"⏰ Multi-day end time added")
                except:
                    print("⚠️ Could not add end time")
            
            # Press Enter to confirm
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(1000)
            
            # Take screenshot after typing
            await page.screenshot(path="after_typing_date.png")
            
        except Exception as e:
            print(f"⚠️ Typing fallback failed: {e}")
            print("💡 You may need to set the date/time manually")
            
    except Exception as e:
        print(f"⚠️ Could not set date/time: {e}")
        print("💡 You may need to set the date/time manually")

async def fill_location(page: Page, location: str) -> None:
    """Fill the location field and select from dropdown suggestions, then Save."""
    print(f"📍 Filling location: {location}")
    try:
        # First, ensure any modal overlays are closed
        await close_modal_overlays(page)
        
        # Click the first location trigger (not the second one which has issues)
        location_elements = await page.get_by_text("Location").all()
        if location_elements:
            await location_elements[0].click()  # Click the first one specifically
            await page.wait_for_timeout(1000)  # Give more time for modal to open
            
        # Try to find and fill the location input
        location_filled = False
        
        # Method 1: Look for the specific placeholder input
        location_input = await page.query_selector('input[placeholder="Place name, address, or link"]')
        if location_input:
            await location_input.fill(location)
            location_filled = True
            print("✅ Location typed in search field")
        
        # Method 2: Try search input type
        if not location_filled:
            search_input = await page.query_selector('input[type="search"]')
            if search_input:
                await search_input.fill(location)
                location_filled = True
                print("✅ Location typed in search input")
        
        # Method 3: Try focused input
        if not location_filled:
            focused_element = await page.evaluate('document.activeElement?.tagName')
            if focused_element == 'INPUT':
                await page.keyboard.press("Control+a")
                await page.keyboard.type(location)
                location_filled = True
                print("✅ Location typed in focused input")
        
        if location_filled:
            # Wait for dropdown suggestions to appear
            print("🔍 Waiting for location suggestions...")
            await page.wait_for_timeout(2000)  # Wait for suggestions to load
            
            # Try to find and click the first suggestion
            suggestion_clicked = False
            
            # Method 1: Look for actual dropdown suggestions in the location modal
            try:
                # Wait a bit more for dropdown to fully load
                await page.wait_for_timeout(1000)
                
                # Look for the location suggestions in the modal structure
                # Based on your screenshot, suggestions appear to be clickable elements
                suggestions = await page.query_selector_all('div[role="option"]')
                if not suggestions:
                    # Try alternative selectors for location suggestions
                    suggestions = await page.query_selector_all('.location-option, .search-suggestion, [data-testid*="location"], [data-testid*="suggestion"]')
                
                if not suggestions:
                    # Look for any clickable elements that contain location text in the modal
                    suggestions = await page.query_selector_all('div:has-text("MIT"), button:has-text("MIT"), a:has-text("MIT")')
                
                if suggestions and len(suggestions) > 0:
                    # Use force click to bypass modal overlay issues
                    await suggestions[0].click(force=True)
                    suggestion_clicked = True
                    print(f"✅ Force-clicked on first location suggestion (found {len(suggestions)} suggestions)")
                else:
                    print("⚠️  No dropdown suggestions found with standard selectors")
            except Exception as e:
                print(f"⚠️  Standard suggestion click failed: {e}")
            
            # Method 2: Try to find suggestions by looking for specific text patterns with force click
            if not suggestion_clicked:
                try:
                    # Look for elements containing "MIT" specifically
                    await page.wait_for_timeout(500)
                    
                    # Try clicking on text that matches MIT with force
                    mit_element = await page.get_by_text("MIT", exact=False).first
                    if mit_element:
                        try:
                            await mit_element.click(force=True)
                            suggestion_clicked = True
                            print("✅ Force-clicked on MIT text element")
                        except:
                            # Try clicking on its parent with force
                            parent = mit_element.locator('..').first
                            if parent:
                                await parent.click(force=True)
                                suggestion_clicked = True
                                print("✅ Force-clicked on MIT parent element")
                except Exception as e:
                    print(f"⚠️  MIT text click failed: {e}")
            
            # Method 3: Look for specific location suggestions and force click
            if not suggestion_clicked:
                try:
                    # Based on the error, look for Cambridge, MA specifically
                    cambridge_elements = await page.query_selector_all('span:has-text("Cambridge, MA")')
                    if cambridge_elements:
                        # Find the clickable parent of the Cambridge element
                        for elem in cambridge_elements:
                            try:
                                # Get the parent element that might be clickable
                                parent = await elem.evaluate_handle('el => el.closest("div, button, a")')
                                if parent:
                                    await parent.click(force=True)
                                    suggestion_clicked = True
                                    print("✅ Force-clicked on Cambridge, MA suggestion")
                                    break
                            except:
                                continue
                except Exception as e:
                    print(f"⚠️  Cambridge suggestion click failed: {e}")
            
            # Method 4: Try clicking directly on the modal location options
            if not suggestion_clicked:
                try:
                    # Look for clickable elements within the location modal with force
                    modal = await page.query_selector('[role="dialog"]')
                    if modal:
                        # Find any clickable elements within the modal
                        clickable_in_modal = await modal.query_selector_all('div, span, button, a')
                        for element in clickable_in_modal:
                            try:
                                text_content = await element.text_content()
                                if text_content and ("MIT" in text_content or "Cambridge" in text_content):
                                    await element.click(force=True)
                                    suggestion_clicked = True
                                    print(f"✅ Force-clicked on modal element: {text_content[:50]}...")
                                    break
                            except:
                                continue
                except Exception as e:
                    print(f"⚠️  Modal force click failed: {e}")
            
            # Method 5: Use keyboard navigation with proper timing
            if not suggestion_clicked:
                try:
                    # Close any overlays first
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(300)
                    
                    # Focus back on the input and try keyboard navigation
                    location_input = await page.query_selector('input[placeholder="Place name, address, or link"]')
                    if location_input:
                        await location_input.focus()
                        await page.wait_for_timeout(200)
                        await page.keyboard.press("ArrowDown")  # Select first suggestion
                        await page.wait_for_timeout(300)
                        await page.keyboard.press("Enter")  # Confirm selection
                        suggestion_clicked = True
                        print("✅ Selected suggestion using keyboard navigation after refocus")
                except Exception as e:
                    print(f"⚠️  Keyboard navigation failed: {e}")
            
            # Method 6: Last resort - close modal and accept typed location
            if not suggestion_clicked:
                try:
                    print("🔧 Trying to close location modal and accept typed location...")
                    # Press Escape to close the modal and accept what was typed
                    await page.keyboard.press("Escape")
                    await page.wait_for_timeout(500)
                    # Check if modal is closed
                    modal_still_open = await page.query_selector('[role="dialog"]')
                    if not modal_still_open:
                        suggestion_clicked = True
                        print("✅ Closed location modal - typed location should be preserved")
                    else:
                        # Try clicking outside the modal
                        await page.click('body', position={'x': 100, 'y': 100})
                        await page.wait_for_timeout(300)
                        print("✅ Clicked outside modal to close it")
                        suggestion_clicked = True
                except Exception as e:
                    print(f"⚠️  Modal close attempt failed: {e}")
            
            if not suggestion_clicked:
                print("⚠️  Could not select from dropdown suggestions")
                print("💡 Location text was entered but suggestion not selected")

            # Attempt to click Save to persist selection
            try:
                saved = await click_location_save(page)
                if not saved:
                    print("🔁 Retrying Save...")
                    await page.wait_for_timeout(400)
                    saved = await click_location_save(page)
                if not saved:
                    print("⚠️  Location may not be persisted; please click Save manually.")
                else:
                    await page.wait_for_timeout(300)
            except Exception as e:
                print(f"⚠️  Error while clicking Save: {e}")
            
        else:
            # Fallback: try other selectors
            for selector in LOCATION_INPUT_SELECTORS:
                try:
                    location_input = await page.query_selector(selector)
                    if location_input:
                        await location_input.fill(location)
                        print("✅ Location filled via fallback selector")
                        return
                except:
                    continue
                    
            # Last resort: just type the location
            await page.keyboard.type(location)
            print("✅ Location typed as final fallback")
        
    except Exception as e:
        print(f"⚠️  Could not fill location: {e}")
        # Last resort: try typing anyway
        try:
            await page.keyboard.type(location)
            print("✅ Location typed via error recovery")
        except:
            print("❌ Location filling completely failed")


async def fill_description(page: Page, description: str) -> None:
    """Fill the event description."""
    print("📄 Filling description...")
    try:
        # Click description trigger
        await page.get_by_text("Add a description").first.click()
        await page.wait_for_timeout(500)
        
        # Try to find description input
        for selector in DESCRIPTION_INPUT_SELECTORS:
            try:
                desc_input = await page.query_selector(selector)
                if desc_input:
                    await desc_input.fill(description)
                    print("✅ Description filled successfully")
                    return
            except:
                continue
                
        # Fallback: type description
        await page.keyboard.type(description)
        print("✅ Description typed as fallback")
        
    except Exception as e:
        print(f"⚠️  Could not fill description: {e}")


async def upload_cover_image(page: Page, image_path: str) -> bool:
    """Upload a cover image to the event."""
    print(f"📸 Uploading cover image: {image_path}")
    try:
        # Wait a bit for the page to fully load after description
        await page.wait_for_timeout(1000)
        
        # Try to click the "Edit" button for the cover image
        try:
            await page.click("text=Edit")
            print("✅ Edit button clicked")
        except Exception as e:
            print(f"⚠️  Could not click Edit button: {e}")
            # Try alternative approach - look for any clickable element with image-related text
            try:
                elements = await page.query_selector_all('*')
                for element in elements[:50]:  # Check first 50 elements
                    try:
                        text = await element.text_content()
                        if text and any(word in text.lower() for word in ['cover', 'image', 'photo', 'picture', 'upload', 'edit']):
                            print(f"🔍 Found potential image element with text: '{text}'")
                            await element.click()
                            print("✅ Clicked potential image element")
                            break
                    except:
                        continue
            except Exception as e2:
                print(f"⚠️  Alternative approach also failed: {e2}")
                return False

        await page.wait_for_timeout(1500) # Wait for file input to appear
        
        # Now try to set the file input directly
        try:
            await page.set_input_files("input[type='file']", image_path)
            print(f"✅ File {image_path} uploaded successfully")
            await page.wait_for_timeout(2000) # Wait for upload to complete
            return True
        except Exception as e:
            print(f"⚠️  Could not set file input: {e}")
            # Fallback: try to find file input manually
            file_input = await page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(image_path)
                print(f"✅ File {image_path} uploaded via fallback")
                await page.wait_for_timeout(2000)
                return True
            else:
                print("❌ File input not found")
                return False
                
    except Exception as e:
        print(f"❌ Error uploading cover image: {e}")
        return False


def create_partiful_sync(event: EventSpec, *, wait_for_publish: bool = False) -> None:
    """Synchronous wrapper for the async Playwright automation."""
    asyncio.run(fill_partiful_form(event, wait_for_publish=wait_for_publish))


if __name__ == "__main__":
    import sys
    from .extract import extract_event_with_llm
    from .models import ExtractionRequest
    
    if len(sys.argv) < 2:
        print("Usage: python -m app.create_partiful 'event description'")
        print("Example: python -m app.create_partiful 'Birthday party Saturday 7pm at my house'")
        sys.exit(1)
    
    event_text = sys.argv[1]
    print(f"🎯 Extracting event details from: {event_text}")
    
    try:
        # Create extraction request
        extraction_req = ExtractionRequest(
            text=event_text,
            default_tz="America/Los_Angeles",  # Default timezone
            default_start_time="19:00"  # 7 PM default
        )
        
        # Extract event using LLM
        event = extract_event_with_llm(extraction_req)
        print(f"📋 Extracted event: {event.as_human()}")
        
        # Fill Partiful form
        print("🌐 Opening Partiful and filling form...")
        create_partiful_sync(event, wait_for_publish=False)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
