import sqlite3
import shutil
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from pathlib import Path

from config import DB_PATH
from utils.logger import logger
from models.website import Website
from models.version import WebsiteVersion

class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                
                # Create Websites Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS websites (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        url TEXT NOT NULL UNIQUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        monitoring_enabled INTEGER DEFAULT 1,
                        check_interval INTEGER DEFAULT 10,
                        similarity_threshold REAL DEFAULT 0.95
                    )
                ''')

                # Create Versions Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS versions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        website_id INTEGER NOT NULL,
                        version_number INTEGER NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        content TEXT,
                        content_hash TEXT,
                        content_length INTEGER,
                        response_time REAL,
                        previous_version_id INTEGER,
                        FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
                    )
                ''')

                # Create Keyword Alerts Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS keyword_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        website_id INTEGER NOT NULL,
                        keyword TEXT NOT NULL,
                        enabled INTEGER DEFAULT 1,
                        FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
                    )
                ''')

                # Create Change Events Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS change_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        website_id INTEGER NOT NULL,
                        version_id INTEGER,
                        event_type TEXT,
                        matched_keywords TEXT,
                        added_words_count INTEGER,
                        removed_words_count INTEGER,
                        similarity_score REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (website_id) REFERENCES websites(id) ON DELETE CASCADE
                    )
                ''')

                # Create Settings Table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL
                    )
                ''')

                conn.commit()
                logger.info("Database initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    # --- Backup ---
    def backup_database(self, backup_dir: Path) -> bool:
        try:
            backup_path = backup_dir / f"tracker_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(DB_PATH, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

    # --- Website Operations ---
    def add_website(self, website: Website) -> Optional[int]:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO websites (name, url, monitoring_enabled, check_interval, similarity_threshold)
                    VALUES (?, ?, ?, ?, ?)
                ''', (website.name, website.url, 1 if website.monitoring_enabled else 0, 
                      website.check_interval, website.similarity_threshold))
                website_id = cursor.lastrowid
                conn.commit()
                
                # Add keywords
                for kw in website.keywords:
                    self.add_keyword(website_id, kw)
                    
                logger.info(f"Added website: {website.name} ({website.url})")
                return website_id
        except sqlite3.IntegrityError:
            logger.warning(f"Website URL already exists: {website.url}")
            return None
        except Exception as e:
            logger.error(f"Error adding website: {e}")
            return None

    def get_websites(self) -> List[Website]:
        websites = []
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM websites')
                rows = cursor.fetchall()
                
                for row in rows:
                    w = Website(
                        id=row['id'],
                        name=row['name'],
                        url=row['url'],
                        monitoring_enabled=bool(row['monitoring_enabled']),
                        check_interval=row['check_interval'],
                        similarity_threshold=row['similarity_threshold'],
                        created_at=datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S') if isinstance(row['created_at'], str) else row['created_at']
                    )
                    w.keywords = self.get_keywords(w.id)
                    
                    # Fetch latest version info for UI state
                    latest_version = self.get_latest_version(w.id)
                    if latest_version:
                        w.last_checked = latest_version.timestamp
                        w.current_hash = latest_version.content_hash
                        w.response_time = latest_version.response_time
                        
                    websites.append(w)
        except Exception as e:
            logger.error(f"Error fetching websites: {e}")
        return websites

    def update_website(self, website: Website) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE websites 
                    SET name=?, url=?, monitoring_enabled=?, check_interval=?, similarity_threshold=?
                    WHERE id=?
                ''', (website.name, website.url, 1 if website.monitoring_enabled else 0,
                      website.check_interval, website.similarity_threshold, website.id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error updating website {website.id}: {e}")
            return False

    def delete_website(self, website_id: int) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                # PRAGMA foreign_keys = ON is required for ON DELETE CASCADE to work in sqlite3 connection
                conn.execute("PRAGMA foreign_keys = ON")
                cursor = conn.cursor()
                cursor.execute('DELETE FROM websites WHERE id=?', (website_id,))
                conn.commit()
                logger.info(f"Deleted website ID {website_id}")
                return True
        except Exception as e:
            logger.error(f"Error deleting website {website_id}: {e}")
            return False

    # --- Version Operations ---
    def add_version(self, version: WebsiteVersion) -> Optional[int]:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO versions 
                    (website_id, version_number, content, content_hash, content_length, response_time, previous_version_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (version.website_id, version.version_number, version.content, version.content_hash,
                      version.content_length, version.response_time, version.previous_version_id))
                version_id = cursor.lastrowid
                conn.commit()
                return version_id
        except Exception as e:
            logger.error(f"Error adding version for website {version.website_id}: {e}")
            return None

    def get_latest_version(self, website_id: int) -> Optional[WebsiteVersion]:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM versions 
                    WHERE website_id=? 
                    ORDER BY version_number DESC LIMIT 1
                ''', (website_id,))
                row = cursor.fetchone()
                if row:
                    return WebsiteVersion(
                        id=row['id'],
                        website_id=row['website_id'],
                        version_number=row['version_number'],
                        timestamp=datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S') if isinstance(row['timestamp'], str) else row['timestamp'],
                        content=row['content'],
                        content_hash=row['content_hash'],
                        content_length=row['content_length'],
                        response_time=row['response_time'],
                        previous_version_id=row['previous_version_id']
                    )
        except Exception as e:
            logger.error(f"Error fetching latest version for website {website_id}: {e}")
        return None

    def get_versions(self, website_id: int) -> List[WebsiteVersion]:
        versions = []
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT id, website_id, version_number, timestamp, content_hash, content_length, response_time, previous_version_id 
                    FROM versions WHERE website_id=? ORDER BY version_number DESC
                ''', (website_id,))
                rows = cursor.fetchall()
                for row in rows:
                    # Note: We omit 'content' here to save memory, fetch it explicitly when needed for diffing
                    versions.append(WebsiteVersion(
                        id=row['id'],
                        website_id=row['website_id'],
                        version_number=row['version_number'],
                        timestamp=datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S') if isinstance(row['timestamp'], str) else row['timestamp'],
                        content="", # Omitted
                        content_hash=row['content_hash'],
                        content_length=row['content_length'],
                        response_time=row['response_time'],
                        previous_version_id=row['previous_version_id']
                    ))
        except Exception as e:
            logger.error(f"Error fetching versions for website {website_id}: {e}")
        return versions

    def get_version_by_id(self, version_id: int) -> Optional[WebsiteVersion]:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM versions WHERE id=?', (version_id,))
                row = cursor.fetchone()
                if row:
                    return WebsiteVersion(
                        id=row['id'],
                        website_id=row['website_id'],
                        version_number=row['version_number'],
                        timestamp=datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S') if isinstance(row['timestamp'], str) else row['timestamp'],
                        content=row['content'],
                        content_hash=row['content_hash'],
                        content_length=row['content_length'],
                        response_time=row['response_time'],
                        previous_version_id=row['previous_version_id']
                    )
        except Exception as e:
            logger.error(f"Error fetching version {version_id}: {e}")
        return None

    # --- Keyword Operations ---
    def add_keyword(self, website_id: int, keyword: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO keyword_alerts (website_id, keyword) VALUES (?, ?)', (website_id, keyword))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error adding keyword '{keyword}' to website {website_id}: {e}")
            return False

    def get_keywords(self, website_id: int) -> List[str]:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT keyword FROM keyword_alerts WHERE website_id=? AND enabled=1', (website_id,))
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching keywords for website {website_id}: {e}")
            return []

    def remove_keyword(self, website_id: int, keyword: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM keyword_alerts WHERE website_id=? AND keyword=?', (website_id, keyword))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error removing keyword '{keyword}' from website {website_id}: {e}")
            return False

    # --- Event Operations ---
    def add_change_event(self, website_id: int, version_id: Optional[int], event_type: str, 
                         matched_keywords: str = "", added_words: int = 0, removed_words: int = 0, similarity: float = 1.0):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO change_events 
                    (website_id, version_id, event_type, matched_keywords, added_words_count, removed_words_count, similarity_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (website_id, version_id, event_type, matched_keywords, added_words, removed_words, similarity))
                conn.commit()
        except Exception as e:
            logger.error(f"Error adding change event: {e}")

    def get_recent_events(self, limit: int = 50) -> List[Dict]:
        events = []
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT e.*, w.name as website_name 
                    FROM change_events e
                    JOIN websites w ON e.website_id = w.id
                    ORDER BY e.timestamp DESC LIMIT ?
                ''', (limit,))
                rows = cursor.fetchall()
                for row in rows:
                    events.append(dict(row))
        except Exception as e:
            logger.error(f"Error fetching recent events: {e}")
        return events

    # --- Global Settings ---
    def get_setting(self, key: str, default: str = "") -> str:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM settings WHERE key=?', (key,))
                row = cursor.fetchone()
                if row:
                    return row[0]
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
        return default

    def set_setting(self, key: str, value: str) -> bool:
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO settings (key, value) VALUES (?, ?)
                    ON CONFLICT(key) DO UPDATE SET value=excluded.value
                ''', (key, value))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False
