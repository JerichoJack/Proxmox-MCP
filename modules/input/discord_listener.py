# modules/input/discord_listener.py
import asyncio
import json
from datetime import datetime, timedelta

import aiohttp

from core.utils import setup_logger

logger = setup_logger()


class DiscordListener:
    """
    MCP input listener for Discord webhook events.
    This implementation polls Discord messages via webhook or monitors a specific channel.
    Note: For full Discord bot functionality, consider using discord.py library.
    """
    
    def __init__(self, config, event_callback):
        self.webhook_url = getattr(config, "discord_in_webhook", None)
        self.poll_interval = getattr(config, "discord_in_poll_interval", 30)
        self.event_callback = event_callback
        self._running = False
        self._task = None
        self._last_message_id = None
        
    async def start(self):
        """Start Discord message monitoring."""
        if not self.webhook_url:
            logger.warning("[DiscordListener] Missing webhook URL. Listener not started.")
            return
            
        logger.info("[DiscordListener] Starting Discord message monitoring...")
        self._running = True
        
        # Start monitoring task
        self._task = asyncio.create_task(self._monitor_messages())
        
    async def stop(self):
        """Stop Discord message monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
                
        logger.info("[DiscordListener] Discord listener stopped.")
        
    async def _monitor_messages(self):
        """
        Monitor Discord messages for Proxmox-related content.
        Note: This is a simplified implementation. For production use,
        consider implementing a proper Discord bot with discord.py.
        """
        while self._running:
            try:
                await self._check_for_messages()
                await asyncio.sleep(self.poll_interval)
                
            except Exception as e:
                logger.error(f"[DiscordListener] Error monitoring Discord: {e}")
                await asyncio.sleep(self.poll_interval)
                
    async def _check_for_messages(self):
        """
        Check for new Discord messages.
        This is a placeholder implementation - actual Discord integration
        would require proper bot setup or different API approach.
        """
        # For demonstration purposes, we'll simulate receiving Discord webhook events
        # In a real implementation, this would either:
        # 1. Use Discord bot API to monitor channels
        # 2. Set up a webhook endpoint to receive Discord events
        # 3. Use Discord.py library for full bot functionality
        
        logger.debug("[DiscordListener] Checking for Discord messages...")
        
        # Simulate processing a Discord message about Proxmox
        # This would be replaced with actual Discord API calls
        pass
    
    async def process_discord_webhook(self, webhook_data):
        """
        Process incoming Discord webhook data.
        This method would be called by a web server receiving Discord webhooks.
        """
        try:
            # Extract message content
            content = webhook_data.get('content', '')
            author = webhook_data.get('author', {})
            username = author.get('username', 'Unknown')
            
            # Check if message contains Proxmox-related keywords
            proxmox_keywords = [
                'proxmox', 'pve', 'pbs', 'vm', 'virtual machine',
                'backup', 'cluster', 'node', 'migration', 'storage'
            ]
            
            content_lower = content.lower()
            if any(keyword in content_lower for keyword in proxmox_keywords):
                # Process as Proxmox-related Discord message
                title = f"Discord Message from {username}"
                message = f"Content: {content}"
                
                await self.event_callback(title, message)
                logger.info(f"[DiscordListener] Processed Proxmox-related message from {username}")
            else:
                logger.debug(f"[DiscordListener] Ignored non-Proxmox message from {username}")
                
        except Exception as e:
            logger.error(f"[DiscordListener] Error processing Discord webhook: {e}")
    
    async def test_connection(self, timeout: int = 5) -> bool:
        """
        Test Discord connection capabilities.
        Since Discord input is webhook-based, we test the webhook URL validity.
        """
        if not self.webhook_url:
            logger.warning("[DiscordListener] Missing webhook URL for test.")
            return False
            
        try:
            # Test by sending a test message to the webhook
            async with aiohttp.ClientSession() as session:
                test_payload = {
                    "content": "🧪 MCP Discord Listener Test - Connection successful!",
                    "username": "Proxmox MCP Test",
                    "embeds": [{
                        "title": "Discord Listener Test",
                        "description": "Testing Discord webhook connectivity for input monitoring.",
                        "color": 0x00FF00,
                        "timestamp": datetime.utcnow().isoformat()
                    }]
                }
                
                async with session.post(
                    self.webhook_url,
                    json=test_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=timeout
                ) as resp:
                    if resp.status in [200, 204]:
                        logger.info("[DiscordListener] Test webhook message sent successfully.")
                        return True
                    else:
                        logger.error(f"[DiscordListener] Test failed with status {resp.status}")
                        return False
                        
        except asyncio.TimeoutError:
            logger.error("[DiscordListener] Test connection timed out.")
            return False
        except Exception as e:
            logger.error(f"[DiscordListener] Test connection failed: {e}")
            return False


# Webhook endpoint handler (for use with web framework like FastAPI/Flask)
class DiscordWebhookHandler:
    """
    Separate class for handling Discord webhook HTTP endpoints.
    Use this with a web server to receive Discord webhook events.
    """
    
    def __init__(self, discord_listener):
        self.discord_listener = discord_listener
        
    async def handle_webhook(self, request_data):
        """
        Handle incoming Discord webhook HTTP request.
        
        Args:
            request_data: Dict containing webhook payload from Discord
        """
        await self.discord_listener.process_discord_webhook(request_data)