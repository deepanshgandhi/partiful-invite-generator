#!/usr/bin/env python3
"""
Debug script to analyze Partiful's date picker behavior step by step.
"""

import asyncio
import json
from playwright.async_api import async_playwright

async def debug_date_picker():
    """Debug the date picker interaction step by step."""
    
    async with async_playwright() as p:
        # Launch browser in headful mode so we can see what's happening
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🌐 Loading Partiful create page...")
        await page.goto("https://partiful.com/create", timeout=15000)
        await page.wait_for_load_state("networkidle", timeout=10000)
        
        print("📸 Taking initial screenshot...")
        await page.screenshot(path="partiful_initial.png", full_page=True)
        
        # Close any modal overlays first
        try:
            modal = await page.query_selector('[role="dialog"].legacy-modal-overlay')
            if modal:
                print("🔄 Closing initial modal overlay...")
                await page.keyboard.press("Escape")
                await page.wait_for_timeout(500)
        except:
            pass
            
        print("🔍 Looking for date button...")
        
        # Find the date button element
        date_button = await page.query_selector('.ptf-l-EDGV-')
        if date_button:
            print("✅ Found date button with CSS selector")
            
            # Get button text and attributes
            button_text = await date_button.text_content()
            print(f"📝 Button text: '{button_text}'")
            
            # Get button HTML
            button_html = await date_button.inner_html()
            print(f"🏷️ Button HTML: {button_html}")
            
            # Check if button is visible and clickable
            is_visible = await date_button.is_visible()
            is_enabled = await date_button.is_enabled()
            print(f"👁️ Visible: {is_visible}, Enabled: {is_enabled}")
            
            # Get bounding box
            box = await date_button.bounding_box()
            print(f"📐 Bounding box: {box}")
            
        else:
            print("❌ Date button not found with CSS selector")
            
        # Try alternative selectors
        alt_selectors = [
            'text="Set a date"',
            '[class*="EDGV"]',
            'time[class*="V4zs2"] div',
            '.dtstart div'
        ]
        
        for selector in alt_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.text_content()
                    print(f"🎯 Found with selector '{selector}': '{text}'")
            except Exception as e:
                print(f"⚠️ Selector '{selector}' failed: {e}")
        
        print("\n🖱️ Attempting to click date button...")
        
        try:
            # Click the date button
            if date_button:
                await date_button.click(force=True)
                print("✅ Date button clicked")
                
                # Wait for any modal or popup to appear
                await page.wait_for_timeout(2000)
                
                print("📸 Taking screenshot after click...")
                await page.screenshot(path="partiful_after_date_click.png", full_page=True)
                
                # Check for calendar modal
                modal_selectors = [
                    '[role="dialog"]',
                    '.calendar',
                    '[class*="Calendar"]',
                    '[class*="DatePicker"]',
                    '[class*="Modal"]'
                ]
                
                calendar_found = False
                for selector in modal_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"🗓️ Found {len(elements)} elements with selector '{selector}'")
                            for i, elem in enumerate(elements):
                                text = await elem.text_content()
                                html = await elem.inner_html()
                                is_visible = await elem.is_visible()
                                print(f"  Element {i}: visible={is_visible}, text='{text[:100]}...'")
                                if i == 0:  # Save HTML of first element for inspection
                                    with open(f"calendar_element_{selector.replace('[', '').replace(']', '').replace('=', '_').replace('"', '')}.html", "w") as f:
                                        f.write(html)
                            calendar_found = True
                    except Exception as e:
                        print(f"⚠️ Selector '{selector}' error: {e}")
                
                if not calendar_found:
                    print("❌ No calendar modal found after clicking")
                
                # Look for specific date navigation elements
                nav_selectors = [
                    'button[aria-label*="Next"]',
                    'button[aria-label*="Previous"]',
                    'button:has-text("›")',
                    'button:has-text("‹")',
                    '[class*="next"]',
                    '[class*="prev"]'
                ]
                
                for selector in nav_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"🧭 Found {len(elements)} navigation elements with '{selector}'")
                    except:
                        pass
                
                # Look for grid/calendar structure
                grid_selectors = [
                    '[role="grid"]',
                    '[role="gridcell"]',
                    'table',
                    '[class*="grid"]',
                    '[class*="day"]'
                ]
                
                for selector in grid_selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements:
                            print(f"📅 Found {len(elements)} grid elements with '{selector}'")
                    except:
                        pass
                
                # Save full page HTML after click
                html_content = await page.content()
                with open("partiful_after_click_full.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("💾 Full HTML saved to partiful_after_click_full.html")
                
        except Exception as e:
            print(f"❌ Error clicking date button: {e}")
        
        print("\n⏸️ Pausing for manual inspection... Press Enter to continue")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_date_picker())
