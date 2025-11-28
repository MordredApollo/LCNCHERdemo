"""
Session persistence and encrypted cookie storage
"""
import os
import json
import logging
import hashlib
import base64
import secrets
from typing import Dict, List, Optional
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from lewdcorner.config import SESSION_FILE, SALT_FILE

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages encrypted session cookie persistence"""
    
    def __init__(self):
        self.session_file = Path(SESSION_FILE)
        self.salt_file = Path(SALT_FILE)
        self._fernet_key = None
    
    def _get_or_create_salt(self) -> bytes:
        """Get existing salt or create new one"""
        if not self.salt_file.exists():
            salt = secrets.token_bytes(32)
            self.salt_file.write_bytes(salt)
            logger.info("Created new salt file")
        return self.salt_file.read_bytes()
    
    def _derive_key(self, master_password: str | bytes) -> bytes:
        """Derive encryption key from master password"""
        if isinstance(master_password, str):
            master_password = master_password.encode('utf-8')
        
        # Check if already a valid Fernet key
        if len(master_password) == 44:
            try:
                Fernet(master_password)
                return master_password
            except Exception:
                pass
        
        # Derive key using salt
        salt = self._get_or_create_salt()
        key_material = hashlib.pbkdf2_hmac(
            'sha256',
            master_password,
            salt,
            100000,  # iterations
            dklen=32
        )
        return base64.urlsafe_b64encode(key_material)
    
    def save_cookies(self, cookies: List[Dict], master_password: str | bytes) -> bool:
        """Save cookies to encrypted file"""
        try:
            key = self._derive_key(master_password)
            fernet = Fernet(key)
            
            # Serialize cookies
            cookie_data = json.dumps(cookies, indent=2)
            
            # Encrypt
            encrypted_data = fernet.encrypt(cookie_data.encode('utf-8'))
            
            # Save to file
            self.session_file.write_bytes(encrypted_data)
            
            logger.info(f"Saved {len(cookies)} cookies to encrypted session file")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cookies: {e}")
            return False
    
    def load_cookies(self, master_password: str | bytes) -> Optional[List[Dict]]:
        """Load cookies from encrypted file"""
        if not self.session_file.exists():
            logger.debug("Session file does not exist")
            return None
        
        try:
            key = self._derive_key(master_password)
            fernet = Fernet(key)
            
            # Read encrypted data
            encrypted_data = self.session_file.read_bytes()
            
            # Decrypt
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Parse cookies
            cookies = json.loads(decrypted_data.decode('utf-8'))
            
            logger.info(f"Loaded {len(cookies)} cookies from encrypted session file")
            return cookies
            
        except InvalidToken:
            logger.error("Invalid master password or corrupted session file")
            return None
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return None
    
    def delete_session(self) -> bool:
        """Delete session file"""
        try:
            if self.session_file.exists():
                self.session_file.unlink()
                logger.info("Session file deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session file: {e}")
            return False
    
    def session_exists(self) -> bool:
        """Check if session file exists"""
        return self.session_file.exists()
    
    def validate_cookies(self, cookies: List[Dict]) -> bool:
        """Validate cookie structure"""
        if not cookies:
            return False
        
        required_fields = ['name', 'value']
        for cookie in cookies:
            if not all(field in cookie for field in required_fields):
                return False
        
        return True
