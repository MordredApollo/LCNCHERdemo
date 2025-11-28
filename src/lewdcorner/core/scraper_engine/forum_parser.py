"""
Forum listing parser for extracting game threads
"""
import logging
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from lewdcorner.config import BASE_URL, ALLOWED_FORUMS
from lewdcorner.core.scraper_engine.breadcrumb_parser import BreadcrumbParser
from lewdcorner.core.scraper_engine.metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class ForumParser:
    """Parses forum listings to extract game threads"""
    
    def __init__(self):
        self.breadcrumb_parser = BreadcrumbParser()
        self.metadata_extractor = MetadataExtractor()
    
    def parse_forum_page(self, html: str, current_url: str) -> List[Dict[str, Any]]:
        """
        Parse a single forum page and extract game threads
        
        Returns list of game dictionaries with basic info
        """
        soup = BeautifulSoup(html, 'html.parser')
        games = []
        
        # Get category from breadcrumbs
        category = self.breadcrumb_parser.get_category(soup)
        forum_id = self.breadcrumb_parser.get_forum_id(soup)
        
        # Check if forum is allowed
        if forum_id and not self.breadcrumb_parser.is_allowed_forum(forum_id):
            logger.info(f"Skipping non-allowed forum: {forum_id}")
            return games
        
        # Find all thread items
        thread_items = soup.select('.structItem--thread, .structItem')
        
        logger.info(f"Found {len(thread_items)} threads on page")
        
        for item in thread_items:
            try:
                game_data = self._parse_thread_item(item, category, forum_id)
                if game_data:
                    games.append(game_data)
            except Exception as e:
                logger.error(f"Failed to parse thread item: {e}")
        
        return games
    
    def _parse_thread_item(self, item: BeautifulSoup, category: str, forum_id: str) -> Optional[Dict[str, Any]]:
        """Parse a single thread item"""
        # Get title and link
        title_elem = item.select_one('.structItem-title a[data-tp-primary]')
        if not title_elem:
            title_elem = item.select_one('.structItem-title a')
        
        if not title_elem:
            return None
        
        title = title_elem.get_text(strip=True)
        url = title_elem.get('href', '')
        
        # Make URL absolute
        if url and not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        if not url:
            return None
        
        # Extract thread ID
        thread_id = self.metadata_extractor.extract_thread_id(url)
        
        # Get labels
        labels = []
        label_elems = item.select('.label')
        for label in label_elems:
            labels.append(label.get_text(strip=True))
        
        # Extract engine from labels (CSS classes)
        engine = "Unknown"
        for label in label_elems:
            classes = label.get('class', [])
            for cls in classes:
                if cls.startswith('label--'):
                    from lewdcorner.config import ENGINE_LABELS
                    if cls in ENGINE_LABELS:
                        engine = ENGINE_LABELS[cls]
                        break
            if engine != "Unknown":
                break
        
        # Extract status from label text
        status = "Unknown"
        status_keywords = ["Completed", "Ongoing", "Abandoned", "On Hold"]
        for label_text in labels:
            if label_text in status_keywords:
                status = label_text
                break
        
        # Extract version from title
        version = self.metadata_extractor.extract_version(title)
        
        # Get thumbnail
        thumbnail_url = ""
        img_elem = item.select_one('.structItem-iconContainer img, .contentRow-figure img')
        if img_elem:
            thumbnail_url = img_elem.get('src') or img_elem.get('data-src', '')
            if thumbnail_url and not thumbnail_url.startswith('http'):
                thumbnail_url = urljoin(BASE_URL, thumbnail_url)
        
        # Get last update time
        last_update = ""
        time_elem = item.select_one('time.structItem-latestDate')
        if time_elem:
            last_update = time_elem.get('datetime') or time_elem.get('title', '')
        
        # Build game data
        game_data = {
            'title': title,
            'url': url,
            'thread_id': thread_id,
            'version': version,
            'engine': engine,
            'status': status,
            'cover_image': thumbnail_url,
            'category': category,
            'forum_id': forum_id,
            'last_update': last_update,
            'labels': labels,
            'developer': '',  # Will be filled by detail scrape if needed
        }
        
        return game_data
    
    def has_next_page(self, html: str) -> bool:
        """Check if there's a next page"""
        soup = BeautifulSoup(html, 'html.parser')
        next_button = soup.select_one('a.pageNav-jump--next')
        
        if not next_button:
            return False
        
        # Check if disabled
        classes = next_button.get('class', [])
        if 'is-disabled' in classes:
            return False
        
        return True
    
    def get_next_page_url(self, html: str, current_url: str) -> Optional[str]:
        """Get next page URL"""
        soup = BeautifulSoup(html, 'html.parser')
        next_button = soup.select_one('a.pageNav-jump--next')
        
        if not next_button:
            return None
        
        # Check if disabled
        classes = next_button.get('class', [])
        if 'is-disabled' in classes:
            return None
        
        next_url = next_button.get('href', '')
        if next_url and not next_url.startswith('http'):
            next_url = urljoin(BASE_URL, next_url)
        
        return next_url if next_url else None
