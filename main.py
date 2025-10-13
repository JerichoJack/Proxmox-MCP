# main.py
import argparse
import asyncio
import signal
import sys

from core.config import MCPConfig
from core.event_dispatcher import EventDispatcher

# Input listeners
from modules.input.websocket_listener import WebSocketListener
from modules.input.email_listener import EmailListener
from modules.input.gotify_listener import GotifyListener

# Output notifiers
from modules.output.gotify_notifier import GotifyNotifier
# from modules.output.discord_notifier import DiscordNotifier

# --------------------------
# Load configuration
# --------------------------
config = MCPConfig(".env")
print(config.summary())

# --------------------------
# Parse CLI arguments
# --------------------------
parser = argparse.ArgumentParser(description="MCP Server for Proxmox")
parser.add_argument(
    "--test-connection",
    action="store_true",
    help="Test connectivity to all configured PVE/PBS nodes and exit",
)
args = parser.parse_args()

# --------------------------
# Setup Notifiers (Output)
# --------------------------
notifiers = []
if config.gotify_out_enabled:
    notifiers.append(GotifyNotifier(config))
# if config.discord_out_enabled:
#     notifiers.append(DiscordNotifier(config))

dispatcher = EventDispatcher(notifiers)

# --------------------------
# Setup Event Listeners (Input)
# --------------------------
listeners = []
if config.event_ws_enabled:
    listeners.append(WebSocketListener(config, event_callback=dispatcher.dispatch))
if config.event_email_enabled:
    listeners.append(EmailListener(config, event_callback=dispatcher.dispatch))
if config.gotify_in_enabled:
    listeners.append(GotifyListener(config, event_callback=dispatcher.dispatch))
# if config.discord_in_enabled:
#     listeners.append(DiscordListener(config, event_callback=dispatcher.dispatch))

# --------------------------
# Test Connection & IO Modules
# --------------------------
if args.test_connection:
    print("\n🔗 Testing connectivity to configured nodes...")
    from core.api_tester import test_nodes

    all_success = test_nodes(config)

    async def test_notifiers():
        success = True
        if config.gotify_out_enabled:
            print("🔔 Testing Gotify output notifier...")
            notifier = GotifyNotifier(config)
            try:
                await notifier.send("MCP Test", "Testing Gotify output notifier.")
                print("✅ Gotify output test sent successfully.")
            except Exception as e:
                print(f"❌ Gotify output test failed: {e}")
                success = False
        return success

    async def test_listeners():
        success = True
        if config.gotify_in_enabled:
            print("🔔 Testing Gotify input listener (stream)...")
            listener = GotifyListener(config, event_callback=lambda t, m: None)
            result = await listener.test_connection()
            if result:
                print("✅ Gotify input test stream succeeded.")
            else:
                print("❌ Gotify input test stream failed.")
                success = False
        return success

    async def run_io_tests():
        notifier_result = await test_notifiers()
        listener_result = await test_listeners()
        return notifier_result and listener_result

    io_success = asyncio.run(run_io_tests())

    if all_success and io_success:
        print("\n🎉 All nodes and IO modules are reachable and ready!\n")
    else:
        print("\n⚠ Some nodes or IO modules failed. Check configuration and network.\n")
    sys.exit(0)
    
# --------------------------
# Main Event Loop
# --------------------------
async def start_listeners():
    for listener in listeners:
        await listener.start()
    print("✅ All listeners started")

async def stop_listeners():
    for listener in listeners:
        await listener.stop()
    print("🛑 All listeners stopped")

async def main():
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def shutdown():
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    await start_listeners()
    await stop_event.wait()
    await stop_listeners()

# --------------------------
# Entry Point
# --------------------------
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Interrupted by user, shutting down...")
