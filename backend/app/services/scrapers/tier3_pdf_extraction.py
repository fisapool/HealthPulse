"""
Tier 3 Scraper - PDF extraction
Medium confidence, used when Tier 1-2 are not available
"""
import logging
import requests
import pdfplumber
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from app.config import scraper_config
from app.services.source_gate import is_official_dosm_domain

logger = logging.getLogger(__name__)


class Tier3PDFExtractionScraper:
    """Scraper for extracting data from PDF files"""
    
    def __init__(self):
        self.timeout = scraper_config.request_timeout_seconds
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def _download_file(self, url: str) -> bytes:
        """
        Download PDF file content
        
        Args:
            url: URL to PDF file
            
        Returns:
            PDF content as bytes
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
    
    def extract_tables_from_pdf(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """
        Extract tables from PDF content
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            List of records extracted from tables
        """
        records = []
        
        try:
            import io
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract tables from page
                    tables = page.extract_tables()
                    
                    for table in tables:
                        if not table or len(table) < 2:
                            continue
                        
                        # First row as headers
                        headers = [str(cell).strip() if cell else "" for cell in table[0]]
                        
                        # Skip if no valid headers
                        if not any(headers):
                            continue
                        
                        # Process data rows
                        for row in table[1:]:
                            if not row or not any(row):
                                continue
                            
                            # Create record dictionary
                            record = {}
                            for i, header in enumerate(headers):
                                if i < len(row) and header:
                                    value = row[i]
                                    # Clean value
                                    if value:
                                        value = str(value).strip()
                                    else:
                                        value = None
                                    record[header] = value
                            
                            if record:
                                records.append(record)
            
            logger.info(f"Extracted {len(records)} records from PDF")
            return records
            
        except Exception as e:
            logger.error(f"Error extracting tables from PDF: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract all text from PDF (fallback if tables not found)
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Extracted text
        """
        try:
            import io
            text = ""
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise
    
    def scrape(self, source_url: str) -> tuple[List[Dict[str, Any]], bytes]:
        """
        Main scrape method - extracts data from PDF
        
        Args:
            source_url: URL to PDF file
            
        Returns:
            Tuple of (records, content_bytes)
        """
        try:
            logger.info(f"Extracting data from PDF: {source_url}")
            content = self._download_file(source_url)
            
            # Try to extract tables first
            records = self.extract_tables_from_pdf(content)
            
            # If no tables found, extract text and create a single record
            if not records:
                text = self.extract_text_from_pdf(content)
                if text:
                    records = [{"extracted_text": text}]
            
            logger.info(f"Retrieved {len(records)} records from PDF")
            return records, content
            
        except Exception as e:
            logger.error(f"Error scraping PDF {source_url}: {e}")
            raise

