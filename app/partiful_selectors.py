"""CSS selectors for Partiful's Create page.

Partiful uses a click-to-reveal interface where many fields appear after clicking trigger elements.
These selectors are based on the actual DOM structure as of 2025.
"""

# Title - contenteditable H1 element
TITLE_SELECTOR = "h1.EditableEventTitle_title__JRGfG"

# Date/Time - trigger button and subsequent inputs
DATE_TRIGGER = 'text="Set a date"'  # Playwright text selector
DATE_INPUT_SELECTORS = [
    'input[type="date"]',
    'input[type="datetime-local"]', 
    'input[placeholder*="date"]',
    'input[placeholder*="Date"]',
    'input[aria-label*="date"]',
    '[data-testid*="date"]'
]

# Location - trigger and input (now with correct selector)
LOCATION_TRIGGER = 'text="Location"'  # Will click the first Location text
LOCATION_INPUT_SELECTORS = [
    'input[placeholder="Place name, address, or link"]',  # Actual Partiful placeholder
    'input[type="search"]',  # The location input is type="search"
    'input[placeholder*="Place name"]',
    'input[placeholder*="address"]',
    'input[placeholder*="location"]',
    'input[placeholder*="Location"]',
    'input[aria-label*="location"]'
]

# Description - trigger and input area
DESCRIPTION_TRIGGER = 'text="Add a description"'
DESCRIPTION_INPUT_SELECTORS = [
    'textarea[placeholder*="description"]',
    'textarea[placeholder*="Description"]',
    '[contenteditable="true"][role="textbox"]',
    'textarea[aria-label*="description"]'
]

# Action buttons
SAVE_DRAFT_BUTTON = 'button:has-text("Save draft")'
PUBLISH_BUTTON = 'button:has-text("Publish")'
PREVIEW_BUTTON = 'button:has-text("Preview")'

# Image upload selectors
IMAGE_UPLOAD_TRIGGER = 'text="Add a cover image"'
IMAGE_UPLOAD_INPUT = 'input[type="file"]'
IMAGE_UPLOAD_BUTTON = 'button:has-text("Upload")'
IMAGE_REMOVE_BUTTON = 'button:has-text("Remove")'

# Fallback selectors for various form states
GENERIC_TEXT_INPUT = 'input[type="text"]'
GENERIC_TEXTAREA = 'textarea'
GENERIC_CONTENTEDITABLE = '[contenteditable="true"]'
