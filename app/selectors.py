"""CSS selectors for Partiful's Create page.

We only target public web UI controls. Keep all selectors centralized for easy updates.
URLs are now configured in settings.py.
"""

# These are best-effort, and may require updates if Partiful changes markup.
# Prefer role-based and placeholder-based selectors when possible.
TITLE_INPUT = 'input[placeholder="Event name"], input[name="title"], [data-testid="event-title"]'
DESCRIPTION_TEXTAREA = (
    'textarea[placeholder="Description"], textarea[name="description"], [data-testid="event-description"]'
)
LOCATION_INPUT = 'input[placeholder="Location"], input[name="location"], [data-testid="event-location"]'
DATE_START_INPUT = 'input[name="start"], [data-testid="event-start"] input'
DATE_END_INPUT = 'input[name="end"], [data-testid="event-end"] input'
COVER_IMAGE_BUTTON = 'input[type="file"], [data-testid="cover-upload"] input[type="file"]'
SAVE_DRAFT_BUTTON = (
    'button:has-text("Save"), button:has-text("Save Draft"), [data-testid="save-draft"]'
)
PUBLISH_BUTTON = 'button:has-text("Publish"), [data-testid="publish-event"]'
