from __future__ import annotations

import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralized configuration using Pydantic settings."""
    
    # Timezone settings
    default_tz: str = Field(default="America/New_York", description="Default timezone for events")
    
    # Partiful URLs (primary and fallback options)
    partiful_create_urls: List[str] = Field(
        default=[
            "https://partiful.com/create",
            "https://www.partiful.com/create", 
            "https://partiful.com/invite/new"
        ],
        description="List of Partiful create event URLs to try"
    )
    
    # Browser settings
    browser_profile_dir: str = Field(
        default=".partiful-profile", 
        description="Directory for browser profile persistence"
    )
    headless: bool = Field(
        default=False, 
        description="Run browser in headless mode"
    )
    
    # OpenAI settings
    openai_api_key: str = Field(
        default="", 
        description="OpenAI API key for LLM extraction"
    )
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        # Map environment variable names to field names
        "env_prefix": "",
        "case_sensitive": False,
    }


# Global settings instance
settings = Settings()
