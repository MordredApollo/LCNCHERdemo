"""
Main application window - Complete redesign with modern UI
"""
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QStatusBar, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMenu,
    QLineEdit, QComboBox, QStackedWidget, QScrollArea,
    QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QAction

from lewdcorner.core.auth.auth_service import AuthService
from lewdcorner.core.db.database import DatabaseManager
from lewdcorner.core.settings.settings_service import SettingsService
from lewdcorner.core.notifications.notification_service import NotificationService
from lewdcorner.workers.scraper_worker.scraper_worker import ScraperWorker
from lewdcorner.ui.widgets.game_grid import GameGrid
from lewdcorner.ui.dialogs.settings_dialog import SettingsDialog
from lewdcorner.ui.qss import load_theme

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main application window with modern UI"""
    
    def __init__(self, auth_service: AuthService, db_manager: DatabaseManager):
        super().__init__()
        
        self.auth_service = auth_service
        self.db = db_manager
        self.settings = SettingsService(db_manager)
        self.notifications = NotificationService(db_manager)
        
        self.scraper_worker = None
        self.current_view = "grid"  # grid or list
        self.current_games = []
        
        self.setWindowTitle("LewdCornerLauncher")
        self.resize(1600, 1000)
        
        # Apply theme
        self._apply_theme()
        
        self._setup_ui()
        self._connect_signals()
        
        # Load initial data
        QTimer.singleShot(100, self.refresh_library)
    
    def _apply_theme(self):
        """Apply theme from settings"""
        theme = self.settings.get('theme', 'dark')
        stylesheet = load_theme(theme)
        if stylesheet:
            self.setStyleSheet(stylesheet)
    
    def _setup_ui(self):
        """Setup modern UI components"""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Header
        header = self._create_header()
        main_layout.addWidget(header)
        
        # Content area (sidebar + main content)
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        # Sidebar
        sidebar = self._create_sidebar()
        content_splitter.addWidget(sidebar)
        
        # Main content area
        content_widget = self._create_content_area()
        content_splitter.addWidget(content_widget)
        
        # Set splitter sizes
        content_splitter.setStretchFactor(0, 0)
        content_splitter.setStretchFactor(1, 1)
        content_splitter.setSizes([250, 1350])
        
        main_layout.addWidget(content_splitter)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Menu bar
        self._create_menu_bar()
    
    def _create_header(self) -> QWidget:
        """Create modern header with account info"""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(70)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        
        # Logo/Title
        title_container = QVBoxLayout()
        title = QLabel("LewdCorner")
        title.setObjectName("sidebarTitle")
        title.setStyleSheet("background: transparent; border: none; font-size: 24px;")
        title_container.addWidget(title)
        
        subtitle = QLabel("Game Library Manager")
        subtitle.setObjectName("subheadingLabel")
        subtitle.setStyleSheet("font-size: 11px; color: #909090;")
        title_container.addWidget(subtitle)
        
        layout.addLayout(title_container)
        layout.addStretch()
        
        # Notification icon
        notif_btn = QPushButton(f"🔔 {self.db.get_unread_count()}")
        notif_btn.setObjectName("secondaryButton")
        notif_btn.setFixedHeight(40)
        notif_btn.clicked.connect(self.show_notifications)
        layout.addWidget(notif_btn)
        
        # Account info
        account_container = QHBoxLayout()
        account_container.setSpacing(12)
        
        # Username
        username = self.auth_service.current_username or "Guest"
        username_label = QLabel(f"👤 {username}")
        username_label.setObjectName("accountUsername")
        account_container.addWidget(username_label)
        
        layout.addLayout(account_container)
        
        return header
    
    def _create_sidebar(self) -> QWidget:
        """Create modern sidebar with navigation"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Navigation section
        nav_container = QWidget()
        nav_layout = QVBoxLayout(nav_container)
        nav_layout.setContentsMargins(10, 20, 10, 10)
        nav_layout.setSpacing(6)
        
        # Navigation label
        nav_label = QLabel("LIBRARY")
        nav_label.setStyleSheet("color: #909090; font-size: 11px; font-weight: 600; padding: 10px 10px 5px 10px;")
        nav_layout.addWidget(nav_label)
        
        # Navigation buttons
        self.btn_all_games = self._create_nav_button("📚 All Games", active=True)
        self.btn_all_games.clicked.connect(self.show_all_games)
        nav_layout.addWidget(self.btn_all_games)
        
        self.btn_favorites = self._create_nav_button("⭐ Favorites")
        self.btn_favorites.clicked.connect(self.show_favorites)
        nav_layout.addWidget(self.btn_favorites)
        
        self.btn_recent = self._create_nav_button("🕐 Recently Played")
        self.btn_recent.clicked.connect(self.show_recently_played)
        nav_layout.addWidget(self.btn_recent)
        
        self.btn_bookmarks = self._create_nav_button("🔖 Bookmarks")
        self.btn_bookmarks.clicked.connect(self.show_bookmarks)
        nav_layout.addWidget(self.btn_bookmarks)
        
        nav_layout.addSpacing(10)
        
        # Collections label
        coll_label = QLabel("COLLECTIONS")
        coll_label.setStyleSheet("color: #909090; font-size: 11px; font-weight: 600; padding: 10px 10px 5px 10px;")
        nav_layout.addWidget(coll_label)
        
        self.btn_collections = self._create_nav_button("📁 My Collections")
        self.btn_collections.clicked.connect(self.show_collections)
        nav_layout.addWidget(self.btn_collections)
        
        nav_layout.addSpacing(10)
        
        # Stats label
        stats_label = QLabel("STATISTICS")
        stats_label.setStyleSheet("color: #909090; font-size: 11px; font-weight: 600; padding: 10px 10px 5px 10px;")
        nav_layout.addWidget(stats_label)
        
        self.btn_stats = self._create_nav_button("📊 Statistics")
        self.btn_stats.clicked.connect(self.show_statistics)
        nav_layout.addWidget(self.btn_stats)
        
        layout.addWidget(nav_container)
        layout.addStretch()
        
        # Action buttons section
        actions_container = QWidget()
        actions_layout = QVBoxLayout(actions_container)
        actions_layout.setContentsMargins(10, 10, 10, 20)
        actions_layout.setSpacing(10)
        
        btn_scan = QPushButton("🔄 Scan Forums")
        btn_scan.setFixedHeight(40)
        btn_scan.clicked.connect(self.start_scan)
        actions_layout.addWidget(btn_scan)
        
        btn_settings = QPushButton("⚙️ Settings")
        btn_settings.setObjectName("secondaryButton")
        btn_settings.setFixedHeight(40)
        btn_settings.clicked.connect(self.show_settings)
        actions_layout.addWidget(btn_settings)
        
        layout.addWidget(actions_container)
        
        return sidebar
    
    def _create_nav_button(self, text: str, active: bool = False) -> QPushButton:
        """Create navigation button"""
        btn = QPushButton(text)
        btn.setObjectName("sidebarButton")
        btn.setProperty("active", active)
        btn.setFixedHeight(44)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn
    
    def _set_active_nav_button(self, button: QPushButton):
        """Set active navigation button"""
        for btn in [self.btn_all_games, self.btn_favorites, self.btn_recent, 
                    self.btn_bookmarks, self.btn_collections, self.btn_stats]:
            btn.setProperty("active", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        button.setProperty("active", True)
        button.style().unpolish(button)
        button.style().polish(button)
    
    def _create_content_area(self) -> QWidget:
        """Create main content area"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Stacked widget for grid/list view
        self.view_stack = QStackedWidget()
        
        # Grid view
        self.grid_view = GameGrid()
        self.grid_view.game_clicked.connect(self.on_game_clicked)
        self.grid_view.play_clicked.connect(self.on_play_game)
        self.view_stack.addWidget(self.grid_view)
        
        # List view (table)
        self.list_view = self._create_list_view()
        self.view_stack.addWidget(self.list_view)
        
        layout.addWidget(self.view_stack)
        
        return container
    
    def _create_toolbar(self) -> QWidget:
        """Create toolbar with search and filters"""
        toolbar = QFrame()
        toolbar.setObjectName("toolbar")
        toolbar.setFixedHeight(70)
        
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Search games...")
        self.search_box.setFixedHeight(40)
        self.search_box.setMinimumWidth(300)
        self.search_box.textChanged.connect(self.on_search)
        layout.addWidget(self.search_box)
        
        # Filter combo
        self.filter_combo = QComboBox()
        self.filter_combo.setFixedHeight(40)
        self.filter_combo.addItems([
            "All Games", "Favorites", "Recently Played", 
            "Completed", "In Progress", "Bookmarked"
        ])
        self.filter_combo.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.filter_combo)
        
        # Engine filter
        self.engine_filter = QComboBox()
        self.engine_filter.setFixedHeight(40)
        self.engine_filter.addItems([
            "All Engines", "Ren'Py", "Unity", "RPGM", "HTML", 
            "Unreal Engine", "Others"
        ])
        self.engine_filter.currentTextChanged.connect(self.on_filter_changed)
        layout.addWidget(self.engine_filter)
        
        layout.addStretch()
        
        # View toggle buttons
        self.btn_grid_view = QPushButton("▦ Grid")
        self.btn_grid_view.setFixedHeight(40)
        self.btn_grid_view.clicked.connect(lambda: self.switch_view("grid"))
        layout.addWidget(self.btn_grid_view)
        
        self.btn_list_view = QPushButton("☰ List")
        self.btn_list_view.setObjectName("secondaryButton")
        self.btn_list_view.setFixedHeight(40)
        self.btn_list_view.clicked.connect(lambda: self.switch_view("list"))
        layout.addWidget(self.btn_list_view)
        
        return toolbar
    
    def _create_list_view(self) -> QWidget:
        """Create table list view"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.game_table = QTableWidget()
        self.game_table.setColumnCount(7)
        self.game_table.setHorizontalHeaderLabels(
            ["Title", "Version", "Engine", "Status", "Developer", "Last Update", "Actions"]
        )
        self.game_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.game_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.game_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.game_table.customContextMenuRequested.connect(self.show_context_menu)
        self.game_table.cellDoubleClicked.connect(self.on_table_double_clicked)
        self.game_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.game_table)
        
        return container
    
    def _create_menu_bar(self):
        """Create menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        refresh_action = QAction("Refresh Library", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.refresh_library)
        file_menu.addAction(refresh_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        scan_action = QAction("Scan Forums", self)
        scan_action.triggered.connect(self.start_scan)
        tools_menu.addAction(scan_action)
        
        bookmarks_action = QAction("Scan Bookmarks", self)
        bookmarks_action.triggered.connect(self.scan_bookmarks)
        tools_menu.addAction(bookmarks_action)
        
        tools_menu.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings)
        tools_menu.addAction(settings_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        grid_action = QAction("Grid View", self)
        grid_action.triggered.connect(lambda: self.switch_view("grid"))
        view_menu.addAction(grid_action)
        
        list_action = QAction("List View", self)
        list_action.triggered.connect(lambda: self.switch_view("list"))
        view_menu.addAction(list_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _connect_signals(self):
        """Connect internal signals"""
        pass
    
    # === View Management ===
    
    def switch_view(self, view_type: str):
        """Switch between grid and list view"""
        self.current_view = view_type
        
        if view_type == "grid":
            self.view_stack.setCurrentIndex(0)
            self.btn_grid_view.setObjectName("")
            self.btn_list_view.setObjectName("secondaryButton")
        else:
            self.view_stack.setCurrentIndex(1)
            self.btn_list_view.setObjectName("")
            self.btn_grid_view.setObjectName("secondaryButton")
        
        # Reapply styles
        self.btn_grid_view.style().unpolish(self.btn_grid_view)
        self.btn_grid_view.style().polish(self.btn_grid_view)
        self.btn_list_view.style().unpolish(self.btn_list_view)
        self.btn_list_view.style().polish(self.btn_list_view)
        
        # Refresh display
        self._display_games(self.current_games)
    
    def _display_games(self, games: list):
        """Display games in current view"""
        self.current_games = games
        
        if self.current_view == "grid":
            # Convert to dict format
            games_data = [g.to_dict() if hasattr(g, 'to_dict') else g for g in games]
            self.grid_view.set_games(games_data)
        else:
            self._populate_table(games)
    
    def _populate_table(self, games):
        """Populate table with games"""
        self.game_table.setRowCount(0)
        
        for game in games:
            row = self.game_table.rowCount()
            self.game_table.insertRow(row)
            
            game_dict = game.to_dict() if hasattr(game, 'to_dict') else game
            
            self.game_table.setItem(row, 0, QTableWidgetItem(game_dict.get('title', '')))
            self.game_table.setItem(row, 1, QTableWidgetItem(game_dict.get('version', '') or 'Unknown'))
            self.game_table.setItem(row, 2, QTableWidgetItem(game_dict.get('engine', '') or 'Unknown'))
            self.game_table.setItem(row, 3, QTableWidgetItem(game_dict.get('status', '') or 'Unknown'))
            self.game_table.setItem(row, 4, QTableWidgetItem(game_dict.get('developer', '') or 'Unknown'))
            self.game_table.setItem(row, 5, QTableWidgetItem(
                str(game_dict.get('last_update', '')) if game_dict.get('last_update') else ''
            ))
            
            # Store game ID
            self.game_table.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, 
                game_dict.get('id')
            )
    
    # === Data Loading ===
    
    def refresh_library(self):
        """Refresh game library display"""
        try:
            games = self.db.get_all_games()
            self._display_games(games)
            self.status_bar.showMessage(f"Loaded {len(games)} games")
        except Exception as e:
            logger.error(f"Failed to refresh library: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load games: {e}")
    
    def show_all_games(self):
        """Show all games"""
        self._set_active_nav_button(self.btn_all_games)
        self.refresh_library()
    
    def show_favorites(self):
        """Show favorites"""
        self._set_active_nav_button(self.btn_favorites)
        games = self.db.filter_games({'is_favorite': True})
        self._display_games(games)
        self.status_bar.showMessage(f"Showing {len(games)} favorites")
    
    def show_recently_played(self):
        """Show recently played"""
        self._set_active_nav_button(self.btn_recent)
        games = self.db.get_recently_played(50)
        self._display_games(games)
        self.status_bar.showMessage(f"Showing {len(games)} recently played games")
    
    def show_bookmarks(self):
        """Show bookmarked games"""
        self._set_active_nav_button(self.btn_bookmarks)
        games = self.db.filter_games({'is_bookmarked': True})
        self._display_games(games)
        self.status_bar.showMessage(f"Showing {len(games)} bookmarked games")
    
    def show_collections(self):
        """Show collections"""
        self._set_active_nav_button(self.btn_collections)
        QMessageBox.information(self, "Collections", "Collections feature coming soon!")
    
    def show_statistics(self):
        """Show statistics"""
        self._set_active_nav_button(self.btn_stats)
        QMessageBox.information(self, "Statistics", "Statistics feature coming soon!")
    
    def show_notifications(self):
        """Show notifications"""
        unread = self.db.get_unread_notifications(20)
        if not unread:
            QMessageBox.information(self, "Notifications", "No new notifications")
        else:
            msg = "\n\n".join([f"{n.title}\n{n.message}" for n in unread[:5]])
            QMessageBox.information(self, f"Notifications ({len(unread)})", msg)
    
    # === Scanning ===
    
    def start_scan(self):
        """Start forum scanning"""
        if self.scraper_worker and self.scraper_worker.isRunning():
            QMessageBox.information(self, "Info", "Scan already in progress")
            return
        
        self.scraper_worker = ScraperWorker(self.auth_service, self.db)
        self.scraper_worker.set_scan_type('forums', max_pages=3)
        self.scraper_worker.progress.connect(self.on_scan_progress)
        self.scraper_worker.game_found.connect(self.on_game_found)
        self.scraper_worker.finished_signal.connect(self.on_scan_finished)
        self.scraper_worker.error_occurred.connect(self.on_scan_error)
        
        self.scraper_worker.start()
        self.status_bar.showMessage("Scanning started...")
    
    def scan_bookmarks(self):
        """Scan bookmarks"""
        if self.scraper_worker and self.scraper_worker.isRunning():
            QMessageBox.information(self, "Info", "Scan already in progress")
            return
        
        self.scraper_worker = ScraperWorker(self.auth_service, self.db)
        self.scraper_worker.set_scan_type('bookmarks', max_pages=10)
        self.scraper_worker.progress.connect(self.on_scan_progress)
        self.scraper_worker.game_found.connect(self.on_game_found)
        self.scraper_worker.finished_signal.connect(self.on_bookmark_scan_finished)
        self.scraper_worker.error_occurred.connect(self.on_scan_error)
        
        self.scraper_worker.start()
        self.status_bar.showMessage("Scanning bookmarks...")
    
    def on_scan_progress(self, message: str, percent: int):
        """Handle scan progress"""
        self.status_bar.showMessage(f"{message} ({percent}%)")
    
    def on_game_found(self, game_data: dict):
        """Handle game found during scan"""
        pass
    
    def on_scan_finished(self, total_games: int):
        """Handle scan completion"""
        self.status_bar.showMessage(f"Scan complete! Found {total_games} games")
        self.refresh_library()
        QMessageBox.information(self, "Scan Complete", f"Found {total_games} games")
    
    def on_bookmark_scan_finished(self, total_games: int):
        """Handle bookmark scan completion"""
        self.status_bar.showMessage(f"Bookmark scan complete! Found {total_games} bookmarked games")
        # Automatically switch to bookmarks view to show the results
        self.show_bookmarks()
        QMessageBox.information(self, "Bookmark Scan Complete", 
                              f"Found {total_games} bookmarked games.\n\nThe bookmarks are now displayed.")
    
    def on_scan_error(self, error_msg: str):
        """Handle scan error"""
        self.status_bar.showMessage("Scan error")
        QMessageBox.warning(self, "Scan Error", error_msg)
    
    # === Search and Filter ===
    
    def on_search(self, text: str):
        """Handle search"""
        if not text:
            self.refresh_library()
            return
        
        try:
            games = self.db.search_games(text)
            self._display_games(games)
            self.status_bar.showMessage(f"Found {len(games)} results")
        except Exception as e:
            logger.error(f"Search error: {e}")
    
    def on_filter_changed(self, filter_text: str):
        """Handle filter change"""
        try:
            filters = {}
            
            # Main filter
            if filter_text == "Favorites":
                filters['is_favorite'] = True
            elif filter_text == "Recently Played":
                games = self.db.get_recently_played(50)
                self._display_games(games)
                return
            elif filter_text == "Completed":
                filters['completed_status'] = 'Completed'
            elif filter_text == "Bookmarked":
                filters['is_bookmarked'] = True
            
            # Engine filter
            engine = self.engine_filter.currentText()
            if engine != "All Engines":
                filters['engine'] = engine
            
            if filters:
                games = self.db.filter_games(filters)
            else:
                games = self.db.get_all_games()
            
            self._display_games(games)
            self.status_bar.showMessage(f"Showing {len(games)} games")
        except Exception as e:
            logger.error(f"Filter error: {e}")
    
    # === Context Menu ===
    
    def show_context_menu(self, position):
        """Show context menu for game"""
        menu = QMenu()
        
        play_action = menu.addAction("▶ Play")
        menu.addSeparator()
        open_action = menu.addAction("🌐 Open in Browser")
        fav_action = menu.addAction("⭐ Toggle Favorite")
        refresh_action = menu.addAction("🔄 Refresh Metadata")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.setObjectName("dangerButton")
        
        action = menu.exec(self.game_table.viewport().mapToGlobal(position))
        
        if action == play_action:
            self.play_selected_game()
        elif action == open_action:
            self.open_game_in_browser()
        elif action == fav_action:
            self.toggle_favorite()
        elif action == refresh_action:
            self.refresh_game_metadata()
        elif action == delete_action:
            self.delete_game()
    
    # === Game Actions ===
    
    def on_game_clicked(self, game_id: int):
        """Handle game card click"""
        QMessageBox.information(self, "Game Details", f"Game ID: {game_id}\n\nDetails view coming soon!")
    
    def on_play_game(self, game_id: int):
        """Handle play button click"""
        game = self.db.get_game(game_id)
        if game:
            QMessageBox.information(self, "Play Game", f"Launching: {game.title}\n\nGame launch feature coming soon!")
    
    def on_table_double_clicked(self, row: int, column: int):
        """Handle double-click on table row"""
        game_id = self.game_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.on_game_clicked(game_id)
    
    def play_selected_game(self):
        """Play selected game"""
        current_row = self.game_table.currentRow()
        if current_row >= 0:
            game_id = self.game_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            self.on_play_game(game_id)
    
    def open_game_in_browser(self):
        """Open selected game in browser"""
        current_row = self.game_table.currentRow()
        if current_row >= 0:
            game_id = self.game_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            game = self.db.get_game(game_id)
            if game and game.url:
                import webbrowser
                webbrowser.open(game.url)
    
    def toggle_favorite(self):
        """Toggle favorite status"""
        current_row = self.game_table.currentRow()
        if current_row >= 0:
            game_id = self.game_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            game = self.db.get_game(game_id)
            if game:
                game.is_favorite = not game.is_favorite
                self.db.update_game(game)
                self.refresh_library()
    
    def refresh_game_metadata(self):
        """Refresh metadata for selected game"""
        current_row = self.game_table.currentRow()
        if current_row >= 0:
            game_id = self.game_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            game = self.db.get_game(game_id)
            if game and game.url:
                self.scraper_worker = ScraperWorker(self.auth_service, self.db)
                self.scraper_worker.set_scan_type('details', game_urls=[game.url])
                self.scraper_worker.finished_signal.connect(lambda: self.refresh_library())
                self.scraper_worker.start()
                self.status_bar.showMessage("Refreshing game metadata...")
    
    def delete_game(self):
        """Delete selected game"""
        current_row = self.game_table.currentRow()
        if current_row >= 0:
            game_id = self.game_table.item(current_row, 0).data(Qt.ItemDataRole.UserRole)
            game = self.db.get_game(game_id)
            if game:
                reply = QMessageBox.question(
                    self,
                    "Delete Game",
                    f"Are you sure you want to delete '{game.title}'?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.db.delete_game(game_id)
                    self.refresh_library()
    
    # === Settings ===
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = SettingsDialog(self.settings, self)
        dialog.theme_changed.connect(self._on_theme_changed)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec()
    
    def _on_theme_changed(self, theme: str):
        """Handle theme change"""
        self._apply_theme()
    
    def _on_settings_changed(self):
        """Handle settings change"""
        self.refresh_library()
    
    # === About ===
    
    def show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About LewdCornerLauncher",
            "LewdCornerLauncher v3.0\n\n"
            "A modern, beautiful game library manager for LewdCorner.\n\n"
            "Features:\n"
            "• Modern dark/light themes\n"
            "• Grid and list views\n"
            "• Full-text search\n"
            "• Automatic scraping\n"
            "• Bookmark sync\n"
            "• Download management\n"
            "• And much more!"
        )
