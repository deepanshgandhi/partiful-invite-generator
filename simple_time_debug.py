#!/usr/bin/env python3
"""
Simple debug to capture the date/time picker structure
"""
import asyncio
from playwright.async_api import async_playwright

async def capture_time_structure():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()
        
        print("🌐 Going to Partiful...")
        await page.goto("https://partiful.com/e/new")
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)
        
        print("📅 Clicking date button...")
        try:
            # Click the date button to open the picker
            await page.click(".ptf-l-EDGV-")
            await asyncio.sleep(2)
            
            # Save HTML after opening date picker
            html = await page.content()
            with open("date_time_picker_open.html", "w") as f:
                f.write(html)
                
            print("✅ Saved HTML to date_time_picker_open.html")
            
            # Look for time-related elements
            print("\n🔍 Searching for time elements...")
            
            # Check for input fields
            inputs = await page.query_selector_all('input')
            print(f"Found {len(inputs)} input elements:")
            for i, inp in enumerate(inputs):
                tag_name = await inp.evaluate('el => el.tagName')
                input_type = await inp.get_attribute('type')
                placeholder = await inp.get_attribute('placeholder')
                name = await inp.get_attribute('name')
                classes = await inp.get_attribute('class')
                value = await inp.get_attribute('value')
                print(f"  Input {i}: type='{input_type}', placeholder='{placeholder}', name='{name}', value='{value}'")
                print(f"    classes: {classes}")
            
            # Look for any elements with "time" in text or attributes
            print("\n⏰ Looking for elements containing 'time'...")
            time_elements = await page.evaluate('''
                () => {
                    const elements = [];
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_ELEMENT,
                        null,
                        false
                    );
                    
                    let node;
                    while (node = walker.nextNode()) {
                        const text = node.textContent.toLowerCase();
                        const className = node.className || '';
                        const placeholder = node.placeholder || '';
                        
                        if (text.includes('time') || className.includes('time') || placeholder.includes('time')) {
                            elements.push({
                                tagName: node.tagName,
                                textContent: node.textContent.trim(),
                                className: className,
                                placeholder: placeholder,
                                type: node.type || '',
                                name: node.name || ''
                            });
                        }
                    }
                    return elements;
                }
            ''')
            
            for i, elem in enumerate(time_elements):
                print(f"  Time element {i}: {elem['tagName']} - '{elem['textContent']}'")
                print(f"    class: {elem['className']}, placeholder: {elem['placeholder']}")
                
            print(f"\n🎯 Keeping browser open - check the page manually!")
            print("Press Ctrl+C when done...")
            await asyncio.sleep(120)  # 2 minutes
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_time_structure())
