"""
Background worker for scraping operations
"""
import logging
from typing import List, Dict, Any
from PyQt6.QtCore import QThread, pyqtSignal

from lewdcorner.core.auth.auth_service import AuthService
from lewdcorner.core.scraper_engine.game_scraper import GameScraper
from lewdcorner.core.db.database import DatabaseManager
from lewdcorner.config import ALLOWED_FORUMS

logger = logging.getLogger(__name__)


class ScraperWorker(QThread):
    """Worker thread for scraping games"""
    
    # Signals
    progress = pyqtSignal(str, int)  # message, percentage
    game_found = pyqtSignal(dict)  # game data
    error_occurred = pyqtSignal(str)  # error message
    finished_signal = pyqtSignal(int)  # total games found
    
    def __init__(self, auth_service: AuthService, db_manager: DatabaseManager):
        super().__init__()
        self.auth_service = auth_service
        self.db = db_manager
        self.scraper = None
        self._should_stop = False
        self.scan_type = 'forums'  # 'forums', 'bookmarks', 'details'
        self.max_pages = 5
        self.game_urls = []  # For detail scraping
    
    def stop(self):
        """Stop the worker"""
        self._should_stop = True
    
    def set_scan_type(self, scan_type: str, max_pages: int = 5, game_urls: List[str] = None):
        """Configure scan parameters"""
        self.scan_type = scan_type
        self.max_pages = max_pages
        self.game_urls = game_urls or []
    
    def run(self):
        """Execute scraping task"""
        try:
            self.progress.emit("Initializing scraper...", 0)
            
            self.scraper = GameScraper(self.auth_service)
            self.scraper.initialize()
            
            if self.scan_type == 'forums':
                self._scan_forums()
            elif self.scan_type == 'bookmarks':
                self._scan_bookmarks()
            elif self.scan_type == 'details':
                self._scrape_details()
            
        except Exception as e:
            logger.error(f"Scraper worker error: {e}")
            self.error_occurred.emit(f"Scraping error: {str(e)}")
    
    def _scan_forums(self):
        """Scan all allowed forums"""
        all_games = []
        
        total_forums = len(ALLOWED_FORUMS)
        
        for idx, forum_url in enumerate(ALLOWED_FORUMS):
            if self._should_stop:
                break
            
            forum_name = forum_url.split('/')[-2] if '/' in forum_url else 'Unknown'
            self.progress.emit(f"Scanning forum {idx + 1}/{total_forums}: {forum_name}", 
                             int((idx / total_forums) * 90))
            
            try:
                games = self.scraper.scan_forum(forum_url, self.max_pages)
                
                # Save to database
                for game in games:
                    if self._should_stop:
                        break
                    
                    try:
                        game_id = self.db.upsert_game(game)
                        game['id'] = game_id
                        self.game_found.emit(game)
                        all_games.append(game)
                    except Exception as e:
                        logger.error(f"Failed to save game: {e}")
                
            except Exception as e:
                logger.error(f"Failed to scan forum {forum_url}: {e}")
                self.error_occurred.emit(f"Error scanning forum: {str(e)}")
        
        self.progress.emit("Scan complete!", 100)
        self.finished_signal.emit(len(all_games))
    
    def _scan_bookmarks(self):
        """Scan user bookmarks"""
        self.progress.emit("Scanning bookmarks...", 10)
        
        try:
            games = self.scraper.scrape_bookmarks(self.max_pages)
            
            self.progress.emit(f"Found {len(games)} bookmarked games", 50)
            
            # Save to database
            saved_count = 0
            for idx, game in enumerate(games):
                if self._should_stop:
                    break
                
                try:
                    game['is_bookmarked'] = True
                    game_id = self.db.upsert_game(game)
                    game['id'] = game_id
                    self.game_found.emit(game)
                    saved_count += 1
                    
                    progress = 50 + int((idx / len(games)) * 50)
                    self.progress.emit(f"Saved {saved_count}/{len(games)} games", progress)
                    
                except Exception as e:
                    logger.error(f"Failed to save bookmark: {e}")
            
            self.progress.emit("Bookmark scan complete!", 100)
            self.finished_signal.emit(saved_count)
            
        except Exception as e:
            logger.error(f"Failed to scan bookmarks: {e}")
            self.error_occurred.emit(f"Bookmark scan error: {str(e)}")
    
    def _scrape_details(self):
        """Scrape detailed info for specific games"""
        total = len(self.game_urls)
        
        for idx, url in enumerate(self.game_urls):
            if self._should_stop:
                break
            
            self.progress.emit(f"Scraping game {idx + 1}/{total}", int((idx / total) * 100))
            
            try:
                metadata = self.scraper.scrape_game_details(url)
                if metadata:
                    game_id = self.db.upsert_game(metadata)
                    metadata['id'] = game_id
                    self.game_found.emit(metadata)
            except Exception as e:
                logger.error(f"Failed to scrape details for {url}: {e}")
        
        self.progress.emit("Detail scraping complete!", 100)
        self.finished_signal.emit(len(self.game_urls))
