"""Basic tests for the extraction functionality."""

from datetime import datetime

from app.extract import extract, ExtractionRequest


def test_extract():
    """Test basic event extraction from natural language."""
    req = ExtractionRequest(
        text="Birthday party at John's house on Friday 7pm",
        default_tz="America/New_York"
    )
    
    response = extract(req)
    
    assert response.event.title
    assert response.event.start
    assert isinstance(response.event.start, datetime)
    assert 0.0 <= response.confidence <= 1.0
