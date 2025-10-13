# modules/output/gotify_notifier.py
import aiohttp
from .base import BaseNotifier
from core.utils import setup_logger

logger = setup_logger()


class GotifyNotifier(BaseNotifier):
    """
    MCP output notifier for Gotify v2.
    Uses MCPConfig for server URL and application token.
    """
    def __init__(self, config):
        super().__init__(config, name="GotifyNotifier")
        self.server_url = getattr(config, "gotify_out_server_url", None)
        self.app_token = getattr(config, "gotify_out_app_token", None)

    async def send(self, title, message, priority=5):
        if not self.server_url or not self.app_token:
            logger.warning("[GotifyNotifier] Missing server URL or app token in config.")
            return False

        url = f"{self.server_url}/message"
        headers = {"X-Gotify-Key": self.app_token}
        payload = {
            "title": title,
            "message": message,
            "priority": priority
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        logger.info(f"[GotifyNotifier] Sent: {title}")
                        return True
                    else:
                        text = await resp.text()
                        logger.error(f"[GotifyNotifier] Failed ({resp.status}): {text}")
                        return False
        except Exception as e:
            logger.error(f"[GotifyNotifier] Error sending notification: {e}")
            return False