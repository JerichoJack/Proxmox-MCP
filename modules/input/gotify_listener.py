# modules/input/gotify_listener.py
import asyncio
from gotify import AsyncGotify
from core.utils import setup_logger

logger = setup_logger()


class GotifyListener:
    """
    MCP input listener for Gotify using AsyncGotify client token streaming.
    """
    def __init__(self, config, event_callback):
        self.base_url = getattr(config, "gotify_in_server_url", None)
        self.client_token = getattr(config, "gotify_in_client_token", None)
        self.event_callback = event_callback
        self._running = False
        self._task = None

    async def start(self):
        if not self.base_url or not self.client_token:
            logger.warning("[GotifyListener] Missing URL or client token. Listener not started.")
            return

        logger.info("[GotifyListener] Connecting to Gotify stream...")
        self._running = True
        async_gotify = AsyncGotify(base_url=self.base_url, client_token=self.client_token)

        try:
            async for msg in async_gotify.stream():
                if not self._running:
                    break
                title = msg.get("title", "Gotify Event")
                message = msg.get("message", "")
                await self.event_callback(title, message)
        except Exception as e:
            logger.error(f"[GotifyListener] Gotify stream error: {e}")

    async def stop(self):
        self._running = False
        logger.info("[GotifyListener] Stream stopped.")

    async def test_connection(self, timeout: int = 5) -> bool:
        """
        Quick connection test: attempt to connect and listen briefly.
        """
        if not self.base_url or not self.client_token:
            logger.warning("[GotifyListener] Missing URL or client token for test.")
            return False

        try:
            async_gotify = AsyncGotify(base_url=self.base_url, client_token=self.client_token)
            # Run the stream for a short time
            stream = async_gotify.stream()
            await asyncio.wait_for(stream.__anext__(), timeout=timeout)
            logger.info("[GotifyListener] Test stream connected successfully.")
            return True
        except asyncio.TimeoutError:
            logger.info("[GotifyListener] Test stream connection succeeded (no messages in timeout).")
            return True
        except Exception as e:
            logger.error(f"[GotifyListener] Test connection failed: {e}")
            return False
