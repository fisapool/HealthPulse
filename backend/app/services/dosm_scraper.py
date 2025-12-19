"""
DOSM Scraper - Main orchestrator
Routes to appropriate tier scrapers, enriches with metadata, tracks versions
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.dosm_dataset import DOSMDataset, ScrapeTier
from app.models.dosm_record import DOSMRecord
from app.schemas.dosm_record import RecordMetadata
from app.services.source_gate import validate_and_gate_source, SourceGateError
from app.services.version_tracker import track_dataset_version, is_duplicate_version
from app.services.scrapers.tier1_opendosm import Tier1OpenDOSMScraper
from app.services.scrapers.tier2_direct_download import Tier2DirectDownloadScraper
from app.services.scrapers.tier3_pdf_extraction import Tier3PDFExtractionScraper
from app.services.scrapers.tier4_html_parsing import Tier4HTMLParsingScraper
from app.services.scrapers.tier5_browser_automation import Tier5BrowserAutomationScraper
from app.config import TIER_CONFIDENCE_MAP

logger = logging.getLogger(__name__)


class DOSMScraper:
    """Main scraper orchestrator for DOSM data"""
    
    def __init__(self, db: Session):
        self.db = db
        self.tier1_scraper = Tier1OpenDOSMScraper()
        self.tier2_scraper = Tier2DirectDownloadScraper()
        self.tier3_scraper = Tier3PDFExtractionScraper()
        self.tier4_scraper = Tier4HTMLParsingScraper()
        self.tier5_scraper = Tier5BrowserAutomationScraper()
    
    def _get_dataset(self, dataset_id: str) -> Optional[DOSMDataset]:
        """Get dataset from database"""
        return self.db.query(DOSMDataset).filter(
            DOSMDataset.dataset_id == dataset_id
        ).first()
    
    def _route_to_tier_scraper(
        self,
        tier: ScrapeTier,
        source_url: str,
        **kwargs
    ) -> tuple[List[Dict[str, Any]], bytes]:
        """
        Route to appropriate tier scraper
        
        Args:
            tier: Scraping tier
            source_url: Source URL
            **kwargs: Additional arguments for scrapers
            
        Returns:
            Tuple of (records, content_bytes)
        """
        if tier == ScrapeTier.TIER1_OPENDOSM:
            return self.tier1_scraper.scrape(source_url)
        elif tier == ScrapeTier.TIER2_DIRECT_DOWNLOAD:
            return self.tier2_scraper.scrape(source_url, **kwargs)
        elif tier == ScrapeTier.TIER3_PDF_EXTRACTION:
            return self.tier3_scraper.scrape(source_url)
        elif tier == ScrapeTier.TIER4_HTML_PARSING:
            return self.tier4_scraper.scrape(source_url)
        elif tier == ScrapeTier.TIER5_BROWSER_AUTOMATION:
            return self.tier5_scraper.scrape(source_url, **kwargs)
        else:
            raise ValueError(f"Unknown tier: {tier}")
    
    def _enrich_with_metadata(
        self,
        records: List[Dict[str, Any]],
        dataset_id: str,
        source_url: str,
        tier: ScrapeTier,
        published_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Enrich records with mandatory metadata block
        
        Args:
            records: Raw records
            dataset_id: Dataset identifier
            source_url: Source URL
            tier: Scraping tier
            published_date: Optional published date
            
        Returns:
            Records with metadata added
        """
        from app.services.source_gate import get_metadata_for_tier
        
        metadata_info = get_metadata_for_tier(tier, source_url)
        confidence = TIER_CONFIDENCE_MAP.get(tier.value, "medium")
        
        enriched_records = []
        retrieved_at = datetime.utcnow()
        
        for record in records:
            # Create metadata block
            metadata = {
                "source": "DOSM",
                "dataset_id": dataset_id,
                "source_url": source_url,
                "file_type": metadata_info["file_type"],
                "published_date": published_date.isoformat() if published_date else None,
                "retrieved_at": retrieved_at.isoformat(),
                "scrape_method": metadata_info["scrape_method"],
                "confidence": confidence
            }
            
            # Add metadata to record
            enriched_record = {
                "data": record,
                "metadata": metadata
            }
            
            enriched_records.append(enriched_record)
        
        return enriched_records
    
    def scrape(
        self,
        dataset_id: str,
        force: bool = False,
        tier_override: Optional[ScrapeTier] = None,
        **scraper_kwargs
    ) -> Dict[str, Any]:
        """
        Main scrape method
        
        Args:
            dataset_id: Dataset identifier
            force: Force scrape even if version unchanged
            tier_override: Override assigned tier (use with caution)
            **scraper_kwargs: Additional arguments for scrapers
            
        Returns:
            Dictionary with scrape results
        """
        # Get dataset from database
        dataset = self._get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found. Run discovery first.")
        
        if not dataset.is_active:
            raise ValueError(f"Dataset {dataset_id} is not active")
        
        # Use tier override if provided, otherwise use dataset tier
        tier = tier_override if tier_override else dataset.tier
        source_url = dataset.source_url
        
        # Validate source through gate
        try:
            validated_url, validated_tier, confidence, metadata_info = validate_and_gate_source(
                dataset_id,
                source_url
            )
            # Use validated tier if no override
            if not tier_override:
                tier = validated_tier
            source_url = validated_url
        except SourceGateError as e:
            logger.error(f"Source gate blocked dataset {dataset_id}: {e}")
            raise
        
        # Check version if not forcing
        # We'll check after scraping to compare hashes
        
        # Route to appropriate scraper
        try:
            logger.info(f"Scraping dataset {dataset_id} using {tier.value}")
            records, content = self._route_to_tier_scraper(tier, source_url, **scraper_kwargs)
        except Exception as e:
            logger.error(f"Scraping failed for dataset {dataset_id}: {e}")
            # Update dataset last_checked
            dataset.last_checked = datetime.utcnow()
            self.db.commit()
            raise
        
        # Check version and track
        is_new_version, version = track_dataset_version(
            self.db,
            dataset_id,
            content,
            records,
            force=force
        )
        
        if not is_new_version and not force:
            logger.info(f"Dataset {dataset_id} version unchanged, skipping record storage")
            return {
                "dataset_id": dataset_id,
                "is_new_version": False,
                "version": version.version_number if version else None,
                "records_count": 0,
                "message": "Version unchanged, no new records stored"
            }
        
        # Enrich with metadata
        enriched_records = self._enrich_with_metadata(
            records,
            dataset_id,
            source_url,
            tier,
            published_date=None  # Could be extracted from dataset or response
        )
        
        # Store records
        stored_count = 0
        for enriched_record in enriched_records:
            db_record = DOSMRecord(
                dataset_id=dataset_id,
                data=enriched_record["data"],
                record_metadata=enriched_record["metadata"]
            )
            self.db.add(db_record)
            stored_count += 1
        
        # Update dataset
        dataset.last_checked = datetime.utcnow()
        dataset.last_successful_scrape = datetime.utcnow()
        self.db.commit()
        
        logger.info(
            f"Successfully scraped dataset {dataset_id}: "
            f"{stored_count} records stored, version={version.version_number if version else 'N/A'}"
        )
        
        return {
            "dataset_id": dataset_id,
            "is_new_version": is_new_version,
            "version": version.version_number if version else None,
            "records_count": stored_count,
            "tier_used": tier.value,
            "confidence": confidence
        }

