""" Fetches full details for a thread. """
import sys
import json
import logging
import traceback
from scraper_engine import Scraper
from cryptography.fernet import InvalidToken
logging.basicConfig(level=logging.INFO, format='%(levelname)s: (details_handler) %(message)s')
def main():
    if len(sys.argv) < 5:
        sys.stderr.write("Usage: python details_handler.py <thread_url> <headless> <master_key> <is_premium>\n")
        sys.exit(1)
    url = sys.argv[1]
    headless = sys.argv[2] == "true"
    master_key = sys.argv[3]
    is_premium = sys.argv[4] == "True"
    scraper = Scraper(headless=headless, is_premium=is_premium)
    try:
        if not scraper.load_session(master_key):
            raise Exception("No session or invalid master password.")
        details = scraper.scrape_thread_details(url)
        print(json.dumps(details))
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
