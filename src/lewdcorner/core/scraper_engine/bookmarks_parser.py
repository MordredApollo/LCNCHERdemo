"""
Bookmarks parser for extracting bookmarked threads
"""
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from lewdcorner.config import BASE_URL
from lewdcorner.core.scraper_engine.metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class BookmarksParser:
    """Parses bookmarks page to extract game threads"""
    
    def __init__(self):
        self.metadata_extractor = MetadataExtractor()
    
    def parse_bookmarks_page(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse bookmarks page and extract game threads
        
        Bookmarks page structure is different from forum listings
        Usually has:
        - .contentRow items
        - .contentRow-title with link
        - .contentRow-snippet with preview
        - .contentRow-figure with thumbnail
        """
        soup = BeautifulSoup(html, 'html.parser')
        games = []
        
        # Try different selectors for bookmark items
        # Structure 1: .contentRow
        bookmark_items = soup.select('.contentRow.contentRow--bookmark')
        if not bookmark_items:
            # Structure 2: Generic .contentRow
            bookmark_items = soup.select('.contentRow')
        if not bookmark_items:
            # Structure 3: .structItem (some forums use this)
            bookmark_items = soup.select('.structItem')
        
        logger.info(f"Found {len(bookmark_items)} bookmark items")
        
        for item in bookmark_items:
            try:
                game_data = self._parse_bookmark_item(item)
                if game_data:
                    # Mark as bookmarked
                    game_data['is_bookmarked'] = True
                    games.append(game_data)
            except Exception as e:
                logger.error(f"Failed to parse bookmark item: {e}")
        
        return games
    
    def _parse_bookmark_item(self, item: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse a single bookmark item"""
        
        # Get title and link
        title_elem = item.select_one('.contentRow-title a, .structItem-title a')
        if not title_elem:
            logger.debug("No title element found in bookmark item")
            return None
        
        title = title_elem.get_text(strip=True)
        url = title_elem.get('href', '')
        
        # Make URL absolute
        if url and not url.startswith('http'):
            url = urljoin(BASE_URL, url)
        
        if not url:
            logger.debug(f"No URL for bookmark: {title}")
            return None
        
        # Extract thread ID
        thread_id = self.metadata_extractor.extract_thread_id(url)
        
        # Get labels/tags
        labels = []
        label_elems = item.select('.label')
        for label in label_elems:
            labels.append(label.get_text(strip=True))
        
        # Extract engine from labels
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
        status_keywords = ["Completed", "Ongoing", "Abandoned", "On Hold", "On-Hold"]
        for label_text in labels:
            if label_text in status_keywords:
                status = label_text
                break
        
        # Extract version from title
        version = self.metadata_extractor.extract_version(title)
        
        # Get thumbnail
        thumbnail_url = ""
        img_elem = item.select_one('.contentRow-figure img, .structItem-iconContainer img')
        if img_elem:
            thumbnail_url = img_elem.get('src') or img_elem.get('data-src', '')
            if thumbnail_url and not thumbnail_url.startswith('http'):
                thumbnail_url = urljoin(BASE_URL, thumbnail_url)
        
        # Get snippet/description preview
        description = ""
        snippet_elem = item.select_one('.contentRow-snippet, .structItem-minor')
        if snippet_elem:
            description = snippet_elem.get_text(strip=True)
        
        # Get last update time
        last_update = ""
        time_elem = item.select_one('time, .u-dt')
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
            'description': description,
            'last_update': last_update,
            'labels': labels,
            'is_bookmarked': True,
            'developer': '',  # Will be filled by full details fetch
        }
        
        logger.debug(f"Parsed bookmark: {title}")
        return game_data
    
    def has_next_page(self, html: str) -> bool:
        """Check if there's a next page in bookmarks"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for next button
        next_button = soup.select_one('a.pageNav-jump--next')
        if not next_button:
            return False
        
        # Check if disabled
        classes = next_button.get('class', [])
        if 'is-disabled' in classes:
            return False
        
        return True
    
    def get_next_page_url(self, html: str, current_url: str) -> Optional[str]:
        """Get next page URL for bookmarks"""
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
