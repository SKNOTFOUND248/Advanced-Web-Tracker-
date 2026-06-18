import threading
import time
import requests
import schedule
from datetime import datetime
from queue import Queue
from typing import Dict, Optional

from database.database_manager import DatabaseManager
from models.website import Website
from models.version import WebsiteVersion
from parser.html_parser import HTMLParser
from tracker.change_detector import ChangeDetector
from notifications.notifier import Notifier
from utils.logger import logger
from utils.hashing import generate_hash
from config import REQUEST_TIMEOUT

class MonitorService:
    def __init__(self):
        self.db = DatabaseManager()
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.update_queue = Queue() # For sending UI updates to the main thread
        
        # Keep track of schedule jobs per website to easily remove/update them
        self.jobs: Dict[int, schedule.Job] = {}

    def start(self):
        \"\"\"Starts the background monitoring thread.\"\"\"
        if self.running:
            return
            
        self.running = True
        self.schedule_all_active_websites()
        
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Monitor service started.")

    def stop(self):
        \"\"\"Stops the background monitoring thread.\"\"\"
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        schedule.clear()
        self.jobs.clear()
        logger.info("Monitor service stopped.")

    def _run_scheduler(self):
        \"\"\"The main loop for the background thread.\"\"\"
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def schedule_all_active_websites(self):
        \"\"\"Loads all active websites from DB and schedules them.\"\"\"
        schedule.clear()
        self.jobs.clear()
        websites = self.db.get_websites()
        for w in websites:
            if w.monitoring_enabled:
                self.schedule_website(w)

    def schedule_website(self, website: Website):
        \"\"\"Schedules a single website for monitoring.\"\"\"
        if website.id in self.jobs:
            schedule.cancel_job(self.jobs[website.id])
            
        if not website.monitoring_enabled:
            return
            
        job = schedule.every(website.check_interval).minutes.do(self.check_website, website_id=website.id)
        self.jobs[website.id] = job
        logger.debug(f"Scheduled website {website.id} ({website.name}) every {website.check_interval} mins.")

    def unschedule_website(self, website_id: int):
        if website_id in self.jobs:
            schedule.cancel_job(self.jobs[website_id])
            del self.jobs[website_id]

    def trigger_check_now(self, website_id: int):
        \"\"\"Triggers an immediate check for a website in a separate short-lived thread.\"\"\"
        t = threading.Thread(target=self.check_website, args=(website_id,), daemon=True)
        t.start()

    def check_website(self, website_id: int):
        \"\"\"
        The core logic to download, parse, hash, compare, and alert.
        Runs in the background scheduler thread or on demand.
        \"\"\"
        # Reload website from DB to get latest settings (e.g. keywords, threshold)
        websites = [w for w in self.db.get_websites() if w.id == website_id]
        if not websites:
            logger.warning(f"Check requested for unknown website ID {website_id}")
            return
            
        website = websites[0]
        
        logger.info(f"Checking website: {website.name} ({website.url})")
        start_time = time.time()
        
        try:
            # 1. Download
            response = requests.get(website.url, timeout=REQUEST_TIMEOUT, 
                                    headers={'User-Agent': 'WebsiteChangeTracker/1.0'})
            response.raise_for_status()
            raw_html = response.text
            response_time = time.time() - start_time
            
            # 2. Parse
            clean_text = HTMLParser.extract_text(raw_html)
            if not clean_text:
                raise ValueError("Parsed content is empty.")
                
            # 3. Hash
            new_hash = generate_hash(clean_text)
            new_length = len(clean_text)
            
            # 4. Compare with previous version
            latest_version = self.db.get_latest_version(website.id)
            
            changed = False
            report = None
            
            if latest_version is None:
                # First time tracking
                changed = True
                logger.info(f"First time tracking for {website.name}")
                event_type = "initial_tracking"
            else:
                # Hash comparison
                if ChangeDetector.hash_comparison(latest_version.content, clean_text):
                    # Detailed Comparison
                    report = ChangeDetector.generate_detailed_diff(latest_version.content, clean_text)
                    
                    if report.similarity_score < website.similarity_threshold:
                        changed = True
                        event_type = "content_changed"
                        logger.info(f"Change detected on {website.name}! Similarity: {report.similarity_score:.4f}")
                    else:
                        logger.info(f"Change ignored for {website.name}. Similarity {report.similarity_score:.4f} >= threshold {website.similarity_threshold}")
                else:
                    logger.debug(f"No changes for {website.name}")

            # 5. Handle Changes
            if changed:
                # Save new version
                new_ver = WebsiteVersion(
                    website_id=website.id,
                    version_number=(latest_version.version_number + 1) if latest_version else 1,
                    content=clean_text,
                    content_hash=new_hash,
                    content_length=new_length,
                    response_time=response_time,
                    previous_version_id=latest_version.id if latest_version else None
                )
                new_ver_id = self.db.add_version(new_ver)
                
                # Check keywords
                matched_keywords = ChangeDetector.check_keywords(clean_text, website.keywords)
                if matched_keywords:
                    Notifier.notify_keyword(website.name, matched_keywords)
                    event_type = "keyword_alert"
                
                # Log Event
                self.db.add_change_event(
                    website_id=website.id,
                    version_id=new_ver_id,
                    event_type=event_type,
                    matched_keywords=",".join(matched_keywords),
                    added_words=len(report.added_words) if report else 0,
                    removed_words=len(report.removed_words) if report else 0,
                    similarity=report.similarity_score if report else 1.0
                )
                
                # Notify
                if latest_version is not None:
                    Notifier.notify_change(website.name, report.similarity_score if report else 0.0)

            # Signal GUI update (even if no change, to update "last checked" time)
            self.update_queue.put({"type": "website_checked", "website_id": website.id})
            
        except requests.RequestException as e:
            logger.error(f"Request failed for {website.name}: {e}")
            Notifier.notify_error(website.name, f"Connection failed: {e}")
            self.db.add_change_event(website.id, None, "error", matched_keywords=str(e))
            self.update_queue.put({"type": "check_error", "website_id": website.id, "error": str(e)})
        except Exception as e:
            logger.error(f"Error checking {website.name}: {e}")
            self.update_queue.put({"type": "check_error", "website_id": website.id, "error": str(e)})
