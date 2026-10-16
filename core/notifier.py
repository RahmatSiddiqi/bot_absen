import logging
import os
import subprocess
import threading
from typing import Optional
import requests

logger = logging.getLogger("Notifier")

class Notifier:
    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        discord_webhook: Optional[str] = None,
        enable_desktop_toast: bool = True
    ):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.discord_webhook = discord_webhook
        self.enable_desktop_toast = enable_desktop_toast

    def send(self, title: str, message: str, level: str = "INFO"):
        """
        Send notification across all enabled channels asynchronously.
        level: "INFO", "SUCCESS", "WARNING", "ERROR"
        """
        log_msg = f"[{level}] {title}: {message}"
        if level == "ERROR":
            logger.error(log_msg)
        elif level == "WARNING":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)

        # Dispatch async to avoid blocking the main scheduler
        thread = threading.Thread(target=self._dispatch_all, args=(title, message, level), daemon=True)
        thread.start()

    def _dispatch_all(self, title: str, message: str, level: str):
        # 1. Desktop Notification
        if self.enable_desktop_toast:
            self._send_windows_toast(title, message)

        # 2. Telegram
        if self.telegram_token and self.telegram_chat_id:
            self._send_telegram(title, message, level)

        # 3. Discord
        if self.discord_webhook:
            self._send_discord(title, message, level)

    def _send_windows_toast(self, title: str, message: str):
        """Send Windows native desktop notification using non-blocking PowerShell."""
        try:
            # Clean single/double quotes to prevent powershell injection
            safe_title = title.replace('"', '`"').replace("'", "''")
            safe_msg = message.replace('"', '`"').replace("'", "''")

            ps_cmd = (
                f"[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null; "
                f"$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); "
                f"$textNodes = $template.GetElementsByTagName('text'); "
                f"$textNodes.Item(0).AppendChild($template.CreateTextNode('{safe_title}')) > $null; "
                f"$textNodes.Item(1).AppendChild($template.CreateTextNode('{safe_msg}')) > $null; "
                f"$toast = [Windows.UI.Notifications.ToastNotification]::new($template); "
                f"[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('E-Kinerja Bot Absensi').Show($toast);"
            )

            subprocess.Popen(
                ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps_cmd],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
        except Exception as e:
            logger.debug(f"Desktop notification failed: {e}")

    def _send_telegram(self, title: str, message: str, level: str):
        """Send notification to Telegram."""
        icons = {
            "SUCCESS": "✅",
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌"
        }
        icon = icons.get(level, "📌")
        text = f"{icon} *{title}*\n\n{message}"

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        try:
            requests.post(url, json=payload, timeout=10)
        except Exception as e:
            logger.warning(f"Gagal mengirim Telegram notification: {e}")

    def _send_discord(self, title: str, message: str, level: str):
        """Send notification to Discord Webhook."""
        colors = {
            "SUCCESS": 0x2ecc71, # green
            "INFO": 0x3498db,    # blue
            "WARNING": 0xf39c12, # orange
            "ERROR": 0xe74c3c    # red
        }
        color = colors.get(level, 0x95a5a6)

        payload = {
            "embeds": [{
                "title": title,
                "description": message,
                "color": color,
            }]
        }
        try:
            requests.post(self.discord_webhook, json=payload, timeout=10)
        except Exception as e:
            logger.warning(f"Gagal mengirim Discord webhook: {e}")
