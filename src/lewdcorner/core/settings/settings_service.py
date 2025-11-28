"""
Settings service for managing application settings
"""
import logging
from typing import Any, Dict

from lewdcorner.core.db.database import DatabaseManager
from lewdcorner.config import (
    DEFAULT_THEME, DEFAULT_FONT_SIZE, DEFAULT_VIEW_MODE,
    CACHE_MAX_SIZE_MB, DEFAULT_CHECK_INTERVAL
)

logger = logging.getLogger(__name__)


class SettingsService:
    """Manages application settings"""
    
    DEFAULT_SETTINGS = {
        'theme': DEFAULT_THEME,
        'font_size': DEFAULT_FONT_SIZE,
        'view_mode': DEFAULT_VIEW_MODE,
        'cache_max_size_mb': CACHE_MAX_SIZE_MB,
        'check_interval': DEFAULT_CHECK_INTERVAL,
        'auto_check_updates': True,
        'show_thumbnails': True,
        'headless_scraping': True,
        'notifications_enabled': True,
        'sound_enabled': False,
        'minimize_to_tray': False,
        'start_minimized': False,
    }
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        self._cache = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get setting value"""
        if key in self._cache:
            return self._cache[key]
        
        value = self.db.get_setting(key, default)
        if value is None and key in self.DEFAULT_SETTINGS:
            value = self.DEFAULT_SETTINGS[key]
        
        self._cache[key] = value
        return value
    
    def set(self, key: str, value: Any):
        """Set setting value"""
        self.db.set_setting(key, value)
        self._cache[key] = value
        logger.debug(f"Setting updated: {key} = {value}")
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings"""
        settings = self.DEFAULT_SETTINGS.copy()
        # Override with stored values
        for key in settings.keys():
            stored_value = self.db.get_setting(key)
            if stored_value is not None:
                settings[key] = stored_value
        return settings
    
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        for key, value in self.DEFAULT_SETTINGS.items():
            self.set(key, value)
        self._cache.clear()
        logger.info("Settings reset to defaults")
