"""
Secure credential storage using keyring and encrypted files
"""
import logging
import keyring
from typing import Optional

from lewdcorner.config import KEYRING_SERVICE, KEYRING_USERNAME

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages secure storage of user credentials"""
    
    def __init__(self):
        self.service = KEYRING_SERVICE
        self.username = KEYRING_USERNAME
    
    def save_master_password(self, password: str) -> bool:
        """Save master password to system keyring"""
        try:
            keyring.set_password(self.service, self.username, password)
            logger.info("Master password saved to keyring")
            return True
        except Exception as e:
            logger.error(f"Failed to save master password: {e}")
            return False
    
    def get_master_password(self) -> Optional[str]:
        """Retrieve master password from system keyring"""
        try:
            password = keyring.get_password(self.service, self.username)
            if password:
                logger.debug("Master password retrieved from keyring")
            return password
        except Exception as e:
            logger.error(f"Failed to retrieve master password: {e}")
            return None
    
    def delete_master_password(self) -> bool:
        """Delete master password from system keyring"""
        try:
            keyring.delete_password(self.service, self.username)
            logger.info("Master password deleted from keyring")
            return True
        except Exception as e:
            logger.error(f"Failed to delete master password: {e}")
            return False
    
    def save_credentials(self, username: str, password: str) -> bool:
        """Save login credentials to keyring"""
        try:
            keyring.set_password(self.service, f"{username}_login", password)
            keyring.set_password(self.service, "last_username", username)
            logger.info(f"Credentials saved for user: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False
    
    def get_credentials(self) -> Optional[tuple[str, str]]:
        """Retrieve login credentials from keyring"""
        try:
            username = keyring.get_password(self.service, "last_username")
            if not username:
                return None
            
            password = keyring.get_password(self.service, f"{username}_login")
            if not password:
                return None
            
            logger.debug(f"Credentials retrieved for user: {username}")
            return (username, password)
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {e}")
            return None
    
    def delete_credentials(self, username: Optional[str] = None) -> bool:
        """Delete login credentials from keyring"""
        try:
            if not username:
                username = keyring.get_password(self.service, "last_username")
            
            if username:
                keyring.delete_password(self.service, f"{username}_login")
                keyring.delete_password(self.service, "last_username")
                logger.info(f"Credentials deleted for user: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False
