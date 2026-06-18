import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Database
DB_PATH = DATA_DIR / "tracker.db"

# Logs
LOG_FILE_PATH = LOG_DIR / "tracker.log"

# Monitoring Defaults
DEFAULT_CHECK_INTERVAL = 10  # minutes
DEFAULT_SIMILARITY_THRESHOLD = 0.95
REQUEST_TIMEOUT = 15  # seconds

# Application Info
APP_NAME = "Website Change Tracker"
APP_VERSION = "1.0.0"

# UI Settings
THEME_DARK = True
