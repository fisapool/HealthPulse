"""
Tier 1 Scraper - OpenDOSM API and direct CSV/Parquet downloads
Highest confidence, preferred method
"""
import logging
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import scraper_config
from app.services.source_gate import is_official_dosm_domain

logger = logging.getLogger(__name__)


class Tier1OpenDOSMScraper:
    """Scraper for OpenDOSM API and direct data file downloads"""
    
    def __init__(self):
        self.base_url = scraper_config.base_url_opendosm
        self.timeout = scraper_config.request_timeout_seconds
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _make_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """
        Make HTTP request with retry logic
        
        Args:
            url: URL to request
            params: Optional query parameters
            
        Returns:
            Response object
        """
        if not is_official_dosm_domain(url):
            raise ValueError(f"URL {url} is not from official DOSM domain")
        
        response = requests.get(
            url,
            params=params,
            timeout=self.timeout,
            headers={
                "User-Agent": "HealthPulse-Registry/1.0 (Data Collection Bot)"
            }
        )
        response.raise_for_status()
        return response
    
    def scrape_api(self, api_url: str) -> List[Dict[str, Any]]:
        """
        Scrape data from OpenDOSM API endpoint
        
        Args:
            api_url: API endpoint URL
            
        Returns:
            List of records as dictionaries
        """
        try:
            logger.info(f"Scraping OpenDOSM API: {api_url}")
            response = self._make_request(api_url)
            
            # Try to parse as JSON
            data = response.json()
            
            # Handle different API response formats
            if isinstance(data, list):
                records = data
            elif isinstance(data, dict):
                # Common patterns: data, results, records, items
                records = (
                    data.get("data") or
                    data.get("results") or
                    data.get("records") or
                    data.get("items") or
                    [data]  # Single record
                )
            else:
                raise ValueError(f"Unexpected API response format: {type(data)}")
            
            logger.info(f"Retrieved {len(records)} records from OpenDOSM API")
            return records
            
        except Exception as e:
            logger.error(f"Error scraping OpenDOSM API {api_url}: {e}")
            raise
    
    def scrape_csv(self, csv_url: str) -> List[Dict[str, Any]]:
        """
        Scrape data from CSV file
        
        Args:
            csv_url: URL to CSV file
            
        Returns:
            List of records as dictionaries
        """
        try:
            logger.info(f"Scraping CSV file: {csv_url}")
            response = self._make_request(csv_url)
            
            # Read CSV into pandas DataFrame
            df = pd.read_csv(
                csv_url,
                encoding='utf-8',
                low_memory=False
            )
            
            # Convert to list of dictionaries
            records = df.to_dict('records')
            
            logger.info(f"Retrieved {len(records)} records from CSV")
            return records
            
        except Exception as e:
            logger.error(f"Error scraping CSV {csv_url}: {e}")
            raise
    
    def scrape_parquet(self, parquet_url: str) -> List[Dict[str, Any]]:
        """
        Scrape data from Parquet file
        
        Args:
            parquet_url: URL to Parquet file
            
        Returns:
            List of records as dictionaries
        """
        try:
            logger.info(f"Scraping Parquet file: {parquet_url}")
            response = self._make_request(parquet_url)
            
            # Read Parquet into pandas DataFrame
            df = pd.read_parquet(parquet_url)
            
            # Convert to list of dictionaries
            records = df.to_dict('records')
            
            logger.info(f"Retrieved {len(records)} records from Parquet")
            return records
            
        except Exception as e:
            logger.error(f"Error scraping Parquet {parquet_url}: {e}")
            raise
    
    def scrape(self, source_url: str) -> tuple[List[Dict[str, Any]], bytes]:
        """
        Main scrape method - automatically detects file type and scrapes
        
        Args:
            source_url: Source URL (API, CSV, or Parquet)
            
        Returns:
            Tuple of (records, content_bytes)
        """
        url_lower = source_url.lower()
        
        # Determine file type and scrape accordingly
        if "/api/" in url_lower or url_lower.endswith(".json"):
            records = self.scrape_api(source_url)
            # For API, we don't have raw content, so create minimal representation
            import json
            content = json.dumps(records).encode('utf-8')
        elif url_lower.endswith(".csv"):
            records = self.scrape_csv(source_url)
            # Get raw CSV content
            response = self._make_request(source_url)
            content = response.content
        elif url_lower.endswith(".parquet"):
            records = self.scrape_parquet(source_url)
            # Get raw Parquet content
            response = self._make_request(source_url)
            content = response.content
        else:
            # Try API first, then CSV
            try:
                records = self.scrape_api(source_url)
                import json
                content = json.dumps(records).encode('utf-8')
            except:
                records = self.scrape_csv(source_url)
                response = self._make_request(source_url)
                content = response.content
        
        return records, content

