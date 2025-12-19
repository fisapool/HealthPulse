"""
Configuration settings for DOSM scraper
"""
import os
from typing import List
from app.schemas.scraper_config import ScraperConfig

# DOSM Official Domains (whitelist)
DOSM_OFFICIAL_DOMAINS: List[str] = [
    "open.dosm.gov.my",
    "statsdw.dosm.gov.my",
    "www.dosm.gov.my",
    "dosm.gov.my",
    "data.gov.my"  # Malaysian government data portal
]

# Load configuration from environment or use defaults
def get_scraper_config() -> ScraperConfig:
    """Get scraper configuration from environment variables or defaults"""
    return ScraperConfig(
        base_url_opendosm=os.getenv("DOSM_OPENDOSM_URL", "https://open.dosm.gov.my"),
        base_url_statsdw=os.getenv("DOSM_STATSDW_URL", "https://statsdw.dosm.gov.my"),
        base_url_main=os.getenv("DOSM_MAIN_URL", "https://www.dosm.gov.my"),
        rate_limit_requests_per_minute=int(os.getenv("DOSM_RATE_LIMIT", "30")),
        max_retries=int(os.getenv("DOSM_MAX_RETRIES", "3")),
        retry_backoff_factor=float(os.getenv("DOSM_RETRY_BACKOFF", "2.0")),
        request_timeout_seconds=int(os.getenv("DOSM_TIMEOUT", "60")),
        enable_browser_automation=os.getenv("DOSM_ENABLE_BROWSER_AUTOMATION", "false").lower() == "true"
    )

# Global config instance
scraper_config = get_scraper_config()

# Confidence thresholds based on tier
TIER_CONFIDENCE_MAP = {
    "tier1_opendosm": "high",
    "tier2_direct_download": "high",
    "tier3_pdf_extraction": "medium",
    "tier4_html_parsing": "medium",
    "tier5_browser_automation": "low"
}

# File type mapping based on tier
TIER_FILE_TYPE_MAP = {
    "tier1_opendosm": "api",
    "tier2_direct_download": "csv",  # or xlsx, determined at runtime
    "tier3_pdf_extraction": "pdf",
    "tier4_html_parsing": "html",
    "tier5_browser_automation": "html"
}

# Scrape method mapping based on tier
TIER_SCRAPE_METHOD_MAP = {
    "tier1_opendosm": "opendosm_api",
    "tier2_direct_download": "direct_download",
    "tier3_pdf_extraction": "pdf_extraction",
    "tier4_html_parsing": "html_parsing",
    "tier5_browser_automation": "browser_automation"
}


# Overpass API Configuration
def get_overpass_config() -> dict:
    """Get Overpass API configuration from environment variables or defaults"""
    base_url = os.getenv("OVERPASS_API_URL", "https://overpass-api.de")
    # Remove /api/interpreter if present (for backward compatibility)
    if base_url.endswith("/api/interpreter"):
        base_url = base_url[:-15]
    return {
        "url": base_url.rstrip("/"),
        "cache_ttl": int(os.getenv("OVERPASS_CACHE_TTL", "300")),  # 5 minutes default
        "rate_limit": int(os.getenv("OVERPASS_RATE_LIMIT", "60")),  # 60 queries per minute
        "timeout": int(os.getenv("OVERPASS_TIMEOUT", "60"))  # 60 seconds default
    }
