"""
Login dialog for authentication
"""
import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QMessageBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from lewdcorner.core.auth.auth_service import AuthService
from lewdcorner.core.auth.credential_manager import CredentialManager

logger = logging.getLogger(__name__)


class LoginWorker(QThread):
    """Worker thread for login operations"""
    
    finished = pyqtSignal(bool, str, dict)  # success, message, data
    
    def __init__(self, auth_service: AuthService, operation: str, **kwargs):
        super().__init__()
        self.auth_service = auth_service
        self.operation = operation
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.operation == 'login':
                result = self.auth_service.login(
                    self.kwargs['username'],
                    self.kwargs['password'],
                    remember=self.kwargs.get('remember', True),
                    save_credentials=self.kwargs.get('save_credentials', True)
                )
            elif self.operation == 'load_session':
                result = self.auth_service.load_session(self.kwargs['master_password'])
            else:
                result = {'status': 'error', 'message': 'Unknown operation'}
            
            success = result.get('status') == 'success'
            message = result.get('message', '')
            self.finished.emit(success, message, result)
            
        except Exception as e:
            logger.error(f"Login worker error: {e}")
            self.finished.emit(False, str(e), {})


class LoginDialog(QDialog):
    """Login dialog"""
    
    login_successful = pyqtSignal(dict)  # auth result
    
    def __init__(self, auth_service: AuthService, parent=None):
        super().__init__(parent)
        
        self.auth_service = auth_service
        self.credential_manager = CredentialManager()
        self.login_worker = None
        
        self.setWindowTitle("Login to LewdCorner")
        self.setModal(True)
        self.resize(400, 300)
        
        self._setup_ui()
        self._load_saved_credentials()
    
    def _setup_ui(self):
        """Setup UI"""
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("LewdCorner Launcher")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Please log in to continue")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Username
        layout.addWidget(QLabel("Username:"))
        self.username_input = QLineEdit()
        layout.addWidget(self.username_input)
        
        # Password
        layout.addWidget(QLabel("Password:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)
        
        # Remember me
        self.remember_check = QCheckBox("Remember credentials")
        self.remember_check.setChecked(True)
        layout.addWidget(self.remember_check)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.on_login)
        self.login_button.setDefault(True)
        button_layout.addWidget(self.login_button)
        
        self.session_button = QPushButton("Load Session")
        self.session_button.clicked.connect(self.on_load_session)
        button_layout.addWidget(self.session_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _load_saved_credentials(self):
        """Load saved credentials if available"""
        credentials = self.credential_manager.get_credentials()
        if credentials:
            username, password = credentials
            self.username_input.setText(username)
            self.password_input.setText(password)
    
    def on_login(self):
        """Handle login button click"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter username and password")
            return
        
        self._set_loading(True)
        
        # Start login in background thread
        self.login_worker = LoginWorker(
            self.auth_service,
            'login',
            username=username,
            password=password,
            remember=True,
            save_credentials=self.remember_check.isChecked()
        )
        self.login_worker.finished.connect(self.on_login_finished)
        self.login_worker.start()
    
    def on_load_session(self):
        """Handle load session button click"""
        master_password = self.credential_manager.get_master_password()
        
        if not master_password:
            # Prompt for master password
            from PyQt6.QtWidgets import QInputDialog
            password, ok = QInputDialog.getText(
                self,
                "Master Password",
                "Enter master password:",
                QLineEdit.EchoMode.Password
            )
            
            if not ok or not password:
                return
            
            master_password = password
        
        self._set_loading(True)
        
        # Start session load in background
        self.login_worker = LoginWorker(
            self.auth_service,
            'load_session',
            master_password=master_password
        )
        self.login_worker.finished.connect(self.on_login_finished)
        self.login_worker.start()
    
    def on_login_finished(self, success: bool, message: str, data: dict):
        """Handle login completion"""
        self._set_loading(False)
        
        if success:
            # Save session
            master_password = self.credential_manager.get_master_password()
            if not master_password:
                master_password = self.password_input.text()
                self.credential_manager.save_master_password(master_password)
            
            self.auth_service.save_session(master_password)
            
            self.login_successful.emit(data)
            self.accept()
        else:
            QMessageBox.critical(self, "Login Failed", message)
    
    def _set_loading(self, loading: bool):
        """Set loading state"""
        self.progress_bar.setVisible(loading)
        self.login_button.setEnabled(not loading)
        self.session_button.setEnabled(not loading)
        self.username_input.setEnabled(not loading)
        self.password_input.setEnabled(not loading)
