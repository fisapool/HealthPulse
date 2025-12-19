"""
Dataset Discovery Service
Scans OpenDOSM catalog and identifies health-related datasets
Auto-assigns scraping tiers based on available formats
"""
import logging
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.dosm_dataset import DOSMDataset, ScrapeTier
from app.services.source_gate import validate_and_gate_source, SourceGateError
from app.config import scraper_config

logger = logging.getLogger(__name__)


class DatasetDiscovery:
    """Service for discovering DOSM datasets"""
    
    def __init__(self, db: Session):
        self.db = db
        self.base_url = scraper_config.base_url_opendosm
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """Make HTTP request"""
        response = requests.get(
            url,
            params=params,
            timeout=scraper_config.request_timeout_seconds,
            headers={
                "User-Agent": "HealthPulse-Registry/1.0 (Data Collection Bot)"
            }
        )
        response.raise_for_status()
        return response
    
    def _determine_tier_from_format(self, formats: List[str], source_url: str) -> ScrapeTier:
        """
        Determine scraping tier from available formats
        
        Args:
            formats: List of available formats
            source_url: Source URL
            
        Returns:
            Appropriate ScrapeTier
        """
        formats_lower = [f.lower() for f in formats]
        url_lower = source_url.lower()
        
        # Tier 1: API, CSV, Parquet
        if any(f in ["api", "json", "csv", "parquet"] for f in formats_lower):
            if "open.dosm.gov.my" in url_lower:
                return ScrapeTier.TIER1_OPENDOSM
            return ScrapeTier.TIER2_DIRECT_DOWNLOAD
        
        # Tier 2: Direct file downloads
        if any(f in ["csv", "xlsx", "xls"] for f in formats_lower):
            return ScrapeTier.TIER2_DIRECT_DOWNLOAD
        
        # Tier 3: PDF
        if "pdf" in formats_lower:
            return ScrapeTier.TIER3_PDF_EXTRACTION
        
        # Tier 4: HTML (default)
        return ScrapeTier.TIER4_HTML_PARSING
    
    def _is_health_related(self, dataset: Dict[str, Any]) -> bool:
        """
        Check if dataset is health-related
        
        Args:
            dataset: Dataset metadata
            
        Returns:
            True if health-related
        """
        health_keywords = [
            "health", "hospital", "clinic", "medical", "healthcare",
            "mortality", "morbidity", "disease", "epidemic", "pandemic",
            "patient", "treatment", "diagnosis", "vaccine", "immunization"
        ]
        
        # Check in various fields
        text_to_check = " ".join([
            dataset.get("name", ""),
            dataset.get("description", ""),
            dataset.get("category", ""),
            dataset.get("tags", ""),
        ]).lower()
        
        return any(keyword in text_to_check for keyword in health_keywords)
    
    def discover_opendosm_catalog(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Discover datasets from OpenDOSM catalog
        
        Args:
            category: Optional category filter
            limit: Maximum number of datasets to discover
            
        Returns:
            List of discovered dataset metadata
        """
        discovered = []
        
        try:
            # Try to access OpenDOSM catalog API
            # Note: Actual API endpoint may vary, this is a template
            catalog_url = f"{self.base_url}/api/data-catalogue"
            
            params = {}
            if category:
                params["category"] = category
            params["limit"] = limit
            
            try:
                response = self._make_request(catalog_url, params=params)
                data = response.json()
                
                # Handle different response formats
                if isinstance(data, list):
                    datasets = data
                elif isinstance(data, dict):
                    datasets = data.get("data") or data.get("results") or data.get("datasets") or []
                else:
                    datasets = []
                
                for dataset in datasets:
                    # Filter health-related if category is health
                    if category and category.lower() == "health":
                        if not self._is_health_related(dataset):
                            continue
                    
                    discovered.append(dataset)
                
            except requests.RequestException as e:
                logger.warning(f"Could not access OpenDOSM catalog API: {e}")
                logger.info("Falling back to manual discovery - datasets must be added manually")
                # Return empty list - manual discovery required
                return []
            
            logger.info(f"Discovered {len(discovered)} datasets from OpenDOSM catalog")
            return discovered
            
        except Exception as e:
            logger.error(f"Error discovering datasets: {e}")
            raise
    
    def register_dataset(
        self,
        dataset_id: str,
        name: str,
        source_url: str,
        description: Optional[str] = None,
        auto_assign_tier: bool = True,
        tier: Optional[ScrapeTier] = None,
        update_frequency: Optional[str] = None
    ) -> DOSMDataset:
        """
        Register a discovered dataset in the database
        
        Args:
            dataset_id: Unique dataset identifier
            name: Dataset name
            source_url: Source URL
            description: Optional description
            auto_assign_tier: Automatically assign tier based on URL
            tier: Optional tier override
            update_frequency: Optional update frequency
            
        Returns:
            Created or updated DOSMDataset
        """
        # Validate source through gate
        try:
            validated_url, validated_tier, confidence, metadata_info = validate_and_gate_source(
                dataset_id,
                source_url
            )
        except SourceGateError as e:
            logger.error(f"Source gate blocked dataset {dataset_id}: {e}")
            raise
        
        # Use provided tier or auto-assign
        final_tier = tier if tier else validated_tier
        
        # Check if dataset already exists
        existing = self.db.query(DOSMDataset).filter(
            DOSMDataset.dataset_id == dataset_id
        ).first()
        
        if existing:
            # Update existing
            existing.name = name
            existing.description = description
            existing.source_url = validated_url
            if auto_assign_tier or tier:
                existing.tier = final_tier
            existing.scrape_method = metadata_info["scrape_method"]
            existing.confidence = confidence
            if update_frequency:
                existing.update_frequency = update_frequency
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            logger.info(f"Updated existing dataset: {dataset_id}")
            return existing
        
        # Create new
        dataset = DOSMDataset(
            dataset_id=dataset_id,
            name=name,
            description=description,
            source_url=validated_url,
            tier=final_tier,
            scrape_method=metadata_info["scrape_method"],
            update_frequency=update_frequency,
            confidence=confidence,
            is_statistical=True,  # DOSM is statistical reference
            is_active=True
        )
        
        self.db.add(dataset)
        self.db.commit()
        self.db.refresh(dataset)
        
        logger.info(f"Registered new dataset: {dataset_id} with tier {final_tier.value}")
        return dataset
    
    def discover_and_register(
        self,
        category: Optional[str] = None,
        limit: int = 100,
        auto_assign_tiers: bool = True
    ) -> List[DOSMDataset]:
        """
        Discover datasets and register them in database
        
        Args:
            category: Optional category filter
            limit: Maximum number of datasets
            auto_assign_tiers: Automatically assign tiers
            
        Returns:
            List of registered datasets
        """
        discovered = self.discover_opendosm_catalog(category=category, limit=limit)
        
        registered = []
        for dataset_info in discovered:
            try:
                # Extract dataset information
                dataset_id = dataset_info.get("id") or dataset_info.get("dataset_id")
                name = dataset_info.get("name") or dataset_info.get("title")
                source_url = dataset_info.get("url") or dataset_info.get("source_url") or dataset_info.get("download_url")
                description = dataset_info.get("description")
                formats = dataset_info.get("formats", [])
                update_frequency = dataset_info.get("update_frequency")
                
                if not dataset_id or not name or not source_url:
                    logger.warning(f"Skipping incomplete dataset info: {dataset_info}")
                    continue
                
                # Determine tier if auto-assigning
                tier = None
                if auto_assign_tiers:
                    tier = self._determine_tier_from_format(formats, source_url)
                
                # Register dataset
                dataset = self.register_dataset(
                    dataset_id=dataset_id,
                    name=name,
                    source_url=source_url,
                    description=description,
                    auto_assign_tier=auto_assign_tiers,
                    tier=tier,
                    update_frequency=update_frequency
                )
                
                registered.append(dataset)
                
            except Exception as e:
                logger.error(f"Error registering dataset {dataset_info.get('id')}: {e}")
                continue
        
        logger.info(f"Registered {len(registered)} datasets")
        return registered

