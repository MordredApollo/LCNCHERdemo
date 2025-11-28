"""
Metadata extraction from game threads - FIXED AND IMPROVED
"""
import re
import logging
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup, Tag

from lewdcorner.config import ENGINE_LABELS, STATUS_LABELS

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts metadata from game pages"""
    
    @staticmethod
    def extract_engine_from_labels(soup: BeautifulSoup) -> str:
        """
        Extract engine from label CSS classes
        Labels have classes like 'label label--renpy'
        """
        try:
            labels = soup.select('.label')
            
            for label in labels:
                classes = label.get('class', [])
                for cls in classes:
                    if cls in ENGINE_LABELS:
                        return ENGINE_LABELS[cls]
            
        except Exception as e:
            logger.error(f"Failed to extract engine: {e}")
        
        return "Unknown"
    
    @staticmethod
    def extract_status_from_labels(soup: BeautifulSoup) -> str:
        """Extract status from labels (Completed, Ongoing, etc.)"""
        try:
            labels = soup.select('.label')
            
            for label in labels:
                text = label.get_text(strip=True)
                # Check exact matches
                if text in STATUS_LABELS:
                    return STATUS_LABELS[text]
                # Check case-insensitive
                for status_key in STATUS_LABELS:
                    if text.lower() == status_key.lower():
                        return STATUS_LABELS[status_key]
            
        except Exception as e:
            logger.error(f"Failed to extract status: {e}")
        
        return "Unknown"
    
    @staticmethod
    def extract_version(title: str) -> str:
        """Extract version from title string"""
        # Common patterns: [v1.0], [1.0], [Version 1.0], [Final], [v0.1.2]
        patterns = [
            r'\[v\.?(\d+[\d.]*[a-zA-Z0-9]*)\]',  # [v1.0], [v.1.0]
            r'\[(\d+\.[\d.]+[a-zA-Z0-9]*)\]',     # [1.0.1]
            r'\bv\.?(\d+\.[\d.]+[a-zA-Z0-9]*)\b',  # v1.0, v.1.0
            r'version\s+(\d+\.[\d.]+[a-zA-Z0-9]*)',  # version 1.0
            r'\[(Final|Completed|Complete)\]',     # [Final]
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"
    
    @staticmethod
    def extract_developer(title: str, description: str = "", soup: BeautifulSoup = None) -> str:
        """
        Extract developer name - FIXED TO NOT USE UPLOADER
        
        Priority:
        1. "Developer:" field in description/overview
        2. Thread meta information
        3. Title prefix (before game name)
        4. First bracket in title (but NOT last bracket which might be version)
        """
        developer = "Unknown"
        
        # METHOD 1: Look for "Developer:" in description
        if description:
            dev_patterns = [
                r'Developer:\s*(.+?)(?:\n|<br|$)',
                r'Dev:\s*(.+?)(?:\n|<br|$)',
                r'Made\s+by:\s*(.+?)(?:\n|<br|$)',
                r'Creator:\s*(.+?)(?:\n|<br|$)',
                r'Author:\s*(.+?)(?:\n|<br|$)',
            ]
            
            for pattern in dev_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    potential_dev = match.group(1).strip()
                    # Clean up HTML tags if any
                    potential_dev = re.sub(r'<[^>]+>', '', potential_dev)
                    potential_dev = potential_dev.split('\n')[0].strip()
                    # Remove common suffixes
                    potential_dev = re.sub(r'\s+\[.*?\]$', '', potential_dev)
                    if potential_dev and len(potential_dev) > 2:
                        return potential_dev
        
        # METHOD 2: Look in BeautifulSoup for structured data
        if soup:
            try:
                # Check for definition lists (common forum format)
                dls = soup.find_all('dl')
                for dl in dls:
                    dt = dl.find('dt')
                    dd = dl.find('dd')
                    if dt and dd:
                        dt_text = dt.get_text(strip=True).lower()
                        if any(keyword in dt_text for keyword in ['developer', 'dev', 'creator', 'author']):
                            dev_text = dd.get_text(strip=True)
                            if dev_text and len(dev_text) > 2 and len(dev_text) < 100:
                                return dev_text
                
                # Check for bold/strong labels
                for strong in soup.find_all(['strong', 'b']):
                    text = strong.get_text(strip=True).lower()
                    if any(keyword in text for keyword in ['developer:', 'dev:', 'creator:', 'author:']):
                        # Get next sibling text
                        next_text = strong.next_sibling
                        if next_text and isinstance(next_text, str):
                            dev_text = next_text.strip().lstrip(':').strip()
                            if dev_text and len(dev_text) > 2:
                                return dev_text
            except Exception as e:
                logger.debug(f"Soup parsing for developer failed: {e}")
        
        # METHOD 3: Extract from title - look for prefix patterns
        # Pattern: "Developer - Game Name [Version]"
        # Pattern: "[Developer] Game Name [Version]"
        
        # Try "Developer - Game" pattern
        dash_match = re.match(r'^([^-\[]+?)\s*-\s*(.+)$', title)
        if dash_match:
            potential_dev = dash_match.group(1).strip()
            # Check if it's not a version
            if not re.match(r'v?\d+\.', potential_dev) and len(potential_dev) > 2 and len(potential_dev) < 50:
                # Make sure it's not the entire title
                if len(potential_dev) < len(title) * 0.5:
                    return potential_dev
        
        # Try bracket pattern but ONLY first bracket, not last
        brackets = re.findall(r'\[([^\]]+)\]', title)
        if len(brackets) > 1:
            # If multiple brackets, first is likely developer, last is likely version
            potential_dev = brackets[0]
            # Verify it's not a version
            if not re.match(r'v?\d+[\d.]*', potential_dev):
                return potential_dev
        elif len(brackets) == 1:
            # Single bracket - could be dev or version, check carefully
            potential_dev = brackets[0]
            # Only use if it doesn't look like a version or status
            if not re.match(r'v?\d+[\d.]*', potential_dev) and potential_dev.lower() not in ['final', 'completed', 'complete', 'abandoned', 'ongoing', 'on hold']:
                if len(potential_dev) > 2 and len(potential_dev) < 50:
                    return potential_dev
        
        return developer
    
    @staticmethod
    def extract_description(soup: BeautifulSoup) -> str:
        """Extract game description from first post"""
        try:
            # Find first message body
            message_body = soup.select_one('.message-body .bbWrapper')
            if message_body:
                # Get text, preserving newlines
                description = message_body.get_text('\n', strip=True)
                # Limit length
                if len(description) > 5000:
                    description = description[:5000] + "..."
                return description
        except Exception as e:
            logger.error(f"Failed to extract description: {e}")
        
        return ""
    
    @staticmethod
    def extract_changelog(soup: BeautifulSoup) -> str:
        """Extract changelog from thread"""
        try:
            # Look for sections with "changelog" in heading
            for heading in soup.select('h1, h2, h3, h4, b, strong'):
                text = heading.get_text(strip=True).lower()
                if 'changelog' in text or 'change log' in text:
                    # Get following content
                    changelog_parts = []
                    for sibling in heading.next_siblings:
                        if isinstance(sibling, Tag):
                            if sibling.name in ['h1', 'h2', 'h3', 'h4']:
                                break
                            changelog_parts.append(sibling.get_text('\n', strip=True))
                    
                    if changelog_parts:
                        return '\n'.join(changelog_parts)[:3000]
        
        except Exception as e:
            logger.error(f"Failed to extract changelog: {e}")
        
        return ""
    
    @staticmethod
    def extract_tags(soup: BeautifulSoup, description: str = "") -> List[str]:
        """Extract tags/genres"""
        tags = []
        
        try:
            # Look in thread tags
            tag_elements = soup.select('.tagItem, [class*="tag"]')
            for tag_elem in tag_elements:
                tag_text = tag_elem.get_text(strip=True)
                if tag_text and len(tag_text) < 30:
                    tags.append(tag_text)
            
            # Look in description
            tag_patterns = [
                r'Tags?:\s*(.+?)(?:\n|$)',
                r'Genres?:\s*(.+?)(?:\n|$)',
            ]
            
            for pattern in tag_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    tag_text = match.group(1)
                    # Split by common separators
                    found_tags = re.split(r'[,/;]', tag_text)
                    tags.extend([t.strip() for t in found_tags if t.strip()])
        
        except Exception as e:
            logger.error(f"Failed to extract tags: {e}")
        
        # Deduplicate and limit
        tags = list(set(tags))[:20]
        return tags
    
    @staticmethod
    def extract_images(soup: BeautifulSoup) -> List[str]:
        """Extract image URLs from post"""
        images = []
        
        try:
            # Find images in message body
            # Look for images in first post
            first_post = soup.select_one('.message--post.js-post')
            if first_post:
                img_elements = first_post.select('img.bbImage, img[src]')
            else:
                img_elements = soup.select('.message-body img.bbImage, .message-body img[src]')
            
            for img in img_elements:
                src = img.get('src') or img.get('data-src') or img.get('data-url')
                if src:
                    # Filter out avatars, smilies, icons
                    if not any(x in src.lower() for x in ['avatar', 'smiley', 'emoji', 'icon', 'rating']):
                        images.append(src)
            
            # Also check for meta og:image
            og_image = soup.select_one('meta[property="og:image"]')
            if og_image and og_image.get('content'):
                images.insert(0, og_image['content'])
        
        except Exception as e:
            logger.error(f"Failed to extract images: {e}")
        
        # Deduplicate while preserving order
        seen = set()
        unique_images = []
        for img in images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
        
        return unique_images[:10]  # Limit to 10 images
    
    @staticmethod
    def extract_download_links(soup: BeautifulSoup, description: str = "") -> List[Dict[str, str]]:
        """
        Extract download links from post
        
        Returns list of dicts with 'host', 'url', 'label'
        """
        downloads = []
        
        try:
            # Look for download sections
            download_keywords = ['download', 'mirror', 'links', 'get the game']
            
            # METHOD 1: Find headings with "download"
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'b', 'strong']):
                heading_text = heading.get_text(strip=True).lower()
                if any(keyword in heading_text for keyword in download_keywords):
                    # Get links after this heading
                    for sibling in heading.next_siblings:
                        if isinstance(sibling, Tag):
                            # Stop at next heading
                            if sibling.name in ['h1', 'h2', 'h3', 'h4']:
                                break
                            
                            # Find links
                            links = sibling.find_all('a', href=True)
                            for link in links:
                                url = link['href']
                                text = link.get_text(strip=True)
                                host = MetadataExtractor._identify_host(url)
                                
                                if host:
                                    downloads.append({
                                        'host': host,
                                        'url': url,
                                        'label': text or host
                                    })
            
            # METHOD 2: Find all links and filter by known hosts
            all_links = soup.find_all('a', href=True)
            known_hosts = ['mega.nz', 'gofile.io', 'pixeldrain.com', 'workupload.com', 
                          'anonfiles.com', 'mediafire.com', 'drive.google.com',
                          'uploadhaven.com', 'mixdrop.co', 'krakenfiles.com']
            
            for link in all_links:
                url = link['href']
                text = link.get_text(strip=True)
                
                # Check if URL contains known host
                for host_pattern in known_hosts:
                    if host_pattern in url.lower():
                        host = MetadataExtractor._identify_host(url)
                        if host:
                            downloads.append({
                                'host': host,
                                'url': url,
                                'label': text or host
                            })
                        break
            
        except Exception as e:
            logger.error(f"Failed to extract download links: {e}")
        
        # Deduplicate by URL
        seen_urls = set()
        unique_downloads = []
        for dl in downloads:
            if dl['url'] not in seen_urls:
                seen_urls.add(dl['url'])
                unique_downloads.append(dl)
        
        return unique_downloads
    
    @staticmethod
    def _identify_host(url: str) -> Optional[str]:
        """Identify file host from URL"""
        url_lower = url.lower()
        
        hosts = {
            'mega.nz': 'Mega',
            'gofile.io': 'GoFile',
            'pixeldrain.com': 'Pixeldrain',
            'workupload.com': 'WorkUpload',
            'anonfiles.com': 'AnonFiles',
            'mediafire.com': 'MediaFire',
            'drive.google.com': 'Google Drive',
            'uploadhaven.com': 'UploadHaven',
            'mixdrop.co': 'Mixdrop',
            'krakenfiles.com': 'KrakenFiles',
            'dropbox.com': 'Dropbox',
        }
        
        for pattern, name in hosts.items():
            if pattern in url_lower:
                return name
        
        return None
    
    @staticmethod
    def extract_thread_id(url: str) -> Optional[str]:
        """Extract thread ID from URL"""
        # URL pattern: /threads/game-name.12345/
        match = re.search(r'/threads/[^/]+\.(\d+)', url)
        if match:
            return match.group(1)
        return None
    
    @staticmethod
    def extract_all_metadata(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract all metadata from a game page"""
        # Get title
        title_elem = soup.select_one('h1.p-title-value')
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        # Get description
        description = MetadataExtractor.extract_description(soup)
        
        # Extract developer (improved method)
        developer = MetadataExtractor.extract_developer(title, description, soup)
        
        # Extract various fields
        metadata = {
            'title': title,
            'url': url,
            'thread_id': MetadataExtractor.extract_thread_id(url),
            'version': MetadataExtractor.extract_version(title),
            'engine': MetadataExtractor.extract_engine_from_labels(soup),
            'status': MetadataExtractor.extract_status_from_labels(soup),
            'developer': developer,
            'description': description,
            'changelog': MetadataExtractor.extract_changelog(soup),
            'tags': MetadataExtractor.extract_tags(soup, description),
            'images': MetadataExtractor.extract_images(soup),
            'download_links': MetadataExtractor.extract_download_links(soup, description),
        }
        
        return metadata
