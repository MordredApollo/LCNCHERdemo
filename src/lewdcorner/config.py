"""
Configuration module for LewdCorner Launcher
"""
from pathlib import Path
import os

# === Directory Paths ===
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
LOGS_DIR = ROOT_DIR / "logs"
CACHE_DIR = DATA_DIR / "cache"
THUMBS_DIR = DATA_DIR / "thumbs"
HEADERS_DIR = DATA_DIR / "headers"
BACKUPS_DIR = DATA_DIR / "backups"
PROFILE_DIR = DATA_DIR / "launcher_profile"

# === Database ===
DB_PATH = DATA_DIR / "lewdcorner.db"

# === Security ===
SESSION_FILE = DATA_DIR / "session.enc"
SALT_FILE = DATA_DIR / "salt.bin"
KEYRING_SERVICE = "LewdCornerLauncher"
KEYRING_USERNAME = "master_user"

# === Site URLs ===
BASE_URL = "https://lewdcorner.com"
LOGIN_URL = f"{BASE_URL}/login/"
BOOKMARKS_URL = f"{BASE_URL}/account/bookmarks"
ACCOUNT_URL = f"{BASE_URL}/account/"

# === Forum URLs (Allowed Forums) ===
FORUM_GAMES_6 = f"{BASE_URL}/forums/games.6/"  # Main Games
FORUM_GAMES_119 = f"{BASE_URL}/forums/games.119/"  # Adult Games
FORUM_PORTS_110 = f"{BASE_URL}/forums/ports.110/"  # Game Ports

ALLOWED_FORUMS = [FORUM_GAMES_6, FORUM_GAMES_119, FORUM_PORTS_110]

# === Scraper Settings ===
DEFAULT_HEADLESS = True
IMPLICIT_WAIT = 10
PAGE_LOAD_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# === Engine Labels (CSS class prefixes) ===
ENGINE_LABELS = {
    "label--renpy": "Ren'Py",
    "label--unity": "Unity",
    "label--rpgm": "RPG Maker",
    "label--html": "HTML",
    "label--unreal": "Unreal Engine",
    "label--flash": "Flash",
    "label--java": "Java",
    "label--others": "Others",
    "label--qsp": "QSP",
    "label--rags": "RAGS",
    "label--tads": "TADS",
    "label--adrift": "Adrift",
    "label--twine": "Twine",
    "label--wolf": "Wolf RPG",
}

# === Status Labels ===
STATUS_LABELS = {
    "Completed": "Completed",
    "Ongoing": "Ongoing",
    "On Hold": "On Hold",
    "Abandoned": "Abandoned",
}

# === Cache Settings ===
CACHE_MAX_SIZE_MB = 1000
CACHE_TTL_SECONDS = 3600  # 1 hour
IMAGE_CACHE_SIZE_MB = 500

# === Download Settings ===
MAX_CONCURRENT_DOWNLOADS = 3
DOWNLOAD_TIMEOUT = 300  # 5 minutes
CHUNK_SIZE = 8192

# === Notification Settings ===
NOTIFICATION_RETENTION_DAYS = 30
MAX_NOTIFICATIONS = 1000

# === Scheduler Settings ===
DEFAULT_CHECK_INTERVAL = 3600  # 1 hour
BACKGROUND_REFRESH_INTERVAL = 7200  # 2 hours

# === UI Settings ===
DEFAULT_THEME = "dark"
DEFAULT_FONT_SIZE = 12
DEFAULT_VIEW_MODE = "list"
THUMBNAIL_SIZE = 200
GRID_COLUMNS = 4

# === Logging ===
LOG_LEVEL = "INFO"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5

# === Application Settings ===
APP_NAME = "LewdCornerLauncher"
APP_VERSION = "3.0.0"
ORG_NAME = "LewdCorner"
ORG_DOMAIN = "lewdcorner.com"

# Ensure all directories exist
for directory in [DATA_DIR, LOGS_DIR, CACHE_DIR, THUMBS_DIR, HEADERS_DIR, BACKUPS_DIR, PROFILE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
