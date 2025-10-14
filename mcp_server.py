#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server for Proxmox AI Agent
This implements the actual MCP protocol that n8n's MCP Client can connect to.
"""
import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional, Sequence

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-proxmox")

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
        self.dispatcher = EventDispatcher(self.notifiers)
        
        logger.info("Proxmox MCP Server initialized")
        logger.info(f"Lab mode: {self.config.lab_mode}")
        logger.info(f"PVE nodes: {len(self.config.pve_nodes)}")
        logger.info(f"PBS nodes: {len(self.config.pbs_nodes)}")

    def setup_handlers(self):
        """Setup MCP protocol handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available Proxmox tools"""
            return [
                Tool(
                    name="get_cluster_status",
                    description="Get comprehensive status of all Proxmox nodes, VMs, and LXCs",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_details": {
                                "type": "boolean",
                                "description": "Include detailed performance metrics",
                                "default": False
                            }
                        }
                    }
                ),
                Tool(
                    name="get_node_status", 
                    description="Get detailed status of a specific Proxmox node",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name"
                            }
                        },
                        "required": ["node"]
                    }
                ),
                Tool(
                    name="get_vm_status",
                    description="Get status of specific VM or all VMs",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name (optional)"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "VM ID (optional)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_lxc_status",
                    description="Get status of LXC containers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string", 
                                "description": "Node name (optional)"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "Container ID (optional)" 
                            }
                        }
                    }
                ),
                Tool(
                    name="check_node_health",
                    description="Perform comprehensive health check on Proxmox nodes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Specific node to check (optional - checks all if not specified)"
                            }
                        }
                    }
                ),
                Tool(
                    name="monitor_storage",
                    description="Monitor storage usage and health across nodes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name (optional)"
                            }
                        }
                    }
                ),
                Tool(
                    name="send_notification",
                    description="Send notification through configured channels",
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
                            "severity": {
                                "type": "string",
                                "description": "Severity level",
                                "enum": ["info", "warning", "critical"],
                                "default": "info"
                            }
                        },
                        "required": ["title", "message"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[TextContent]:
            """Handle tool calls"""
            
            try:
                if name == "get_cluster_status":
                    return await self._get_cluster_status(arguments)
                elif name == "get_node_status":
                    return await self._get_node_status(arguments)
                elif name == "get_vm_status":
                    return await self._get_vm_status(arguments)
                elif name == "get_lxc_status":
                    return await self._get_lxc_status(arguments)
                elif name == "check_node_health":
                    return await self._check_node_health(arguments)
                elif name == "monitor_storage":
                    return await self._monitor_storage(arguments)
                elif name == "send_notification":
                    return await self._send_notification(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}"
                    )]
                    
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error executing {name}: {str(e)}"
                )]

        @self.server.list_resources()
        async def list_resources() -> List[Resource]:
            """List available resources"""
            return [
                Resource(
                    uri="proxmox://config",
                    name="Proxmox Configuration", 
                    description="Current Proxmox MCP Server configuration"
                ),
                Resource(
                    uri="proxmox://nodes",
                    name="Node List",
                    description="List of configured PVE and PBS nodes"
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri == "proxmox://config":
                return json.dumps({
                    "lab_mode": self.config.lab_mode,
                    "pve_nodes": list(self.config.pve_nodes.keys()),
                    "pbs_nodes": list(self.config.pbs_nodes.keys()),
                    "notifications": {
                        "discord": self.config.discord_out_enabled,
                        "gotify": self.config.gotify_out_enabled
                    }
                }, indent=2)
            elif uri == "proxmox://nodes":
                return json.dumps({
                    "pve_nodes": self.config.pve_nodes,
                    "pbs_nodes": self.config.pbs_nodes
                }, indent=2)
            else:
                raise ValueError(f"Unknown resource: {uri}")

        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """List available prompts"""
            return [
                Prompt(
                    name="proxmox_health_check",
                    description="Perform comprehensive health check of Proxmox infrastructure"
                ),
                Prompt(
                    name="proxmox_status_report", 
                    description="Generate detailed status report for all nodes and VMs"
                )
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> List[PromptMessage]:
            """Get prompt content"""
            if name == "proxmox_health_check":
                return [
                    PromptMessage(
                        role="system",
                        content=TextContent(
                            type="text",
                            text="""You are a Proxmox infrastructure health monitoring assistant. 
                            Use the available MCP tools to check node health, VM status, and storage usage.
                            Identify any critical issues or warnings that need attention.
                            Provide a comprehensive status report with recommendations."""
                        )
                    )
                ]
            elif name == "proxmox_status_report":
                return [
                    PromptMessage(
                        role="system", 
                        content=TextContent(
                            type="text",
                            text="""Generate a detailed Proxmox status report including:
                            1. Node health and resource usage
                            2. VM and LXC status
                            3. Storage utilization 
                            4. Any alerts or issues requiring attention
                            Use the MCP tools to gather current data."""
                        )
                    )
                ]
            else:
                raise ValueError(f"Unknown prompt: {name}")

    async def _get_cluster_status(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get comprehensive cluster status"""
        include_details = args.get("include_details", False)
        
        # Test node connectivity
        success, results = await test_nodes(self.config)
        
        status = {
            "timestamp": asyncio.get_event_loop().time(),
            "nodes_tested": len(results),
            "nodes_reachable": len([r for r in results if r["success"]]),
            "overall_success": success,
            "results": results if include_details else None
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(status, indent=2)
        )]

    async def _get_node_status(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get status of specific node"""
        node_name = args["node"]
        
        # Check if node exists in config
        node_config = self.config.pve_nodes.get(node_name) or self.config.pbs_nodes.get(node_name)
        
        if not node_config:
            return [TextContent(
                type="text",
                text=f"Node '{node_name}' not found in configuration"
            )]
        
        # Test specific node
        success, results = await test_nodes(self.config, target_nodes=[node_name])
        
        return [TextContent(
            type="text", 
            text=json.dumps(results[0] if results else {"error": "No results"}, indent=2)
        )]

    async def _get_vm_status(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get VM status - placeholder implementation"""
        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "VM status check - feature under development",
                "requested_node": args.get("node"),
                "requested_vmid": args.get("vmid"),
                "status": "placeholder"
            }, indent=2)
        )]

    async def _get_lxc_status(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get LXC status - placeholder implementation"""
        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "LXC status check - feature under development", 
                "requested_node": args.get("node"),
                "requested_vmid": args.get("vmid"),
                "status": "placeholder"
            }, indent=2)
        )]

    async def _check_node_health(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Perform node health check"""
        target_node = args.get("node")
        target_nodes = [target_node] if target_node else None
        
        success, results = await test_nodes(self.config, target_nodes=target_nodes)
        
        health_summary = {
            "health_check_timestamp": asyncio.get_event_loop().time(),
            "overall_health": "healthy" if success else "degraded",
            "nodes_checked": len(results),
            "nodes_healthy": len([r for r in results if r["success"]]),
            "detailed_results": results
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(health_summary, indent=2)
        )]

    async def _monitor_storage(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Monitor storage - placeholder implementation"""
        return [TextContent(
            type="text",
            text=json.dumps({
                "message": "Storage monitoring - feature under development",
                "requested_node": args.get("node"),
                "status": "placeholder"
            }, indent=2)
        )]

    async def _send_notification(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Send notification through configured channels"""
        title = args["title"]
        message = args["message"]
        severity = args.get("severity", "info")
        
        if self.dispatcher:
            await self.dispatcher.dispatch(
                title=title,
                message=message,
                severity=severity
            )
            
        return [TextContent(
            type="text",
            text=json.dumps({
                "status": "sent",
                "title": title,
                "message": message,
                "severity": severity,
                "channels": len(self.notifiers)
            }, indent=2)
        )]

async def main():
    """Main server entry point"""
    # Create server instance
    proxmox_server = ProxmoxMCPServer()
    
    # Run server
    async with server.stdio.stdio_server() as (read_stream, write_stream):
        await proxmox_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="proxmox-mcp-server",
                server_version="1.0.0",
                capabilities=proxmox_server.server.get_capabilities(
                    notification_options=NotificationOptions(
                        prompts_changed=False,
                        resources_changed=False,
                        tools_changed=False
                    ),
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    # Print connection info for n8n configuration
    print("🚀 Proxmox MCP Server starting...", file=sys.stderr)
    print("", file=sys.stderr)
    print("📋 CONNECTION INFORMATION FOR N8N:", file=sys.stderr)
    print("   Server Type: stdio", file=sys.stderr) 
    print("   Command: python", file=sys.stderr)
    print(f"   Arguments: {sys.argv[0]}", file=sys.stderr)
    print("", file=sys.stderr)
    print("🔧 Configure n8n MCP Client node with:", file=sys.stderr)
    print("   - Connection Type: stdio", file=sys.stderr)
    print("   - Command: python", file=sys.stderr)
    print(f"   - Args: ['{sys.argv[0]}']", file=sys.stderr)
    print("", file=sys.stderr)
    print("✅ Server ready for connections", file=sys.stderr)
    
    asyncio.run(main())