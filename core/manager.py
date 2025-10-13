# core/manager.py
import asyncio
from core.config import MCPConfig
from core.event_dispatcher import EventDispatcher
from modules.output.gotify_notifier import GotifyNotifier
from modules.discord_notifier import DiscordNotifier
from modules.input.websocket_listener import WebsocketListener
from modules.input.email_listener import EmailListener

class MCPManager:
    def __init__(self, env_path=".env"):
        self.config = MCPConfig(env_path)
        self.notifiers = []
        self.listeners = []
        self.dispatcher = None

    def setup(self):
        print(self.config.summary())

        # --- Initialize Notifiers ---
        if self.config.gotify_enabled and self.config.gotify_url:
            self.notifiers.append(GotifyNotifier(self.config.gotify_url, self.config.gotify_token))

        if self.config.discord_enabled and self.config.discord_webhook:
            self.notifiers.append(DiscordNotifier(self.config.discord_webhook))

        # --- Initialize Event Listeners ---
        if "WEBSOCKET" in self.config.enabled_event_listeners:
            self.listeners.append(WebsocketListener(self.config, self.on_event))

        if "EMAIL" in self.config.enabled_event_listeners:
            self.listeners.append(EmailListener(self.config, self.on_event))

        # --- Dispatcher ---
        self.dispatcher = EventDispatcher(self.notifiers)

    async def on_event(self, title, message):
        await self.dispatcher.dispatch(title, message)

    async def run(self):
        await asyncio.gather(*(listener.start() for listener in self.listeners))
