"""
Complete database schema for LewdCorner Launcher
"""

# Schema version
SCHEMA_VERSION = 3

# Complete SQL schema
SCHEMA_SQL = """
-- Settings table
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Games table
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    url TEXT UNIQUE,
    thread_id TEXT UNIQUE,
    version TEXT,
    status TEXT DEFAULT 'Unknown',
    engine TEXT DEFAULT 'Unknown',
    developer TEXT,
    release_date TEXT,
    last_update TIMESTAMP,
    cover_image TEXT,
    header_image TEXT,
    rating REAL,
    description TEXT,
    changelog TEXT,
    local_path TEXT,
    install_size INTEGER,
    
    -- User data
    is_favorite INTEGER DEFAULT 0,
    is_hidden INTEGER DEFAULT 0,
    is_archived INTEGER DEFAULT 0,
    is_bookmarked INTEGER DEFAULT 0,
    completed_status TEXT DEFAULT 'Not Started',
    completion_percentage INTEGER DEFAULT 0,
    user_rating REAL,
    user_notes TEXT,
    
    -- Play tracking
    play_time INTEGER DEFAULT 0,
    play_count INTEGER DEFAULT 0,
    last_played TIMESTAMP,
    
    -- Metadata
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    scraped_date TIMESTAMP,
    last_checked TIMESTAMP,
    
    -- Categories
    category TEXT,
    forum_id TEXT
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game-Tags relationship
CREATE TABLE IF NOT EXISTS game_tags (
    game_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, tag_id),
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Labels table (custom user labels)
CREATE TABLE IF NOT EXISTS labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    color TEXT DEFAULT '#3498db',
    icon TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game-Labels relationship
CREATE TABLE IF NOT EXISTS game_labels (
    game_id INTEGER NOT NULL,
    label_id INTEGER NOT NULL,
    PRIMARY KEY (game_id, label_id),
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE,
    FOREIGN KEY (label_id) REFERENCES labels(id) ON DELETE CASCADE
);

-- Collections table
CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    icon TEXT DEFAULT '📁',
    color TEXT DEFAULT '#3498db',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Collection-Games relationship
CREATE TABLE IF NOT EXISTS collection_games (
    collection_id INTEGER NOT NULL,
    game_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (collection_id, game_id),
    FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

-- Play sessions table
CREATE TABLE IF NOT EXISTS play_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration INTEGER DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    game_id INTEGER,
    is_read INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    data TEXT,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

-- Backups table
CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    filepath TEXT,
    type TEXT DEFAULT 'manual',
    size INTEGER,
    game_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Cache metadata table
CREATE TABLE IF NOT EXISTS cache_metadata (
    thread_id TEXT PRIMARY KEY,
    last_checked TIMESTAMP,
    last_modified TIMESTAMP,
    version_hash TEXT,
    etag TEXT,
    needs_full_scrape INTEGER DEFAULT 0,
    check_frequency INTEGER DEFAULT 3600,
    retry_count INTEGER DEFAULT 0
);

-- Scrape queue table
CREATE TABLE IF NOT EXISTS scrape_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id TEXT NOT NULL,
    url TEXT,
    priority INTEGER DEFAULT 5,
    status TEXT DEFAULT 'pending',
    retries INTEGER DEFAULT 0,
    error_message TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(thread_id, status)
);

-- Download queue table
CREATE TABLE IF NOT EXISTS download_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER,
    url TEXT NOT NULL,
    filename TEXT,
    destination TEXT,
    size INTEGER,
    downloaded INTEGER DEFAULT 0,
    status TEXT DEFAULT 'pending',
    error_message TEXT,
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

-- Analytics table
CREATE TABLE IF NOT EXISTS analytics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    event_data TEXT,
    game_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (game_id) REFERENCES games(id) ON DELETE CASCADE
);

-- FTS5 Virtual table for full-text search
CREATE VIRTUAL TABLE IF NOT EXISTS games_fts USING fts5(
    title,
    description,
    developer,
    tags,
    engine,
    changelog,
    content='games',
    content_rowid='id'
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_games_thread_id ON games(thread_id);
CREATE INDEX IF NOT EXISTS idx_games_status ON games(status);
CREATE INDEX IF NOT EXISTS idx_games_engine ON games(engine);
CREATE INDEX IF NOT EXISTS idx_games_favorite ON games(is_favorite);
CREATE INDEX IF NOT EXISTS idx_games_completed_status ON games(completed_status);
CREATE INDEX IF NOT EXISTS idx_games_last_played ON games(last_played);
CREATE INDEX IF NOT EXISTS idx_games_added_date ON games(added_date);
CREATE INDEX IF NOT EXISTS idx_games_category ON games(category);

CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_game ON notifications(game_id);

CREATE INDEX IF NOT EXISTS idx_play_sessions_game ON play_sessions(game_id);
CREATE INDEX IF NOT EXISTS idx_play_sessions_start ON play_sessions(start_time);

CREATE INDEX IF NOT EXISTS idx_scrape_queue_status ON scrape_queue(status);
CREATE INDEX IF NOT EXISTS idx_scrape_queue_priority ON scrape_queue(priority);

CREATE INDEX IF NOT EXISTS idx_download_queue_status ON download_queue(status);
CREATE INDEX IF NOT EXISTS idx_download_queue_game ON download_queue(game_id);
""".strip()

# FTS5 triggers to keep search index synchronized
FTS_TRIGGERS_SQL = """
-- Drop existing triggers
DROP TRIGGER IF EXISTS games_ai;
DROP TRIGGER IF EXISTS games_ad;
DROP TRIGGER IF EXISTS games_au;

-- Insert trigger
CREATE TRIGGER games_ai AFTER INSERT ON games BEGIN
    INSERT INTO games_fts(rowid, title, description, developer, engine, tags, changelog)
    VALUES (new.id, new.title, new.description, new.developer, new.engine, '', new.changelog);
END;

-- Delete trigger
CREATE TRIGGER games_ad AFTER DELETE ON games BEGIN
    INSERT INTO games_fts(games_fts, rowid, title, description, developer, engine, tags, changelog)
    VALUES('delete', old.id, old.title, old.description, old.developer, old.engine, '', old.changelog);
END;

-- Update trigger
CREATE TRIGGER games_au AFTER UPDATE ON games BEGIN
    INSERT INTO games_fts(games_fts, rowid, title, description, developer, engine, tags, changelog)
    VALUES('delete', old.id, old.title, old.description, old.developer, old.engine, '', old.changelog);
    INSERT INTO games_fts(rowid, title, description, developer, engine, tags, changelog)
    VALUES (new.id, new.title, new.description, new.developer, new.engine, '', new.changelog);
END;
""".strip()
