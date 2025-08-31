"""CLI interface for the Partiful invite generator."""

from __future__ import annotations

import argparse
from typing import Optional

from .extract import extract, ExtractionRequest
from .create_partiful import create_partiful_sync


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Generate Partiful invites from natural language")
    parser.add_argument("text", help="Natural language description of the event")
    parser.add_argument("--tz", default="UTC", help="Default timezone (default: UTC)")
    parser.add_argument("--wait", action="store_true", help="Wait for manual publish")
    parser.add_argument("--cover-image", help="Path to cover image file")
    
    args = parser.parse_args()
    
    # Extract event data
    req = ExtractionRequest(text=args.text, default_tz=args.tz)
    response = extract(req)
    
    # Set cover image if provided
    if args.cover_image:
        response.event.cover_image_path = args.cover_image
        print(f"🖼️  Cover image set: {args.cover_image}")
    
    print(f"Extracted event: {response.event.title}")
    print(f"Confidence: {response.confidence:.2f}")
    
    # Fill Partiful form
    create_partiful_sync(response.event, wait_for_publish=args.wait)


if __name__ == "__main__":
    main()
