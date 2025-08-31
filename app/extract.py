from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv
from zoneinfo import ZoneInfo

from .models import EventSpec, ExtractionRequest, ExtractionResponse
from .settings import settings

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def extract_event_with_llm(req: ExtractionRequest) -> EventSpec:
    """Extract structured event data using OpenAI GPT model."""
    
    system_prompt = """You are an expert at extracting structured event information from natural language text.

Extract the following fields from the user's text:
- title: A clear, concise event title (remove filler words like "Event", "Party", etc. if they're redundant)
- start: ISO 8601 datetime with timezone (use the provided default_tz if timezone not specified)
- end: ISO 8601 datetime with timezone (optional, if not mentioned you can estimate duration)
- location_text: EXACT location text only (remove prepositions like "at", "in", "near", etc.)
- description_md: Clean description in markdown format
- privacy: "private" or "public" (default to "private" if not specified)

CRITICAL LOCATION RULES:
- Extract ONLY the actual location name/address
- Remove prepositions: "at MIT" → "MIT", "in Boston" → "Boston", "near downtown" → "downtown"
- Remove articles: "at the park" → "park", "in the office" → "office"
- Keep specific addresses intact: "123 Main St" stays "123 Main St"
- Examples:
  * "at John's house" → "John's house"
  * "at MIT, Cambridge" → "MIT, Cambridge"
  * "in the conference room" → "conference room"
  * "near downtown Boston" → "downtown Boston"

Important guidelines:
- Always include timezone information in datetime fields
- If only a date is given, use the default_start_time for the time
- Be conservative with privacy (default to "private")
- Keep titles concise but descriptive
- Extract exact location text without prepositions or articles

Return ONLY a valid JSON object with these fields. Do not include any other text."""

    user_prompt = f"""Extract event information from this text. Pay special attention to location extraction - remove any prepositions or articles.

Text: {req.text}

Default timezone: {req.default_tz}
Default start time if only date given: {req.default_start_time}

Examples of correct location extraction:
- "meeting at MIT Cambridge" → location_text: "MIT Cambridge"
- "party at John's house" → location_text: "John's house" 
- "conference in the downtown office" → location_text: "downtown office"
- "dinner at 123 Main Street" → location_text: "123 Main Street"

Return the extracted event data as JSON with clean, exact field values."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using GPT-4o-mini as the most capable mini model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")
            
        # Parse the JSON response
        extracted_data = json.loads(content)
        
        # Convert string datetimes to datetime objects
        start_dt = datetime.fromisoformat(extracted_data["start"])
        end_dt = None
        if extracted_data.get("end"):
            end_dt = datetime.fromisoformat(extracted_data["end"])
        
        # Create EventSpec with extracted data
        return EventSpec(
            title=extracted_data["title"],
            start=start_dt,
            end=end_dt,
            time_zone=req.default_tz or "UTC",
            location_text=extracted_data.get("location_text"),
            description_md=extracted_data.get("description_md"),
            privacy=extracted_data.get("privacy", "private")
        )
        
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse OpenAI response as JSON: {e}")
    except KeyError as e:
        raise ValueError(f"Missing required field in OpenAI response: {e}")
    except Exception as e:
        raise ValueError(f"Error calling OpenAI API: {e}")


def extract_event(req: ExtractionRequest) -> EventSpec:
    """Extract event data - now using LLM extraction."""
    return extract_event_with_llm(req)


def extract(req: ExtractionRequest) -> ExtractionResponse:
    """Main extraction function returning response with confidence."""
    try:
        event = extract_event(req)
        # Higher confidence when using LLM extraction
        confidence = 0.9 if event.title and event.start else 0.7
        return ExtractionResponse(event=event, confidence=confidence)
    except Exception as e:
        # Fallback: create a basic event from the text
        fallback_event = EventSpec(
            title=req.text[:50] + "..." if len(req.text) > 50 else req.text,
            start=datetime.now().replace(hour=19, minute=0, second=0, microsecond=0, 
                                      tzinfo=ZoneInfo(req.default_tz or "UTC")),
            description_md=req.text
        )
        return ExtractionResponse(event=fallback_event, confidence=0.3)
