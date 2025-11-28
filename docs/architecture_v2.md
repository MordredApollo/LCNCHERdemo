# LewdCorner Launcher Architecture V2

## Structure

### Core (`src/lewdcorner/core/`)
- **Database**: SQLite with FTS5 (`database.py`).
- **Auth**: Service for managing Selenium session and Login (`auth_service.py`).
- **Scraper**: Selenium/BS4 based scraper using breadcrumbs for categorization (`scraper.py`).
- **Models**: Dataclasses for type safety (`models.py`).

### UI (`src/lewdcorner/ui/`)
- **MainWindow**: Main shell with Sidebar and Content Area.
- **LibraryView**: Grid display of games.
- **GameCard**: Widget for individual game.
- **LoginDialog**: Modal for authentication.

### Workers (`src/lewdcorner/workers/`)
- **ScraperWorker**: Background thread for scanning forums and updating DB.

## Data Flow
1. **Startup**: `main.py` init DB -> Check Auth -> Show Login if needed -> Show MainWindow.
2. **Scanning**: User clicks "Scan" -> `ScraperWorker` starts -> Uses `GameScraper` to fetch data -> Updates `db` -> Emits signals -> UI updates status.
3. **Library**: `LibraryView` queries `db` -> Populates `GameCard` grid.

## Database Schema
- `games`: Core game data.
- `games_fts`: Full-text search index.
- `tags`, `labels`, `collections`: Metadata.
- `play_sessions`: Analytics.

## Dependencies
- PyQt6
- Selenium / Undetected Chromedriver
- BeautifulSoup4
- Requests
- Cryptography
