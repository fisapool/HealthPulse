"""
Pydantic schemas for scraper configuration
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.models.dosm_dataset import ScrapeTier


class ScraperConfig(BaseModel):
    """Configuration for DOSM scraper"""
    base_url_opendosm: str = Field(
        default="https://open.dosm.gov.my",
        description="OpenDOSM base URL"
    )
    base_url_statsdw: str = Field(
        default="https://statsdw.dosm.gov.my",
        description="StatsDW portal base URL"
    )
    base_url_main: str = Field(
        default="https://www.dosm.gov.my",
        description="DOSM main website URL"
    )
    rate_limit_requests_per_minute: int = Field(
        default=30,
        ge=1,
        le=1000,
        description="Rate limit for requests per minute"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retries for failed requests"
    )
    retry_backoff_factor: float = Field(
        default=2.0,
        ge=1.0,
        le=10.0,
        description="Exponential backoff factor for retries"
    )
    request_timeout_seconds: int = Field(
        default=60,
        ge=10,
        le=300,
        description="Request timeout in seconds"
    )
    enable_browser_automation: bool = Field(
        default=False,
        description="Enable Tier 5 browser automation (last resort)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "base_url_opendosm": "https://open.dosm.gov.my",
                "base_url_statsdw": "https://statsdw.dosm.gov.my",
                "base_url_main": "https://www.dosm.gov.my",
                "rate_limit_requests_per_minute": 30,
                "max_retries": 3,
                "retry_backoff_factor": 2.0,
                "request_timeout_seconds": 60,
                "enable_browser_automation": False
            }
        }


class DatasetDiscoveryRequest(BaseModel):
    """Request schema for dataset discovery"""
    category: Optional[str] = Field(None, description="Category filter (e.g., 'health', 'demographics')")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of datasets to discover")
    auto_assign_tiers: bool = Field(default=True, description="Automatically assign scraping tiers")


class ScrapeRequest(BaseModel):
    """Request schema for triggering a scrape"""
    dataset_id: str = Field(..., description="Dataset ID to scrape")
    force: bool = Field(default=False, description="Force scrape even if version unchanged")
    tier_override: Optional[ScrapeTier] = Field(None, description="Override assigned tier (use with caution)")

