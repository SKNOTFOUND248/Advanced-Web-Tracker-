# Website Change Tracker

A desktop Python application that continuously monitors registered websites and tracks changes between versions.

## Features
- **Background Monitoring:** Configurable check intervals (1, 5, 10, 30, 60 minutes) that run seamlessly in a background thread.
- **Smart Change Detection:** Uses SHA256 hashing for fast verification and `difflib` for detailed textual comparisons.
- **Visual Diff Viewer:** See exact additions, removals, and similarity percentages between any two versions.
- **Keyword Alerts:** Get notified if specific keywords (e.g., "Result", "Vacancy", "Admission") appear on the tracked page.
- **Desktop Notifications:** Real-time system alerts when pages update or keywords are found.
- **SQLite Database:** Robust local storage for version history and metadata with auto-backup options.
- **Exporting:** Export full version history reports to CSV, JSON, or TXT.

## Installation

1. Clone or download this repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Requirements
- Python 3.10+
- `requests`
- `beautifulsoup4`
- `schedule`
- `plyer`
- `lxml`
