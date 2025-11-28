"""
Complete authentication service with login and session management
"""
import time
import logging
from typing import Dict, Any, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException
)

try:
    import undetected_chromedriver as uc
    HAVE_UC = True
except ImportError:
    from selenium import webdriver
    HAVE_UC = False

from lewdcorner.config import (
    BASE_URL, LOGIN_URL, PROFILE_DIR, IMPLICIT_WAIT,
    PAGE_LOAD_TIMEOUT, MAX_RETRIES, RETRY_DELAY
)
from lewdcorner.core.auth.session_manager import SessionManager
from lewdcorner.core.auth.credential_manager import CredentialManager

logger = logging.getLogger(__name__)


class AuthService:
    """Complete authentication service"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.session_manager = SessionManager()
        self.credential_manager = CredentialManager()
        self.current_username = None
        self._initialized = False
    
    def initialize_driver(self):
        """Initialize Chrome WebDriver with proper configuration"""
        if self.driver:
            logger.debug("Driver already initialized")
            return
        
        PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        
        if HAVE_UC:
            options = uc.ChromeOptions()
        else:
            from selenium.webdriver.chrome.options import Options
            options = Options()
        
        # Chrome options
        options.add_argument(f"--user-data-dir={PROFILE_DIR}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-popup-blocking")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        
        if self.headless:
            options.add_argument("--headless=new")

        try:
            if HAVE_UC:
                logger.info("Initializing undetected ChromeDriver...")
                self.driver = uc.Chrome(
                    options=options, 
                    use_subprocess=False,
                    version_main=None
                )
            else:
                logger.info("Initializing standard ChromeDriver...")
                self.driver = webdriver.Chrome(options=options)
            
            self.driver.implicitly_wait(IMPLICIT_WAIT)
            self.driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
            
            # Remove webdriver flag
            try:
                self.driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )
            except Exception as e:
                logger.debug(f"Could not remove webdriver flag: {e}")
            
            self._initialized = True
            logger.info("WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise RuntimeError(f"WebDriver initialization failed: {e}")
    
    def login(self, username: str, password: str, remember: bool = True, 
              save_credentials: bool = True) -> Dict[str, Any]:
        """
        Perform login with username and password
        
        Returns:
            Dict with status, message, and optional data
        """
        self.initialize_driver()
        
        try:
            logger.info(f"Attempting login for user: {username}")
            self.driver.get(LOGIN_URL)
            time.sleep(2)
            
            # Check if already logged in
            if self._check_logged_in():
                logger.info("Already logged in")
                self.current_username = self._get_username_from_html(
                    self.driver.page_source
                )
                return {
                    "status": "success",
                    "message": "Already logged in",
                    "username": self.current_username
                }
            
            # Fill login form
            wait = WebDriverWait(self.driver, 30)
            
            username_field = wait.until(
                EC.presence_of_element_located((By.NAME, "login"))
            )
            username_field.clear()
            username_field.send_keys(username)
            
            password_field = self.driver.find_element(By.NAME, "password")
            password_field.clear()
            password_field.send_keys(password)
            
            # Try to check remember me
            if remember:
                try:
                    remember_checkbox = self.driver.find_element(By.NAME, "remember")
                    if not remember_checkbox.is_selected():
                        self.driver.execute_script("arguments[0].click();", remember_checkbox)
                except NoSuchElementException:
                    logger.debug("Remember me checkbox not found")
            
            # Click login button
            login_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.button--icon--login"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", login_button)
            time.sleep(1)
            login_button.click()
            
            # Wait for login to complete
            try:
                wait.until(EC.any_of(
                    EC.url_changes(LOGIN_URL),
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".p-navgroup-link--user"))
                ))
                time.sleep(2)
            except TimeoutException:
                logger.warning("Login timeout - checking manually")
            
            # Verify login success
            if not self._check_logged_in():
                return {
                    "status": "error",
                    "message": "Login failed. Please check credentials or solve CAPTCHA."
                }
            
            # Get username
            self.current_username = self._get_username_from_html(
                self.driver.page_source
            )
            
            # Save credentials if requested
            if save_credentials:
                self.credential_manager.save_credentials(username, password)
            
            logger.info(f"Login successful: {self.current_username}")
            
            return {
                "status": "success",
                "message": "Login successful",
                "username": self.current_username
            }
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return {
                "status": "error",
                "message": f"Login error: {str(e)}"
            }
    
    def load_session(self, master_password: str) -> Dict[str, Any]:
        """
        Load session from encrypted file
        
        Returns:
            Dict with status, message, and optional data
        """
        self.initialize_driver()
        
        cookies = self.session_manager.load_cookies(master_password)
        if not cookies:
            return {
                "status": "error",
                "message": "No saved session or invalid master password"
            }
        
        try:
            logger.info("Loading saved session...")
            self.driver.get(BASE_URL)
            time.sleep(1)
            
            # Inject cookies
            for cookie in cookies:
                # Remove problematic fields
                cookie.pop('expiry', None)
                cookie.pop('sameSite', None)
                
                try:
                    self.driver.add_cookie(cookie)
                except Exception as e:
                    logger.debug(f"Failed to add cookie {cookie.get('name')}: {e}")
            
            # Refresh page
            self.driver.refresh()
            time.sleep(2)
            
            # Verify logged in
            if not self._check_logged_in():
                return {
                    "status": "error",
                    "message": "Session expired or invalid"
                }
            
            # Get username
            self.current_username = self._get_username_from_html(
                self.driver.page_source
            )
            
            logger.info(f"Session loaded: {self.current_username}")
            
            return {
                "status": "success",
                "message": "Session loaded successfully",
                "username": self.current_username
            }
            
        except Exception as e:
            logger.error(f"Session load error: {e}")
            return {
                "status": "error",
                "message": f"Failed to load session: {str(e)}"
            }
    
    def save_session(self, master_password: str) -> bool:
        """Save current session to encrypted file"""
        if not self.driver:
            logger.error("Cannot save session: driver not initialized")
            return False
        
        try:
            cookies = self.driver.get_cookies()
            return self.session_manager.save_cookies(cookies, master_password)
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def refresh_session(self) -> bool:
        """Refresh session by checking login status"""
        if not self.driver:
            return False
        
        try:
            current_url = self.driver.current_url
            self.driver.get(BASE_URL)
            time.sleep(1)
            
            is_logged_in = self._check_logged_in()
            
            # Navigate back
            if current_url and current_url != BASE_URL:
                self.driver.get(current_url)
            
            return is_logged_in
            
        except Exception as e:
            logger.error(f"Session refresh error: {e}")
            return False
    
    def logout(self) -> bool:
        """Logout from the website"""
        if not self.driver:
            return False
        
        try:
            # Navigate to logout URL or click logout
            self.driver.get(f"{BASE_URL}/logout/")
            time.sleep(2)
            
            self.current_username = None
            
            logger.info("Logged out successfully")
            return True
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def _check_logged_in(self) -> bool:
        """Check if currently logged in"""
        try:
            # Wait briefly for user nav element
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".p-navgroup-link--user"))
            )
            return True
        except TimeoutException:
            # Check page source
            return 'data-logged-in="true"' in self.driver.page_source
    
    def _get_username_from_html(self, html: str) -> Optional[str]:
        """Extract username from HTML"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Try various selectors
            selectors = [
                '.p-navgroup-link--user .p-navgroup-linkText',
                '.username',
                '[data-user-id]',
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    username = element.get_text(strip=True)
                    if username:
                        return username
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to extract username: {e}")
            return None
    
    def get_driver(self):
        """Get the WebDriver instance"""
        if not self.driver:
            self.initialize_driver()
        return self.driver
    
    def quit(self):
        """Close driver and cleanup"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error quitting driver: {e}")
            finally:
                self.driver = None
                self._initialized = False
        logger.info("Driver closed")
    
    def __del__(self):
        """Cleanup on destruction"""
        self.quit()
