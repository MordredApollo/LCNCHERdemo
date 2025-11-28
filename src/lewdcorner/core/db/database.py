"""
Complete database manager with all operations
"""
import sqlite3
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from lewdcorner.config import DB_PATH
from lewdcorner.core.db.schema import SCHEMA_SQL, FTS_TRIGGERS_SQL, SCHEMA_VERSION
from lewdcorner.core.db.models import Game, Tag, Label, Collection, PlaySession, Notification, Backup

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Complete database manager"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._connection = None
        logger.info(f"DatabaseManager initialized with path: {db_path}")
    
    def connect(self) -> sqlite3.Connection:
        """Establish database connection"""
        if self._connection:
            return self._connection
        
        try:
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA journal_mode = WAL")
            logger.info("Database connected")
            return self._connection
        except sqlite3.Error as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database closed")
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Query failed: {query[:100]}... - {e}")
            raise
    
    def executemany(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """Execute many queries"""
        conn = self.connect()
        try:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Executemany failed: {e}")
            raise
    
    def commit(self):
        """Commit transaction"""
        if self._connection:
            self._connection.commit()
    
    def rollback(self):
        """Rollback transaction"""
        if self._connection:
            self._connection.rollback()
    
    def initialize_schema(self):
        """Initialize database schema"""
        logger.info("Initializing database schema...")
        
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.executescript(SCHEMA_SQL)
            cursor.executescript(FTS_TRIGGERS_SQL)
        except sqlite3.Error as e:
            logger.error(f"Schema/Trigger execution failed: {e}")
            raise

        # Set schema version
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),)
        )
        
        conn.commit()
        logger.info("Database schema initialized")
    
    # === Game Operations ===
    
    def add_game(self, game: Game) -> int:
        """Add a new game"""
        data = game.to_dict()
        data.pop('id', None)
        data.pop('tags', None)
        data.pop('labels', None)
        data.pop('collections', None)
        
        keys = [k for k in data.keys() if data[k] is not None]
        values = [data[k] for k in keys]
        
        placeholders = ', '.join(['?' for _ in keys])
        columns = ', '.join(keys)
        
        query = f"INSERT INTO games ({columns}) VALUES ({placeholders})"
        cursor = self.execute(query, tuple(values))
        self.commit()
        
        game_id = cursor.lastrowid
        logger.info(f"Added game: {game.title} (ID: {game_id})")
        
        # Add tags if present
        if game.tags:
            self.add_tags_to_game(game_id, game.tags)
        
        return game_id
    
    def update_game(self, game: Game):
        """Update existing game"""
        if not game.id:
            raise ValueError("Game ID required for update")
        
        data = game.to_dict()
        data.pop('id')
        data.pop('tags', None)
        data.pop('labels', None)
        data.pop('collections', None)
        data['updated_date'] = datetime.now().isoformat()
        
        keys = [k for k in data.keys() if data[k] is not None]
        values = [data[k] for k in keys]
        
        set_clause = ', '.join([f"{k} = ?" for k in keys])
        query = f"UPDATE games SET {set_clause} WHERE id = ?"
        
        self.execute(query, tuple(values) + (game.id,))
        self.commit()
        
        logger.info(f"Updated game ID: {game.id}")
        
        # Update tags if present
        if game.tags:
            self.set_game_tags(game.id, game.tags)
    
    def upsert_game(self, game_data: Dict[str, Any]) -> int:
        """Insert or update game based on URL or thread_id"""
        # Check if game exists
        thread_id = game_data.get('thread_id')
        url = game_data.get('url')
        
        game_id = None
        if thread_id:
            row = self.execute("SELECT id FROM games WHERE thread_id = ?", (thread_id,)).fetchone()
            if row:
                game_id = row['id']
        elif url:
            row = self.execute("SELECT id FROM games WHERE url = ?", (url,)).fetchone()
            if row:
                game_id = row['id']
        
        if game_id:
            # Update
            game_data['id'] = game_id
            game = Game.from_dict(game_data)
            self.update_game(game)
            return game_id
        else:
            # Insert
            game = Game.from_dict(game_data)
            return self.add_game(game)
    
    def get_game(self, game_id: int) -> Optional[Game]:
        """Get game by ID"""
        row = self.execute("SELECT * FROM games WHERE id = ?", (game_id,)).fetchone()
        if not row:
            return None
        
        game_dict = dict(row)
        game = Game.from_dict(game_dict)
        
        # Load tags
        game.tags = self.get_game_tags(game_id)
        game.labels = self.get_game_labels(game_id)
        
        return game
    
    def get_game_by_url(self, url: str) -> Optional[Game]:
        """Get game by URL"""
        row = self.execute("SELECT * FROM games WHERE url = ?", (url,)).fetchone()
        if row:
            return Game.from_dict(dict(row))
        return None
    
    def get_game_by_thread_id(self, thread_id: str) -> Optional[Game]:
        """Get game by thread ID"""
        row = self.execute("SELECT * FROM games WHERE thread_id = ?", (thread_id,)).fetchone()
        if row:
            return Game.from_dict(dict(row))
        return None
    
    def get_all_games(self, include_hidden: bool = False) -> List[Game]:
        """Get all games"""
        if include_hidden:
            query = "SELECT * FROM games ORDER BY title"
        else:
            query = "SELECT * FROM games WHERE is_hidden = 0 ORDER BY title"
        
        rows = self.execute(query).fetchall()
        return [Game.from_dict(dict(row)) for row in rows]
    
    def search_games(self, search_query: str) -> List[Game]:
        """Full-text search games"""
        query = """
            SELECT g.* FROM games g
            JOIN games_fts ON g.id = games_fts.rowid
            WHERE games_fts MATCH ?
            ORDER BY rank
        """
        rows = self.execute(query, (search_query,)).fetchall()
        return [Game.from_dict(dict(row)) for row in rows]
    
    def filter_games(self, filters: Dict[str, Any]) -> List[Game]:
        """Filter games with various criteria"""
        query = "SELECT * FROM games WHERE 1=1"
        params = []
        
        if filters.get('is_favorite'):
            query += " AND is_favorite = 1"
        
        if filters.get('completed_status'):
            query += " AND completed_status = ?"
            params.append(filters['completed_status'])
        
        if filters.get('engine'):
            query += " AND engine = ?"
            params.append(filters['engine'])
        
        if filters.get('status'):
            query += " AND status = ?"
            params.append(filters['status'])
        
        if not filters.get('include_hidden', False):
            query += " AND is_hidden = 0"
        
        query += " ORDER BY title"
        
        rows = self.execute(query, tuple(params)).fetchall()
        return [Game.from_dict(dict(row)) for row in rows]
    
    def delete_game(self, game_id: int):
        """Delete a game"""
        self.execute("DELETE FROM games WHERE id = ?", (game_id,))
        self.commit()
        logger.info(f"Deleted game ID: {game_id}")
    
    def get_recently_played(self, limit: int = 20) -> List[Game]:
        """Get recently played games"""
        query = """
            SELECT * FROM games 
            WHERE last_played IS NOT NULL 
            ORDER BY last_played DESC 
            LIMIT ?
        """
        rows = self.execute(query, (limit,)).fetchall()
        return [Game.from_dict(dict(row)) for row in rows]
    
    def get_most_played(self, limit: int = 20) -> List[Game]:
        """Get most played games"""
        query = """
            SELECT * FROM games 
            WHERE play_time > 0 
            ORDER BY play_time DESC 
            LIMIT ?
        """
        rows = self.execute(query, (limit,)).fetchall()
        return [Game.from_dict(dict(row)) for row in rows]
    
    # === Tag Operations ===
    
    def add_tag(self, name: str) -> int:
        """Add a tag"""
        cursor = self.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        self.commit()
        
        if cursor.lastrowid:
            return cursor.lastrowid
        
        # Tag already existed, get its ID
        row = self.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
        return row['id'] if row else 0
    
    def get_tag_id(self, name: str) -> Optional[int]:
        """Get tag ID by name"""
        row = self.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()
        return row['id'] if row else None
    
    def add_tags_to_game(self, game_id: int, tags: List[str]):
        """Add multiple tags to a game"""
        for tag_name in tags:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            
            tag_id = self.add_tag(tag_name)
            self.execute(
                "INSERT OR IGNORE INTO game_tags (game_id, tag_id) VALUES (?, ?)",
                (game_id, tag_id)
            )
        self.commit()
    
    def get_game_tags(self, game_id: int) -> List[str]:
        """Get all tags for a game"""
        query = """
            SELECT t.name FROM tags t
            JOIN game_tags gt ON t.id = gt.tag_id
            WHERE gt.game_id = ?
        """
        rows = self.execute(query, (game_id,)).fetchall()
        return [row['name'] for row in rows]
    
    def set_game_tags(self, game_id: int, tags: List[str]):
        """Set tags for a game (replaces existing)"""
        # Remove existing
        self.execute("DELETE FROM game_tags WHERE game_id = ?", (game_id,))
        # Add new
        self.add_tags_to_game(game_id, tags)
    
    def get_all_tags(self) -> List[str]:
        """Get all tag names"""
        rows = self.execute("SELECT name FROM tags ORDER BY name").fetchall()
        return [row['name'] for row in rows]
    
    # === Label Operations ===
    
    def add_label(self, label: Label) -> int:
        """Add a label"""
        cursor = self.execute(
            "INSERT INTO labels (name, color, icon) VALUES (?, ?, ?)",
            (label.name, label.color, label.icon)
        )
        self.commit()
        return cursor.lastrowid
    
    def get_label(self, label_id: int) -> Optional[Label]:
        """Get label by ID"""
        row = self.execute("SELECT * FROM labels WHERE id = ?", (label_id,)).fetchone()
        if row:
            return Label(**dict(row))
        return None
    
    def get_all_labels(self) -> List[Label]:
        """Get all labels"""
        rows = self.execute("SELECT * FROM labels ORDER BY name").fetchall()
        return [Label(**dict(row)) for row in rows]
    
    def add_label_to_game(self, game_id: int, label_id: int):
        """Add label to game"""
        self.execute(
            "INSERT OR IGNORE INTO game_labels (game_id, label_id) VALUES (?, ?)",
            (game_id, label_id)
        )
        self.commit()
    
    def get_game_labels(self, game_id: int) -> List[str]:
        """Get label names for a game"""
        query = """
            SELECT l.name FROM labels l
            JOIN game_labels gl ON l.id = gl.label_id
            WHERE gl.game_id = ?
        """
        rows = self.execute(query, (game_id,)).fetchall()
        return [row['name'] for row in rows]
    
    # === Collection Operations ===
    
    def add_collection(self, collection: Collection) -> int:
        """Add a collection"""
        cursor = self.execute(
            "INSERT INTO collections (name, description, icon, color) VALUES (?, ?, ?, ?)",
            (collection.name, collection.description, collection.icon, collection.color)
        )
        self.commit()
        return cursor.lastrowid
    
    def get_collection(self, collection_id: int) -> Optional[Collection]:
        """Get collection by ID"""
        row = self.execute("SELECT * FROM collections WHERE id = ?", (collection_id,)).fetchone()
        if not row:
            return None
        
        collection = Collection(**dict(row))
        
        # Get game count
        count_row = self.execute(
            "SELECT COUNT(*) as count FROM collection_games WHERE collection_id = ?",
            (collection_id,)
        ).fetchone()
        collection.game_count = count_row['count'] if count_row else 0
        
        return collection
    
    def get_all_collections(self) -> List[Collection]:
        """Get all collections"""
        rows = self.execute("SELECT * FROM collections ORDER BY name").fetchall()
        collections = []
        for row in rows:
            collection = Collection(**dict(row))
            count_row = self.execute(
                "SELECT COUNT(*) as count FROM collection_games WHERE collection_id = ?",
                (collection.id,)
            ).fetchone()
            collection.game_count = count_row['count'] if count_row else 0
            collections.append(collection)
        return collections
    
    def add_game_to_collection(self, collection_id: int, game_id: int):
        """Add game to collection"""
        self.execute(
            "INSERT OR IGNORE INTO collection_games (collection_id, game_id) VALUES (?, ?)",
            (collection_id, game_id)
        )
        self.commit()
    
    def get_collection_games(self, collection_id: int) -> List[Game]:
        """Get all games in a collection"""
        query = """
            SELECT g.* FROM games g
            JOIN collection_games cg ON g.id = cg.game_id
            WHERE cg.collection_id = ?
            ORDER BY g.title
        """
        rows = self.execute(query, (collection_id,)).fetchall()
        return [Game.from_dict(dict(row)) for row in rows]
    
    # === Notification Operations ===
    
    def add_notification(self, notification: Notification) -> int:
        """Add a notification"""
        cursor = self.execute(
            """INSERT INTO notifications 
               (type, title, message, game_id, priority, data)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (notification.type, notification.title, notification.message,
             notification.game_id, notification.priority, notification.data)
        )
        self.commit()
        return cursor.lastrowid
    
    def get_unread_notifications(self, limit: int = 50) -> List[Notification]:
        """Get unread notifications"""
        query = """
            SELECT * FROM notifications 
            WHERE is_read = 0 
            ORDER BY created_at DESC 
            LIMIT ?
        """
        rows = self.execute(query, (limit,)).fetchall()
        return [Notification.from_dict(dict(row)) for row in rows]
    
    def mark_notification_read(self, notification_id: int):
        """Mark notification as read"""
        self.execute(
            "UPDATE notifications SET is_read = 1, read_at = ? WHERE id = ?",
            (datetime.now().isoformat(), notification_id)
        )
        self.commit()
    
    def get_unread_count(self) -> int:
        """Get count of unread notifications"""
        row = self.execute("SELECT COUNT(*) as count FROM notifications WHERE is_read = 0").fetchone()
        return row['count'] if row else 0
    
    # === Stats & Analytics ===
    
    def get_total_playtime(self) -> int:
        """Get total playtime across all games (seconds)"""
        row = self.execute("SELECT SUM(play_time) as total FROM games").fetchone()
        return row['total'] if row and row['total'] else 0
    
    def get_game_count(self) -> int:
        """Get total game count"""
        row = self.execute("SELECT COUNT(*) as count FROM games WHERE is_hidden = 0").fetchone()
        return row['count'] if row else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics"""
        total_games = self.get_game_count()
        total_playtime = self.get_total_playtime()
        
        favorites_row = self.execute("SELECT COUNT(*) as count FROM games WHERE is_favorite = 1").fetchone()
        favorites = favorites_row['count'] if favorites_row else 0
        
        completed_row = self.execute(
            "SELECT COUNT(*) as count FROM games WHERE completed_status = 'Completed'"
        ).fetchone()
        completed = completed_row['count'] if completed_row else 0
        
        return {
            'total_games': total_games,
            'total_playtime': total_playtime,
            'favorites': favorites,
            'completed': completed,
            'completion_rate': (completed / total_games * 100) if total_games > 0 else 0
        }
    
    # === Settings ===
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        row = self.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row:
            try:
                return json.loads(row['value'])
            except:
                return row['value']
        return default
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        if not isinstance(value, str):
            value = json.dumps(value)
        
        self.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.commit()
