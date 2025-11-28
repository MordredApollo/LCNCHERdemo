"""
Breadcrumb parser for extracting forum/category information
"""
import logging
from typing import List, Optional
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class BreadcrumbParser:
    """Parses breadcrumb navigation to determine category/forum"""
    
    @staticmethod
    def parse_breadcrumbs(soup: BeautifulSoup) -> List[str]:
        """
        Extract breadcrumb trail from <ul class="p-breadcrumbs">
        
        Returns list of breadcrumb items in order
        """
        breadcrumbs = []
        
        try:
            # Find breadcrumb list
            breadcrumb_list = soup.select_one('ul.p-breadcrumbs')
            if not breadcrumb_list:
                logger.debug("No breadcrumbs found")
                return breadcrumbs
            
            # Extract each breadcrumb item
            items = breadcrumb_list.select('li')
            for item in items:
                # Look for the span with itemprop="name"
                name_span = item.select_one('span[itemprop="name"]')
                if name_span:
                    text = name_span.get_text(strip=True)
                    if text:
                        breadcrumbs.append(text)
                else:
                    # Fallback: get link text
                    link = item.select_one('a')
                    if link:
                        text = link.get_text(strip=True)
                        if text:
                            breadcrumbs.append(text)
            
            logger.debug(f"Parsed breadcrumbs: {breadcrumbs}")
            
        except Exception as e:
            logger.error(f"Failed to parse breadcrumbs: {e}")
        
        return breadcrumbs
    
    @staticmethod
    def get_category(soup: BeautifulSoup) -> str:
        """Get category name from breadcrumbs (last non-thread item)"""
        breadcrumbs = BreadcrumbParser.parse_breadcrumbs(soup)
        
        if not breadcrumbs:
            return "Unknown"
        
        # Last item is usually the current thread, so take second to last
        if len(breadcrumbs) >= 2:
            return breadcrumbs[-2]
        elif len(breadcrumbs) == 1:
            return breadcrumbs[0]
        
        return "Unknown"
    
    @staticmethod
    def get_forum_id(soup: BeautifulSoup) -> Optional[str]:
        """Extract forum ID from breadcrumb links"""
        try:
            breadcrumb_list = soup.select_one('ul.p-breadcrumbs')
            if not breadcrumb_list:
                return None
            
            # Look for forum links
            links = breadcrumb_list.select('a[href*="/forums/"]')
            for link in links:
                href = link.get('href', '')
                # Extract forum ID from URL like /forums/games.6/
                if '/forums/' in href:
                    parts = href.split('/forums/')
                    if len(parts) > 1:
                        forum_part = parts[1].rstrip('/')
                        # Extract number after dot
                        if '.' in forum_part:
                            forum_id = forum_part.split('.')[1]
                            return forum_id
            
        except Exception as e:
            logger.error(f"Failed to extract forum ID: {e}")
        
        return None
    
    @staticmethod
    def is_allowed_forum(forum_id: str, allowed_forums: List[str] = None) -> bool:
        """Check if forum ID is in allowed list"""
        if allowed_forums is None:
            # Default allowed forums
            allowed_forums = ['6', '119', '110']
        
        return forum_id in allowed_forums
