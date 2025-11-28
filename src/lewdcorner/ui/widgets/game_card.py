"""
Game card widget for grid view
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPixmap, QPainter, QBrush, QColor
from pathlib import Path


class GameCard(QFrame):
    """Card widget displaying game information"""
    
    clicked = pyqtSignal(int)  # game_id
    play_clicked = pyqtSignal(int)  # game_id
    
    def __init__(self, game_data: dict, parent=None):
        super().__init__(parent)
        
        self.game_id = game_data.get('id')
        self.game_data = game_data
        
        self.setObjectName("gameCard")
        self.setFixedSize(280, 380)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup card UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Image container
        image_container = QWidget()
        image_container.setObjectName("gameCardImage")
        image_container.setFixedHeight(200)
        
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(False)
        
        # Load image
        self._load_image()
        
        image_layout.addWidget(self.image_label)
        layout.addWidget(image_container)
        
        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 12, 12, 12)
        content_layout.setSpacing(8)
        
        # Title
        title = self.game_data.get('title', 'Unknown Game')
        if len(title) > 60:
            title = title[:57] + "..."
        
        title_label = QLabel(title)
        title_label.setObjectName("gameCardTitle")
        title_label.setWordWrap(True)
        title_label.setMaximumHeight(50)
        content_layout.addWidget(title_label)
        
        # Developer
        developer = self.game_data.get('developer') or 'Unknown'
        if developer and developer != "Unknown" and developer.strip():
            developer_label = QLabel(f"👤 {developer}")
            developer_label.setObjectName("gameCardMeta")
            developer_label.setStyleSheet("font-weight: 600; color: #6A9FB5;")
            content_layout.addWidget(developer_label)
        
        # Version
        version = self.game_data.get('version') or 'Unknown'
        if version and version.strip():
            version_label = QLabel(f"Version: {version}")
            version_label.setObjectName("gameCardMeta")
            content_layout.addWidget(version_label)
        
        # Engine
        engine = self.game_data.get('engine') or 'Unknown'
        if engine and engine.strip():
            engine_label = QLabel(f"Engine: {engine}")
            engine_label.setObjectName("gameCardMeta")
            content_layout.addWidget(engine_label)
        
        # Status
        status = self.game_data.get('status') or 'Unknown'
        if status and status.strip():
            status_label = QLabel(f"Status: {status}")
            status_label.setObjectName("gameCardMeta")
            content_layout.addWidget(status_label)
        
        content_layout.addStretch()
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        play_btn = QPushButton("▶ Play")
        play_btn.setFixedHeight(32)
        play_btn.clicked.connect(lambda: self.play_clicked.emit(self.game_id))
        
        info_btn = QPushButton("ℹ Info")
        info_btn.setObjectName("secondaryButton")
        info_btn.setFixedHeight(32)
        info_btn.clicked.connect(lambda: self.clicked.emit(self.game_id))
        
        button_layout.addWidget(play_btn)
        button_layout.addWidget(info_btn)
        
        content_layout.addLayout(button_layout)
        
        layout.addWidget(content)
    
    def _load_image(self):
        """Load thumbnail image with fallback"""
        cover_image = self.game_data.get('cover_image', '')
        
        # Try to load the image
        if cover_image and Path(cover_image).exists():
            pixmap = QPixmap(cover_image)
            if not pixmap.isNull():
                # Scale maintaining aspect ratio
                scaled = pixmap.scaled(
                    280, 200,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.image_label.setPixmap(scaled)
                return
        
        # Fallback: Show game title with icon
        title = self.game_data.get('title', 'Unknown Game')
        engine = self.game_data.get('engine', '')
        
        # Choose icon based on engine
        icon = "🎮"
        if engine == "Ren'Py":
            icon = "🐍"
        elif engine == "Unity":
            icon = "🔷"
        elif engine == "RPGM" or "RPG Maker" in engine:
            icon = "⚔️"
        elif engine == "HTML":
            icon = "🌐"
        
        fallback_text = f"{icon}\n\n{title[:30]}..."
        self.image_label.setText(fallback_text)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setWordWrap(True)
        self.image_label.setStyleSheet(
            "color: #909090; font-size: 12px; padding: 20px; "
            "background: qlineargradient(x1:0, y1:0, x2:0, y2:1, "
            "stop:0 #2a2a2a, stop:1 #1a1a1a);"
        )
    
    def mousePressEvent(self, event):
        """Handle mouse press"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.game_id)
        super().mousePressEvent(event)
