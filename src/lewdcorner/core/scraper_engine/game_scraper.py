"""
Complete game scraper with all functionality
"""
import logging
import time
import hashlib
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from lewdcorner.config import (
    BASE_URL, ALLOWED_FORUMS, THUMBS_DIR, HEADERS_DIR,
    MAX_RETRIES, RETRY_DELAY, IMPLICIT_WAIT
)
from lewdcorner.core.auth.auth_service import AuthService
from lewdcorner.core.scraper_engine.forum_parser import ForumParser
from lewdcorner.core.scraper_engine.metadata_extractor import MetadataExtractor
from lewdcorner.core.scraper_engine.breadcrumb_parser import BreadcrumbParser
from lewdcorner.core.scraper_engine.bookmarks_parser import BookmarksParser

logger = logging.getLogger(__name__)


class GameScraper:
    """Complete game scraping functionality"""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.driver = None
        self.session = None
        self.forum_parser = ForumParser()
        self.metadata_extractor = MetadataExtractor()
        self.breadcrumb_parser = BreadcrumbParser()
        self.bookmarks_parser = BookmarksParser()
    
    def initialize(self):
        """Initialize scraper"""
        self.driver = self.auth_service.get_driver()
        self._init_requests_session()
    
    def _init_requests_session(self):
        """Initialize requests session with cookies from driver"""
        if not self.session:
            self.session = requests.Session()
        
        # Copy cookies from Selenium
        if self.driver:
            for cookie in self.driver.get_cookies():
                self.session.cookies.set(cookie['name'], cookie['value'])
            
            # Set headers
            user_agent = self.driver.execute_script("return navigator.userAgent;")
            self.session.headers.update({
                'User-Agent': user_agent,
                'Referer': BASE_URL,
                'Accept': 'text/html,application/xhtml+xml,application/xml',
            })
    
    def make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute"""
        if not url:
            return ""
        if url.startswith(('http://', 'https://')):
            return url
        return urljoin(BASE_URL, url)
    
    def download_image(self, url: str, context: str = "", cache_dir: Path = THUMBS_DIR) -> str:
        """
        Download image with cookie-aware session
        
        Args:
            url: Image URL
            context: Context string for unique filename
            cache_dir: Directory to save image
            
        Returns:
            Local file path or empty string on failure
        """
        if not url:
            return ""
        
        url = self.make_absolute_url(url)
        
        # Create hash for filename
        hash_input = f"{url}{context}"
        filename = hashlib.md5(hash_input.encode()).hexdigest() + ".jpg"
        local_path = cache_dir / filename
        
        # Check if already cached
        if local_path.exists():
            logger.debug(f"Image already cached: {filename}")
            return str(local_path)
        
        # Ensure session initialized
        if not self.session:
            self._init_requests_session()
        
        # Download
        try:
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type:
                logger.warning(f"URL is not an image: {url}")
                return ""
            
            # Save to file
            cache_dir.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.debug(f"Downloaded image: {filename}")
            return str(local_path)
            
        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
            return ""
    
    def scan_forum(self, forum_url: str, max_pages: int = 10) -> List[Dict[str, Any]]:
        """
        Scan a forum for game threads
        
        Args:
            forum_url: Forum URL to scan
            max_pages: Maximum pages to scan
            
        Returns:
            List of game data dictionaries
        """
        self.initialize()
        
        all_games = []
        current_url = forum_url
        page_num = 1
        
        logger.info(f"Scanning forum: {forum_url}")
        
        while current_url and page_num <= max_pages:
            try:
                logger.info(f"Scanning page {page_num}: {current_url}")
                
                # Load page
                self.driver.get(current_url)
                
                # Wait for content
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".structItem--thread, .structItem"))
                )
                
                time.sleep(2)
                
                # Parse page
                html = self.driver.page_source
                games = self.forum_parser.parse_forum_page(html, current_url)
                
                logger.info(f"Found {len(games)} games on page {page_num}")
                
                # Download thumbnails
                for game in games:
                    if game.get('cover_image'):
                        local_path = self.download_image(
                            game['cover_image'],
                            context=game.get('url', '')
                        )
                        game['cover_image'] = local_path
                
                all_games.extend(games)
                
                # Check for next page
                if not self.forum_parser.has_next_page(html):
                    logger.info("No more pages")
                    break
                
                next_url = self.forum_parser.get_next_page_url(html, current_url)
                if not next_url or next_url == current_url:
                    break
                
                current_url = next_url
                page_num += 1
                time.sleep(RETRY_DELAY)
                
            except TimeoutException:
                logger.warning(f"Timeout on page {page_num}")
                break
            except Exception as e:
                logger.error(f"Error scanning page {page_num}: {e}")
                break
        
        logger.info(f"Scan complete: found {len(all_games)} total games")
        return all_games
    
    def scrape_game_details(self, url: str, retries: int = MAX_RETRIES) -> Optional[Dict[str, Any]]:
        """
        Scrape full game details from thread page
        
        Args:
            url: Game thread URL
            retries: Number of retries on failure
            
        Returns:
            Dictionary with game metadata
        """
        self.initialize()
        
        for attempt in range(retries):
            try:
                logger.info(f"Scraping game details: {url} (attempt {attempt + 1})")
                
                self.driver.get(url)
                
                # Wait for content
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".message-body, .p-title"))
                )
                
                time.sleep(2)
                
                # Parse page
                html = self.driver.page_source
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract all metadata
                metadata = self.metadata_extractor.extract_all_metadata(soup, url)
                
                # Get category and forum from breadcrumbs
                metadata['category'] = self.breadcrumb_parser.get_category(soup)
                metadata['forum_id'] = self.breadcrumb_parser.get_forum_id(soup)
                
                # Download header image if available
                if metadata.get('images'):
                    header_url = metadata['images'][0]
                    header_local = self.download_image(
                        header_url,
                        context=url,
                        cache_dir=HEADERS_DIR
                    )
                    metadata['header_image'] = header_local
                
                logger.info(f"Successfully scraped: {metadata.get('title', 'Unknown')}")
                return metadata
                
            except Exception as e:
                logger.error(f"Failed to scrape {url} (attempt {attempt + 1}): {e}")
                if attempt < retries - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"All retries exhausted for {url}")
                    return None
        
        return None
    
    def scrape_bookmarks(self, max_pages: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape user's bookmarked games
        
        Bookmarks page has different HTML structure than forums
        Now fetches full details for proper thumbnails
        """
        from lewdcorner.config import BOOKMARKS_URL
        
        self.initialize()
        
        all_games = []
        current_url = BOOKMARKS_URL
        page_num = 1
        
        logger.info(f"Scraping bookmarks: {BOOKMARKS_URL}")
        
        while current_url and page_num <= max_pages:
            try:
                logger.info(f"Scraping bookmarks page {page_num}: {current_url}")
                
                # Load page
                self.driver.get(current_url)
                
                # Wait for content
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".contentRow, .structItem"))
                )
                
                time.sleep(2)
                
                # Parse page using bookmarks parser
                html = self.driver.page_source
                games = self.bookmarks_parser.parse_bookmarks_page(html)
                
                logger.info(f"Found {len(games)} bookmarked games on page {page_num}")
                
                # For each bookmark, fetch full details to get proper thumbnails
                for game in games:
                    try:
                        if game.get('url'):
                            logger.debug(f"Fetching full details for bookmark: {game.get('title', 'Unknown')}")
                            
                            # Navigate to thread page
                            self.driver.get(game['url'])
                            time.sleep(1)
                            
                            # Parse the thread page
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                            
                            # Extract thumbnail from thread page (proper game thumbnail)
                            images = self.metadata_extractor.extract_images(soup)
                            if images:
                                # Download first image (main game thumbnail)
                                thumbnail_url = images[0]
                                local_path = self.download_image(
                                    thumbnail_url,
                                    context=game['url']
                                )
                                if local_path:
                                    game['cover_image'] = local_path
                                    logger.debug(f"Downloaded thumbnail for: {game.get('title', 'Unknown')}")
                            
                            # Also extract developer while we're here
                            title = game.get('title', '')
                            description = self.metadata_extractor.extract_description(soup)
                            developer = self.metadata_extractor.extract_developer(title, description, soup)
                            if developer and developer != "Unknown":
                                game['developer'] = developer
                            
                            time.sleep(0.5)  # Small delay between requests
                            
                    except Exception as e:
                        logger.error(f"Failed to fetch details for bookmark {game.get('title', 'Unknown')}: {e}")
                        # Fall back to listing thumbnail if available
                        if game.get('cover_image'):
                            local_path = self.download_image(
                                game['cover_image'],
                                context=game.get('url', '')
                            )
                            game['cover_image'] = local_path
                
                all_games.extend(games)
                
                # Check for next page
                if not self.bookmarks_parser.has_next_page(html):
                    logger.info("No more bookmark pages")
                    break
                
                next_url = self.bookmarks_parser.get_next_page_url(html, current_url)
                if not next_url or next_url == current_url:
                    break
                
                current_url = next_url
                page_num += 1
                time.sleep(RETRY_DELAY)
                
            except TimeoutException:
                logger.warning(f"Timeout on bookmarks page {page_num}")
                break
            except Exception as e:
                logger.error(f"Error scraping bookmarks page {page_num}: {e}")
                break
        
        logger.info(f"Bookmark scrape complete: found {len(all_games)} total games")
        return all_games
    
    def scrape_all_forums(self, max_pages_per_forum: int = 10) -> List[Dict[str, Any]]:
        """Scrape all allowed forums"""
        all_games = []
        
        for forum_url in ALLOWED_FORUMS:
            logger.info(f"Scanning forum: {forum_url}")
            games = self.scan_forum(forum_url, max_pages_per_forum)
            all_games.extend(games)
            time.sleep(3)  # Be nice to the server
        
        return all_games
    
    def like_thread(self, thread_url: str) -> bool:
        """Like a thread (requires Selenium)"""
        self.initialize()
        
        try:
            self.driver.get(thread_url)
            
            # Find and click like button
            like_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".actionBar-action--reaction"))
            )
            like_button.click()
            time.sleep(1)
            
            logger.info(f"Liked thread: {thread_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to like thread: {e}")
            return False
    
    def check_for_updates(self, game_url: str, last_known_version: str = "") -> Optional[Dict[str, Any]]:
        """
        Check if a game has been updated
        
        Returns dict with 'has_update' boolean and new metadata
        """
        self.initialize()
        
        try:
            self.driver.get(game_url)
            time.sleep(2)
            
            html = self.driver.page_source
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            title_elem = soup.select_one('h1.p-title-value')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            new_version = self.metadata_extractor.extract_version(title)
            
            has_update = (new_version != last_known_version and 
                         new_version != "Unknown" and 
                         last_known_version != "Unknown")
            
            return {
                'has_update': has_update,
                'old_version': last_known_version,
                'new_version': new_version,
                'title': title,
                'url': game_url
            }
            
        except Exception as e:
            logger.error(f"Failed to check for updates: {e}")
            return None
