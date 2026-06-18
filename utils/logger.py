import logging
from logging.handlers import RotatingFileHandler
from config import LOG_FILE_PATH

def setup_logger(name="tracker"):
    logger = logging.getLogger(name)
    
    # If already configured, return it to avoid duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # File Handler - Max 5MB per file, keep 3 backups
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)

    # Console Handler for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Create the global logger instance
logger = setup_logger()
