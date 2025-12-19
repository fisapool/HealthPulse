"""
Tier 5 Scraper - Browser automation (Playwright)
Low confidence, last resort when all other tiers fail
Only enabled if explicitly configured
"""
import logging
from typing import List, Dict, Any, Optional
from app.config import scraper_config

logger = logging.getLogger(__name__)


class Tier5BrowserAutomationScraper:
    """Scraper using browser automation (Playwright) - Last resort"""
    
    def __init__(self):
        self.enabled = scraper_config.enable_browser_automation
        if not self.enabled:
            logger.warning("Browser automation is disabled. Enable via DOSM_ENABLE_BROWSER_AUTOMATION=true")
    
    def scrape(self, source_url: str, **kwargs) -> tuple[List[Dict[str, Any]], bytes]:
        """
        Main scrape method using browser automation
        
        Args:
            source_url: URL to scrape
            **kwargs: Additional arguments (e.g., wait_selector, click_selectors)
            
        Returns:
            Tuple of (records, content_bytes)
        """
        if not self.enabled:
            raise RuntimeError(
                "Browser automation is disabled. "
                "This is a last-resort method and should only be used when all other tiers fail. "
                "Enable via DOSM_ENABLE_BROWSER_AUTOMATION=true environment variable."
            )
        
        try:
            from playwright.sync_api import sync_playwright
            
            logger.warning(
                f"Using browser automation (Tier 5) for {source_url}. "
                "This is resource-intensive and should be avoided if possible."
            )
            
            records = []
            html_content = None
            
            with sync_playwright() as p:
                # Launch browser
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Navigate to URL
                page.goto(source_url, wait_until="networkidle", timeout=60000)
                
                # Wait for specific selector if provided
                wait_selector = kwargs.get("wait_selector")
                if wait_selector:
                    page.wait_for_selector(wait_selector, timeout=30000)
                
                # Click elements if provided (for dynamic content)
                click_selectors = kwargs.get("click_selectors", [])
                for selector in click_selectors:
                    try:
                        page.click(selector, timeout=5000)
                        page.wait_for_timeout(2000)  # Wait for content to load
                    except:
                        logger.warning(f"Could not click selector: {selector}")
                
                # Get page content
                html_content = page.content()
                
                # Try to extract tables using BeautifulSoup
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html_content, 'lxml')
                tables = soup.find_all('table')
                
                for table in tables:
                    headers = []
                    header_row = table.find('tr')
                    if header_row:
                        th_tags = header_row.find_all(['th', 'td'])
                        headers = [th.get_text(strip=True) for th in th_tags if th.get_text(strip=True)]
                    
                    if not headers:
                        first_data_row = table.find_all('tr')[1] if len(table.find_all('tr')) > 1 else None
                        if first_data_row:
                            headers = [f"column_{i+1}" for i in range(len(first_data_row.find_all(['td', 'th'])))]
                    
                    data_rows = table.find_all('tr')[1:] if headers else table.find_all('tr')
                    
                    for row in data_rows:
                        if row == header_row:
                            continue
                        cells = row.find_all(['td', 'th'])
                        if not cells:
                            continue
                        
                        record = {}
                        for i, cell in enumerate(cells):
                            value = cell.get_text(strip=True)
                            if i < len(headers):
                                header = headers[i]
                            else:
                                header = f"column_{i+1}"
                            record[header] = value if value else None
                        
                        if record and any(record.values()):
                            records.append(record)
                
                browser.close()
            
            if not records:
                # Fallback: create record with page text
                if html_content:
                    soup = BeautifulSoup(html_content, 'lxml')
                    text = soup.get_text(separator=' ', strip=True)
                    if text:
                        records = [{"extracted_text": text[:1000]}]
            
            content = html_content.encode('utf-8') if html_content else b""
            
            logger.info(f"Retrieved {len(records)} records using browser automation")
            return records, content
            
        except ImportError:
            raise RuntimeError(
                "Playwright is not installed. Install with: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            logger.error(f"Error in browser automation scraping {source_url}: {e}")
            raise

