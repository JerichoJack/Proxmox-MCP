# modules/input/websocket_listener.py
import asyncio
import json
import websockets
from core.config import MCPConfig


class WebSocketListener:
    """
    Connects to Proxmox nodes via WebSocket for live event ingestion.
    Supports standalone, clustered, and mixed lab topologies.
    """

    def __init__(self, config: MCPConfig, event_callback):
        """
        :param config: MCPConfig instance
        :param event_callback: async function to handle incoming events
        """
        self.config = config
        self.event_callback = event_callback
        self._tasks = []
        self._running = False

    async def _connect_to_node(self, node_name: str):
        """Connect to a single Proxmox node's WebSocket and listen for events."""
        node_info = self.config.get_pve_node(node_name)
        host = node_info.get("host")
        user = node_info.get("user")
        token_name = node_info.get("token_name")
        token_value = node_info.get("token_value")

        if not all([host, user, token_name, token_value]):
            print(f"[WS] Node {node_name} missing credentials, skipping.")
            return

        url = f"wss://{host}:8006/api2/json/nodes/{node_name}/tasks?type=vm"
        headers = {"Authorization": f"PVEAPIToken={user}!{token_name}={token_value}"}

        while self._running:
            try:
                async with websockets.connect(url, extra_headers=headers, ssl=not self.config.verify_ssl) as ws:
                    print(f"[WS] Connected to node {node_name} WebSocket")
                    async for message in ws:
                        try:
                            data = json.loads(message)
                            await self.event_callback(node_name, data)
                        except Exception as e:
                            print(f"[WS] Error parsing message from {node_name}: {e}")
            except Exception as e:
                print(f"[WS] Connection error for node {node_name}: {e}")
            # Reconnect after interval
            await asyncio.sleep(self.config.ws_interval)

    async def test_connection(self):
        """Test WebSocket connectivity for all PVE nodes."""
        results = {}
        for node_name in self.config.pve_nodes:
            node_info = self.config.get_pve_node(node_name)
            host = node_info.get("host")
            user = node_info.get("user")
            token_name = node_info.get("token_name")
            token_value = node_info.get("token_value")
            if not all([host, user, token_name, token_value]):
                results[node_name] = "Missing credentials"
                continue

            url = f"wss://{host}:8006/api2/json/nodes/{node_name}/tasks?type=vm"
            headers = {"Authorization": f"PVEAPIToken={user}!{token_name}={token_value}"}
            try:
                async with websockets.connect(url, extra_headers=headers, ssl=not self.config.verify_ssl) as ws:
                    results[node_name] = "Success"
            except Exception as e:
                results[node_name] = f"Failed: {e}"
        return results

    async def start(self):
        """Start WebSocket listeners for all PVE nodes."""
        if not self.config.event_ws_enabled:
            print("[WS] WebSocket listener is disabled in config.")
            return

        self._running = True
        for node_name in self.config.pve_nodes:
            task = asyncio.create_task(self._connect_to_node(node_name))
            self._tasks.append(task)
        print(f"[WS] WebSocket listener started for nodes: {', '.join(self.config.pve_nodes)}")

    async def stop(self):
        """Stop all WebSocket listeners."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        print("[WS] WebSocket listener stopped.")
