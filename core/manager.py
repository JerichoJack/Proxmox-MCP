# core/manager.py
import asyncio
import signal
import sys
from typing import List, Optional

from core.config import MCPConfig
from core.event_dispatcher import EventDispatcher
from core.utils import setup_logger
# Input modules
from modules.input.discord_listener import DiscordListener
from modules.input.email_listener import EmailListener
from modules.input.gotify_listener import GotifyListener
from modules.input.syslog_listener import SyslogListener
from modules.input.websocket_listener import WebSocketListener
# Output modules
from modules.output.discord_notifier import DiscordNotifier
from modules.output.gotify_notifier import GotifyNotifier

logger = setup_logger()


class MCPManager:
    """
    Central orchestrator for the MCP Server.
    Manages the complete lifecycle of input listeners, output notifiers, and event processing.
    Follows the architecture: Input → EventDispatcher → Output
    """
    
    def __init__(self, env_path: str = ".env"):
        self.config = MCPConfig(env_path)
        self.notifiers: List = []
        self.listeners: List = []
        self.dispatcher: Optional[EventDispatcher] = None
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Setup graceful shutdown handlers
        self._setup_signal_handlers()
        
        logger.info("MCPManager initialized")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating shutdown...")
            asyncio.create_task(self.shutdown())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def setup(self):
        """
        Initialize all components based on configuration.
        Sets up notifiers first, then listeners, then the event dispatcher.
        """
        logger.info("Setting up MCP Manager components...")
        print(self.config.summary())

        # -----------------------
        # Initialize Output Notifiers
        # -----------------------
        self._setup_notifiers()
        
        # -----------------------
        # Initialize Event Dispatcher
        # -----------------------
        self.dispatcher = EventDispatcher(self.notifiers)
        
        # -----------------------
        # Initialize Input Listeners
        # -----------------------
        self._setup_listeners()
        
        logger.info(f"Setup complete: {len(self.listeners)} listener(s), {len(self.notifiers)} notifier(s)")

    def _setup_notifiers(self):
        """Initialize all configured output notifiers."""
        logger.info("Setting up output notifiers...")
        
        # Gotify Output
        if self.config.gotify_out_enabled:
            if self.config.gotify_out_server_url and self.config.gotify_out_app_token:
                self.notifiers.append(GotifyNotifier(self.config))
                logger.info("✅ GotifyNotifier enabled")
            else:
                logger.warning("⚠️ Gotify output enabled but missing server URL or app token")

        # Discord Output
        if self.config.discord_out_enabled:
            if self.config.discord_out_webhook:
                self.notifiers.append(DiscordNotifier(self.config))
                logger.info("✅ DiscordNotifier enabled")
            else:
                logger.warning("⚠️ Discord output enabled but missing webhook URL")

        if not self.notifiers:
            logger.warning("⚠️ No output notifiers configured - events will be logged only")

    def _setup_listeners(self):
        """Initialize all configured input listeners."""
        logger.info("Setting up input listeners...")
        
        # WebSocket Listener
        if self.config.event_ws_enabled and "WEBSOCKET" in self.config.enabled_event_listeners:
            self.listeners.append(WebSocketListener(self.config, event_callback=self.on_event))
            logger.info("✅ WebSocketListener enabled")

        # Email Listener
        if self.config.event_email_enabled and "EMAIL" in self.config.enabled_event_listeners:
            self.listeners.append(EmailListener(self.config, event_callback=self.on_event))
            logger.info("✅ EmailListener enabled")

        # Syslog Listener
        if self.config.event_syslog_enabled and "SYSLOG" in self.config.enabled_event_listeners:
            self.listeners.append(SyslogListener(self.config, event_callback=self.on_event))
            logger.info("✅ SyslogListener enabled")

        # Gotify Input Listener
        if self.config.gotify_in_enabled and "GOTIFY_IN" in self.config.enabled_event_listeners:
            if self.config.gotify_in_server_url and self.config.gotify_in_client_token:
                self.listeners.append(GotifyListener(self.config, event_callback=self.on_event))
                logger.info("✅ GotifyListener (input) enabled")
            else:
                logger.warning("⚠️ Gotify input enabled but missing server URL or client token")

        # Discord Input Listener
        if self.config.discord_in_enabled and "DISCORD_IN" in self.config.enabled_event_listeners:
            if self.config.discord_in_webhook:
                self.listeners.append(DiscordListener(self.config, event_callback=self.on_event))
                logger.info("✅ DiscordListener (input) enabled")
            else:
                logger.warning("⚠️ Discord input enabled but missing webhook URL")

        if not self.listeners:
            logger.warning("⚠️ No input listeners configured - no events will be received")

    async def on_event(self, title: str, message: str, **kwargs):
        """
        Event callback for all input listeners.
        Receives events and dispatches them through the EventDispatcher.
        """
        if self.dispatcher and self._running:
            try:
                await self.dispatcher.dispatch(title, message, **kwargs)
            except Exception as e:
                logger.error(f"Error processing event '{title}': {e}")
        else:
            logger.warning(f"Event received but dispatcher not ready: {title}")

    async def start_all_listeners(self):
        """Start all configured input listeners."""
        if not self.listeners:
            logger.warning("No listeners to start")
            return

        logger.info(f"Starting {len(self.listeners)} listener(s)...")
        
        tasks = []
        for listener in self.listeners:
            try:
                task = asyncio.create_task(listener.start())
                tasks.append(task)
                logger.info(f"Started {listener.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to start {listener.__class__.__name__}: {e}")

        return tasks

    async def stop_all_listeners(self):
        """Stop all running input listeners."""
        logger.info(f"Stopping {len(self.listeners)} listener(s)...")
        
        stop_tasks = []
        for listener in self.listeners:
            try:
                if hasattr(listener, 'stop'):
                    task = asyncio.create_task(listener.stop())
                    stop_tasks.append(task)
                    logger.info(f"Stopping {listener.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error stopping {listener.__class__.__name__}: {e}")

        if stop_tasks:
            await asyncio.gather(*stop_tasks, return_exceptions=True)

    async def test_connectivity(self) -> bool:
        """
        Test connectivity to all configured Proxmox nodes and I/O modules.
        Returns True if all tests pass, False otherwise.
        """
        logger.info("🔗 Testing system connectivity...")
        
        # Test Proxmox nodes
        from core.api_tester import test_nodes
        nodes_ok = test_nodes(self.config)
        
        # Test output notifiers
        notifiers_ok = await self._test_notifiers()
        
        # Test input listeners
        listeners_ok = await self._test_listeners()
        
        overall_success = nodes_ok and notifiers_ok and listeners_ok
        
        if overall_success:
            logger.info("🎉 All connectivity tests passed!")
        else:
            logger.warning("⚠️ Some connectivity tests failed")
            
        return overall_success

    async def _test_notifiers(self) -> bool:
        """Test all configured output notifiers."""
        if not self.notifiers:
            return True
            
        success = True
        logger.info("🔔 Testing output notifiers...")
        
        for notifier in self.notifiers:
            try:
                if hasattr(notifier, 'test_connection'):
                    result = await notifier.test_connection()
                    if result:
                        logger.info(f"✅ {notifier.__class__.__name__} test passed")
                    else:
                        logger.error(f"❌ {notifier.__class__.__name__} test failed")
                        success = False
                else:
                    # Send a test message if no test_connection method
                    await notifier.send("MCP Test", "Testing notifier connectivity", priority="info")
                    logger.info(f"✅ {notifier.__class__.__name__} test sent")
            except Exception as e:
                logger.error(f"❌ {notifier.__class__.__name__} test failed: {e}")
                success = False
                
        return success

    async def _test_listeners(self) -> bool:
        """Test all configured input listeners."""
        if not self.listeners:
            return True
            
        success = True
        logger.info("📡 Testing input listeners...")
        
        for listener in self.listeners:
            try:
                if hasattr(listener, 'test_connection'):
                    result = await listener.test_connection()
                    if result:
                        logger.info(f"✅ {listener.__class__.__name__} test passed")
                    else:
                        logger.error(f"❌ {listener.__class__.__name__} test failed")
                        success = False
                else:
                    logger.info(f"ℹ️ {listener.__class__.__name__} - no test method available")
            except Exception as e:
                logger.error(f"❌ {listener.__class__.__name__} test failed: {e}")
                success = False
                
        return success

    async def run(self):
        """
        Main execution loop - starts all listeners and runs until shutdown.
        """
        if not self.dispatcher:
            raise RuntimeError("Manager not properly set up. Call setup() first.")
            
        self._running = True
        logger.info("🚀 Starting MCP Server...")
        
        try:
            # Start all listeners
            listener_tasks = await self.start_all_listeners()
            
            if not listener_tasks:
                logger.warning("No listeners started - server will only handle direct API calls")
                await self._shutdown_event.wait()
            else:
                logger.info("MCP Server is running. Press Ctrl+C to stop.")
                
                # Wait for shutdown signal or listener failure
                done, pending = await asyncio.wait(
                    listener_tasks + [asyncio.create_task(self._shutdown_event.wait())],
                    return_when=asyncio.FIRST_COMPLETED
                )
                
                # Cancel any pending tasks
                for task in pending:
                    task.cancel()
                    
                # Check if any listener task failed
                for task in done:
                    if not task.cancelled() and task.exception():
                        logger.error(f"Listener task failed: {task.exception()}")
                        
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            raise
        finally:
            await self.stop_all_listeners()
            self._running = False
            logger.info("MCP Server stopped")

    async def shutdown(self):
        """Initiate graceful shutdown."""
        logger.info("Initiating graceful shutdown...")
        self._shutdown_event.set()


# Convenience function for CLI usage
async def run_mcp_server(env_path: str = ".env", test_only: bool = False):
    """
    Convenience function to run the MCP server.
    
    Args:
        env_path: Path to .env configuration file
        test_only: If True, run connectivity tests and exit
    """
    manager = MCPManager(env_path)
    manager.setup()
    
    if test_only:
        success = await manager.test_connectivity()
        sys.exit(0 if success else 1)
    else:
        await manager.run()


# Optional test when run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Server Manager")
    parser.add_argument("--test", action="store_true", help="Run connectivity tests and exit")
    parser.add_argument("--config", default=".env", help="Configuration file path")
    args = parser.parse_args()
    
    asyncio.run(run_mcp_server(args.config, args.test))
