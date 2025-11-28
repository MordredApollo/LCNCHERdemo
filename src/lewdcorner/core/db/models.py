"""
Data models for database entities
"""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Game:
    """Game model"""
    id: Optional[int] = None
    title: str = ""
    url: str = ""
    thread_id: str = ""
    version: str = ""
    status: str = "Unknown"
    engine: str = "Unknown"
    developer: str = ""
    release_date: str = ""
    last_update: Optional[datetime] = None
    cover_image: str = ""
    header_image: str = ""
    rating: float = 0.0
    description: str = ""
    changelog: str = ""
    local_path: str = ""
    install_size: int = 0
    
    # User data
    is_favorite: bool = False
    is_hidden: bool = False
    is_archived: bool = False
    is_bookmarked: bool = False
    completed_status: str = "Not Started"
    completion_percentage: int = 0
    user_rating: float = 0.0
    user_notes: str = ""
    
    # Play tracking
    play_time: int = 0
    play_count: int = 0
    last_played: Optional[datetime] = None
    
    # Metadata
    added_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    scraped_date: Optional[datetime] = None
    last_checked: Optional[datetime] = None
    
    category: str = ""
    forum_id: str = ""
    
    # Related data (not in DB)
    tags: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    collections: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        # Convert booleans to integers for SQLite
        for key in ['is_favorite', 'is_hidden', 'is_archived', 'is_bookmarked']:
            if key in data:
                data[key] = 1 if data[key] else 0
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Game':
        """Create from dictionary"""
        # Convert integers to booleans
        for key in ['is_favorite', 'is_hidden', 'is_archived', 'is_bookmarked']:
            if key in data and isinstance(data[key], int):
                data[key] = bool(data[key])
        
        # Handle datetime fields
        for key in ['last_update', 'last_played', 'added_date', 'updated_date', 'scraped_date', 'last_checked']:
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = datetime.fromisoformat(data[key])
                except:
                    data[key] = None
        
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Tag:
    """Tag model"""
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Label:
    """Custom label model"""
    id: Optional[int] = None
    name: str = ""
    color: str = "#3498db"
    icon: str = ""
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Collection:
    """Collection model"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    icon: str = "📁"
    color: str = "#3498db"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    game_count: int = 0  # Not in DB, calculated
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlaySession:
    """Play session model"""
    id: Optional[int] = None
    game_id: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: int = 0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Notification:
    """Notification model"""
    id: Optional[int] = None
    type: str = "info"
    title: str = ""
    message: str = ""
    game_id: Optional[int] = None
    is_read: bool = False
    priority: int = 0
    created_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    data: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['is_read'] = 1 if data['is_read'] else 0
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Notification':
        if 'is_read' in data and isinstance(data['is_read'], int):
            data['is_read'] = bool(data['is_read'])
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


@dataclass
class Backup:
    """Backup model"""
    id: Optional[int] = None
    filename: str = ""
    filepath: str = ""
    type: str = "manual"
    size: int = 0
    game_count: int = 0
    created_at: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
