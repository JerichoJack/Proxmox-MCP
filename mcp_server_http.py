#!/usr/bin/env python3
"""
HTTP/WebSocket MCP Server for Proxmox AI Agent
This implements a network-accessible MCP server that n8n can connect to remotely.
Enhanced version with comprehensive Proxmox API functionality.
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
from core.proxmox_api import ProxmoxAPIManager
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
    """Enhanced MCP Server for comprehensive Proxmox operations"""
    
    def __init__(self):
        self.config = MCPConfig(".env")
        self.server = Server("proxmox-mcp-server")
        
        # Initialize Proxmox API manager (lazy initialization)
        self.api_manager = None
        
        self.setup_handlers()
        
        # Initialize notifiers for status updates
        self.notifiers = []
        if self.config.gotify_out_enabled:
            self.notifiers.append(GotifyNotifier(self.config))
        if self.config.discord_out_enabled:
            self.notifiers.append(DiscordNotifier(self.config))
        self.dispatcher = EventDispatcher(self.notifiers)
        
        logger.info("Enhanced Proxmox MCP Server initialized")
        logger.info(f"Lab mode: {self.config.lab_mode}")
        logger.info(f"PVE nodes configured: {len(self.config.pve_nodes)}")
        logger.info(f"PBS nodes configured: {len(self.config.pbs_nodes)}")
        logger.info("API connections will be established when first tool is used")

    def _ensure_api_manager(self):
        """Lazy initialization of API manager"""
        if self.api_manager is None:
            logger.info("Initializing Proxmox API connections...")
            self.api_manager = ProxmoxAPIManager(self.config)
            logger.info(f"API Manager initialized - PVE: {len(self.api_manager.pve_clients)}, PBS: {len(self.api_manager.pbs_clients)}")
        return self.api_manager

    def setup_handlers(self):
        """Setup enhanced MCP protocol handlers with comprehensive Proxmox functionality"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available Proxmox tools with comprehensive functionality"""
            return [
                # Core cluster and node operations
                Tool(
                    name="get_cluster_status",
                    description="Get comprehensive status of Proxmox cluster including nodes, resources, and health",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_details": {
                                "type": "boolean",
                                "description": "Include detailed performance metrics and resource usage",
                                "default": False
                            }
                        }
                    }
                ),
                Tool(
                    name="get_nodes",
                    description="Get detailed information about all Proxmox nodes including status and resources",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "include_details": {
                                "type": "boolean",
                                "description": "Include detailed node metrics and performance data",
                                "default": True
                            }
                        }
                    }
                ),
                Tool(
                    name="get_node_status", 
                    description="Get detailed status of a specific Proxmox node including CPU, memory, storage usage",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name to query"
                            }
                        },
                        "required": ["node"]
                    }
                ),
                
                # VM operations
                Tool(
                    name="get_vms",
                    description="Get comprehensive VM information including status, configuration, and performance",
                    inputSchema={
                        "type": "object", 
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name to filter VMs (optional - gets all VMs if not specified)"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "Specific VM ID to query (optional)"
                            }
                        }
                    }
                ),
                Tool(
                    name="execute_vm_command",
                    description="Execute commands on VMs (start, stop, restart, suspend, resume, reset, status)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name where the VM is located"
                            },
                            "vmid": {
                                "type": "string", 
                                "description": "VM ID to operate on"
                            },
                            "command": {
                                "type": "string",
                                "description": "Command to execute",
                                "enum": ["start", "stop", "shutdown", "restart", "reboot", "suspend", "resume", "reset", "status", "config"]
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Force the operation (for stop/shutdown)",
                                "default": False
                            }
                        },
                        "required": ["node", "vmid", "command"]
                    }
                ),
                
                # LXC operations
                Tool(
                    name="get_lxcs",
                    description="Get comprehensive LXC container information including status and configuration",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string", 
                                "description": "Node name to filter containers (optional - gets all if not specified)"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "Specific container ID to query (optional)" 
                            }
                        }
                    }
                ),
                Tool(
                    name="execute_lxc_command",
                    description="Execute commands on LXC containers (start, stop, restart, suspend, resume, status)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name where the container is located"
                            },
                            "vmid": {
                                "type": "string",
                                "description": "Container ID to operate on"
                            },
                            "command": {
                                "type": "string",
                                "description": "Command to execute",
                                "enum": ["start", "stop", "shutdown", "restart", "reboot", "suspend", "resume", "status", "config"]
                            },
                            "force": {
                                "type": "boolean",
                                "description": "Force the operation (for stop/shutdown)",
                                "default": False
                            }
                        },
                        "required": ["node", "vmid", "command"]
                    }
                ),
                
                # Storage operations
                Tool(
                    name="get_storage",
                    description="Get detailed storage information including usage, content, and health status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name to filter storage (optional - gets all storage if not specified)"
                            },
                            "storage": {
                                "type": "string",
                                "description": "Specific storage name to query (optional)"
                            }
                        }
                    }
                ),
                
                # Advanced operations
                Tool(
                    name="get_node_tasks",
                    description="Get recent tasks and operations for nodes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name to get tasks for"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of tasks to return",
                                "default": 50
                            }
                        },
                        "required": ["node"]
                    }
                ),
                Tool(
                    name="get_backup_info", 
                    description="Get backup job information and status",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name to filter backups (optional)"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_network_info",
                    description="Get network configuration and interface information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "node": {
                                "type": "string",
                                "description": "Node name to get network info for (optional - gets all if not specified)"
                            }
                        }
                    }
                ),
                
                # Health and monitoring
                Tool(
                    name="check_node_health",
                    description="Perform comprehensive health check on Proxmox nodes including connectivity and resource status",
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
                
                # Notification
                Tool(
                    name="send_notification",
                    description="Send notification through configured channels (Discord, Gotify)",
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
            """Handle enhanced tool calls with comprehensive Proxmox functionality"""
            
            try:
                # Core cluster and node operations
                if name == "get_cluster_status":
                    return await self._get_cluster_status(arguments)
                elif name == "get_nodes":
                    return await self._get_nodes(arguments)
                elif name == "get_node_status":
                    return await self._get_node_status(arguments)
                
                # VM operations
                elif name == "get_vms":
                    return await self._get_vms(arguments)
                elif name == "execute_vm_command":
                    return await self._execute_vm_command(arguments)
                
                # LXC operations
                elif name == "get_lxcs":
                    return await self._get_lxcs(arguments)
                elif name == "execute_lxc_command":
                    return await self._execute_lxc_command(arguments)
                
                # Storage operations
                elif name == "get_storage":
                    return await self._get_storage(arguments)
                
                # Advanced operations
                elif name == "get_node_tasks":
                    return await self._get_node_tasks(arguments)
                elif name == "get_backup_info":
                    return await self._get_backup_info(arguments)
                elif name == "get_network_info":
                    return await self._get_network_info(arguments)
                
                # Health and monitoring
                elif name == "check_node_health":
                    return await self._check_node_health(arguments)
                
                # Notification
                elif name == "send_notification":
                    return await self._send_notification(arguments)
                
                else:
                    return [TextContent(
                        type="text",
                        text=f"Unknown tool: {name}. Available tools: get_cluster_status, get_nodes, get_node_status, get_vms, get_lxcs, get_storage, execute_vm_command, execute_lxc_command, get_node_tasks, get_backup_info, get_network_info, check_node_health, send_notification"
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
                    description="Current Proxmox MCP Server configuration including connected clients"
                ),
                Resource(
                    uri="proxmox://nodes",
                    name="Node List",
                    description="List of configured PVE and PBS nodes with connection status"
                ),
                Resource(
                    uri="proxmox://capabilities",
                    name="Server Capabilities",
                    description="Available MCP server capabilities and tool descriptions"
                ),
                Resource(
                    uri="proxmox://status",
                    name="Server Status",
                    description="Current server status and health of all connections"
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read enhanced resource content"""
            if uri == "proxmox://config":
                # Use lazy initialization for API manager info
                pve_connected = []
                pbs_connected = []
                total_connected = 0
                connection_health = "not_initialized"
                
                if self.api_manager is not None:
                    pve_connected = list(self.api_manager.pve_clients.keys())
                    pbs_connected = list(self.api_manager.pbs_clients.keys())
                    total_connected = len(pve_connected) + len(pbs_connected)
                    connection_health = "healthy" if total_connected > 0 else "no_connections"
                
                return json.dumps({
                    "server_info": {
                        "version": "2.0.0-enhanced",
                        "capabilities": ["vm_management", "lxc_management", "storage_monitoring", "cluster_management", "task_monitoring", "backup_info", "network_info"]
                    },
                    "lab_mode": self.config.lab_mode,
                    "nodes": {
                        "pve_configured": list(self.config.pve_nodes),
                        "pbs_configured": list(self.config.pbs_nodes),
                        "pve_connected": pve_connected,
                        "pbs_connected": pbs_connected
                    },
                    "notifications": {
                        "discord": self.config.discord_out_enabled,
                        "gotify": self.config.gotify_out_enabled
                    },
                    "connection_summary": {
                        "total_configured": len(self.config.pve_nodes) + len(self.config.pbs_nodes),
                        "total_connected": total_connected,
                        "connection_health": connection_health
                    }
                }, indent=2)
            elif uri == "proxmox://nodes":
                node_details = {}
                
                # Add PVE node details
                for node_name in self.config.pve_nodes:
                    node_config = self.config.get_pve_node(node_name)
                    connected = False
                    if self.api_manager is not None:
                        connected = node_name in self.api_manager.pve_clients
                        
                    node_details[node_name] = {
                        "type": "PVE",
                        "host": node_config.get("host", "unknown"),
                        "connected": connected,
                        "api_available": connected
                    }
                
                # Add PBS node details
                for node_name in self.config.pbs_nodes:
                    node_config = self.config.get_pbs_node(node_name)
                    connected = False
                    if self.api_manager is not None:
                        connected = node_name in self.api_manager.pbs_clients
                        
                    node_details[node_name] = {
                        "type": "PBS",
                        "host": node_config.get("host", "unknown"),
                        "connected": connected,
                        "api_available": connected
                    }
                
                return json.dumps(node_details, indent=2)
            elif uri == "proxmox://capabilities":
                return json.dumps({
                    "mcp_server_capabilities": {
                        "cluster_management": {
                            "get_cluster_status": "Get comprehensive cluster status and health",
                            "get_nodes": "List all nodes with detailed information",
                            "get_node_status": "Get detailed status of specific node"
                        },
                        "virtual_machine_management": {
                            "get_vms": "List and query VM information",
                            "execute_vm_command": "Start, stop, restart, suspend, resume VMs"
                        },
                        "container_management": {
                            "get_lxcs": "List and query LXC container information",
                            "execute_lxc_command": "Start, stop, restart, suspend, resume containers"
                        },
                        "storage_management": {
                            "get_storage": "Monitor storage usage and health"
                        },
                        "monitoring_and_tasks": {
                            "get_node_tasks": "View recent tasks and operations",
                            "check_node_health": "Comprehensive health checks",
                            "get_backup_info": "Backup job status and information",
                            "get_network_info": "Network configuration and status"
                        },
                        "notifications": {
                            "send_notification": "Send alerts via Discord/Gotify"
                        }
                    }
                }, indent=2)
            elif uri == "proxmox://status":
                # Get current status with lazy initialization
                total_clients = 0
                pve_clients = 0
                pbs_clients = 0
                connected_nodes = []
                overall_status = "not_initialized"
                
                if self.api_manager is not None:
                    all_clients = self.api_manager.get_all_clients()
                    total_clients = len(all_clients)
                    pve_clients = len(self.api_manager.pve_clients)
                    pbs_clients = len(self.api_manager.pbs_clients)
                    connected_nodes = list(all_clients.keys())
                    overall_status = "healthy" if total_clients > 0 else "no_connections"
                
                return json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "server_status": "running",
                    "api_connections": {
                        "total_clients": total_clients,
                        "pve_clients": pve_clients,
                        "pbs_clients": pbs_clients,
                        "connected_nodes": connected_nodes
                    },
                    "health_summary": {
                        "overall_status": overall_status,
                        "configuration_status": "loaded",
                        "notification_channels": len(self.notifiers)
                    }
                }, indent=2, default=str)
            else:
                raise ValueError(f"Unknown resource: {uri}")

        @self.server.list_prompts()
        async def list_prompts() -> List[Prompt]:
            """List available enhanced prompts"""
            return [
                Prompt(
                    name="proxmox_health_check",
                    description="Perform comprehensive health check of Proxmox infrastructure with detailed analysis"
                ),
                Prompt(
                    name="proxmox_status_report", 
                    description="Generate detailed status report for all nodes, VMs, and LXCs with recommendations"
                ),
                Prompt(
                    name="proxmox_vm_management",
                    description="Assist with VM lifecycle management operations"
                ),
                Prompt(
                    name="proxmox_storage_analysis",
                    description="Analyze storage usage and provide optimization recommendations"
                ),
                Prompt(
                    name="proxmox_incident_response",
                    description="Guide through incident response procedures for Proxmox issues"
                )
            ]

        @self.server.get_prompt()
        async def get_prompt(name: str, arguments: Optional[Dict[str, str]] = None) -> List[PromptMessage]:
            """Get enhanced prompt content"""
            if name == "proxmox_health_check":
                return [
                    PromptMessage(
                        role="system",
                        content=TextContent(
                            type="text",
                            text="""You are an expert Proxmox infrastructure health monitoring assistant with comprehensive capabilities.

AVAILABLE TOOLS:
- get_cluster_status: Get overall cluster health and status
- get_nodes: List all nodes with detailed information  
- get_node_status: Get specific node details including CPU, memory, storage
- get_vms: List VMs with status and performance metrics
- get_lxcs: List LXC containers with status information
- get_storage: Monitor storage usage across all nodes
- get_node_tasks: Review recent operations and tasks
- get_backup_info: Check backup job status
- get_network_info: Review network configuration
- check_node_health: Perform connectivity and API health checks

HEALTH CHECK PROCEDURE:
1. Start with check_node_health for connectivity assessment
2. Get cluster_status for overall infrastructure view
3. Review get_nodes for resource utilization
4. Check get_vms and get_lxcs for virtual machine health
5. Analyze get_storage for capacity and performance issues
6. Review get_node_tasks for recent errors or warnings
7. Check get_backup_info for backup job status

Identify critical issues, performance bottlenecks, capacity concerns, and provide actionable recommendations."""
                        )
                    )
                ]
            elif name == "proxmox_status_report":
                return [
                    PromptMessage(
                        role="system", 
                        content=TextContent(
                            type="text",
                            text="""Generate a comprehensive Proxmox infrastructure status report using the enhanced MCP tools.

REPORT STRUCTURE:
1. EXECUTIVE SUMMARY
   - Overall health status
   - Critical issues requiring immediate attention
   - Summary metrics (nodes, VMs, LXCs, storage)

2. INFRASTRUCTURE OVERVIEW
   - Use get_cluster_status for cluster health
   - Use get_nodes for node status and resource utilization
   - Connectivity and API status from check_node_health

3. VIRTUAL MACHINES AND CONTAINERS
   - VM status and performance from get_vms
   - LXC container status from get_lxcs
   - Resource allocation and utilization analysis

4. STORAGE AND BACKUP STATUS
   - Storage utilization from get_storage
   - Backup job status from get_backup_info
   - Capacity planning recommendations

5. NETWORK AND OPERATIONS
   - Network configuration from get_network_info
   - Recent tasks and operations from get_node_tasks
   - Performance trends and anomalies

6. RECOMMENDATIONS AND ALERTS
   - Capacity planning suggestions
   - Performance optimization opportunities
   - Security and maintenance recommendations

Use the MCP tools systematically to gather all required data."""
                        )
                    )
                ]
            elif name == "proxmox_vm_management":
                return [
                    PromptMessage(
                        role="system",
                        content=TextContent(
                            type="text",
                            text="""You are a Proxmox VM management specialist with access to comprehensive VM operations.

AVAILABLE VM OPERATIONS:
- get_vms: List VMs and check their current status
- execute_vm_command: Perform VM lifecycle operations
  * start: Start a VM
  * stop/shutdown: Stop a VM (use force=true for immediate stop)
  * restart/reboot: Restart a VM
  * suspend: Suspend VM to memory
  * resume: Resume suspended VM
  * reset: Hard reset VM
  * status: Get current VM status
  * config: Get VM configuration

VM MANAGEMENT BEST PRACTICES:
1. Always check VM status before operations using get_vms
2. Use shutdown instead of stop when possible for graceful shutdown
3. Monitor get_node_tasks to track operation progress
4. Check node resources with get_node_status before starting VMs
5. Use get_storage to verify sufficient space for operations

SAFETY GUIDELINES:
- Confirm VM ID and node before executing commands
- Use graceful operations (shutdown) before forced operations (stop)
- Check for running services before stopping VMs
- Monitor task completion and handle errors appropriately
- Send notifications for critical VM operations

Help users manage their VMs safely and efficiently."""
                        )
                    )
                ]
            elif name == "proxmox_storage_analysis":
                return [
                    PromptMessage(
                        role="system",
                        content=TextContent(
                            type="text",
                            text="""You are a Proxmox storage analysis expert specializing in storage optimization and capacity planning.

STORAGE ANALYSIS TOOLS:
- get_storage: Get detailed storage information including usage and health
- get_nodes: Check node-level storage metrics and performance  
- get_vms: Analyze VM disk usage and allocation
- get_lxcs: Review LXC container storage consumption
- get_backup_info: Monitor backup storage requirements

ANALYSIS FRAMEWORK:
1. CAPACITY ANALYSIS
   - Current storage utilization across all nodes
   - Growth trends and capacity planning
   - Storage pool efficiency and fragmentation

2. PERFORMANCE ANALYSIS  
   - I/O performance metrics
   - Storage bottleneck identification
   - Workload distribution optimization

3. HEALTH AND RELIABILITY
   - Storage pool health status
   - Backup storage verification
   - Data protection assessment

4. OPTIMIZATION RECOMMENDATIONS
   - Storage rebalancing opportunities
   - Performance tuning suggestions
   - Cost optimization strategies
   - Capacity expansion planning

Provide detailed analysis with specific recommendations for storage optimization, performance improvements, and capacity planning based on current usage patterns."""
                        )
                    )
                ]
            elif name == "proxmox_incident_response":
                return [
                    PromptMessage(
                        role="system",
                        content=TextContent(
                            type="text",
                            text="""You are a Proxmox incident response specialist with expertise in diagnosing and resolving infrastructure issues.

INCIDENT RESPONSE TOOLKIT:
- check_node_health: Immediate connectivity and health assessment
- get_cluster_status: Cluster-wide issue identification
- get_node_status: Detailed node diagnostics
- get_node_tasks: Recent operations and error analysis
- get_vms/get_lxcs: Virtual machine and container status
- get_storage: Storage-related issue diagnosis
- get_network_info: Network connectivity problems
- send_notification: Alert relevant teams

INCIDENT RESPONSE PROCEDURE:
1. IMMEDIATE ASSESSMENT (0-5 minutes)
   - Run check_node_health for quick status
   - Check get_cluster_status for cluster-wide issues
   - Identify scope and severity of the incident

2. DETAILED DIAGNOSIS (5-15 minutes)
   - Analyze get_node_status for affected nodes
   - Review get_node_tasks for recent failures
   - Check get_storage for storage-related problems
   - Examine get_vms/get_lxcs for service impact

3. IMPACT ANALYSIS (15-30 minutes)
   - Determine affected services and users
   - Assess data integrity and availability
   - Evaluate business impact and urgency

4. RESOLUTION ACTIONS
   - Use execute_vm_command/execute_lxc_command for service recovery
   - Coordinate with team via send_notification
   - Document findings and actions taken

5. POST-INCIDENT REVIEW
   - Generate comprehensive status report
   - Identify root cause and prevention measures
   - Update procedures and monitoring

Guide users through systematic incident response with clear priorities and actionable steps."""
                        )
                    )
                ]
            else:
                raise ValueError(f"Unknown prompt: {name}")

    async def _get_cluster_status(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get comprehensive cluster status using enhanced API"""
        api_manager = self._ensure_api_manager()
        include_details = args.get("include_details", False)
        
        results = []
        
        # Get cluster status from all PVE clients
        for node_name, client in api_manager.pve_clients.items():
            try:
                cluster_data = await client.get_cluster_status()
                cluster_data["node_name"] = node_name
                results.append(cluster_data)
            except Exception as e:
                logger.error(f"Failed to get cluster status from {node_name}: {e}")
                results.append({
                    "error": str(e),
                    "node_name": node_name,
                    "host": client.host
                })
        
        # Also test basic connectivity
        connectivity_success, connectivity_results = await test_nodes(self.config)
        
        status = {
            "timestamp": asyncio.get_event_loop().time(),
            "connectivity_test": {
                "overall_success": connectivity_success,
                "results": connectivity_results
            },
            "cluster_data": results if results else None,
            "summary": {
                "total_nodes_configured": len(self.config.pve_nodes) + len(self.config.pbs_nodes),
                "pve_nodes_connected": len(api_manager.pve_clients),
                "pbs_nodes_connected": len(api_manager.pbs_clients),
                "overall_health": "healthy" if connectivity_success and results else "degraded"
            }
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(status, indent=2, default=str)
        )]

    async def _get_nodes(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get detailed information about all nodes"""
        api_manager = self._ensure_api_manager()
        include_details = args.get("include_details", True)
        
        async def get_nodes_from_client(client):
            return await client.get_nodes()
        
        results = await api_manager.aggregate_results(get_nodes_from_client)
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "timestamp": asyncio.get_event_loop().time(),
                "nodes": results,
                "summary": {
                    "total_nodes": len(results),
                    "successful_queries": len([r for r in results if "error" not in r])
                }
            }, indent=2, default=str)
        )]

    async def _get_node_status(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get detailed status of specific node"""
        api_manager = self._ensure_api_manager()
        node_name = args["node"]
        
        client = api_manager.get_client(node_name)
        if not client:
            return [TextContent(
                type="text",
                text=f"Node '{node_name}' not found in connected clients. Available nodes: {list(api_manager.get_all_clients().keys())}"
            )]
        
        try:
            node_status = await client.get_node_status()
            return [TextContent(
                type="text",
                text=json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "node_name": node_name,
                    "status": node_status
                }, indent=2, default=str)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "node_name": node_name,
                    "timestamp": asyncio.get_event_loop().time()
                }, indent=2)
            )]

    async def _get_vms(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get comprehensive VM information"""
        api_manager = self._ensure_api_manager()
        node = args.get("node")
        vmid = args.get("vmid")
        
        if node:
            # Get VMs from specific node
            client = api_manager.get_client(node)
            if not client:
                return [TextContent(
                    type="text",
                    text=f"Node '{node}' not found in connected clients"
                )]
            
            try:
                vms = await client.get_vms(node=node, vmid=vmid)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "timestamp": asyncio.get_event_loop().time(),
                        "node": node,
                        "vmid": vmid,
                        "vms": vms
                    }, indent=2, default=str)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e), "node": node}, indent=2)
                )]
        else:
            # Get VMs from all nodes
            async def get_vms_from_client(client):
                return await client.get_vms(vmid=vmid)
            
            results = await api_manager.aggregate_results(get_vms_from_client)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "vms": results,
                    "summary": {
                        "total_vms": len([vm for vm in results if "vmid" in vm])
                    }
                }, indent=2, default=str)
            )]

    async def _get_lxcs(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get comprehensive LXC information"""
        api_manager = self._ensure_api_manager()
        node = args.get("node")
        vmid = args.get("vmid")
        
        if node:
            # Get LXCs from specific node
            client = api_manager.get_client(node)
            if not client:
                return [TextContent(
                    type="text",
                    text=f"Node '{node}' not found in connected clients"
                )]
            
            try:
                lxcs = await client.get_lxcs(node=node, vmid=vmid)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "timestamp": asyncio.get_event_loop().time(),
                        "node": node,
                        "vmid": vmid,
                        "lxcs": lxcs
                    }, indent=2, default=str)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e), "node": node}, indent=2)
                )]
        else:
            # Get LXCs from all nodes
            async def get_lxcs_from_client(client):
                return await client.get_lxcs(vmid=vmid)
            
            results = await api_manager.aggregate_results(get_lxcs_from_client)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "lxcs": results,
                    "summary": {
                        "total_lxcs": len([lxc for lxc in results if "vmid" in lxc])
                    }
                }, indent=2, default=str)
            )]

    async def _get_storage(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get comprehensive storage information"""
        api_manager = self._ensure_api_manager()
        node = args.get("node")
        storage = args.get("storage")
        
        if node:
            # Get storage from specific node
            client = api_manager.get_client(node)
            if not client:
                return [TextContent(
                    type="text",
                    text=f"Node '{node}' not found in connected clients"
                )]
            
            try:
                storage_info = await client.get_storage(node=node, storage=storage)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "timestamp": asyncio.get_event_loop().time(),
                        "node": node,
                        "storage": storage,
                        "storage_info": storage_info
                    }, indent=2, default=str)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e), "node": node}, indent=2)
                )]
        else:
            # Get storage from all nodes
            async def get_storage_from_client(client):
                return await client.get_storage(storage=storage)
            
            results = await api_manager.aggregate_results(get_storage_from_client)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "storage_info": results,
                    "summary": {
                        "total_storage_entries": len([s for s in results if "storage" in s])
                    }
                }, indent=2, default=str)
            )]

    async def _execute_vm_command(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute VM commands"""
        api_manager = self._ensure_api_manager()
        node = args["node"]
        vmid = args["vmid"]
        command = args["command"]
        force = args.get("force", False)
        
        client = api_manager.get_client(node)
        if not client:
            return [TextContent(
                type="text",
                text=f"Node '{node}' not found in connected clients"
            )]
        
        try:
            kwargs = {"force": force} if command in ["stop", "shutdown"] and force else {}
            result = await client.execute_vm_command(node, vmid, command, **kwargs)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "operation": "vm_command",
                    **result
                }, indent=2, default=str)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "node": node,
                    "vmid": vmid,
                    "command": command,
                    "timestamp": asyncio.get_event_loop().time()
                }, indent=2)
            )]

    async def _execute_lxc_command(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Execute LXC commands"""
        api_manager = self._ensure_api_manager()
        node = args["node"]
        vmid = args["vmid"]
        command = args["command"]
        force = args.get("force", False)
        
        client = api_manager.get_client(node)
        if not client:
            return [TextContent(
                type="text",
                text=f"Node '{node}' not found in connected clients"
            )]
        
        try:
            kwargs = {"force": force} if command in ["stop", "shutdown"] and force else {}
            result = await client.execute_lxc_command(node, vmid, command, **kwargs)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "operation": "lxc_command",
                    **result
                }, indent=2, default=str)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "node": node,
                    "vmid": vmid,
                    "command": command,
                    "timestamp": asyncio.get_event_loop().time()
                }, indent=2)
            )]

    async def _get_node_tasks(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get recent tasks for a node"""
        api_manager = self._ensure_api_manager()
        node = args["node"]
        limit = args.get("limit", 50)
        
        client = api_manager.get_client(node)
        if not client:
            return [TextContent(
                type="text",
                text=f"Node '{node}' not found in connected clients"
            )]
        
        try:
            tasks = await client.get_node_tasks(node, limit)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "node": node,
                    "limit": limit,
                    "tasks": tasks
                }, indent=2, default=str)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": str(e),
                    "node": node,
                    "timestamp": asyncio.get_event_loop().time()
                }, indent=2)
            )]

    async def _get_backup_info(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get backup information"""
        api_manager = self._ensure_api_manager()
        node = args.get("node")
        
        if node:
            client = api_manager.get_client(node)
            if not client:
                return [TextContent(
                    type="text",
                    text=f"Node '{node}' not found in connected clients"
                )]
            
            try:
                backup_info = await client.get_backup_info(node)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "timestamp": asyncio.get_event_loop().time(),
                        "node": node,
                        "backup_info": backup_info
                    }, indent=2, default=str)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e), "node": node}, indent=2)
                )]
        else:
            # Get backup info from all nodes
            async def get_backup_from_client(client):
                return await client.get_backup_info()
            
            results = await api_manager.aggregate_results(get_backup_from_client)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "backup_info": results
                }, indent=2, default=str)
            )]

    async def _get_network_info(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Get network information"""
        api_manager = self._ensure_api_manager()
        node = args.get("node")
        
        if node:
            client = api_manager.get_client(node)
            if not client:
                return [TextContent(
                    type="text",
                    text=f"Node '{node}' not found in connected clients"
                )]
            
            try:
                network_info = await client.get_network_info(node)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "timestamp": asyncio.get_event_loop().time(),
                        "node": node,
                        "network_info": network_info
                    }, indent=2, default=str)
                )]
            except Exception as e:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": str(e), "node": node}, indent=2)
                )]
        else:
            # Get network info from all nodes
            async def get_network_from_client(client):
                return await client.get_network_info()
            
            results = await api_manager.aggregate_results(get_network_from_client)
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "timestamp": asyncio.get_event_loop().time(),
                    "network_info": results
                }, indent=2, default=str)
            )]

    async def _check_node_health(self, args: Dict[str, Any]) -> Sequence[TextContent]:
        """Perform comprehensive node health check"""
        api_manager = self._ensure_api_manager()
        target_node = args.get("node")
        target_nodes = [target_node] if target_node else None
        
        # Test basic connectivity
        success, connectivity_results = await test_nodes(self.config, target_nodes=target_nodes)
        
        # Get detailed status from connected clients
        detailed_results = []
        if target_node:
            client = api_manager.get_client(target_node)
            if client:
                try:
                    node_status = await client.get_node_status(target_node)
                    detailed_results.append({
                        "node": target_node,
                        "detailed_status": node_status,
                        "api_connected": True
                    })
                except Exception as e:
                    detailed_results.append({
                        "node": target_node,
                        "error": str(e),
                        "api_connected": False
                    })
        else:
            # Check all nodes
            for node_name, client in api_manager.get_all_clients().items():
                try:
                    node_status = await client.get_node_status()
                    detailed_results.append({
                        "node": node_name,
                        "detailed_status": node_status,
                        "api_connected": True
                    })
                except Exception as e:
                    detailed_results.append({
                        "node": node_name,
                        "error": str(e),
                        "api_connected": False
                    })
        
        health_summary = {
            "health_check_timestamp": asyncio.get_event_loop().time(),
            "overall_health": "healthy" if success else "degraded",
            "connectivity_test": {
                "nodes_checked": len(connectivity_results),
                "nodes_healthy": len([r for r in connectivity_results if r["success"]]),
                "detailed_connectivity": connectivity_results
            },
            "api_status": {
                "nodes_with_api": len(detailed_results),
                "nodes_api_healthy": len([r for r in detailed_results if r.get("api_connected", False)]),
                "detailed_api_status": detailed_results
            }
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(health_summary, indent=2, default=str)
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
    
    async def _get_available_tools(self) -> list:
        """Get list of available tools for HTTP interface"""
        return [
            {
                "name": "get_cluster_status",
                "description": "Get comprehensive status of Proxmox cluster including nodes, resources, and health",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_details": {
                            "type": "boolean",
                            "description": "Include detailed performance metrics and resource usage",
                            "default": False
                        }
                    }
                }
            },
            {
                "name": "get_nodes",
                "description": "Get detailed information about all Proxmox nodes including status and resources",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "include_details": {
                            "type": "boolean",
                            "description": "Include detailed node metrics and performance data",
                            "default": True
                        }
                    }
                }
            },
            {
                "name": "get_node_status",
                "description": "Get detailed status of a specific Proxmox node including CPU, memory, storage usage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Node name to query"
                        }
                    },
                    "required": ["node"]
                }
            },
            {
                "name": "get_vms",
                "description": "Get comprehensive VM information including status, configuration, and performance",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Node name to filter VMs (optional - gets all VMs if not specified)"
                        },
                        "vmid": {
                            "type": "string",
                            "description": "Specific VM ID to query (optional)"
                        }
                    }
                }
            },
            {
                "name": "execute_vm_command",
                "description": "Execute commands on VMs (start, stop, restart, suspend, resume, reset, status)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Node name where the VM is located"
                        },
                        "vmid": {
                            "type": "string",
                            "description": "VM ID to operate on"
                        },
                        "command": {
                            "type": "string",
                            "description": "Command to execute",
                            "enum": ["start", "stop", "shutdown", "restart", "reboot", "suspend", "resume", "reset", "status", "config"]
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force the operation (for stop/shutdown)",
                            "default": False
                        }
                    },
                    "required": ["node", "vmid", "command"]
                }
            },
            {
                "name": "get_lxcs",
                "description": "Get comprehensive LXC container information including status and configuration",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Node name to filter containers (optional - gets all if not specified)"
                        },
                        "vmid": {
                            "type": "string",
                            "description": "Specific container ID to query (optional)"
                        }
                    }
                }
            },
            {
                "name": "execute_lxc_command",
                "description": "Execute commands on LXC containers (start, stop, restart, suspend, resume, status)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Node name where the container is located"
                        },
                        "vmid": {
                            "type": "string",
                            "description": "Container ID to operate on"
                        },
                        "command": {
                            "type": "string",
                            "description": "Command to execute",
                            "enum": ["start", "stop", "shutdown", "restart", "reboot", "suspend", "resume", "status", "config"]
                        },
                        "force": {
                            "type": "boolean",
                            "description": "Force the operation (for stop/shutdown)",
                            "default": False
                        }
                    },
                    "required": ["node", "vmid", "command"]
                }
            },
            {
                "name": "get_storage",
                "description": "Get detailed storage information including usage, content, and health status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Node name to filter storage (optional - gets all storage if not specified)"
                        },
                        "storage": {
                            "type": "string",
                            "description": "Specific storage name to query (optional)"
                        }
                    }
                }
            },
            {
                "name": "get_node_tasks",
                "description": "Get recent tasks and operations for nodes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Node name to get tasks for"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of tasks to return",
                            "default": 50
                        }
                    },
                    "required": ["node"]
                }
            },
            {
                "name": "get_backup_info",
                "description": "Get backup job information and status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Node name to filter backups (optional)"
                        }
                    }
                }
            },
            {
                "name": "get_network_info",
                "description": "Get network configuration and interface information",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Node name to get network info for (optional - gets all if not specified)"
                        }
                    }
                }
            },
            {
                "name": "check_node_health",
                "description": "Perform comprehensive health check on Proxmox nodes including connectivity and resource status",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "node": {
                            "type": "string",
                            "description": "Specific node to check (optional - checks all if not specified)"
                        }
                    }
                }
            },
            {
                "name": "send_notification",
                "description": "Send notification through configured channels (Discord, Gotify)",
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
                        "severity": {
                            "type": "string",
                            "description": "Severity level",
                            "enum": ["info", "warning", "critical"],
                            "default": "info"
                        }
                    },
                    "required": ["title", "message"]
                }
            }
        ]
    
    async def _execute_tool(self, name: str, arguments: dict) -> str:
        """Execute tool for HTTP interface"""
        try:
            # Core cluster and node operations
            if name == "get_cluster_status":
                result = await self._get_cluster_status(arguments)
            elif name == "get_nodes":
                result = await self._get_nodes(arguments)
            elif name == "get_node_status":
                result = await self._get_node_status(arguments)
            
            # VM operations
            elif name == "get_vms":
                result = await self._get_vms(arguments)
            elif name == "execute_vm_command":
                result = await self._execute_vm_command(arguments)
            
            # LXC operations
            elif name == "get_lxcs":
                result = await self._get_lxcs(arguments)
            elif name == "execute_lxc_command":
                result = await self._execute_lxc_command(arguments)
            
            # Storage operations
            elif name == "get_storage":
                result = await self._get_storage(arguments)
            
            # Advanced operations
            elif name == "get_node_tasks":
                result = await self._get_node_tasks(arguments)
            elif name == "get_backup_info":
                result = await self._get_backup_info(arguments)
            elif name == "get_network_info":
                result = await self._get_network_info(arguments)
            
            # Health and monitoring
            elif name == "check_node_health":
                result = await self._check_node_health(arguments)
            
            # Notification
            elif name == "send_notification":
                result = await self._send_notification(arguments)
            
            else:
                return f"Unknown tool: {name}"
            
            # Extract text content from the result
            if isinstance(result, list) and len(result) > 0 and hasattr(result[0], 'text'):
                return result[0].text
            else:
                return str(result)
                
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return f"Error: {str(e)}"


