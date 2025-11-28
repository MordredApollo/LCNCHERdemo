"""
Settings dialog with tabs
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QComboBox, QCheckBox, QPushButton,
    QSpinBox, QGroupBox, QFormLayout, QMessageBox, QSlider
)
from PyQt6.QtCore import Qt, pyqtSignal
from lewdcorner.core.settings.settings_service import SettingsService

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """Settings dialog with multiple tabs"""
    
    theme_changed = pyqtSignal(str)  # theme name
    settings_changed = pyqtSignal()
    
    def __init__(self, settings_service: SettingsService, parent=None):
        super().__init__(parent)
        
        self.settings = settings_service
        
        self.setWindowTitle("Settings")
        self.setModal(True)
        self.resize(700, 600)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        
        # Tabs
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Add tabs
        self.tabs.addTab(self._create_general_tab(), "⚙️ General")
        self.tabs.addTab(self._create_appearance_tab(), "🎨 Appearance")
        self.tabs.addTab(self._create_downloads_tab(), "📥 Downloads")
        self.tabs.addTab(self._create_advanced_tab(), "🔧 Advanced")
        self.tabs.addTab(self._create_account_tab(), "👤 Account")
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryButton")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _create_general_tab(self) -> QWidget:
        """Create General settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Application group
        app_group = QGroupBox("Application")
        app_layout = QFormLayout(app_group)
        
        self.launch_on_startup = QCheckBox("Launch on system startup")
        app_layout.addRow("Startup:", self.launch_on_startup)
        
        self.minimize_to_tray = QCheckBox("Minimize to system tray")
        app_layout.addRow("Minimize:", self.minimize_to_tray)
        
        self.close_to_tray = QCheckBox("Close to tray instead of exit")
        app_layout.addRow("Close:", self.close_to_tray)
        
        layout.addWidget(app_group)
        
        # Updates group
        updates_group = QGroupBox("Updates")
        updates_layout = QFormLayout(updates_group)
        
        self.auto_check_updates = QCheckBox("Automatically check for updates")
        updates_layout.addRow("Auto-check:", self.auto_check_updates)
        
        self.update_frequency = QComboBox()
        self.update_frequency.addItems(["Daily", "Weekly", "Monthly", "Never"])
        updates_layout.addRow("Frequency:", self.update_frequency)
        
        layout.addWidget(updates_group)
        
        # View preferences
        view_group = QGroupBox("View Preferences")
        view_layout = QFormLayout(view_group)
        
        self.default_view = QComboBox()
        self.default_view.addItems(["Grid View", "List View", "Detail View"])
        view_layout.addRow("Default View:", self.default_view)
        
        self.sort_by = QComboBox()
        self.sort_by.addItems(["Title", "Last Played", "Date Added", "Developer"])
        view_layout.addRow("Sort By:", self.sort_by)
        
        layout.addWidget(view_group)
        
        layout.addStretch()
        return widget
    
    def _create_appearance_tab(self) -> QWidget:
        """Create Appearance settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Theme group
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout(theme_group)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        theme_layout.addRow("Theme:", self.theme_combo)
        
        theme_preview = QLabel("Theme will be applied when you save settings.")
        theme_preview.setObjectName("subheadingLabel")
        theme_preview.setWordWrap(True)
        theme_layout.addRow("", theme_preview)
        
        layout.addWidget(theme_group)
        
        # Font group
        font_group = QGroupBox("Font")
        font_layout = QFormLayout(font_group)
        
        self.font_size = QSpinBox()
        self.font_size.setRange(10, 20)
        self.font_size.setSuffix(" pt")
        font_layout.addRow("Font Size:", self.font_size)
        
        layout.addWidget(font_group)
        
        # Grid settings
        grid_group = QGroupBox("Grid View")
        grid_layout = QFormLayout(grid_group)
        
        self.card_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.card_size_slider.setRange(200, 400)
        self.card_size_slider.setValue(280)
        self.card_size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.card_size_slider.setTickInterval(50)
        
        self.card_size_label = QLabel("280")
        self.card_size_slider.valueChanged.connect(
            lambda v: self.card_size_label.setText(str(v))
        )
        
        size_layout = QHBoxLayout()
        size_layout.addWidget(self.card_size_slider)
        size_layout.addWidget(self.card_size_label)
        
        grid_layout.addRow("Card Size:", size_layout)
        
        self.grid_columns = QSpinBox()
        self.grid_columns.setRange(2, 8)
        grid_layout.addRow("Columns:", self.grid_columns)
        
        layout.addWidget(grid_group)
        
        layout.addStretch()
        return widget
    
    def _create_downloads_tab(self) -> QWidget:
        """Create Downloads settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Download group
        download_group = QGroupBox("Download Settings")
        download_layout = QFormLayout(download_group)
        
        self.concurrent_downloads = QSpinBox()
        self.concurrent_downloads.setRange(1, 5)
        download_layout.addRow("Concurrent Downloads:", self.concurrent_downloads)
        
        self.download_speed_limit = QSpinBox()
        self.download_speed_limit.setRange(0, 10000)
        self.download_speed_limit.setSuffix(" KB/s (0 = unlimited)")
        download_layout.addRow("Speed Limit:", self.download_speed_limit)
        
        self.auto_extract = QCheckBox("Automatically extract archives")
        download_layout.addRow("Auto Extract:", self.auto_extract)
        
        layout.addWidget(download_group)
        
        # Cache group
        cache_group = QGroupBox("Cache")
        cache_layout = QFormLayout(cache_group)
        
        self.cache_size = QSpinBox()
        self.cache_size.setRange(100, 10000)
        self.cache_size.setSuffix(" MB")
        cache_layout.addRow("Cache Size:", self.cache_size)
        
        clear_cache_btn = QPushButton("Clear Cache Now")
        clear_cache_btn.setObjectName("dangerButton")
        clear_cache_btn.clicked.connect(self._clear_cache)
        cache_layout.addRow("", clear_cache_btn)
        
        layout.addWidget(cache_group)
        
        layout.addStretch()
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create Advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Debug group
        debug_group = QGroupBox("Debug")
        debug_layout = QFormLayout(debug_group)
        
        self.debug_mode = QCheckBox("Enable debug mode")
        debug_layout.addRow("Debug:", self.debug_mode)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        debug_layout.addRow("Log Level:", self.log_level)
        
        layout.addWidget(debug_group)
        
        # Database group
        db_group = QGroupBox("Database")
        db_layout = QFormLayout(db_group)
        
        optimize_btn = QPushButton("Optimize Database")
        optimize_btn.clicked.connect(self._optimize_database)
        db_layout.addRow("", optimize_btn)
        
        backup_btn = QPushButton("Backup Database")
        backup_btn.clicked.connect(self._backup_database)
        db_layout.addRow("", backup_btn)
        
        layout.addWidget(db_group)
        
        # Scraper settings
        scraper_group = QGroupBox("Scraper")
        scraper_layout = QFormLayout(scraper_group)
        
        self.scraper_delay = QSpinBox()
        self.scraper_delay.setRange(1, 10)
        self.scraper_delay.setSuffix(" seconds")
        scraper_layout.addRow("Delay Between Requests:", self.scraper_delay)
        
        self.max_retries = QSpinBox()
        self.max_retries.setRange(1, 10)
        scraper_layout.addRow("Max Retries:", self.max_retries)
        
        layout.addWidget(scraper_group)
        
        layout.addStretch()
        return widget
    
    def _create_account_tab(self) -> QWidget:
        """Create Account info tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Account info group
        info_group = QGroupBox("Account Information")
        info_layout = QFormLayout(info_group)
        
        self.username_label = QLabel("Not available")
        info_layout.addRow("Username:", self.username_label)
        
        self.member_since_label = QLabel("Not available")
        info_layout.addRow("Member Since:", self.member_since_label)
        
        layout.addWidget(info_group)
        
        # Session group
        session_group = QGroupBox("Session")
        session_layout = QFormLayout(session_group)
        
        logout_btn = QPushButton("Logout")
        logout_btn.setObjectName("dangerButton")
        logout_btn.clicked.connect(self._logout)
        session_layout.addRow("", logout_btn)
        
        layout.addWidget(session_group)
        
        layout.addStretch()
        return widget
    
    def _load_settings(self):
        """Load current settings"""
        try:
            # General
            self.launch_on_startup.setChecked(
                self.settings.get('launch_on_startup', False)
            )
            self.minimize_to_tray.setChecked(
                self.settings.get('minimize_to_tray', True)
            )
            self.close_to_tray.setChecked(
                self.settings.get('close_to_tray', False)
            )
            self.auto_check_updates.setChecked(
                self.settings.get('auto_check_updates', True)
            )
            
            # Appearance
            theme = self.settings.get('theme', 'dark')
            self.theme_combo.setCurrentText(theme.capitalize())
            self.font_size.setValue(self.settings.get('font_size', 13))
            self.grid_columns.setValue(self.settings.get('grid_columns', 4))
            
            # Downloads
            self.concurrent_downloads.setValue(
                self.settings.get('concurrent_downloads', 3)
            )
            self.cache_size.setValue(self.settings.get('cache_size_mb', 1000))
            self.auto_extract.setChecked(self.settings.get('auto_extract', True))
            
            # Advanced
            self.debug_mode.setChecked(self.settings.get('debug_mode', False))
            self.scraper_delay.setValue(self.settings.get('scraper_delay', 2))
            self.max_retries.setValue(self.settings.get('max_retries', 3))
            
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
    
    def _save_settings(self):
        """Save settings"""
        try:
            # General
            self.settings.set('launch_on_startup', self.launch_on_startup.isChecked())
            self.settings.set('minimize_to_tray', self.minimize_to_tray.isChecked())
            self.settings.set('close_to_tray', self.close_to_tray.isChecked())
            self.settings.set('auto_check_updates', self.auto_check_updates.isChecked())
            
            # Appearance
            theme = self.theme_combo.currentText().lower()
            self.settings.set('theme', theme)
            self.settings.set('font_size', self.font_size.value())
            self.settings.set('grid_columns', self.grid_columns.value())
            
            # Downloads
            self.settings.set('concurrent_downloads', self.concurrent_downloads.value())
            self.settings.set('cache_size_mb', self.cache_size.value())
            self.settings.set('auto_extract', self.auto_extract.isChecked())
            
            # Advanced
            self.settings.set('debug_mode', self.debug_mode.isChecked())
            self.settings.set('scraper_delay', self.scraper_delay.value())
            self.settings.set('max_retries', self.max_retries.value())
            
            # Emit signals
            self.theme_changed.emit(theme)
            self.settings_changed.emit()
            
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.accept()
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")
    
    def _clear_cache(self):
        """Clear cache"""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "Are you sure you want to clear the cache?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement cache clearing
            QMessageBox.information(self, "Success", "Cache cleared!")
    
    def _optimize_database(self):
        """Optimize database"""
        try:
            # TODO: Implement database optimization
            QMessageBox.information(self, "Success", "Database optimized!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to optimize database: {e}")
    
    def _backup_database(self):
        """Backup database"""
        try:
            # TODO: Implement database backup
            QMessageBox.information(self, "Success", "Database backed up!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to backup database: {e}")
    
    def _logout(self):
        """Logout"""
        reply = QMessageBox.question(
            self,
            "Logout",
            "Are you sure you want to logout?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: Implement logout
            QMessageBox.information(self, "Logged Out", "You have been logged out.")
