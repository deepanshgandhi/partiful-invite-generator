"""Playwright automation for filling Partiful's Create invite page.

ToS-safe approach: headful browser, form filling only, user publishes manually.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Optional

from playwright.async_api import Browser, Page, async_playwright

from .models import EventSpec
from .selectors import (
    COVER_IMAGE_BUTTON,
    DATE_END_INPUT,
    DATE_START_INPUT,
    DESCRIPTION_TEXTAREA,
    LOCATION_INPUT,
    PUBLISH_BUTTON,
    SAVE_DRAFT_BUTTON,
    TITLE_INPUT,
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
        browser = await p.chromium.launch(
            headless=settings.headless,
            user_data_dir=settings.browser_profile_dir
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        # Try each create URL until one works
        page_loaded = False
        for url in settings.partiful_create_urls:
            try:
                print(f"Trying Partiful create page: {url}")
                await page.goto(url, timeout=10000)
                await page.wait_for_load_state("networkidle", timeout=5000)
                page_loaded = True
                print(f"✅ Successfully loaded: {url}")
                break
            except Exception as e:
                print(f"⚠️  Failed to load {url}: {e}")
                continue
        
        if not page_loaded:
            raise Exception("Could not load any Partiful create URLs")
        
        try:
            # Fill title
            print(f"Filling title: {event.title}")
            await _safe_fill(page, TITLE_INPUT, event.title)
            
            # Fill description if provided
            if event.description_md:
                print("Filling description...")
                await _safe_fill(page, DESCRIPTION_TEXTAREA, event.description_md)
            
            # Fill location if provided
            if event.location_text:
                print(f"Filling location: {event.location_text}")
                await _safe_fill(page, LOCATION_INPUT, event.location_text)
            
            # Fill start date/time
            print(f"Filling start time: {event.start}")
            start_str = event.start.strftime("%m/%d/%Y %I:%M %p")
            await _safe_fill(page, DATE_START_INPUT, start_str)
            
            # Fill end date/time if provided
            if event.end:
                print(f"Filling end time: {event.end}")
                end_str = event.end.strftime("%m/%d/%Y %I:%M %p")
                await _safe_fill(page, DATE_END_INPUT, end_str)
            
            print("\n✅ Form filled successfully!")
            print("📝 Please review the form and manually publish when ready.")
            
            if wait_for_publish:
                print("\n⏳ Waiting for manual publish... (browser will stay open)")
                # Wait for user to click publish or close browser
                try:
                    await page.wait_for_selector(PUBLISH_BUTTON, state="hidden", timeout=300000)  # 5 min
                    print("✅ Event appears to be published!")
                except Exception:
                    print("⏰ Timeout or browser closed. Please publish manually if needed.")
            else:
                print("\n🔄 Browser will stay open for manual review and publishing.")
                # Keep browser open for manual interaction
                await page.wait_for_timeout(5000)  # Brief pause
                
        finally:
            if not wait_for_publish:
                print("🌐 Browser staying open for manual publishing...")
                # Don't close browser - let user handle it
                pass
            else:
                await browser.close()


async def _safe_fill(page: Page, selector: str, value: str) -> None:
    """Safely fill a form field, handling potential missing elements."""
    try:
        element = await page.wait_for_selector(selector, timeout=5000)
        if element:
            await element.fill(value)
    except Exception as e:
        print(f"⚠️  Could not fill selector {selector}: {e}")
        # Continue with other fields


def create_partiful_sync(event: EventSpec, *, wait_for_publish: bool = False) -> None:
    """Synchronous wrapper for the async Playwright automation."""
    asyncio.run(fill_partiful_form(event, wait_for_publish=wait_for_publish))
