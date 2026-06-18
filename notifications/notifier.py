from plyer import notification
from utils.logger import logger
from config import APP_NAME

class Notifier:
    
    @staticmethod
    def send_notification(title: str, message: str, timeout: int = 10):
        \"\"\"Sends a desktop notification using plyer.\"\"\"
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
    def notify_change(website_name: str, similarity: float):
        Notifier.send_notification(
            title="Website Updated",
            message=f"{website_name} has changed! Similarity: {similarity*100:.1f}%"
        )

    @staticmethod
    def notify_keyword(website_name: str, keywords: list):
        kw_str = ", ".join(keywords)
        Notifier.send_notification(
            title="Keyword Alert!",
            message=f"Keywords found on {website_name}: {kw_str}"
        )

    @staticmethod
    def notify_error(website_name: str, error_msg: str):
        Notifier.send_notification(
            title="Monitoring Error",
            message=f"Failed to check {website_name}: {error_msg}"
        )
