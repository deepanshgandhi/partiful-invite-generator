#!/usr/bin/env python3
"""Test script for Partiful image upload functionality."""

import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.models import EventSpec
from app.create_partiful import create_partiful_sync


def main():
    """Test the image upload functionality."""
    
    # Check if the Sundai logo exists
    logo_path = "Sundai logo.png"
    if not os.path.exists(logo_path):
        print(f"❌ Logo file not found: {logo_path}")
        print("Please make sure 'Sundai logo.png' is in the current directory")
        return
    
    print(f"✅ Found logo file: {logo_path}")
    
    # Create a test event with the cover image
    test_event = EventSpec(
        title="Test Event with Sundai Logo",
        start=datetime.now(ZoneInfo("America/Los_Angeles")) + timedelta(days=1, hours=19),
        end=datetime.now(ZoneInfo("America/Los_Angeles")) + timedelta(days=1, hours=23),
        time_zone="America/Los_Angeles",
        location_text="75 Amherst St, Cambridge, MA 02139",
        description_md="This is a test event to demonstrate the image upload functionality with the Sundai logo.",
        cover_image_path=logo_path,  # This will trigger the image upload
        privacy="private"
    )
    
    print(f"🎯 Test event created: {test_event.title}")
    print(f"🖼️  Cover image: {test_event.cover_image_path}")
    print(f"📅 Date: {test_event.start.strftime('%Y-%m-%d %I:%M %p')}")
    print(f"📍 Location: {test_event.location_text}")
    
    print("\n🌐 Opening Partiful and filling form...")
    print("💡 The browser will stay open for you to review and publish manually")
    
    try:
        # Fill the Partiful form (browser will stay open)
        create_partiful_sync(test_event, wait_for_publish=False)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
