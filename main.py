import sys
from gui.main_window import MainWindow
from utils.logger import logger

def main():
    logger.info("Starting Website Change Tracker...")
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
