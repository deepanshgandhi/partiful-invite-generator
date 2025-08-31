# Partiful Invite Generator

Generate Partiful invites from natural language descriptions using a ToS-safe approach.

## Approach

This tool uses **only public web UI automation** with a headful browser:
- No private APIs or reverse engineering
- Form filling only through standard web controls
- User manually reviews and publishes events
- Complies with Partiful's Terms of Service

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browser:
```bash
python -m playwright install chromium
```

## Usage

### CLI
```bash
python -m app.cli "Birthday party at John's house Friday 7pm"
```

### CLI with Cover Image
```bash
python -m app.cli "Birthday party at John's house Friday 7pm" --cover-image "Sundai logo.png"
```

### Test Image Upload
```bash
python test_image_upload.py
```

### FastAPI Server
```bash
python -m app.server
# Then POST to http://localhost:8000/extract
```

### How it works

1. **Extract**: Parses natural language using `dateparser` to create structured event data
2. **Automate**: Opens Partiful's create page in a real browser and fills the form
3. **Manual**: User reviews the form and clicks "Publish" manually

This ensures compliance with terms of service while providing automation convenience.
