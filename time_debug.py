#!/usr/bin/env python3
"""
Debug script to analyze time picker HTML structure on Partiful
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def debug_time_picker():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        # Navigate to Partiful create page
        print("🌐 Navigating to Partiful...")
        await page.goto("https://partiful.com/create")
        await page.wait_for_load_state('networkidle')
        
        # Wait for page to be ready
        await asyncio.sleep(3)
        
        print("📅 Looking for date/time elements...")
        
        # Look for date button first
        try:
            date_elements = await page.query_selector_all('[class*="date"], [class*="Date"], button[data-testid*="date"]')
            print(f"Found {len(date_elements)} potential date elements")
            
            for i, elem in enumerate(date_elements):
                text = await elem.text_content()
                classes = await elem.get_attribute('class')
                print(f"  Date element {i}: '{text}' - classes: {classes}")
        except Exception as e:
            print(f"Error finding date elements: {e}")
        
        # Look for time elements
        try:
            time_elements = await page.query_selector_all('[class*="time"], [class*="Time"], input[type="time"], select[name*="time"]')
            print(f"Found {len(time_elements)} potential time elements")
            
            for i, elem in enumerate(time_elements):
                text = await elem.text_content()
                classes = await elem.get_attribute('class')
                tag = await elem.evaluate('el => el.tagName')
                print(f"  Time element {i}: '{text}' - tag: {tag}, classes: {classes}")
        except Exception as e:
            print(f"Error finding time elements: {e}")
            
        # Try to click the date button to open calendar
        try:
            print("\n🎯 Clicking date button to see if time fields appear...")
            date_selector = ".ptf-l-EDGV-"  # Based on previous debug
            await page.click(date_selector)
            await asyncio.sleep(2)
            
            # After clicking date, look for time elements again
            print("📝 Looking for time elements after opening date picker...")
            time_elements = await page.query_selector_all('[class*="time"], [class*="Time"], input[type="time"], select[name*="time"], button[class*="time"]')
            print(f"Found {len(time_elements)} time elements after opening date picker")
            
            for i, elem in enumerate(time_elements):
                text = await elem.text_content()
                classes = await elem.get_attribute('class')
                tag = await elem.evaluate('el => el.tagName')
                value = await elem.get_attribute('value') if tag.lower() == 'input' else None
                print(f"  Time element {i}: '{text}' - tag: {tag}, classes: {classes}, value: {value}")
                
        except Exception as e:
            print(f"Error clicking date or finding time elements: {e}")
        
        # Let's also look for any dropdown/select elements
        try:
            print("\n🔍 Looking for dropdown/select elements...")
            select_elements = await page.query_selector_all('select, [role="combobox"], [role="listbox"]')
            print(f"Found {len(select_elements)} select/dropdown elements")
            
            for i, elem in enumerate(select_elements):
                text = await elem.text_content()
                classes = await elem.get_attribute('class')
                tag = await elem.evaluate('el => el.tagName')
                name = await elem.get_attribute('name')
                print(f"  Select element {i}: '{text}' - tag: {tag}, name: {name}, classes: {classes}")
        except Exception as e:
            print(f"Error finding select elements: {e}")
        
        # Save full page HTML for analysis
        print("\n💾 Saving page HTML for analysis...")
        html_content = await page.content()
        with open("time_picker_debug.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✅ HTML saved to time_picker_debug.html")
        
        print("\n⏳ Keeping browser open for manual inspection...")
        print("Press Ctrl+C when you're done inspecting the page")
        
        try:
            await asyncio.sleep(300)  # Keep open for 5 minutes
        except KeyboardInterrupt:
            print("\n👋 Closing browser...")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_time_picker())
