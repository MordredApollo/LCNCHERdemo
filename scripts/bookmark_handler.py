import sys
import logging
import traceback
from scraper_engine import Scraper
from cryptography.fernet import InvalidToken
logging.basicConfig(level=logging.INFO, format='%(levelname)s: (bookmark_handler) %(message)s')
def main():
    if len(sys.argv) < 6:
        sys.stderr.write("Usage: python bookmark_handler.py <url> <action: add/remove> <headless> <master_key> <is_premium>\n")
        sys.exit(1)
    url = sys.argv[1]
    action = sys.argv[2]
    headless = sys.argv[3] == "true"
    master_key = sys.argv[4]
    is_premium = sys.argv[5] == "True"
    scraper = Scraper(headless=headless, is_premium=is_premium)
    try:
        if not scraper.load_session(master_key):
            raise Exception("No session or invalid master password.")
        if action == "add":
            scraper.add_bookmark(url)
        elif action == "remove":
            scraper.remove_bookmark(url)
        print("OK")
        sys.exit(0)
    except InvalidToken as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)
    finally:
        scraper.quit()
if __name__ == "__main__":
    main()
