"""
Query helper classes for common database operations
"""
from typing import List, Dict, Any
from lewdcorner.core.db.models import Game, Collection, Notification


class GameQueries:
    """Helper class for game queries"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_favorites(self) -> List[Game]:
        """Get favorite games"""
        return self.db.filter_games({'is_favorite': True})
    
    def get_by_status(self, status: str) -> List[Game]:
        """Get games by completion status"""
        return self.db.filter_games({'completed_status': status})
    
    def get_by_engine(self, engine: str) -> List[Game]:
        """Get games by engine"""
        return self.db.filter_games({'engine': engine})
    
    def get_bookmarked(self) -> List[Game]:
        """Get bookmarked games"""
        query = "SELECT * FROM games WHERE is_bookmarked = 1 ORDER BY title"
        rows = self.db.execute(query).fetchall()
        return [Game.from_dict(dict(row)) for row in rows]
    
    def get_with_updates(self) -> List[Game]:
        """Get games that need updates (placeholder logic)"""
        # This would need more sophisticated logic
        return []


class CollectionQueries:
    """Helper class for collection queries"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_by_name(self, name: str) -> Collection:
        """Get collection by name"""
        row = self.db.execute(
            "SELECT * FROM collections WHERE name = ?", (name,)
        ).fetchone()
        if row:
            return Collection(**dict(row))
        return None


class NotificationQueries:
    """Helper class for notification queries"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_by_game(self, game_id: int) -> List[Notification]:
        """Get notifications for a game"""
        query = "SELECT * FROM notifications WHERE game_id = ? ORDER BY created_at DESC"
        rows = self.db.execute(query, (game_id,)).fetchall()
        return [Notification.from_dict(dict(row)) for row in rows]
    
    def get_by_type(self, notification_type: str) -> List[Notification]:
        """Get notifications by type"""
        query = "SELECT * FROM notifications WHERE type = ? ORDER BY created_at DESC"
        rows = self.db.execute(query, (notification_type,)).fetchall()
        return [Notification.from_dict(dict(row)) for row in rows]
