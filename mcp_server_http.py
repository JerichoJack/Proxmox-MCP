#!/usr/bin/env python3
"""
HTTP/WebSocket MCP Server for Proxmox AI Agent
This implements a network-accessible MCP server that n8n can connect to remotely.
"""
import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence
import argparse

from mcp import server
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import (
    CallToolRequestParams,
    GetPromptRequestParams, 
    Prompt,
    PromptMessage,
    ReadResourceRequestParams,
    Resource,
    TextContent,
    Tool,
)

# Import our Proxmox components
from core.config import MCPConfig
from core.api_tester import test_nodes
from core.event_dispatcher import EventDispatcher
from modules.output.discord_notifier import DiscordNotifier
from modules.output.gotify_notifier import GotifyNotifier

# For HTTP server
from aiohttp import web, WSMsgType
from aiohttp.web import Request, WebSocketResponse
import aiohttp_cors

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-proxmox-http")

class ProxmoxMCPServer:
    """MCP Server for Proxmox operations"""
    
    def __init__(self):
        self.config = MCPConfig(".env")
        self.server = Server("proxmox-mcp-server")
        self.setup_handlers()
        
        # Initialize notifiers for status updates
        self.notifiers = []
        if self.config.gotify_out_enabled:
            self.notifiers.append(GotifyNotifier(self.config))
        if self.config.discord_out_enabled:
            self.notifiers.append(DiscordNotifier(self.config))
            
        # Initialize event dispatcher
        self.event_dispatcher = EventDispatcher(self.notifiers)
        
        logger.info("EventDispatcher initialized with %d notifier(s).", len(self.notifiers))
        logger.info("Proxmox MCP Server initialized")
        logger.info("Lab mode: %s", self.config.lab_mode.upper())
        logger.info("PVE nodes: %d", len(self.config.pve_nodes))
        logger.info("PBS nodes: %d", len(self.config.pbs_nodes))

    def setup_handlers(self):
        """Set up MCP tool and prompt handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available Proxmox management tools"""
            return [
                Tool(
                    name="get_node_status",
                    description="Get status of all Proxmox nodes (PVE and PBS)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_type": {
                                "type": "string",
                                "enum": ["pve", "pbs", "all"],
                                "default": "all",
                                "description": "Type of nodes to query"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_vm_list",
                    description="Get list of VMs/containers from Proxmox nodes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_name": {
                                "type": "string",
                                "description": "Specific node name (optional)"
                            },
                            "vm_type": {
                                "type": "string",
                                "enum": ["qemu", "lxc", "all"],
                                "default": "all",
                                "description": "Type of VMs to list"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_vm_status",
                    description="Get detailed status of a specific VM/container",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_name": {
                                "type": "string",
                                "description": "Name of the Proxmox node"
                            },
                            "vmid": {
                                "type": "string", 
                                "description": "VM/Container ID"
                            }
                        },
                        "required": ["node_name", "vmid"]
                    }
                ),
                Tool(
                    name="start_vm",
                    description="Start a VM/container",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_name": {
                                "type": "string",
                                "description": "Name of the Proxmox node"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM/Container ID"
                            }
                        },
                        "required": ["node_name", "vmid"]
                    }
                ),
                Tool(
                    name="stop_vm",
                    description="Stop a VM/container",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node_name": {
                                "type": "string",
                                "description": "Name of the Proxmox node"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM/Container ID"
                            }
                        },
                        "required": ["node_name", "vmid"]
                    }
                ),
                Tool(
                    name="send_notification",
                    description="Send notification via configured channels",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Notification title"
                            },
                            "message": {
                                "type": "string",
                                "description": "Notification message"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["low", "normal", "high", "critical"],
                                "default": "normal",
                                "description": "Notification priority"
                            }
                        },
                        "required": ["title", "message"]
                    }
                )
            ]

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
            """Handle tool execution"""
            try:
                if name == "get_node_status":
                    result = await self._get_node_status(arguments.get("node_type", "all"))
                elif name == "get_vm_list":
                    result = await self._get_vm_list(
                        arguments.get("node_name"),
                        arguments.get("vm_type", "all")
                    )
                elif name == "get_vm_status":
                    result = await self._get_vm_status(
                        arguments["node_name"],
                        arguments["vmid"]
                    )
                elif name == "start_vm":
                    result = await self._start_vm(
                        arguments["node_name"],
                        arguments["vmid"]
                    )
                elif name == "stop_vm":
                    result = await self._stop_vm(
                        arguments["node_name"],
                        arguments["vmid"]
                    )
                elif name == "send_notification":
                    result = await self._send_notification(
                        arguments["title"],
                        arguments["message"],
                        arguments.get("priority", "normal")
                    )
                else:
                    result = f"Unknown tool: {name}"
                
                return [TextContent(type="text", text=str(result))]
                
            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _get_node_status(self, node_type: str = "all") -> str:
        """Get status of Proxmox nodes"""
        try:
            # test_nodes returns boolean, not dict - need to get actual node data
            node_status = {}
            
            # Test PVE nodes
            if self.config.pve_nodes and (node_type == "all" or node_type == "pve"):
                for node_name in self.config.pve_nodes:
                    node_info = self.config.get_pve_node(node_name)
                    from core.api_tester import test_proxmox_connection
                    is_online = test_proxmox_connection(
                        host=node_info["host"],
                        user=node_info["user"],
                        token_name=node_info["token_name"],
                        token_value=node_info["token_value"],
                        verify_ssl=self.config.verify_ssl,
                        is_pbs=False
                    )
                    node_status[f"PVE-{node_name}"] = {
                        "type": "PVE",
                        "host": node_info["host"],
                        "status": "online" if is_online else "offline",
                        "port": 8006
                    }
            
            # Test PBS nodes
            if self.config.pbs_nodes and (node_type == "all" or node_type == "pbs"):
                for node_name in self.config.pbs_nodes:
                    node_info = self.config.get_pbs_node(node_name)
                    from core.api_tester import test_proxmox_connection
                    is_online = test_proxmox_connection(
                        host=node_info["host"],
                        user=node_info["user"],
                        token_name=node_info["token_name"],
                        token_value=node_info["token_value"],
                        verify_ssl=self.config.verify_ssl,
                        is_pbs=True
                    )
                    node_status[f"PBS-{node_name}"] = {
                        "type": "PBS",
                        "host": node_info["host"],
                        "status": "online" if is_online else "offline",
                        "port": 8007
                    }
                
            return json.dumps(node_status, indent=2)
                
        except Exception as e:
            return f"Error getting node status: {str(e)}"

    async def _get_vm_list(self, node_name: Optional[str] = None, vm_type: str = "all") -> str:
        """Get list of VMs from Proxmox nodes"""
        # Implementation would go here - placeholder for now
        return json.dumps({
            "message": "VM list functionality",
            "node_name": node_name,
            "vm_type": vm_type,
            "note": "Full implementation would query Proxmox API"
        }, indent=2)

    async def _get_vm_status(self, node_name: str, vmid: str) -> str:
        """Get status of specific VM"""
        # Implementation would go here - placeholder for now
        return json.dumps({
            "message": "VM status functionality", 
            "node_name": node_name,
            "vmid": vmid,
            "note": "Full implementation would query Proxmox API"
        }, indent=2)

    async def _start_vm(self, node_name: str, vmid: str) -> str:
        """Start a VM"""
        # Implementation would go here - placeholder for now
        return json.dumps({
            "message": f"Would start VM {vmid} on node {node_name}",
            "note": "Full implementation would use Proxmox API"
        }, indent=2)

    async def _stop_vm(self, node_name: str, vmid: str) -> str:
        """Stop a VM"""
        # Implementation would go here - placeholder for now  
        return json.dumps({
            "message": f"Would stop VM {vmid} on node {node_name}",
            "note": "Full implementation would use Proxmox API"
        }, indent=2)

    async def _send_notification(self, title: str, message: str, priority: str = "normal") -> str:
        """Send notification via configured channels"""
        try:
            event_data = {
                "title": title,
                "message": message,
                "priority": priority,
                "source": "mcp_server"
            }
            
            await self.event_dispatcher.dispatch_event("notification", event_data)
            return f"Notification sent: {title}"
            
        except Exception as e:
            return f"Error sending notification: {str(e)}"
    
    async def _get_available_tools(self) -> list:
        """Get list of available tools for HTTP interface"""
        return [
            {
                "name": "get_node_status",
                "description": "Get status of all Proxmox nodes (PVE and PBS)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node_type": {
                            "type": "string",
                            "enum": ["pve", "pbs", "all"],
                            "default": "all",
                            "description": "Type of nodes to query"
                        }
                    }
                }
            },
            {
                "name": "get_vm_list",
                "description": "Get list of VMs/containers from Proxmox nodes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node_name": {
                            "type": "string",
                            "description": "Specific node name (optional)"
                        },
                        "vm_type": {
                            "type": "string",
                            "enum": ["qemu", "lxc", "all"],
                            "default": "all",
                            "description": "Type of VMs to list"
                        }
                    }
                }
            },
            {
                "name": "get_vm_status",
                "description": "Get detailed status of a specific VM/container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node_name": {
                            "type": "string",
                            "description": "Name of the Proxmox node"
                        },
                        "vmid": {
                            "type": "string",
                            "description": "VM/Container ID"
                        }
                    },
                    "required": ["node_name", "vmid"]
                }
            },
            {
                "name": "start_vm",
                "description": "Start a VM/container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node_name": {
                            "type": "string",
                            "description": "Name of the Proxmox node"
                        },
                        "vmid": {
                            "type": "string",
                            "description": "VM/Container ID"
                        }
                    },
                    "required": ["node_name", "vmid"]
                }
            },
            {
                "name": "stop_vm",
                "description": "Stop a VM/container",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node_name": {
                            "type": "string",
                            "description": "Name of the Proxmox node"
                        },
                        "vmid": {
                            "type": "string",
                            "description": "VM/Container ID"
                        }
                    },
                    "required": ["node_name", "vmid"]
                }
            },
            {
                "name": "send_notification",
                "description": "Send notification via configured channels",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Notification title"
                        },
                        "message": {
                            "type": "string",
                            "description": "Notification message"
                        },
                        "priority": {
                            "type": "string",
                            "enum": ["low", "normal", "high", "critical"],
                            "default": "normal",
                            "description": "Notification priority"
                        }
                    },
                    "required": ["title", "message"]
                }
            }
        ]
    
    async def _execute_tool(self, name: str, arguments: dict) -> str:
        """Execute tool for HTTP interface"""
        try:
            if name == "get_node_status":
                return await self._get_node_status(arguments.get("node_type", "all"))
            elif name == "get_vm_list":
                return await self._get_vm_list(
                    arguments.get("node_name"),
                    arguments.get("vm_type", "all")
                )
            elif name == "get_vm_status":
                return await self._get_vm_status(
                    arguments["node_name"],
                    arguments["vmid"]
                )
            elif name == "start_vm":
                return await self._start_vm(
                    arguments["node_name"],
                    arguments["vmid"]
                )
            elif name == "stop_vm":
                return await self._stop_vm(
                    arguments["node_name"],
                    arguments["vmid"]
                )
            elif name == "send_notification":
                return await self._send_notification(
                    arguments["title"],
                    arguments["message"],
                    arguments.get("priority", "normal")
                )
            else:
                return f"Unknown tool: {name}"
                
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return f"Error: {str(e)}"