class MCPHTTPServer:
    """HTTP/WebSocket server for MCP protocol"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
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
        
        try:
            site = web.TCPSite(runner, self.host, self.port)
            await site.start()
            logger.info(f"Server successfully bound to {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to bind server to {self.host}:{self.port}: {e}")
            print(f"❌ Failed to start server on {self.host}:{self.port}", file=sys.stderr)
            print(f"   Error: {e}", file=sys.stderr)
            print("💡 Try running with different host/port:", file=sys.stderr)
            print("   python mcp_server_http.py --host 0.0.0.0 --port 8888", file=sys.stderr)
            await runner.cleanup()
            return
        
<<<<<<< HEAD
        print(f"🌐 Proxmox MCP HTTP Server started", file=sys.stderr)
        print(f"� Server bound to: {self.host}:{self.port}", file=sys.stderr)
        print(f"�📡 WebSocket endpoint: ws://{self.host}:{self.port}/ws", file=sys.stderr)
        print(f"🔗 HTTP endpoint: http://{self.host}:{self.port}/mcp", file=sys.stderr)
        print(f"🏥 Health check: http://{self.host}:{self.port}/health", file=sys.stderr)
        print("", file=sys.stderr)
        print("🔧 N8N MCP CLIENT CONFIGURATION:", file=sys.stderr)
        print(f"   Endpoint URL: http://{self.host}:{self.port}/mcp", file=sys.stderr)
=======
        print(f"🌐 Enhanced Proxmox MCP HTTP Server started", file=sys.stderr)
        print(f"📡 WebSocket endpoint: ws://{self.host}:{self.port}/ws", file=sys.stderr)
        print(f"🔗 HTTP endpoint: http://{self.host}:{self.port}/mcp", file=sys.stderr)
        print(f"🏥 Health check: http://{self.host}:{self.port}/health", file=sys.stderr)
        print("", file=sys.stderr)
        print("� ENHANCED FEATURES AVAILABLE:", file=sys.stderr)
        print("   ✅ Comprehensive cluster management", file=sys.stderr)
        print("   ✅ VM/LXC lifecycle operations", file=sys.stderr)
        print("   ✅ Storage monitoring and analysis", file=sys.stderr)
        print("   ✅ Task tracking and health checks", file=sys.stderr)
        print("   ✅ Backup status monitoring", file=sys.stderr)
        print("   ✅ Network configuration queries", file=sys.stderr)
        print("   ✅ Smart notifications (Discord/Gotify)", file=sys.stderr)
        print("", file=sys.stderr)
        print("�🔧 N8N MCP CLIENT CONFIGURATION OPTIONS:", file=sys.stderr)
        print("   Option 1 - WebSocket:", file=sys.stderr)
        print("   Connection Type: websocket", file=sys.stderr)
        print(f"   Endpoint: ws://{self.host}:{self.port}/ws", file=sys.stderr)
>>>>>>> 3cb3d4fb59abe8bda4e00d5abaa718d3aeb5ea71
        print("", file=sys.stderr)
        print("🧪 Test the server with:", file=sys.stderr)
        print(f"   python test_mcp_server.py", file=sys.stderr)
        print("", file=sys.stderr)
        print("✅ Enhanced server ready for connections", file=sys.stderr)
        
        # Keep server running
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            await runner.cleanup()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Enhanced Proxmox MCP HTTP Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8888, help="Port to bind to")
    
    args = parser.parse_args()
    
    server = MCPHTTPServer(host=args.host, port=args.port)
    await server.start_server()


if __name__ == "__main__":
    asyncio.run(main())