"""
Main application entry point
"""
import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from lewdcorner.config import LOGS_DIR, LOG_LEVEL
from lewdcorner.core.auth.auth_service import AuthService
from lewdcorner.core.db.database import DatabaseManager
from lewdcorner.ui.main_window.main_window import MainWindow
from lewdcorner.ui.dialogs.login_dialog import LoginDialog


def setup_logging():
    """Setup application logging"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    log_file = LOGS_DIR / "launcher.log"
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("="* 60)
    logger.info("LewdCornerLauncher v3.0 Starting")
    logger.info("="* 60)


def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("LewdCornerLauncher")
        app.setOrganizationName("LewdCorner")
        
        # Note: AA_UseHighDpiPixmaps removed in PyQt6 (now default behavior)
        
        logger.info("Initializing database...")
        
        # Initialize database
        db_manager = DatabaseManager()
        db_manager.connect()
        db_manager.initialize_schema()
        
        logger.info("Database initialized")
        
        # Create auth service
        auth_service = AuthService(headless=True)
        
        # Show login dialog
        logger.info("Showing login dialog...")
        login_dialog = LoginDialog(auth_service)
        
        if login_dialog.exec() != login_dialog.DialogCode.Accepted:
            logger.info("Login cancelled by user")
            auth_service.quit()
            db_manager.close()
            return 0
        
        logger.info("Login successful")
        
        # Create and show main window
        logger.info("Creating main window...")
        main_window = MainWindow(auth_service, db_manager)
        main_window.show()
        
        logger.info("Main window shown")
        
        # Run application
        result = app.exec()
        
        # Cleanup
        logger.info("Application closing...")
        auth_service.quit()
        db_manager.close()
        
        logger.info("Goodbye!")
        return result
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        
        # Show error dialog if possible
        try:
            QMessageBox.critical(
                None,
                "Fatal Error",
                f"A fatal error occurred:\n\n{str(e)}\n\nCheck logs for details."
            )
        except:
            pass
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
