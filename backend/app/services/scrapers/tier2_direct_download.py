"""
Tier 2 Scraper - Direct CSV/XLSX file downloads
High confidence, used when Tier 1 (API) is not available
"""
import logging
import requests
import pandas as pd
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import scraper_config
from app.services.source_gate import is_official_dosm_domain

logger = logging.getLogger(__name__)


class Tier2DirectDownloadScraper:
    """Scraper for direct CSV/XLSX file downloads"""
    
    def __init__(self):
        self.timeout = scraper_config.request_timeout_seconds
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _download_file(self, url: str) -> bytes:
        """
        Download file content
        
        Args:
            url: URL to download
            
        Returns:
            File content as bytes
        """
        if not is_official_dosm_domain(url):
            raise ValueError(f"URL {url} is not from official DOSM domain")
        
        response = requests.get(
            url,
            timeout=self.timeout,
            headers={
                "User-Agent": "HealthPulse-Registry/1.0 (Data Collection Bot)"
            },
            stream=True
        )
        response.raise_for_status()
        return response.content
    
    def scrape_csv(self, csv_url: str) -> tuple[List[Dict[str, Any]], bytes]:
        """
        Scrape data from CSV file
        
        Args:
            csv_url: URL to CSV file
            
        Returns:
            Tuple of (records, content_bytes)
        """
        try:
            logger.info(f"Downloading CSV file: {csv_url}")
            content = self._download_file(csv_url)
            
            # Read CSV from bytes
            import io
            df = pd.read_csv(
                io.BytesIO(content),
                encoding='utf-8',
                low_memory=False
            )
            
            # Convert to list of dictionaries
            records = df.to_dict('records')
            
            logger.info(f"Retrieved {len(records)} records from CSV")
            return records, content
            
        except Exception as e:
            logger.error(f"Error downloading CSV {csv_url}: {e}")
            raise
    
    def scrape_xlsx(self, xlsx_url: str, sheet_name: Optional[str] = None) -> tuple[List[Dict[str, Any]], bytes]:
        """
        Scrape data from XLSX file
        
        Args:
            xlsx_url: URL to XLSX file
            sheet_name: Optional sheet name (reads first sheet if not specified)
            
        Returns:
            Tuple of (records, content_bytes)
        """
        try:
            logger.info(f"Downloading XLSX file: {xlsx_url}")
            content = self._download_file(xlsx_url)
            
            # Read XLSX from bytes
            import io
            if sheet_name:
                df = pd.read_excel(io.BytesIO(content), sheet_name=sheet_name)
            else:
                # Read first sheet
                df = pd.read_excel(io.BytesIO(content), sheet_name=0)
            
            # Convert to list of dictionaries
            records = df.to_dict('records')
            
            logger.info(f"Retrieved {len(records)} records from XLSX")
            return records, content
            
        except Exception as e:
            logger.error(f"Error downloading XLSX {xlsx_url}: {e}")
            raise
    
    def scrape(self, source_url: str, **kwargs) -> tuple[List[Dict[str, Any]], bytes]:
        """
        Main scrape method - automatically detects file type and scrapes
        
        Args:
            source_url: Source URL (CSV or XLSX)
            **kwargs: Additional arguments (e.g., sheet_name for XLSX)
            
        Returns:
            Tuple of (records, content_bytes)
        """
        url_lower = source_url.lower()
        
        if url_lower.endswith(".csv"):
            return self.scrape_csv(source_url)
        elif url_lower.endswith((".xlsx", ".xls")):
            sheet_name = kwargs.get("sheet_name")
            return self.scrape_xlsx(source_url, sheet_name=sheet_name)
        else:
            # Try CSV first, then XLSX
            try:
                return self.scrape_csv(source_url)
            except:
                return self.scrape_xlsx(source_url)

