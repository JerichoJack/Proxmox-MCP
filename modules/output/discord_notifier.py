# modules/output/discord_notifier.py
import json

import aiohttp

from core.utils import setup_logger

from .base import BaseNotifier

logger = setup_logger()


class DiscordNotifier(BaseNotifier):
    """
    MCP output notifier for Discord webhooks.
    Uses MCPConfig for webhook URL and supports rich embed formatting.
    """
    
    def __init__(self, config):
        super().__init__(config, name="DiscordNotifier")
        self.webhook_url = getattr(config, "discord_out_webhook", None)
        
    async def send(self, title, message, priority=None, **kwargs):
        """
        Send notification to Discord via webhook.
        
        Args:
            title: The title/subject of the notification
            message: The main message content
            priority: Optional priority level (affects embed color)
            **kwargs: Additional metadata (vm_id, node, event_type, etc.)
        """
        if not self.webhook_url:
            logger.warning("[DiscordNotifier] Missing webhook URL in config.")
            return False
            
        # Create Discord embed based on message content and metadata
        embed = self._create_embed(title, message, priority, **kwargs)
        
        payload = {
            "embeds": [embed],
            "username": "Proxmox MCP",
            "avatar_url": "https://i.imgur.com/4M34hi2.png"  # Proxmox logo (optional)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.webhook_url, 
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status in [200, 204]:
                        logger.info(f"[DiscordNotifier] Sent: {title}")
                        return True
                    else:
                        text = await resp.text()
                        logger.error(f"[DiscordNotifier] Failed ({resp.status}): {text}")
                        return False
                        
        except Exception as e:
            logger.error(f"[DiscordNotifier] Error sending notification: {e}")
            return False
    
    def _create_embed(self, title, message, priority=None, **kwargs):
        """
        Create a Discord embed with proper formatting and colors.
        """
        # Determine color based on priority/severity
        color_map = {
            'critical': 0xFF0000,  # Red
            'error': 0xFF4500,     # Orange Red  
            'warning': 0xFFA500,   # Orange
            'info': 0x00FF00,      # Green
            'success': 0x00FF00,   # Green
            'default': 0x7289DA    # Discord blurple
        }
        
        severity = kwargs.get('severity', priority)
        if isinstance(severity, str):
            color = color_map.get(severity.lower(), color_map['default'])
        else:
            color = color_map['default']
        
        embed = {
            "title": title[:256],  # Discord title limit
            "description": message[:4096],  # Discord description limit
            "color": color,
            "timestamp": kwargs.get('timestamp') or self._get_current_timestamp(),
            "fields": []
        }
        
        # Add metadata fields
        if kwargs.get('vm_id'):
            embed["fields"].append({
                "name": "VM ID",
                "value": str(kwargs['vm_id']),
                "inline": True
            })
            
        if kwargs.get('vm_name'):
            embed["fields"].append({
                "name": "VM Name", 
                "value": kwargs['vm_name'],
                "inline": True
            })
            
        if kwargs.get('node'):
            embed["fields"].append({
                "name": "Node",
                "value": kwargs['node'],
                "inline": True
            })
            
        if kwargs.get('source'):
            embed["fields"].append({
                "name": "Source IP",
                "value": kwargs['source'],
                "inline": True
            })
            
        if kwargs.get('event_type'):
            embed["fields"].append({
                "name": "Event Type",
                "value": kwargs['event_type'].replace('_', ' ').title(),
                "inline": True
            })
            
        # Add footer with additional context
        footer_parts = []
        if kwargs.get('hostname'):
            footer_parts.append(f"Host: {kwargs['hostname']}")
        if kwargs.get('tag'):
            footer_parts.append(f"Service: {kwargs['tag']}")
            
        if footer_parts:
            embed["footer"] = {
                "text": " | ".join(footer_parts)
            }
            
        return embed
    
    def _get_current_timestamp(self):
        """Get current timestamp in ISO format for Discord."""
        from datetime import datetime
        return datetime.utcnow().isoformat()
    
    async def test_connection(self) -> bool:
        """
        Test Discord webhook connectivity by sending a test message.
        """
        if not self.webhook_url:
            logger.warning("[DiscordNotifier] Missing webhook URL for test.")
            return False
            
        try:
            test_result = await self.send(
                "MCP Test Connection",
                "Discord notifier test message from Proxmox MCP Server.",
                priority="info"
            )
            return test_result
            
        except Exception as e:
            logger.error(f"[DiscordNotifier] Test connection failed: {e}")
            return False