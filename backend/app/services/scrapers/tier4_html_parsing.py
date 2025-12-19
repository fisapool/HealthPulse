"""
Tier 4 Scraper - HTML table parsing
Medium confidence, used when Tier 1-3 are not available
"""
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import scraper_config
from app.services.source_gate import is_official_dosm_domain

logger = logging.getLogger(__name__)


class Tier4HTMLParsingScraper:
    """Scraper for parsing HTML tables"""
    
    def __init__(self):
        self.timeout = scraper_config.request_timeout_seconds
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _fetch_html(self, url: str) -> tuple[str, bytes]:
        """
        Fetch HTML content
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (html_text, content_bytes)
        """
        if not is_official_dosm_domain(url):
            raise ValueError(f"URL {url} is not from official DOSM domain")
        
        response = requests.get(
            url,
            timeout=self.timeout,
            headers={
                "User-Agent": "HealthPulse-Registry/1.0 (Data Collection Bot)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        )
        response.raise_for_status()
        return response.text, response.content
    
    def parse_html_tables(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse HTML tables into records
        
        Args:
            html: HTML content
            
        Returns:
            List of records extracted from tables
        """
        records = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            tables = soup.find_all('table')
            
            for table in tables:
                # Find header row (usually first <tr> with <th> tags)
                headers = []
                header_row = table.find('tr')
                if header_row:
                    th_tags = header_row.find_all(['th', 'td'])
                    headers = [th.get_text(strip=True) for th in th_tags if th.get_text(strip=True)]
                
                # If no headers in first row, try to infer from data
                if not headers:
                    # Try to get headers from first data row
                    first_data_row = table.find_all('tr')[1] if len(table.find_all('tr')) > 1 else None
                    if first_data_row:
                        headers = [f"column_{i+1}" for i in range(len(first_data_row.find_all(['td', 'th'])))]
                
                # Process data rows
                data_rows = table.find_all('tr')[1:] if headers else table.find_all('tr')
                
                for row in data_rows:
                    cells = row.find_all(['td', 'th'])
                    if not cells:
                        continue
                    
                    # Skip if this looks like a header row
                    if row == header_row:
                        continue
                    
                    # Create record
                    record = {}
                    for i, cell in enumerate(cells):
                        value = cell.get_text(strip=True)
                        if i < len(headers):
                            header = headers[i]
                        else:
                            header = f"column_{i+1}"
                        record[header] = value if value else None
                    
                    if record and any(record.values()):  # Only add if has data
                        records.append(record)
            
            logger.info(f"Extracted {len(records)} records from HTML tables")
            return records
            
        except Exception as e:
            logger.error(f"Error parsing HTML tables: {e}")
            raise
    
    def scrape(self, source_url: str) -> tuple[List[Dict[str, Any]], bytes]:
        """
        Main scrape method - parses HTML tables
        
        Args:
            source_url: URL to HTML page
            
        Returns:
            Tuple of (records, content_bytes)
        """
        try:
            logger.info(f"Parsing HTML page: {source_url}")
            html, content = self._fetch_html(source_url)
            
            records = self.parse_html_tables(html)
            
            # If no tables found, create a record with page text
            if not records:
                soup = BeautifulSoup(html, 'lxml')
                text = soup.get_text(separator=' ', strip=True)
                if text:
                    records = [{"extracted_text": text[:1000]}]  # Limit text length
            
            logger.info(f"Retrieved {len(records)} records from HTML")
            return records, content
            
        except Exception as e:
            logger.error(f"Error scraping HTML {source_url}: {e}")
            raise

