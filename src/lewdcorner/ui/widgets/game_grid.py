"""
Grid view for game cards
"""
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PyQt6.QtCore import Qt, pyqtSignal
from lewdcorner.ui.widgets.game_card import GameCard


class GameGrid(QScrollArea):
    """Grid view displaying game cards"""
    
    game_clicked = pyqtSignal(int)  # game_id
    play_clicked = pyqtSignal(int)  # game_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.games = []
        self.cards = []
        self.columns = 4  # Number of columns
        
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget
        self.container = QWidget()
        self.setWidget(self.container)
        
        # Main layout
        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)
        
        # Grid layout for cards
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        self.main_layout.addLayout(self.grid_layout)
        
        # Spacer
        self.main_layout.addStretch()
        
        # Empty state
        self.empty_label = QLabel("No games found")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #707070; font-size: 16px; padding: 40px;")
        self.main_layout.addWidget(self.empty_label)
        self.empty_label.hide()
    
    def set_games(self, games: list):
        """Set games to display"""
        self.games = games
        self._refresh_view()
    
    def clear(self):
        """Clear all cards"""
        self.games = []
        self._clear_grid()
        self.empty_label.show()
    
    def _clear_grid(self):
        """Clear grid layout"""
        for card in self.cards:
            card.deleteLater()
        self.cards.clear()
        
        # Clear grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _refresh_view(self):
        """Refresh the grid view"""
        self._clear_grid()
        
        if not self.games:
            self.empty_label.show()
            return
        
        self.empty_label.hide()
        
        # Create cards
        for index, game in enumerate(self.games):
            card = GameCard(game)
            card.clicked.connect(self.game_clicked.emit)
            card.play_clicked.connect(self.play_clicked.emit)
            
            # Calculate row and column
            row = index // self.columns
            col = index % self.columns
            
            self.grid_layout.addWidget(card, row, col)
            self.cards.append(card)
    
    def set_columns(self, columns: int):
        """Set number of columns"""
        if columns != self.columns:
            self.columns = max(1, columns)
            self._refresh_view()
    
    def resizeEvent(self, event):
        """Handle resize - adjust columns"""
        super().resizeEvent(event)
        
        # Auto-adjust columns based on width
        width = self.viewport().width()
        card_width = 300  # Card width + spacing
        
        new_columns = max(1, width // card_width)
        if new_columns != self.columns:
            self.columns = new_columns
            self._refresh_view()
