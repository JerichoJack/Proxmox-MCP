# Proxmox MCP Server - Enhanced Edition

## Overview
The Enhanced Proxmox MCP (Model Context Protocol) Server provides comprehensive API access to Proxmox Virtual Environment (PVE) and Proxmox Backup Server (PBS) through a standardized MCP interface. This version includes full functionality for managing VMs, LXCs, storage, clustering, and monitoring.

## Features

### 🏗️ Core Infrastructure Management
- **Cluster Management**: Get comprehensive cluster status, resources, and health
- **Node Operations**: Detailed node information including CPU, memory, storage, and network
- **Connectivity Testing**: Real-time API connectivity and health monitoring

### 🖥️ Virtual Machine Management
- **VM Discovery**: List all VMs across nodes with detailed status and configuration
- **VM Lifecycle**: Start, stop, restart, suspend, resume, and reset VMs
- **VM Monitoring**: Real-time status, performance metrics, and configuration details

### 📦 Container Management (LXC)
- **Container Discovery**: List all LXC containers with status and configuration
- **Container Lifecycle**: Start, stop, restart, suspend, and resume containers
- **Container Monitoring**: Real-time status and resource usage

### 💾 Storage Management
- **Storage Monitoring**: Detailed storage usage, health, and performance across all nodes
- **Storage Analysis**: Content analysis, capacity planning, and utilization trends
- **Multi-node Storage**: Comprehensive view across clustered storage

### 📋 Operations and Monitoring
- **Task Monitoring**: Recent operations, jobs, and their status across nodes
- **Backup Management**: Backup job status and PBS integration
- **Network Information**: Network configuration and interface status

### 🚨 Health and Alerting
- **Health Checks**: Comprehensive infrastructure health assessment
- **Notifications**: Integration with Discord and Gotify for alerts
- **Real-time Status**: Live monitoring and status reporting

## Available MCP Tools

### Core Operations
1. **get_cluster_status** - Comprehensive cluster status and health
2. **get_nodes** - Detailed information about all Proxmox nodes
3. **get_node_status** - Specific node status including resources

### VM Management
4. **get_vms** - List and query virtual machines
5. **execute_vm_command** - VM lifecycle operations (start/stop/restart/etc.)

### Container Management
6. **get_lxcs** - List and query LXC containers
7. **execute_lxc_command** - Container lifecycle operations

### Storage and Operations
8. **get_storage** - Storage information and monitoring
9. **get_node_tasks** - Recent tasks and operations
10. **get_backup_info** - Backup job status and information
11. **get_network_info** - Network configuration and status

### Monitoring and Alerts
12. **check_node_health** - Comprehensive health checks
13. **send_notification** - Send alerts via configured channels

## MCP Resources

The server provides the following resources:

- **proxmox://config** - Server configuration and connection status
- **proxmox://nodes** - Node list with connection details
- **proxmox://capabilities** - Available server capabilities
- **proxmox://status** - Current server and connection status

## Enhanced Prompts

The server includes specialized prompts for different use cases:

1. **proxmox_health_check** - Comprehensive infrastructure health monitoring
2. **proxmox_status_report** - Detailed status reporting with recommendations
3. **proxmox_vm_management** - VM lifecycle management assistance
4. **proxmox_storage_analysis** - Storage optimization and capacity planning
5. **proxmox_incident_response** - Incident response and troubleshooting

## Configuration

### Environment Variables (.env file)

```bash
# General Settings
VERIFY_SSL=false
LOG_LEVEL=INFO
LAB_CONFIGURATION=STANDALONE  # or CLUSTERED, MIXED

# PVE Nodes (add as many as needed)
PVE_NODES=pve1,pve2,pve3
PVE1_HOST=192.168.1.10
PVE1_USER=root
PVE1_TOKEN_NAME=mcp-token
PVE1_TOKEN_VALUE=your-token-here

# PBS Nodes (optional)
PBS_NODES=pbs1
PBS1_HOST=192.168.1.20
PBS1_USER=root
PBS1_TOKEN_NAME=mcp-token
PBS1_TOKEN_VALUE=your-token-here

# Notifications (optional)
DISCORD_OUT_ENABLED=true
DISCORD_OUT_WEBHOOK_URL=https://discord.com/api/webhooks/...

GOTIFY_OUT_ENABLED=true
GOTIFY_OUT_SERVER_URL=https://gotify.example.com
GOTIFY_OUT_APP_TOKEN=your-gotify-token
```

