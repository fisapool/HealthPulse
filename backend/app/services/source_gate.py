"""
Source Gate - Validates and gates data sources for safety
Prioritizes official DOSM domains and blocks unsafe sources
"""
import logging
from urllib.parse import urlparse
from typing import Optional, Tuple
from app.config import DOSM_OFFICIAL_DOMAINS, TIER_CONFIDENCE_MAP, TIER_FILE_TYPE_MAP, TIER_SCRAPE_METHOD_MAP
from app.models.dosm_dataset import ScrapeTier

logger = logging.getLogger(__name__)


class SourceGateError(Exception):
    """Exception raised when source gate blocks a request"""
    pass


def is_official_dosm_domain(url: str) -> bool:
    """
    Check if URL belongs to an official DOSM domain
    
    Args:
        url: URL to check
        
    Returns:
        True if URL is from official DOSM domain
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in domain:
            domain = domain.split(':')[0]
        
        # Check against whitelist
        for official_domain in DOSM_OFFICIAL_DOMAINS:
            if domain == official_domain or domain.endswith('.' + official_domain):
                return True
        
        return False
    except Exception as e:
        logger.warning(f"Error parsing URL {url}: {e}")
        return False


def resolve_source(dataset_id: str, source_url: Optional[str] = None) -> Tuple[str, ScrapeTier, str]:
    """
    Resolve and validate source for a dataset
    
    Args:
        dataset_id: Unique dataset identifier
        source_url: Optional source URL (if None, will need to be discovered)
        
    Returns:
        Tuple of (validated_source_url, tier, confidence)
        
    Raises:
        SourceGateError: If source is blocked or invalid
    """
    # If source_url provided, validate it
    if source_url:
        if not is_official_dosm_domain(source_url):
            raise SourceGateError(
                f"Source URL {source_url} is not from an official DOSM domain. "
                f"Only official DOSM sources are allowed for safety."
            )
        
        # Determine tier based on URL pattern
        tier = _determine_tier_from_url(source_url)
        confidence = TIER_CONFIDENCE_MAP.get(tier.value, "medium")
        
        return source_url, tier, confidence
    
    # If no source_url, try to construct from dataset_id
    # This is a fallback - discovery should provide URLs
    logger.warning(f"No source_url provided for dataset {dataset_id}, attempting to construct")
    
    # Default to OpenDOSM (Tier 1) as safest option
    from app.config import scraper_config
    constructed_url = f"{scraper_config.base_url_opendosm}/data-catalogue/{dataset_id}"
    
    return constructed_url, ScrapeTier.TIER1_OPENDOSM, "high"


def _determine_tier_from_url(url: str) -> ScrapeTier:
    """
    Determine scraping tier from URL pattern
    
    Args:
        url: Source URL
        
    Returns:
        Appropriate ScrapeTier
    """
    url_lower = url.lower()
    
    # Tier 1: OpenDOSM API or direct data access
    if "open.dosm.gov.my" in url_lower:
        if "/api/" in url_lower or url_lower.endswith(".csv") or url_lower.endswith(".parquet"):
            return ScrapeTier.TIER1_OPENDOSM
    
    # Tier 2: Direct file downloads
    if url_lower.endswith((".csv", ".xlsx", ".xls", ".parquet")):
        return ScrapeTier.TIER2_DIRECT_DOWNLOAD
    
    # Tier 3: PDF files
    if url_lower.endswith(".pdf"):
        return ScrapeTier.TIER3_PDF_EXTRACTION
    
    # Tier 4: HTML pages (default for web pages)
    if url_lower.startswith("http"):
        return ScrapeTier.TIER4_HTML_PARSING
    
    # Default to Tier 4 (HTML parsing)
    return ScrapeTier.TIER4_HTML_PARSING


def get_metadata_for_tier(tier: ScrapeTier, source_url: str) -> dict:
    """
    Get metadata fields based on tier
    
    Args:
        tier: Scraping tier
        source_url: Source URL
        
    Returns:
        Dictionary with file_type and scrape_method
    """
    file_type = TIER_FILE_TYPE_MAP.get(tier.value, "html")
    scrape_method = TIER_SCRAPE_METHOD_MAP.get(tier.value, "html_parsing")
    
    # Override file_type for direct downloads if URL extension indicates
    if tier == ScrapeTier.TIER2_DIRECT_DOWNLOAD:
        url_lower = source_url.lower()
        if url_lower.endswith(".xlsx") or url_lower.endswith(".xls"):
            file_type = "xlsx"
        elif url_lower.endswith(".csv"):
            file_type = "csv"
    
    return {
        "file_type": file_type,
        "scrape_method": scrape_method
    }


def validate_and_gate_source(dataset_id: str, source_url: str) -> Tuple[str, ScrapeTier, str, dict]:
    """
    Complete source gate validation
    
    Args:
        dataset_id: Dataset identifier
        source_url: Source URL to validate
        
    Returns:
        Tuple of (validated_url, tier, confidence, metadata)
        
    Raises:
        SourceGateError: If source is blocked
    """
    validated_url, tier, confidence = resolve_source(dataset_id, source_url)
    metadata = get_metadata_for_tier(tier, validated_url)
    
    logger.info(
        f"Source gate approved: dataset_id={dataset_id}, "
        f"url={validated_url}, tier={tier.value}, confidence={confidence}"
    )
    
    return validated_url, tier, confidence, metadata

