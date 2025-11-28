"""
Robust wrapper that the UI calls to fetch bookmarks.
Prints JSON to stdout on success:
    {"count": N, "data": [ {title, link}, ... ]}
On error it prints a useful message to stderr (so UI will show it).
"""
import sys
import json
import logging
import traceback
from scraper_engine import Scraper
from cryptography.fernet import InvalidToken
import time
logging.basicConfig(level=logging.INFO, format='%(levelname)s: (update_bookmarks) %(message)s')
def main():
    if len(sys.argv) < 3:
        sys.stderr.write("Usage: python update_bookmarks.py <headless> <master_key>\n")
        sys.exit(1)
    headless = sys.argv[1].lower() == "true"
    master_key = sys.argv[2]
    scraper = Scraper(headless=headless)
    try:
        logging.info("Loading session...")
        loaded = scraper.load_session(master_key)
        if not loaded:
            raise Exception("Invalid master password or session expired.")
        logging.info("Session loaded. Checking login state...")
        user = scraper.get_user_info()
        if not user or not user.get("username"):
            raise Exception("Session expired. Please log in again.")
        logging.info(f"Logged in as: {user.get('username')}")
        # Fetch bookmarks with debug fallback enabled if count==0
        logging.info("Fetching bookmarks from site (attempting robust fetch)...")
        # request debug info if zero so we can better surface the problem
        bookmarks = []
        retries = 5  # Increased retries
        for attempt in range(retries):
            try:
                bookmarks = scraper.scrape_bookmarks(debug=False)
                break
            except Exception as e:
                if attempt < retries - 1:
                    time.sleep(2)
                    continue
                # If scrape_bookmarks raised an exception in debug mode, attempt a non-debug run to be more permissive.
                logging.warning(f"scrape_bookmarks raised: {e}. Attempting permissive fetch.")
                try:
                    bookmarks = scraper.scrape_bookmarks(debug=False)
                except Exception as e2:
                    # At this point return useful error
                    tb = traceback.format_exc()
                    sys.stderr.write(f"Failed to fetch bookmarks: {e2}\n{tb}\n")
                    sys.exit(1)
        if not isinstance(bookmarks, list):
            sys.stderr.write("Unexpected response from scraper (not a list).\n")
            sys.exit(1)
        # If we got zero bookmarks, produce diagnostic info for UI (not fatal)
        if len(bookmarks) == 0:
            # Try one more attempt with debug=True to get diagnostics and print to stderr
            try:
                _ = scraper.scrape_bookmarks(debug=True)
                # If no exception and still 0, fall through
            except Exception as ex:
                # ex likely contains diagnostic payload
                sys.stderr.write(f"No bookmarks found. Diagnostic: {ex}\n")
                # exit with non-zero so UI can show the error to user instead of silently doing nothing
                sys.exit(1)
        # Success: output JSON with count and data
        print(json.dumps({"count": len(bookmarks), "data": bookmarks}))
        sys.exit(0)
    except InvalidToken:
        sys.stderr.write("InvalidToken: Master password incorrect.\n")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        traceback.print_exc()
        sys.stderr.write(str(e) + "\n")
        sys.exit(1)
    finally:
        scraper.quit()
if __name__ == '__main__':
    main()
