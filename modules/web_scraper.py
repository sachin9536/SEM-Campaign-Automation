"""
Web Scraper Module
Handles web scraping for brand and competitor websites to gather data for SEM campaigns.
Enhanced with anti-scraping measures, better content extraction, and robust error handling.
"""

import requests
import logging
import random
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import re
from urllib.parse import urljoin, urlparse
import pandas as pd
from typing import Dict, List, Any, Optional
import json


class WebScraper:
    """Enhanced web scraper for gathering SEM campaign data from websites."""
    
    def __init__(self, config):
        """Initialize the web scraper with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Anti-scraping measures
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
        ]
        
        # Enhanced session with rotating user agents and headers
        self.session = self._create_session()
        
        # Common navigation/header/footer selectors to exclude
        self.exclude_selectors = [
            'header', 'footer', 'nav', '.header', '.footer', '.navigation',
            '.menu', '.sidebar', '.breadcrumb', '.pagination', '.social',
            '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]',
            '.advertisement', '.ads', '.banner', '.popup', '.modal'
        ]
        
        # Service/product indicators
        self.service_indicators = [
            'service', 'services', 'offer', 'offering', 'what we do',
            'our services', 'services we offer', 'products', 'solutions',
            'expertise', 'specialties', 'capabilities', 'offerings',
            'what we provide', 'our expertise', 'specialized in'
        ]
    
    def _create_session(self) -> requests.Session:
        """Create a session with enhanced headers and settings."""
        session = requests.Session()
        
        # Rotate user agent
        user_agent = random.choice(self.user_agents)
        
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        return session
    
    def setup_selenium_driver(self) -> webdriver.Chrome:
        """Setup Selenium WebDriver with enhanced anti-detection options."""
        chrome_options = Options()
        
        # Basic options
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Anti-detection options
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Random user agent
        user_agent = random.choice(self.user_agents)
        chrome_options.add_argument(f'--user-agent={user_agent}')
        
        # Additional stealth options
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")
        # chrome_options.add_argument("--disable-javascript")  # Commented out to avoid issues
        
        try:
            # Try with ChromeDriverManager first
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Execute script to remove webdriver property
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
        except Exception as e:
            self.logger.warning(f"ChromeDriverManager failed: {e}")
            try:
                # Fallback: try without service specification
                driver = webdriver.Chrome(options=chrome_options)
                driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                return driver
            except Exception as e2:
                self.logger.error(f"All Selenium setup attempts failed: {e2}")
                raise Exception(f"Could not initialize Chrome driver: {e2}")
    
    def scrape_website(self, url: str, use_selenium: bool = True) -> Dict[str, Any]:
        """
        Main method to scrape a website and extract structured data.
        
        Args:
            url: Website URL to scrape
            use_selenium: Whether to use Selenium for dynamic content
            
        Returns:
            Dictionary containing structured data about the website
        """
        self.logger.info(f"Starting to scrape website: {url}")
        
        try:
            # Add random delay to avoid detection
            time.sleep(random.uniform(1, 3))
            
            # Respect config to disable Selenium entirely
            config_disables_selenium = bool(self.config.get('scraping', {}).get('use_selenium') is False)
            effective_use_selenium = use_selenium and not config_disables_selenium

            if effective_use_selenium:
                try:
                    return self._scrape_with_selenium(url)
                except Exception as selenium_error:
                    self.logger.warning(f"Selenium failed for {url}: {selenium_error}")
                    self.logger.info(f"Falling back to requests for {url}")
                    return self._scrape_with_requests(url)
            else:
                return self._scrape_with_requests(url)
                
        except Exception as e:
            self.logger.error(f"Error scraping website {url}: {e}")
            return self._create_error_response(url, str(e))
    
    def _scrape_with_selenium(self, url: str) -> Dict[str, Any]:
        """Scrape website using Selenium for dynamic content."""
        driver = None
        try:
            driver = self.setup_selenium_driver()
            
            # Set page load timeout
            driver.set_page_load_timeout(30)
            
            # Navigate to URL
            driver.get(url)
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(2, 4))
            
            # Get page source
            page_source = driver.page_source
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Extract structured data
            return self._extract_structured_data(soup, url)
            
        except TimeoutException:
            self.logger.warning(f"Timeout while loading {url}")
            return self._create_error_response(url, "Page load timeout")
        except WebDriverException as e:
            self.logger.error(f"Selenium error for {url}: {e}")
            return self._create_error_response(url, f"Selenium error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error scraping {url}: {e}")
            return self._create_error_response(url, str(e))
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _scrape_with_requests(self, url: str) -> Dict[str, Any]:
        """Scrape website using requests (for static content)."""
        try:
            # Add random delay
            time.sleep(random.uniform(1, 2))
            
            # Make request with timeout
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract structured data
            return self._extract_structured_data(soup, url)
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request error for {url}: {e}")
            return self._create_error_response(url, f"Request error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error scraping {url}: {e}")
            return self._create_error_response(url, str(e))
    
    def _extract_structured_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract structured data from parsed HTML."""
        try:
            # Clean the soup by removing unwanted elements
            self._clean_soup(soup)
            
            # Extract all data
            data = {
                'url': url,
                'title': self._extract_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'meta_keywords': self._extract_meta_keywords(soup),
                'headings': self._extract_headings(soup),
                'main_content': self._extract_main_content(soup),
                'products_services': self._extract_products_services(soup),
                'business_info': self._extract_business_info(soup),
                'contact_info': self._extract_contact_info(soup),
                'locations': self._extract_locations(soup),
                'keywords': self._extract_keywords_from_page(soup),
                'scraping_success': True,
                'timestamp': time.time()
            }
            
            self.logger.info(f"Successfully extracted data from {url}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error extracting structured data from {url}: {e}")
            return self._create_error_response(url, str(e))
    
    def _clean_soup(self, soup: BeautifulSoup) -> None:
        """Remove unwanted elements from the soup."""
        # Remove script and style elements
        for element in soup(["script", "style", "noscript"]):
            element.decompose()
        
        # Remove navigation, header, footer elements
        for selector in self.exclude_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Remove common ad and tracking elements
        ad_selectors = [
            '[class*="ad"]', '[class*="ads"]', '[class*="banner"]',
            '[id*="ad"]', '[id*="ads"]', '[id*="banner"]',
            'iframe', 'embed', 'object'
        ]
        
        for selector in ad_selectors:
            for element in soup.select(selector):
                element.decompose()
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1 if no title
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        # Fallback to og:description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            return og_desc.get('content', '').strip()
        
        return ""
    
    def _extract_meta_keywords(self, soup: BeautifulSoup) -> List[str]:
        """Extract meta keywords."""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            keywords_text = meta_keywords.get('content', '')
            return [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
        return []
    
    def _extract_headings(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract all headings with hierarchy."""
        headings = []
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            for heading in soup.find_all(tag):
                text = heading.get_text().strip()
                if text:
                    headings.append({
                        'level': tag,
                        'text': text,
                        'importance': self._calculate_heading_importance(tag)
                    })
        return headings
    
    def _calculate_heading_importance(self, tag: str) -> str:
        """Calculate heading importance based on tag level."""
        importance_map = {
            'h1': 'high',
            'h2': 'high',
            'h3': 'medium',
            'h4': 'medium',
            'h5': 'low',
            'h6': 'low'
        }
        return importance_map.get(tag, 'low')
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content while avoiding navigation and ads."""
        # Try to find main content area
        main_selectors = [
            'main', '[role="main"]', '.main', '.content', '.post',
            '.article', '.entry', '#main', '#content', '#post'
        ]
        
        main_content = ""
        
        for selector in main_selectors:
            main_element = soup.select_one(selector)
            if main_element:
                main_content = main_element.get_text(separator=' ', strip=True)
                break
        
        # If no main content found, extract from body
        if not main_content:
            body = soup.find('body')
            if body:
                main_content = body.get_text(separator=' ', strip=True)
        
        # Clean and limit content
        main_content = re.sub(r'\s+', ' ', main_content)
        return main_content[:10000]  # Limit to 10k characters
    
    def _extract_products_services(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract products and services with enhanced detection."""
        products_services = {
            'services': [],
            'products': [],
            'solutions': [],
            'offerings': []
        }
        
        # Look for service/product sections
        for indicator in self.service_indicators:
            # Find elements containing service indicators
            elements = soup.find_all(text=re.compile(indicator, re.IGNORECASE))
            
            for element in elements:
                parent = element.parent
                if parent:
                    # Look for nearby content
                    nearby_elements = parent.find_all(['li', 'p', 'div', 'span'])
                    
                    for elem in nearby_elements:
                        text = elem.get_text().strip()
                        if text and 5 < len(text) < 200:
                            # Categorize based on content
                            if any(word in text.lower() for word in ['service', 'consulting', 'support']):
                                products_services['services'].append(text)
                            elif any(word in text.lower() for word in ['product', 'item', 'goods']):
                                products_services['products'].append(text)
                            elif any(word in text.lower() for word in ['solution', 'system', 'platform']):
                                products_services['solutions'].append(text)
                            else:
                                products_services['offerings'].append(text)
        
        # Remove duplicates
        for key in products_services:
            products_services[key] = list(set(products_services[key]))
        
        return products_services
    
    def _extract_business_info(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract business information."""
        business_info = {
            'name': '',
            'description': '',
            'industry': '',
            'founded': '',
            'mission': ''
        }
        
        # Try to extract business name from various sources
        name_selectors = [
            '.company-name', '.business-name', '.brand-name',
            '[itemtype*="Organization"] .name', '.logo-text'
        ]
        
        for selector in name_selectors:
            element = soup.select_one(selector)
            if element:
                business_info['name'] = element.get_text().strip()
                break
        
        # Extract description from meta or content
        if not business_info['description']:
            business_info['description'] = self._extract_meta_description(soup)
        
        return business_info
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract contact information with enhanced patterns."""
        contact_info = {
            'phone': [],
            'email': [],
            'address': [],
            'social_media': []
        }
        
        text_content = soup.get_text()
        
        # Enhanced phone patterns
        phone_patterns = [
            r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',  # (123) 456-7890
            r'\+\d{1,3}[\s.-]?\d{3}[\s.-]?\d{3}[\s.-]?\d{4}',  # +1-234-567-8900
            r'\d{3}[\s.-]?\d{4}[\s.-]?\d{4}'  # 123-4567-8900
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text_content)
            contact_info['phone'].extend(matches)
        
        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        email_matches = re.findall(email_pattern, text_content)
        contact_info['email'].extend(email_matches)
        
        # Social media links
        social_patterns = [
            r'https?://(?:www\.)?(facebook|twitter|linkedin|instagram)\.com/[^\s<>"]+',
            r'(?:facebook|twitter|linkedin|instagram)\.com/[^\s<>"]+'
        ]
        
        for pattern in social_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            contact_info['social_media'].extend(matches)
        
        # Remove duplicates
        for key in contact_info:
            contact_info[key] = list(set(contact_info[key]))
        
        return contact_info
    
    def _extract_locations(self, soup: BeautifulSoup) -> List[str]:
        """Extract location information with enhanced patterns."""
        locations = []
        
        # Enhanced address patterns
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)',
            r'[A-Za-z\s]+,\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?',
            r'[A-Za-z\s]+,\s*[A-Za-z\s]+,\s*[A-Z]{2}',
            r'\d{5}(?:-\d{4})?'  # ZIP codes
        ]
        
        text_content = soup.get_text()
        for pattern in address_patterns:
            matches = re.findall(pattern, text_content)
            locations.extend(matches)
        
        return list(set(locations))
    
    def _extract_keywords_from_page(self, soup: BeautifulSoup) -> List[str]:
        """Extract potential keywords from page content."""
        keywords = set()
        
        # Extract from title
        title = self._extract_title(soup)
        if title:
            keywords.update(self._extract_keywords_from_text(title))
        
        # Extract from headings
        headings = self._extract_headings(soup)
        for heading in headings:
            keywords.update(self._extract_keywords_from_text(heading['text']))
        
        # Extract from meta description and keywords
        meta_desc = self._extract_meta_description(soup)
        if meta_desc:
            keywords.update(self._extract_keywords_from_text(meta_desc))
        
        # Extract from main content
        main_content = self._extract_main_content(soup)
        if main_content:
            keywords.update(self._extract_keywords_from_text(main_content))
        
        return list(keywords)
    
    def _extract_keywords_from_text(self, text: str) -> set:
        """Extract potential keywords from text."""
        keywords = set()
        
        # Clean text
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Enhanced stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'get', 'got', 'getting', 'go', 'going', 'gone', 'went', 'come',
            'came', 'coming', 'see', 'saw', 'seen', 'seeing', 'know', 'knew',
            'known', 'knowing', 'think', 'thought', 'thinking', 'want', 'wanted',
            'wanting', 'need', 'needed', 'needing', 'use', 'used', 'using'
        }
        
        # Single words
        for word in words:
            if (len(word) > 2 and 
                word not in stop_words and 
                not word.isdigit() and
                not word.startswith('www')):
                keywords.add(word)
        
        # Bigrams
        for i in range(len(words) - 1):
            bigram = f"{words[i]} {words[i+1]}"
            if (len(bigram) > 5 and 
                words[i] not in stop_words and 
                words[i+1] not in stop_words):
                keywords.add(bigram)
        
        # Trigrams
        for i in range(len(words) - 2):
            trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
            if (len(trigram) > 8 and 
                words[i] not in stop_words and 
                words[i+1] not in stop_words and
                words[i+2] not in stop_words):
                keywords.add(trigram)
        
        return keywords
    
    def _create_error_response(self, url: str, error_message: str) -> Dict[str, Any]:
        """Create a standardized error response."""
        return {
            'url': url,
            'scraping_success': False,
            'error_message': error_message,
            'timestamp': time.time(),
            'title': '',
            'meta_description': '',
            'headings': [],
            'main_content': '',
            'products_services': {'services': [], 'products': [], 'solutions': [], 'offerings': []},
            'business_info': {'name': '', 'description': '', 'industry': '', 'founded': '', 'mission': ''},
            'contact_info': {'phone': [], 'email': [], 'address': [], 'social_media': []},
            'locations': [],
            'keywords': []
        }
    
    def scrape_brand_website(self) -> Dict[str, Any]:
        """Scrape the brand website for relevant information."""
        brand_url = self.config['brand']['website']
        self.logger.info(f"Scraping brand website: {brand_url}")
        
        return self.scrape_website(brand_url)
    
    def scrape_competitor_websites(self) -> List[Dict[str, Any]]:
        """Scrape competitor websites for analysis."""
        competitors = self.config['competitors']
        competitor_data = []
        
        self.logger.info(f"Scraping {len(competitors)} competitor websites")
        
        for competitor in competitors:
            try:
                competitor_url = competitor['website']
                self.logger.info(f"Scraping competitor: {competitor['name']} - {competitor_url}")
                
                # Scrape the website
                comp_data = self.scrape_website(competitor_url)
                
                # Add competitor name
                comp_data['competitor_name'] = competitor['name']
                
                competitor_data.append(comp_data)
                
                # Add delay between requests
                time.sleep(random.uniform(2, 5))
                
            except Exception as e:
                self.logger.error(f"Error scraping competitor {competitor['name']}: {e}")
                continue
        
        return competitor_data
    
    def save_scraped_data(self, brand_data: Dict[str, Any], competitor_data: List[Dict[str, Any]], output_dir: str = 'output') -> None:
        """Save scraped data to files with enhanced structure."""
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Save brand data
        if brand_data:
            # Save as JSON for better structure preservation
            with open(f'{output_dir}/brand_data.json', 'w', encoding='utf-8') as f:
                json.dump(brand_data, f, indent=2, ensure_ascii=False)
            
            # Also save as CSV for compatibility
            brand_df = pd.DataFrame([brand_data])
            brand_df.to_csv(f'{output_dir}/brand_data.csv', index=False)
            
            self.logger.info(f"Brand data saved to {output_dir}/brand_data.json and brand_data.csv")
        
        # Save competitor data
        if competitor_data:
            # Save as JSON
            with open(f'{output_dir}/competitor_data.json', 'w', encoding='utf-8') as f:
                json.dump(competitor_data, f, indent=2, ensure_ascii=False)
            
            # Save as CSV
            comp_df = pd.DataFrame(competitor_data)
            comp_df.to_csv(f'{output_dir}/competitor_data.csv', index=False)
            
            self.logger.info(f"Competitor data saved to {output_dir}/competitor_data.json and competitor_data.csv")
        
        # Generate summary report
        self._generate_scraping_summary(brand_data, competitor_data, output_dir)
    
    def _generate_scraping_summary(self, brand_data: Dict[str, Any], competitor_data: List[Dict[str, Any]], output_dir: str) -> None:
        """Generate a summary report of the scraping results."""
        summary = {
            'scraping_timestamp': time.time(),
            'brand_website_scraped': brand_data.get('scraping_success', False),
            'competitors_scraped': len([c for c in competitor_data if c.get('scraping_success', False)]),
            'total_competitors': len(competitor_data),
            'brand_keywords_found': len(brand_data.get('keywords', [])),
            'total_competitor_keywords': sum(len(c.get('keywords', [])) for c in competitor_data),
            'brand_services_found': len(brand_data.get('products_services', {}).get('services', [])),
            'total_competitor_services': sum(len(c.get('products_services', {}).get('services', [])) for c in competitor_data)
        }
        
        # Save summary
        with open(f'{output_dir}/scraping_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Scraping summary saved to {output_dir}/scraping_summary.json") 