class MCPHTTPServer:
    """HTTP/WebSocket server for MCP protocol"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port
        self.proxmox_server = ProxmoxMCPServer()
        
    async def websocket_handler(self, request: Request) -> WebSocketResponse:
        """Handle WebSocket connections for MCP protocol"""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        logger.info(f"WebSocket connection from {request.remote}")
        
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        logger.debug(f"Received: {data}")
                        
                        # Handle MCP protocol messages
                        response = await self._handle_mcp_message(data)
                        if response:
                            await ws.send_str(json.dumps(response))
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON: {e}")
                        error_response = {
                            "jsonrpc": "2.0",
                            "error": {"code": -32700, "message": "Parse error"}
                        }
                        await ws.send_str(json.dumps(error_response))
                        
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            logger.info("WebSocket connection closed")
            
        return ws
    
    async def _handle_mcp_message(self, data: dict) -> Optional[dict]:
        """Handle MCP protocol messages"""
        method = data.get("method")
        request_id = data.get("id")
        params = data.get("params", {})
        
        try:
            if method == "initialize":
                capabilities = self.proxmox_server.server.get_capabilities(
                    notification_options=NotificationOptions(
                        prompts_changed=False,
                        resources_changed=False,
                        tools_changed=False
                    ),
                    experimental_capabilities={}
                )
                
                # Convert capabilities to JSON-serializable dict
                capabilities_dict = {
                    "tools": {"listChanged": False} if hasattr(capabilities, 'tools') else {},
                    "prompts": {"listChanged": False} if hasattr(capabilities, 'prompts') else {},
                    "resources": {"listChanged": False} if hasattr(capabilities, 'resources') else {}
                }
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": capabilities_dict,
                        "serverInfo": {
                            "name": "proxmox-mcp-server",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif method == "tools/list":
                # Use the ProxmoxMCPServer's tool list method directly
                tools = await self.proxmox_server._get_available_tools()
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": tools
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Use the ProxmoxMCPServer's tool execution method directly
                result = await self.proxmox_server._execute_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0", 
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": str(result)}]
                    }
                }
            
            elif method == "initialized":
                # Acknowledgment message, no response needed
                return None
                
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
                
        except Exception as e:
            logger.error(f"Error handling MCP message: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id, 
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def http_handler(self, request: Request) -> web.Response:
        """Handle HTTP POST requests for MCP protocol (for n8n compatibility)"""
        try:
            data = await request.json()
            logger.info(f"HTTP MCP request from {request.remote}: {data.get('method', 'unknown')}")
            
            # Process MCP message
            response = await self._handle_mcp_message(data)
            
            if response:
                return web.json_response(response)
            else:
                # For methods like 'initialized' that don't need a response
                return web.json_response({"status": "ok"})
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in HTTP request: {e}")
            return web.json_response({
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"}
            }, status=400)
        except Exception as e:
            logger.error(f"HTTP handler error: {e}")
            return web.json_response({
                "jsonrpc": "2.0", 
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"}
            }, status=500)

    async def health_check(self, request: Request) -> web.Response:
        """Health check endpoint"""
        return web.json_response({
            "status": "healthy",
            "server": "proxmox-mcp-server",
            "version": "1.0.0"
        })

    async def start_server(self):
        """Start the HTTP/WebSocket server"""
        app = web.Application()
        
        # Setup CORS
        cors = aiohttp_cors.setup(app, defaults={
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*"
            )
        })
        
        # Add routes
        app.router.add_get('/ws', self.websocket_handler)
        app.router.add_post('/ws', self.http_handler)  # Add HTTP POST handler for n8n
        app.router.add_post('/mcp', self.http_handler)  # Alternative endpoint
        app.router.add_get('/health', self.health_check)
        
        # Add CORS to all routes
        for route in list(app.router.routes()):
            cors.add(route)
        
        # Start server
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        print(f"🌐 Proxmox MCP HTTP Server started", file=sys.stderr)
        print(f"📡 WebSocket endpoint: ws://{self.host}:{self.port}/ws", file=sys.stderr)
        print(f"🔗 HTTP endpoint: http://{self.host}:{self.port}/mcp", file=sys.stderr)
        print(f"🏥 Health check: http://{self.host}:{self.port}/health", file=sys.stderr)
        print("", file=sys.stderr)
        print("🔧 N8N MCP CLIENT CONFIGURATION OPTIONS:", file=sys.stderr)
        print("   Option 1 - WebSocket:", file=sys.stderr)
        print("   Connection Type: websocket", file=sys.stderr)
        print(f"   Endpoint: ws://{self.host}:{self.port}/ws", file=sys.stderr)
        print("", file=sys.stderr)
        print("   Option 2 - HTTP:", file=sys.stderr)
        print("   Connection Type: http", file=sys.stderr)
        print(f"   Endpoint: http://{self.host}:{self.port}/mcp", file=sys.stderr)
        print("", file=sys.stderr)
        print("✅ Server ready for connections", file=sys.stderr)
        
        # Keep server running
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            await runner.cleanup()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Proxmox MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = MCPHTTPServer(host=args.host, port=args.port)
    await server.start_server()


if __name__ == "__main__":
    asyncio.run(main())