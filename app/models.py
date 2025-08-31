from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal, Optional
from zoneinfo import ZoneInfo, available_timezones

from pydantic import BaseModel, Field, field_validator, model_validator


class EventSpec(BaseModel):
    """Strict, future-proof event specification with helpful defaults."""
    
    title: str = Field(..., description="Event name/title")
    start: datetime = Field(..., description="Event start datetime (timezone-aware)")
    end: Optional[datetime] = Field(None, description="Event end datetime (auto-filled if None)")
    time_zone: str = Field(
        default="America/New_York", 
        description="IANA timezone name for display purposes"
    )
    location_text: Optional[str] = Field(None, description="Freeform location description")
    location_maps_url: Optional[str] = Field(None, description="Google Maps or similar URL")
    description_md: Optional[str] = Field(None, description="Event description in Markdown")
    privacy: Literal["private", "public"] = Field(
        default="private", 
        description="Event privacy setting"
    )
    cohosts: list[str] = Field(default_factory=list, description="List of cohost names/emails")
    rsvp_questions: list[str] = Field(
        default_factory=list, 
        description="Custom RSVP questions"
    )
    cover_image_path: Optional[str] = Field(
        None, 
        description="Local file path to cover image"
    )
    
    @field_validator("time_zone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        """Validate timezone against zoneinfo.available_timezones()."""
        if v not in available_timezones():
            raise ValueError(f"Invalid timezone: {v}. Must be a valid IANA timezone.")
        return v
    
    @model_validator(mode="after")
    def set_default_end(self) -> "EventSpec":
        """Auto-fill end time if not provided (start + 4 hours)."""
        if self.end is None:
            self.end = self.start + timedelta(hours=4)
        return self
    
    def as_human(self) -> str:
        """Return a concise one-line human preview with localized times."""
        try:
            tz = ZoneInfo(self.time_zone)
            start_local = self.start.astimezone(tz)
            end_local = self.end.astimezone(tz) if self.end else None
            
            date_str = start_local.strftime("%a %b %d")
            start_time = start_local.strftime("%I:%M %p").lstrip("0")
            
            if end_local and end_local.date() == start_local.date():
                # Same day
                end_time = end_local.strftime("%I:%M %p").lstrip("0")
                time_str = f"{start_time}-{end_time}"
            elif end_local:
                # Multi-day
                end_date = end_local.strftime("%a %b %d")
                end_time = end_local.strftime("%I:%M %p").lstrip("0")
                time_str = f"{start_time} to {end_date} {end_time}"
            else:
                time_str = start_time
            
            location_part = f" at {self.location_text}" if self.location_text else ""
            
            return f"{self.title} • {date_str} {time_str}{location_part}"
            
        except Exception:
            # Fallback if timezone conversion fails
            return f"{self.title} • {self.start.strftime('%Y-%m-%d %H:%M')}"


# Legacy models for backward compatibility
class Event(BaseModel):
    """Legacy event model - use EventSpec for new code."""
    
    title: str = Field(..., description="Event name/title")
    description: Optional[str] = Field(None, description="Event description/body")
    location: Optional[str] = Field(None, description="Freeform location string")
    start: datetime = Field(..., description="Event start datetime (timezone-aware preferred)")
    end: Optional[datetime] = Field(None, description="Optional end datetime")
    cover_image_url: Optional[str] = Field(
        None, description="Optional public URL for a cover image"
    )
    is_private: bool = Field(default=True, description="Whether the event is private")


class ExtractionRequest(BaseModel):
    """Input to the extraction pipeline."""

    text: str
    default_tz: Optional[str] = Field(
        default="UTC", description="IANA timezone name used when missing"
    )
    default_start_time: Optional[str] = Field(
        default="7:00 PM",
        description="Fallback time if only a date is present (natural language acceptable)",
    )


class ExtractionResponse(BaseModel):
    """Output from the extraction pipeline."""

    event: EventSpec  # Updated to use EventSpec instead of legacy Event
    confidence: float = Field(
        0.7, ge=0.0, le=1.0, description="Rough confidence of the extraction"
    )