## Usage Examples

### Basic VM Management
```python
# Get all VMs
await mcp_client.call_tool("get_vms", {})

# Get VMs on specific node
await mcp_client.call_tool("get_vms", {"node": "pve1"})

# Start a VM
await mcp_client.call_tool("execute_vm_command", {
    "node": "pve1",
    "vmid": "100",
    "command": "start"
})

# Graceful shutdown
await mcp_client.call_tool("execute_vm_command", {
    "node": "pve1", 
    "vmid": "100",
    "command": "shutdown"
})
```

### Container Management
```python
# Get all containers
await mcp_client.call_tool("get_lxcs", {})

# Restart container
await mcp_client.call_tool("execute_lxc_command", {
    "node": "pve1",
    "vmid": "101", 
    "command": "restart"
})
```

### Storage Monitoring
```python
# Get all storage information
await mcp_client.call_tool("get_storage", {})

# Get storage for specific node
await mcp_client.call_tool("get_storage", {"node": "pve1"})
```

### Health Monitoring
```python
# Check all nodes health
await mcp_client.call_tool("check_node_health", {})

# Check specific node
await mcp_client.call_tool("check_node_health", {"node": "pve1"})

# Get cluster status
await mcp_client.call_tool("get_cluster_status", {"include_details": true})
```

## API Architecture

### ProxmoxAPIClient
- Individual client for each Proxmox node
- Handles PVE and PBS connections
- Comprehensive API method coverage
- Error handling and logging

### ProxmoxAPIManager
- Manages multiple API clients
- Aggregates results across nodes
- Connection health monitoring
- Automatic client initialization

### Enhanced MCP Server
- Full MCP protocol implementation
- Comprehensive tool set
- Rich resource and prompt system
- Advanced error handling

## Security Considerations

1. **API Tokens**: Use dedicated API tokens with minimal required permissions
2. **SSL Verification**: Enable SSL verification in production environments
3. **Network Security**: Ensure Proxmox API endpoints are properly secured
4. **Access Control**: Implement proper access controls for the MCP server
5. **Logging**: Monitor and log all API operations for security auditing

## Error Handling

The enhanced server includes comprehensive error handling:

- Connection failures are gracefully handled and reported
- Invalid node/VM/container IDs return descriptive error messages
- API timeouts and network issues are properly caught and logged
- Partial failures in multi-node operations are clearly indicated

## Performance Considerations

- Connections are established once and reused
- API calls are made concurrently where possible
- Results are cached appropriately to reduce API load
- Timeouts are configured to prevent hanging operations

## Integration with n8n

### MCP Client Configuration
```json
{
  "serverType": "stdio",
  "command": "python",
  "args": ["/path/to/mcp_server.py"],
  "cwd": "/path/to/Proxmox-MCP"
}
```

### Available Operations
All MCP tools are available as n8n operations, allowing for:
- Automated VM lifecycle management
- Infrastructure monitoring workflows
- Alert and notification automation
- Capacity planning and reporting
- Incident response automation

## Troubleshooting

### Common Issues
1. **Connection Failures**: Check network connectivity and API token permissions
2. **SSL Errors**: Verify SSL settings match your Proxmox configuration
3. **Permission Errors**: Ensure API tokens have sufficient privileges
4. **Timeout Issues**: Check network latency and increase timeout values if needed

### Debug Mode
Enable debug logging by setting `LOG_LEVEL=DEBUG` in your .env file.

### Health Check
Use the `check_node_health` tool to verify all connections and identify issues.

## Contributing

The enhanced Proxmox MCP server is designed to be extensible. Additional functionality can be added by:

1. Extending the ProxmoxAPIClient class with new methods
2. Adding new MCP tools in the server setup
3. Implementing additional resource types
4. Creating specialized prompts for specific use cases

## License and Support

This enhanced version builds upon the original Proxmox MCP server and provides comprehensive functionality for production Proxmox environments. 

For issues and feature requests, please refer to the project documentation and logging output for detailed error information.