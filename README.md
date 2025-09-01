# Partiful Invite Generator

Generate Partiful invites from natural language descriptions using a ToS-safe approach.

## Approach

This tool uses **only public web UI automation** with a headful browser:
- No private APIs or reverse engineering
- Form filling only through standard web controls
- User manually reviews and publishes events
- Complies with Partiful's Terms of Service

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install Playwright browser:
```bash
python -m playwright install chromium
```

4. Set up environment variables:
Create a `.env` file with your OpenAI API key:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Main CLI (Direct Event Creation)
```bash
python -m app.create_partiful "AI meetup September 7 2025 from 6 pm to 9 pm at MIT, Cambridge, MA"
```

### Alternative CLI Interface
```bash
python -m app.cli "Birthday party at John's house Friday 7pm"
```

### CLI with Cover Image
```bash
python -m app.cli "Birthday party at John's house Friday 7pm" --cover-image "Sundai logo.png"
```

### Extraction-Only Server (FastAPI)
For just extracting structured data from natural language (no automation):
```bash
python -m app.server
# Then POST to http://localhost:8000/extract with JSON: {"text": "event description", "default_tz": "America/New_York"}
```

## How it works

1. **Extract**: Uses OpenAI GPT to parse natural language and create structured event data
2. **Automate**: Opens Partiful's create page in a real browser and fills the form automatically
3. **Manual**: User reviews the filled form and clicks "Publish" manually

The browser stays open for manual review to ensure compliance with terms of service while providing automation convenience.
