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