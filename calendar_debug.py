#!/usr/bin/env python3
"""
Focused script to capture the calendar HTML/CSS at the exact moment it's open.
"""

import asyncio
from playwright.async_api import async_playwright

async def debug_calendar_modal():
    """Debug the calendar modal structure when it's actually open."""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=500)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("🌐 Loading Partiful...")
        await page.goto("https://partiful.com/create", timeout=15000)
        await page.wait_for_load_state("networkidle", timeout=10000)
        
        # Close any initial modal overlays
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(500)
        except:
            pass
            
        print("🖱️ Clicking date button...")
        date_button = await page.query_selector('.ptf-l-EDGV-')
        if not date_button:
            print("❌ Date button not found!")
            await browser.close()
            return
            
        await date_button.click(force=True)
        await page.wait_for_timeout(2000)  # Wait for calendar to fully load
        
        print("📸 Taking screenshot of open calendar...")
        await page.screenshot(path="calendar_open.png", full_page=True)
        
        print("🔍 Analyzing calendar structure...")
        
        # Find all elements that might be part of the calendar
        grids = await page.query_selector_all('[role="grid"]')
        gridcells = await page.query_selector_all('[role="gridcell"]')
        dialogs = await page.query_selector_all('[role="dialog"]')
        
        print(f"📊 Found: {len(grids)} grids, {len(gridcells)} gridcells, {len(dialogs)} dialogs")
        
        # Save the calendar modal HTML
        if dialogs:
            dialog_html = await dialogs[0].inner_html()
            with open("calendar_modal.html", "w", encoding="utf-8") as f:
                f.write(dialog_html)
            print("💾 Calendar modal HTML saved to calendar_modal.html")
        
        # Look for navigation buttons
        nav_selectors = [
            'button[aria-label*="next"]',
            'button[aria-label*="Next"]', 
            'button[aria-label*="previous"]',
            'button[aria-label*="Previous"]',
            'button:has-text("›")',
            'button:has-text("‹")',
            'button:has-text(">")',
            'button:has-text("<")',
            '[class*="next"]',
            '[class*="prev"]',
            '[class*="arrow"]'
        ]
        
        for selector in nav_selectors:
            elements = await page.query_selector_all(selector)
            if elements:
                print(f"🧭 Found {len(elements)} elements with selector: {selector}")
                for i, elem in enumerate(elements):
                    try:
                        text = await elem.text_content()
                        aria_label = await elem.get_attribute('aria-label')
                        class_name = await elem.get_attribute('class')
                        is_visible = await elem.is_visible()
                        print(f"  Nav {i}: text='{text}', aria-label='{aria_label}', class='{class_name}', visible={is_visible}")
                    except Exception as e:
                        print(f"  Nav {i}: Error getting info - {e}")
        
        # Look for month/year text specifically
        month_year_selectors = [
            'text=/August|September|October|November|December|January|February|March|April|May|June|July/',
            'text=/2024|2025|2026/',
            '[class*="month"]',
            '[class*="year"]',
            '[class*="header"]'
        ]
        
        for selector in month_year_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"📅 Found {len(elements)} elements with selector: {selector}")
                    for i, elem in enumerate(elements[:3]):  # Only show first 3
                        try:
                            text = await elem.text_content()
                            is_visible = await elem.is_visible()
                            tag_name = await elem.evaluate('el => el.tagName')
                            class_name = await elem.get_attribute('class')
                            if is_visible and text and text.strip():
                                print(f"  Month/Year {i}: '{text.strip()}' (tag: {tag_name}, class: {class_name})")
                        except Exception as e:
                            print(f"  Month/Year {i}: Error - {e}")
            except Exception as e:
                print(f"⚠️ Error with selector {selector}: {e}")
        
        # Look for day cells
        day_selectors = [
            '[role="gridcell"]',
            'button[role="gridcell"]',
            '[class*="day"]',
            'button:has-text("1")',
            'button:has-text("15")',
            'button:has-text("31")'
        ]
        
        for selector in day_selectors:
            try:
                elements = await page.query_selector_all(selector)
                if elements:
                    print(f"📆 Found {len(elements)} day elements with selector: {selector}")
                    # Show a few examples
                    for i, elem in enumerate(elements[:5]):
                        try:
                            text = await elem.text_content()
                            is_visible = await elem.is_visible()
                            aria_label = await elem.get_attribute('aria-label')
                            if is_visible and text and text.strip():
                                print(f"  Day {i}: '{text.strip()}' (aria-label: {aria_label})")
                        except:
                            continue
            except Exception as e:
                print(f"⚠️ Error with day selector {selector}: {e}")
        
        # Save full page HTML while calendar is open
        html_content = await page.content()
        with open("calendar_page_full.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("💾 Full page HTML saved to calendar_page_full.html")
        
        print("\n✅ Analysis complete! Check the saved files:")
        print("  - calendar_open.png (screenshot)")
        print("  - calendar_modal.html (modal HTML)")
        print("  - calendar_page_full.html (full page HTML)")
        
        print("\n⏸️ Pausing so you can manually inspect the calendar...")
        print("Press Enter to close browser...")
        input()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_calendar_modal())
