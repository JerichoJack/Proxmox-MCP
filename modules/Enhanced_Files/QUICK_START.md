# Quick Start Guide - Enhanced Proxmox MCP Server

## 🚀 Quick Setup (5 minutes)

### 1. Prerequisites
- Python 3.8+ with pip
- Access to Proxmox VE/PBS nodes
- API tokens configured in Proxmox

### 2. Installation

```bash
# Clone or navigate to the project directory
cd Proxmox-MCP

# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp env_example_enhanced.env .env

# Edit configuration
nano .env  # or your preferred editor
```

### 3. Minimum Configuration

Edit `.env` with your Proxmox details:

```bash
# Basic settings
VERIFY_SSL=false
LAB_CONFIGURATION=STANDALONE
LOG_LEVEL=INFO

# Your Proxmox node
PVE_NODES=pve1
PVE1_HOST=192.168.1.10
PVE1_USER=root
PVE1_TOKEN_NAME=mcp-server
PVE1_TOKEN_VALUE=your-actual-token-here

# Disable notifications for testing
DISCORD_OUT_ENABLED=false
GOTIFY_OUT_ENABLED=false
```

### 4. Test Configuration

```bash
# Test connectivity and functionality
python test_enhanced_server.py
```

Expected output:
```
🚀 Enhanced Proxmox MCP Server Test Suite
========================================================

🔗 Testing Basic Connectivity
==================================================
Overall Success: True
Nodes Tested: 1
  ✅ pve1 (PVE) - 192.168.1.10

🔧 Testing API Manager
==================================================
PVE Clients Connected: 1
PBS Clients Connected: 0
Total Clients: 1
...
🎉 All tests passed! Enhanced MCP Server is ready.
```

### 5. Run the MCP Server

```bash
# Start the MCP server
python mcp_server.py
```

Expected output:
```
🚀 Proxmox MCP Server starting...

📋 CONNECTION INFORMATION FOR N8N:
   Server Type: stdio
   Command: python
   Arguments: mcp_server.py

✅ Server ready for connections
```

## 🔧 Integration with n8n

### MCP Client Node Configuration

In your n8n workflow, add an MCP Client node with:

- **Connection Type**: `stdio`
- **Command**: `python`
- **Arguments**: `["/full/path/to/mcp_server.py"]`
- **Working Directory**: `/full/path/to/Proxmox-MCP`

### Available Operations

Once connected, you'll have access to all enhanced tools:

#### Core Operations
- `get_cluster_status` - Overall cluster health
- `get_nodes` - Node information
- `get_node_status` - Specific node details

#### VM Management
- `get_vms` - List virtual machines
- `execute_vm_command` - Start/stop/restart VMs

#### Container Management
- `get_lxcs` - List LXC containers
- `execute_lxc_command` - Manage containers

#### Storage & Monitoring
- `get_storage` - Storage information
- `get_node_tasks` - Recent operations
- `check_node_health` - Health checks

## 📝 Common Operations

### Get All VMs
```json
{
  "tool": "get_vms",
  "arguments": {}
}
```

### Start a VM
```json
{
  "tool": "execute_vm_command",
  "arguments": {
    "node": "pve1",
    "vmid": "100",
    "command": "start"
  }
}
```

### Check Node Health
```json
{
  "tool": "check_node_health",
  "arguments": {}
}
```

### Get Storage Info
```json
{
  "tool": "get_storage",
  "arguments": {
    "node": "pve1"
  }
}
```

## 🛠️ Troubleshooting

### Connection Issues

1. **"No clients connected"**
   - Verify host IP addresses are correct
   - Check API tokens are valid
   - Ensure network connectivity to Proxmox nodes

2. **SSL/Certificate errors**
   - Set `VERIFY_SSL=false` for testing
   - Check certificate configuration in production

3. **Permission errors**
   - Verify API token has sufficient permissions
   - Check user roles in Proxmox

### Testing Steps

```bash
# 1. Test basic configuration
python -c "from core.config import MCPConfig; print(MCPConfig('.env').summary())"

# 2. Test connectivity
python test_enhanced_server.py

# 3. Test MCP server startup
python mcp_server.py --help
```

## 📚 Next Steps

1. **Configure Notifications**
   - Set up Discord/Gotify webhooks for alerts
   - Test notification delivery

2. **Create Workflows**
   - Build n8n workflows for monitoring
   - Set up automated VM management
   - Create health check schedules

3. **Advanced Features**
   - Enable cluster auto-discovery
   - Configure event listeners
   - Set up backup monitoring

## 🔐 Security Checklist

- [ ] Use dedicated API tokens (not root password)
- [ ] Set minimal required permissions
- [ ] Enable SSL verification in production
- [ ] Secure `.env` file (`chmod 600 .env`)
- [ ] Monitor API access logs
- [ ] Use firewall restrictions for API access

## 📞 Getting Help

1. Check the Enhanced README for detailed documentation
2. Review log outputs for error details
3. Test with `python test_enhanced_server.py`
4. Verify Proxmox API token permissions
5. Check network connectivity and DNS resolution

## ⚡ Performance Tips

- Use specific node names when possible to reduce API calls
- Enable cluster mode for multi-node environments
- Configure appropriate timeout values for large environments
- Use caching for frequently accessed data

---

**You're now ready to use the Enhanced Proxmox MCP Server!** 🎉

The server provides comprehensive Proxmox management through a clean MCP interface, making it easy to integrate with n8n workflows and other MCP-compatible tools.