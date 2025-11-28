"""
Notification service for managing in-app notifications
"""
import logging
from typing import List, Optional
from datetime import datetime

from lewdcorner.core.db.database import DatabaseManager
from lewdcorner.core.db.models import Notification

logger = logging.getLogger(__name__)


class NotificationService:
    """Manages application notifications"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_notification(self, 
                          notification_type: str,
                          title: str,
                          message: str = "",
                          game_id: Optional[int] = None,
                          priority: int = 0) -> int:
        """Create a new notification"""
        notification = Notification(
            type=notification_type,
            title=title,
            message=message,
            game_id=game_id,
            priority=priority,
            created_at=datetime.now()
        )
        
        notification_id = self.db.add_notification(notification)
        logger.info(f"Created notification: {title}")
        return notification_id
    
    def notify_game_update(self, game_id: int, game_title: str, old_version: str, new_version: str):
        """Create game update notification"""
        return self.create_notification(
            "game_update",
            f"Update Available: {game_title}",
            f"Version {old_version} → {new_version}",
            game_id=game_id,
            priority=1
        )
    
    def notify_new_game(self, game_id: int, game_title: str):
        """Create new game notification"""
        return self.create_notification(
            "new_game",
            f"New Game Added: {game_title}",
            game_id=game_id
        )
    
    def notify_download_complete(self, game_id: int, game_title: str):
        """Create download complete notification"""
        return self.create_notification(
            "download_complete",
            f"Download Complete: {game_title}",
            game_id=game_id,
            priority=1
        )
    
    def get_unread_notifications(self, limit: int = 50) -> List[Notification]:
        """Get unread notifications"""
        return self.db.get_unread_notifications(limit)
    
    def mark_as_read(self, notification_id: int):
        """Mark notification as read"""
        self.db.mark_notification_read(notification_id)
    
    def mark_all_as_read(self):
        """Mark all notifications as read"""
        notifications = self.get_unread_notifications(limit=1000)
        for notif in notifications:
            if notif.id:
                self.mark_as_read(notif.id)
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        return self.db.get_unread_count()
