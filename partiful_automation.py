import os
import asyncio
from datetime import datetime
from typing import List
from playwright.async_api import async_playwright, Page
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class InviteInfo(BaseModel):
    TitleFont: str = "Classic"
    Title: str
    StartDate: datetime
    EndDate: datetime
    TimeZone: str  # TimezoneStr
    Hosts: List[str]
    Location: str
    MaxCapacity: int
    Cost: float
    GuestCanInviteFriends: bool
    Description: str
    RSVP_Options: str = "Emojis"
    GuestRequireApproval: bool = True

class PartifulAutomator:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.session_file = "partiful_session.json"
    
    async def create_party(self, invite_info: InviteInfo):
        """Main function to automate party creation"""
        async with async_playwright() as p:
            # Launch browser with persistent context
            browser = await p.chromium.launch(headless=self.headless)
            
            # Try to load existing session
            context_options = {}
            if os.path.exists(self.session_file):
                try:
                    context_options["storage_state"] = self.session_file
                    print("Loading existing session...")
                except Exception as e:
                    print(f"Could not load session: {e}")
            
            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            try:
                # Check if already logged in
                await page.goto("https://partiful.com/dashboard", wait_until="domcontentloaded")
                
                # If redirected to login, handle authentication
                if "login" in page.url:
                    await self._handle_login(page)
                    # Save session after successful login
                    await context.storage_state(path=self.session_file)
                
                # Navigate to create page
                print("Navigating to create page...")
                await page.goto("https://partiful.com/create", wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)  # Wait for page to fully load
                
                # Fill out the form
                await self._fill_party_form(page, invite_info)
                
                print("Party creation completed!")
                
            except Exception as e:
                print(f"Error during automation: {e}")
                # Take screenshot for debugging
                await page.screenshot(path="error_screenshot.png")
                raise
            finally:
                await browser.close()
    
    async def _handle_login(self, page: Page):
        """Handle login process"""
        print("Handling login...")
        host_number = os.getenv("HOST_NUMBER")
        
        if not host_number:
            raise ValueError("HOST_NUMBER not found in environment variables")
        
        # Wait for phone input field and fill it
        phone_selector = "input[type='tel'], input[name='phone'], input[placeholder*='phone' i]"
        await page.wait_for_selector(phone_selector, timeout=10000)
        await page.fill(phone_selector, host_number)
        
        # Click submit/continue button
        submit_selectors = [
            "button[type='submit']",
            "button:has-text('Continue')",
            "button:has-text('Send Code')",
            "button:has-text('Login')"
        ]
        
        for selector in submit_selectors:
            try:
                await page.click(selector, timeout=2000)
                break
            except:
                continue
        
        # Handle verification if needed
        await self._handle_verification(page)
        
        # Wait for successful login (redirect to dashboard)
        try:
            await page.wait_for_url("**/dashboard**", timeout=30000)
            print("Login successful!")
        except:
            # Sometimes it might redirect elsewhere, check if we're no longer on login
            if "login" not in page.url:
                print("Login appears successful (not on login page)")
            else:
                raise Exception("Login failed - still on login page")
    
    async def _handle_verification(self, page: Page):
        """Handle 2FA/verification if present"""
        try:
            # Look for verification code input
            verification_selectors = [
                "input[placeholder*='code' i]",
                "input[type='text'][maxlength='6']",
                "input[name='code']"
            ]
            
            for selector in verification_selectors:
                if await page.locator(selector).count() > 0:
                    print("Verification code required. Please enter it manually...")
                    # Wait for user to manually enter code
                    await page.wait_for_function(
                        "() => !document.querySelector('input[placeholder*=\"code\" i], input[type=\"text\"][maxlength=\"6\"], input[name=\"code\"]') || document.querySelector('input[placeholder*=\"code\" i], input[type=\"text\"][maxlength=\"6\"], input[name=\"code\"]').value.length >= 4",
                        timeout=60000
                    )
                    
                    # Auto-submit if code is filled
                    submit_btn = page.locator("button[type='submit'], button:has-text('Verify'), button:has-text('Continue')")
                    if await submit_btn.count() > 0:
                        await submit_btn.first.click()
                    break
        except Exception as e:
            print(f"Verification handling: {e}")
    
    async def _analyze_form_structure(self, page: Page):
        """Debug method to analyze the form structure"""
        print("=== ANALYZING PARTIFUL FORM STRUCTURE ===")
        
        # Wait for form to load
        await page.wait_for_timeout(3000)
        
        # Get all form inputs
        inputs = await page.locator("input").all()
        print(f"\nFound {len(inputs)} input elements:")
        
        for i, input_elem in enumerate(inputs):
            try:
                input_type = await input_elem.get_attribute("type") or "text"
                name = await input_elem.get_attribute("name") or "no-name"
                placeholder = await input_elem.get_attribute("placeholder") or "no-placeholder"
                class_name = await input_elem.get_attribute("class") or "no-class"
                print(f"  Input {i}: type='{input_type}', name='{name}', placeholder='{placeholder}'")
                print(f"    class='{class_name[:100]}...' " if len(class_name) > 100 else f"    class='{class_name}'")
            except Exception as e:
                print(f"  Input {i}: Error reading attributes - {e}")
        
        # Get all textareas
        textareas = await page.locator("textarea").all()
        print(f"\nFound {len(textareas)} textarea elements:")
        
        for i, textarea in enumerate(textareas):
            try:
                name = await textarea.get_attribute("name") or "no-name"
                placeholder = await textarea.get_attribute("placeholder") or "no-placeholder"
                class_name = await textarea.get_attribute("class") or "no-class"
                print(f"  Textarea {i}: name='{name}', placeholder='{placeholder}'")
                print(f"    class='{class_name[:100]}...' " if len(class_name) > 100 else f"    class='{class_name}'")
            except Exception as e:
                print(f"  Textarea {i}: Error reading attributes - {e}")
        
        # Get all select elements
        selects = await page.locator("select").all()
        print(f"\nFound {len(selects)} select elements:")
        
        for i, select in enumerate(selects):
            try:
                name = await select.get_attribute("name") or "no-name"
                class_name = await select.get_attribute("class") or "no-class"
                options = await select.locator("option").all()
                print(f"  Select {i}: name='{name}', options={len(options)}")
                print(f"    class='{class_name[:100]}...' " if len(class_name) > 100 else f"    class='{class_name}'")
            except Exception as e:
                print(f"  Select {i}: Error reading attributes - {e}")
        
        # Get all buttons
        buttons = await page.locator("button").all()
        print(f"\nFound {len(buttons)} button elements:")
        
        for i, button in enumerate(buttons):
            try:
                button_type = await button.get_attribute("type") or "button"
                text_content = await button.text_content() or "no-text"
                class_name = await button.get_attribute("class") or "no-class"
                print(f"  Button {i}: type='{button_type}', text='{text_content.strip()}'")
                print(f"    class='{class_name[:100]}...' " if len(class_name) > 100 else f"    class='{class_name}'")
            except Exception as e:
                print(f"  Button {i}: Error reading attributes - {e}")
        
        # Get form structure
        forms = await page.locator("form").all()
        print(f"\nFound {len(forms)} form elements")
        
        # Look for div elements that might contain form fields (React forms often use divs)
        form_divs = await page.locator("div[data-testid], div[class*='form'], div[class*='field'], div[class*='input']").all()
        print(f"\nFound {len(form_divs)} potential form container divs")
        
        print("=== END FORM ANALYSIS ===\n")

    async def _fill_party_form(self, page: Page, invite_info: InviteInfo):
        """Fill out Partiful's click-to-reveal form fields"""
        print("Filling out Partiful party form...")
        
        # Wait for page to load completely
        await page.wait_for_timeout(3000)
        
        # Handle each field with click-to-reveal pattern
        
        # 1. Title Font Selection first
        await self._select_title_font(page, invite_info.TitleFont)
        await page.wait_for_timeout(500)
        
        # 2. Event Title - click "Untitled Event" to edit
        await self._fill_title_field(page, invite_info.Title)
        await page.wait_for_timeout(500)
        
        # 3. Date/Time - click "Set a date..." to open date picker
        await self._fill_date_field(page, invite_info)
        await page.wait_for_timeout(500)
        
        # 4. Location - click location area to open location picker
        await self._fill_location_field(page, invite_info.Location)
        await page.wait_for_timeout(500)
        
        # 5. Capacity - click the "U..." (Unlimited) field
        await self._fill_capacity_field(page, invite_info.MaxCapacity)
        await page.wait_for_timeout(500)
        
        # 6. Description - click "Add a description of your event"
        await self._fill_description_field(page, invite_info.Description)
        await page.wait_for_timeout(500)
        
        # 7. Settings buttons
        await self._handle_settings_buttons(page, invite_info)
        
        # 8. RSVP Options
        await self._select_rsvp_option(page, invite_info.RSVP_Options)
        
        print("Form filled successfully!")
        await page.screenshot(path="partiful_form_filled.png")
    
    async def _fill_title_field(self, page: Page, title: str):
        """Click 'Untitled Event' and edit the title"""
        try:
            # Look for the title element to click
            title_selectors = [
                "h1:has-text('Untitled Event')",
                "div:has-text('Untitled Event')",
                "span:has-text('Untitled Event')",
                # More specific from the analysis
                ".EditableEventTitle_input__",  # Partial class match
                "span:has-text('(*Required) Event Title')"
            ]
            
            for selector in title_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        await element.click()
                        await page.wait_for_timeout(1000)
                        
                        # After clicking, look for input field or contenteditable
                        await self._type_in_active_field(page, title)
                        
                        # Press Enter to confirm (as mentioned in analysis)
                        await page.keyboard.press("Enter")
                        
                        print(f"✓ Set title: {title}")
                        return True
                except Exception as e:
                    continue
                    
            print("✗ Could not set title")
            return False
            
        except Exception as e:
            print(f"Error setting title: {e}")
            return False
    
    async def _fill_date_field(self, page: Page, invite_info: InviteInfo):
        """Click 'Set a date...' and handle date picker interface"""
        try:
            # Click to open date picker
            date_triggers = [
                "div:has-text('Set a date...')",
                "span:has-text('Set a date...')",
                "div:has-text('(Optional) Event Date')",
                # From analysis
                ".EditableEventDate_",
                ".EditableEventDetails_"
            ]
            
            for selector in date_triggers:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        await element.click()
                        await page.wait_for_timeout(1500)  # Wait for date picker to appear
                        
                        # Now handle the date picker interface
                        success = await self._handle_date_picker(page, invite_info)
                        if success:
                            return True
                            
                except Exception as e:
                    continue
            
            print("✗ Could not open date picker")
            return False
            
        except Exception as e:
            print(f"Error with date field: {e}")
            return False
    
    async def _handle_date_picker(self, page: Page, invite_info: InviteInfo):
        """Handle the complex date picker UI that appears after clicking"""
        try:
            await page.wait_for_timeout(1000)  # Wait for picker to load
            
            # Strategy 1: Look for date input fields
            date_inputs = await page.locator("input[type='date'], input[type='datetime-local']").all()
            if date_inputs:
                date_str = invite_info.StartDate.strftime("%Y-%m-%d")
                await date_inputs[0].fill(date_str)
                print(f"✓ Set date via input: {date_str}")
                
                # Handle time if there's a time input
                time_inputs = await page.locator("input[type='time']").all()
                if time_inputs:
                    time_str = invite_info.StartDate.strftime("%H:%M")
                    await time_inputs[0].fill(time_str)
                    print(f"✓ Set time: {time_str}")
                
                return True
            
            # Strategy 2: Handle calendar grid (click on date)
            calendar_days = await page.locator("[role='button']:has-text('" + str(invite_info.StartDate.day) + "')").all()
            if calendar_days:
                # Find the correct day button (might need to navigate months)
                await calendar_days[0].click()
                await page.wait_for_timeout(500)
                
                # After selecting date, might need to set time
                await self._set_time_in_picker(page, invite_info.StartDate)
                print(f"✓ Set date via calendar: {invite_info.StartDate.strftime('%m/%d/%Y')}")
                return True
            
            # Strategy 3: Type directly in contenteditable or input
            await page.keyboard.type(invite_info.StartDate.strftime("%m/%d/%Y %I:%M %p"))
            await page.keyboard.press("Enter")
            print(f"✓ Typed date directly: {invite_info.StartDate.strftime('%m/%d/%Y %I:%M %p')}")
            return True
            
        except Exception as e:
            print(f"Error in date picker: {e}")
            return False
    
    async def _set_time_in_picker(self, page: Page, datetime_obj):
        """Set time in time picker interface"""
        try:
            # Look for time-related inputs or buttons
            time_selectors = [
                "input[placeholder*='time' i]",
                "button:has-text('AM')",
                "button:has-text('PM')",
                "select[name*='hour']",
                "select[name*='minute']"
            ]
            
            time_str = datetime_obj.strftime("%I:%M %p")
            
            for selector in time_selectors:
                element = page.locator(selector).first
                if await element.count() > 0:
                    if "input" in selector:
                        await element.fill(datetime_obj.strftime("%H:%M"))
                    elif "AM" in selector or "PM" in selector:
                        period = datetime_obj.strftime("%p")
                        if period in await element.text_content():
                            await element.click()
                    break
            
            print(f"✓ Set time: {time_str}")
            
        except Exception as e:
            print(f"Time setting error: {e}")
    
    async def _fill_location_field(self, page: Page, location: str):
        """Click location area and handle location picker/search"""
        try:
            location_triggers = [
                "div:has-text('Location')",
                "span:has-text('Location')",
                "div:has-text('(Optional) Location')",
                # More specific
                ".EditableEventLocation_",
                ".EditableEventDetails_ div:has-text('Location')"
            ]
            
            for selector in location_triggers:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        await element.click()
                        await page.wait_for_timeout(1500)  # Wait for location picker
                        
                        # Handle location search/input
                        success = await self._handle_location_picker(page, location)
                        if success:
                            return True
                            
                except Exception as e:
                    continue
            
            print("✗ Could not open location picker")
            return False
            
        except Exception as e:
            print(f"Error with location: {e}")
            return False
    
    async def _handle_location_picker(self, page: Page, location: str):
        """Handle location search interface"""
        try:
            await page.wait_for_timeout(1000)
            
            # Look for location input/search field
            location_inputs = [
                "input[placeholder*='location' i]",
                "input[placeholder*='address' i]",
                "input[placeholder*='search' i]",
                "input[type='search']",
                "[contenteditable='true']"  # Might be contenteditable
            ]
            
            for selector in location_inputs:
                element = page.locator(selector).first
                if await element.count() > 0:
                    await element.click()
                    await element.fill(location)
                    await page.wait_for_timeout(1000)  # Wait for suggestions
                    
                    # Look for and click first suggestion or press Enter
                    suggestions = await page.locator("[role='option'], .suggestion, [data-testid*='suggestion']").all()
                    if suggestions:
                        await suggestions[0].click()
                        print(f"✓ Selected location suggestion: {location}")
                    else:
                        await page.keyboard.press("Enter")
                        print(f"✓ Set location: {location}")
                    
                    return True
            
            # Fallback: type directly
            await page.keyboard.type(location)
            await page.keyboard.press("Enter")
            print(f"✓ Typed location: {location}")
            return True
            
        except Exception as e:
            print(f"Location picker error: {e}")
            return False
    
    async def _fill_capacity_field(self, page: Page, capacity: int):
        """Click capacity field (the 'U...' element) and set max capacity"""
        try:
            # From analysis: "U..." text with EditableEventCapacity_input class
            capacity_triggers = [
                ".EditableEventCapacity_input__1tXoG",
                "div:has-text('U...')",
                "div:has-text('Unlimited spots')",
                "div:has-text('(Optional) Max Capacity')"
            ]
            
            for selector in capacity_triggers:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        await element.click()
                        await page.wait_for_timeout(1000)
                        
                        # Clear any existing content and type capacity
                        await page.keyboard.press("Control+a")
                        await page.keyboard.type(str(capacity))
                        await page.keyboard.press("Enter")
                        
                        print(f"✓ Set capacity: {capacity}")
                        return True
                        
                except Exception as e:
                    continue
            
            print("✗ Could not set capacity")
            return False
            
        except Exception as e:
            print(f"Error setting capacity: {e}")
            return False
    
    async def _fill_description_field(self, page: Page, description: str):
        """Click description area and fill description"""
        try:
            # From analysis: "Add a description of your event"
            description_triggers = [
                ".EditableEventDescription_input__S8lha",
                "div:has-text('Add a description of your event')",
                "div:has-text('(Optional) Description')"
            ]
            
            for selector in description_triggers:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        await element.click()
                        await page.wait_for_timeout(1000)
                        
                        # Type description (might support multi-line)
                        await self._type_in_active_field(page, description)
                        
                        # The analysis mentions "Press Shift⇧ + Enter⏎ to skip" - so maybe Shift+Enter to confirm?
                        await page.keyboard.press("Shift+Enter")
                        
                        print(f"✓ Set description: {description[:50]}...")
                        return True
                        
                except Exception as e:
                    continue
            
            print("✗ Could not set description")
            return False
            
        except Exception as e:
            print(f"Error setting description: {e}")
            return False
    
    async def _type_in_active_field(self, page: Page, text: str):
        """Type text in whatever field is currently active/focused"""
        # Clear existing content
        await page.keyboard.press("Control+a")
        # Type new content
        await page.keyboard.type(text)
        # Small delay
        await page.wait_for_timeout(200)
    
    async def _select_title_font(self, page: Page, font: str):
        """Select title font from the button options"""
        try:
            font_button = page.locator(f"button:has-text('{font}')")
            if await font_button.count() > 0:
                await font_button.click()
                print(f"✓ Selected title font: {font}")
            else:
                print(f"✗ Could not find title font: {font}")
        except Exception as e:
            print(f"Error selecting title font: {e}")
    
    async def _fill_contenteditable_field(self, page: Page, field_type: str, value: str):
        """Fill contentEditable fields by clicking and typing"""
        selectors_map = {
            "title": [
                "div[contenteditable='true']:has-text('Add a title')",
                "div[contenteditable='true']:has-text('Party name')",
                "div[contenteditable='true']:has-text('Event name')",
                "[contenteditable='true']",  # Fallback to first contenteditable
                "div:has-text('Add a title')",  # Click trigger
                "div:has-text('Party name')",
                "div:has-text('Event name')"
            ],
            "location": [
                "div[contenteditable='true']:has-text('Where')",
                "div[contenteditable='true']:has-text('Location')",
                "div[contenteditable='true']:has-text('Address')",
                "div:has-text('Where')",
                "div:has-text('Location')",
                "div:has-text('Add location')"
            ],
            "description": [
                "div[contenteditable='true']:has-text('Description')",
                "div[contenteditable='true']:has-text('Add a description')",
                "div:has-text('Add a description')",
                "div:has-text('Description')",
                "div:has-text('Tell guests about your event')"
            ]
        }
        
        selectors = selectors_map.get(field_type, [])
        
        for selector in selectors:
            try:
                element = page.locator(selector).first
                if await element.count() > 0:
                    # Click to focus
                    await element.click()
                    await page.wait_for_timeout(500)
                    
                    # Clear any existing content
                    await page.keyboard.press("Control+a")
                    
                    # Type the new value
                    await page.keyboard.type(value)
                    
                    print(f"✓ Filled {field_type}: {value}")
                    return True
            except Exception as e:
                continue
                
        print(f"✗ Could not find {field_type} field")
        return False
    
    async def _fill_date_time_fields(self, page: Page, invite_info: InviteInfo):
        """Handle date and time fields - likely click-to-edit"""
        try:
            # Look for date/time related clickable elements
            date_triggers = [
                "div:has-text('When')",
                "div:has-text('Date')",
                "div:has-text('Add date')",
                "div:has-text('Select date')"
            ]
            
            for selector in date_triggers:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        await element.click()
                        await page.wait_for_timeout(1000)
                        
                        # Now look for date input that might have appeared
                        date_inputs = [
                            "input[type='date']",
                            "input[type='datetime-local']",
                            "[contenteditable='true']"
                        ]
                        
                        date_str = invite_info.StartDate.strftime("%m/%d/%Y")
                        time_str = invite_info.StartDate.strftime("%I:%M %p")
                        
                        for date_input_selector in date_inputs:
                            date_input = page.locator(date_input_selector).first
                            if await date_input.count() > 0:
                                await date_input.fill(f"{date_str} {time_str}")
                                print(f"✓ Set date/time: {date_str} {time_str}")
                                return True
                        
                        # If no input found, try typing directly
                        await page.keyboard.type(f"{date_str} {time_str}")
                        print(f"✓ Typed date/time: {date_str} {time_str}")
                        return True
                        
                except Exception as e:
                    continue
            
            print("✗ Could not set date/time")
            return False
            
        except Exception as e:
            print(f"Error setting date/time: {e}")
            return False
    
    async def _select_rsvp_option(self, page: Page, rsvp_option: str):
        """Select RSVP option (Emojis, etc.)"""
        try:
            if "emoji" in rsvp_option.lower():
                emoji_button = page.locator("button:has-text('👍 Emojis')")
                if await emoji_button.count() > 0:
                    await emoji_button.click()
                    print("✓ Selected Emoji RSVP option")
                    return True
            
            # Try to find other RSVP options
            rsvp_button = page.locator(f"button:has-text('{rsvp_option}')")
            if await rsvp_button.count() > 0:
                await rsvp_button.click()
                print(f"✓ Selected RSVP option: {rsvp_option}")
                return True
                
            print(f"✗ Could not find RSVP option: {rsvp_option}")
            return False
            
        except Exception as e:
            print(f"Error selecting RSVP option: {e}")
            return False
    
    async def _handle_settings_buttons(self, page: Page, invite_info: InviteInfo):
        """Handle settings buttons like 'Require Guest Approval'"""
        try:
            # Guest approval setting
            if invite_info.GuestRequireApproval:
                approval_button = page.locator("button:has-text('Require Guest Approval')")
                if await approval_button.count() > 0:
                    # Check if it's already selected (might have different class)
                    class_name = await approval_button.get_attribute("class")
                    if "selected" not in class_name.lower():  # Adjust based on actual classes
                        await approval_button.click()
                        print("✓ Enabled guest approval requirement")
            
            # Guest can invite friends (look for related button)
            if invite_info.GuestCanInviteFriends:
                invite_friends_selectors = [
                    "button:has-text('Guest can invite')",
                    "button:has-text('Allow guests to invite')",
                    "button:has-text('Invite friends')"
                ]
                
                for selector in invite_friends_selectors:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        await element.click()
                        print("✓ Enabled guests can invite friends")
                        break
            
        except Exception as e:
            print(f"Error handling settings: {e}")
    
    async def _fill_additional_fields(self, page: Page, invite_info: InviteInfo):
        """Fill capacity and other additional fields"""
        try:
            # Capacity - might be in a settings panel or additional options
            if invite_info.MaxCapacity > 0:
                # Look for capacity-related buttons or fields
                capacity_triggers = [
                    "button:has-text('Capacity')",
                    "button:has-text('Guest limit')",
                    "button:has-text('Max guests')",
                    "div:has-text('Capacity')",
                    "div:has-text('Guest limit')"
                ]
                
                for selector in capacity_triggers:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        await element.click()
                        await page.wait_for_timeout(500)
                        
                        # Look for input that appeared
                        await page.keyboard.type(str(invite_info.MaxCapacity))
                        print(f"✓ Set capacity: {invite_info.MaxCapacity}")
                        break
            
        except Exception as e:
            print(f"Error filling additional fields: {e}")
    
    async def _fill_field_multiple_selectors(self, page: Page, selectors: list, value: str):
        """Try multiple selectors until one works"""
        for selector in selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, value)
                    print(f"✓ Filled '{selector}' with: {value}")
                    return True
            except Exception as e:
                continue
        print(f"✗ Could not find field for value: {value}")
        return False
    
    async def _handle_toggle(self, page: Page, label_text: str, enabled: bool):
        """Handle modern toggle switches by label text"""
        try:
            # Look for toggle by associated label text
            toggle_selectors = [
                f"label:has-text('{label_text}') input",
                f"div:has-text('{label_text}') input[type='checkbox']",
                f"div:has-text('{label_text}') button[role='switch']",
                f"span:has-text('{label_text}') ~ input",
                f"text='{label_text}' >> .. >> input"
            ]
            
            for selector in toggle_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        if enabled:
                            await page.check(selector)
                        else:
                            await page.uncheck(selector)
                        print(f"✓ Set toggle '{label_text}' to: {enabled}")
                        return True
                except:
                    continue
                    
            print(f"✗ Could not find toggle for: {label_text}")
            return False
        except Exception as e:
            print(f"Error with toggle {label_text}: {e}")
            return False
    
    async def _click_button_multiple_selectors(self, page: Page, selectors: list):
        """Try multiple button selectors until one works"""
        for selector in selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.click(selector)
                    print(f"✓ Clicked button: {selector}")
                    return True
            except Exception as e:
                continue
        print("✗ Could not find submit button")
        return False
    
    async def _fill_field(self, page: Page, selector: str, value: str):
        """Helper to fill form fields with error handling"""
        try:
            selectors = selector.split(", ")
            for sel in selectors:
                if await page.locator(sel.strip()).count() > 0:
                    await page.fill(sel.strip(), value)
                    print(f"Filled field {sel.strip()} with: {value}")
                    return
            print(f"Could not find field with selector: {selector}")
        except Exception as e:
            print(f"Error filling field {selector}: {e}")
    
    async def _handle_dropdown(self, page: Page, selector: str, value: str):
        """Helper to handle dropdown selections"""
        try:
            if await page.locator(selector).count() > 0:
                await page.select_option(selector, value)
                print(f"Selected {value} in dropdown {selector}")
        except Exception as e:
            print(f"Error with dropdown {selector}: {e}")
    
    async def _set_checkbox(self, page: Page, selector: str, checked: bool):
        """Helper to set checkbox states"""
        try:
            selectors = selector.split(", ")
            for sel in selectors:
                if await page.locator(sel.strip()).count() > 0:
                    if checked:
                        await page.check(sel.strip())
                    else:
                        await page.uncheck(sel.strip())
                    print(f"Set checkbox {sel.strip()} to: {checked}")
                    return
        except Exception as e:
            print(f"Error with checkbox {selector}: {e}")

# Usage example
async def main():
    # Example party data
    party_data = InviteInfo(
        Title="My Awesome Party",
        StartDate=datetime(2024, 12, 15, 19, 0),  # 7:00 PM
        EndDate=datetime(2024, 12, 15, 23, 0),    # 11:00 PM
        TimeZone="America/New_York",
        Hosts=["John Doe", "Jane Smith"],
        Location="123 Party Street, Fun City",
        MaxCapacity=50,
        Cost=0.0,
        GuestCanInviteFriends=True,
        Description="Come join us for an amazing celebration!",
        GuestRequireApproval=False
    )
    
    automator = PartifulAutomator(headless=False)  # Set to True for production
    await automator.create_party(party_data)

if __name__ == "__main__":
    asyncio.run(main())