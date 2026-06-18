import os
from plyer import notification
import pygame
from utils.logger import logger
from config import APP_NAME
from database.database_manager import DatabaseManager

class Notifier:
    _pygame_initialized = False
    
    @staticmethod
    def send_notification(title: str, message: str, timeout: int = 10):
        """Sends a desktop notification using plyer."""
        try:
            notification.notify(
                title=f"{APP_NAME} - {title}",
                message=message,
                app_name=APP_NAME,
                timeout=timeout,
                # On windows, plyer might need an icon file (.ico). If absent, it might throw an error or skip.
                # Since we don't have an icon yet, we omit it or handle the error gracefully.
            )
            logger.info(f"Desktop notification sent: {title}")
        except Exception as e:
            # Plyer can sometimes fail depending on the OS setup (e.g. missing dbus on linux, or no toast notifications on Windows)
            logger.error(f"Failed to send desktop notification: {e}. Message: {title} - {message}")

    @staticmethod
    def _play_alarm():
        db = DatabaseManager()
        play_alarm = db.get_setting("play_alarm_on_change", "1")
        if play_alarm != "1":
            return
            
        custom_path = db.get_setting("custom_alarm_path", "")
        if custom_path and os.path.exists(custom_path):
            try:
                if not Notifier._pygame_initialized:
                    pygame.mixer.init()
                    Notifier._pygame_initialized = True
                
                pygame.mixer.music.load(custom_path)
                pygame.mixer.music.play()
                logger.info(f"Playing custom alarm: {custom_path}")
            except Exception as e:
                logger.error(f"Failed to play custom alarm: {e}")

    @staticmethod
    def notify_change(website_name: str, similarity: float):
        Notifier.send_notification(
            title="Website Updated",
            message=f"{website_name} has changed! Similarity: {similarity*100:.1f}%"
        )
        Notifier._play_alarm()

    @staticmethod
    def notify_keyword(website_name: str, keywords: list):
        kw_str = ", ".join(keywords)
        Notifier.send_notification(
            title="Keyword Alert!",
            message=f"Keywords found on {website_name}: {kw_str}"
        )
        Notifier._play_alarm()

    @staticmethod
    def notify_error(website_name: str, error_msg: str):
        Notifier.send_notification(
            title="Monitoring Error",
            message=f"Failed to check {website_name}: {error_msg}"
        )
