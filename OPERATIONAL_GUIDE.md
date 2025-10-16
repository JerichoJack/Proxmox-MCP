# Proxmox MCP Server - Operational Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Operational Modes](#operational-modes)
6. [Configuration System](#configuration-system)
7. [Event Processing](#event-processing)
8. [API Integration](#api-integration)
9. [Deployment Scenarios](#deployment-scenarios)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

The **Proxmox MCP (Model Context Protocol) Server** is a sophisticated automation orchestrator that bridges Proxmox infrastructure (Virtual Environment and Backup Server) with AI agents and automation platforms like n8n. It provides:

- **Real-time event ingestion** from multiple sources (WebSocket, Email, Syslog, Gotify, Discord)
- **Bi-directional API communication** with Proxmox VE and PBS clusters
- **Event processing and dispatching** to multiple output channels
- **MCP protocol implementation** for AI agent integration
- **Comprehensive infrastructure management** through standardized tools

### Key Capabilities

🔄 **Real-time Automation**: Responds to Proxmox events instantly for proactive remediation  
🤖 **AI Agent Integration**: Exposes Proxmox operations through MCP protocol for LLM-driven automation  
📡 **Multi-source Event Ingestion**: Consolidates events from various Proxmox notification channels  
🔔 **Multi-channel Notifications**: Dispatches events to Discord, Gotify, webhooks, and more  
🏗️ **Infrastructure Management**: Comprehensive VM, LXC, storage, and cluster operations  

---

## Architecture

The system follows a modular event-driven architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EVENT SOURCES (Input Layer)                   │
├─────────────────────────────────────────────────────────────────┤
│  WebSocket  │  Email  │  Syslog  │  Gotify  │  Discord          │
│  Listener   │ Listener │ Listener │ Listener │  Listener         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CORE PROCESSING LAYER                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────┐    ┌──────────────────┐                   │
│  │   MCPManager    │    │  EventDispatcher │                   │
│  │   (Orchestrator)│───▶│  (Event Router)  │                   │
│  └─────────────────┘    └──────────────────┘                   │
│           │                       │                              │
│           │                       ▼                              │
│           │         ┌──────────────────────────┐               │
│           │         │    Output Notifiers       │               │
│           │         │  (Discord, Gotify, etc.)  │               │
│           │         └──────────────────────────┘               │
│           │                                                      │
│           ▼                                                      │
│  ┌─────────────────────────────────────┐                       │
│  │    ProxmoxAPIManager                │                       │
│  │  (API Client Connection Pool)       │                       │
│  └─────────────────────────────────────┘                       │
│           │                                                      │
└───────────┼──────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MCP PROTOCOL LAYER                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────┐      ┌──────────────────────┐        │
│  │  ProxmoxMCPServer    │      │ ProxmoxMCPServer     │        │
│  │  (stdio mode)        │      │ (HTTP/WebSocket)     │        │
│  │  mcp_server.py       │      │ mcp_server_http.py   │        │
│  └──────────────────────┘      └──────────────────────┘        │
│           │                              │                       │
└───────────┼──────────────────────────────┼──────────────────────┘
            │                              │
            ▼                              ▼
┌───────────────────────┐      ┌────────────────────────┐
│   Local n8n MCP       │      │   Remote n8n MCP       │
│   Client (stdio)      │      │   Client (HTTP/WS)     │
└───────────────────────┘      └────────────────────────┘
            │                              │
            └──────────────┬───────────────┘
                           ▼
                  ┌─────────────────┐
                  │   AI Agent      │
                  │   (n8n + LLM)   │
                  └─────────────────┘
```

### Architectural Layers

1. **Input Layer**: Modular event listeners for different sources
2. **Core Processing Layer**: Event routing, API management, orchestration
3. **MCP Protocol Layer**: Standardized interface for AI agents
4. **External Integration**: n8n workflows and AI agent systems

---

## Core Components

### 1. MCPManager (`core/manager.py`)

**Purpose**: Central orchestrator managing the complete lifecycle of the MCP Server

**Responsibilities**:
- Initializes and coordinates all input listeners and output notifiers
- Manages graceful startup and shutdown
- Handles signal interrupts (SIGINT, SIGTERM)
- Routes events from listeners to the event dispatcher
- Provides connectivity testing and health checks

**Key Methods**:
```python
setup()                    # Initialize all components based on config
start_all_listeners()      # Start all configured event listeners
stop_all_listeners()       # Gracefully stop all listeners
on_event()                 # Callback for processing incoming events
test_connectivity()        # Test all connections and I/O modules
```

**Lifecycle**:
```
Initialize → Setup Components → Start Listeners → Process Events → Shutdown
```

### 2. MCPConfig (`core/config.py`)

**Purpose**: Configuration management and validation

**Features**:
- Loads configuration from `.env` files
- Validates required settings
- Provides helper methods for node access
- Supports three lab modes: STANDALONE, CLUSTERED, MIXED
- Auto-discovery for clustered nodes

**Configuration Sections**:
- General settings (SSL, logging, event listener toggles)
- Lab configuration (topology mode)
- Node definitions (PVE and PBS nodes)
- Event listener configuration (input modules)
- Notification provider configuration (output modules)

### 3. ProxmoxAPIManager (`core/proxmox_api.py`)

**Purpose**: Manages API connections to multiple Proxmox nodes

**Features**:
- Connection pooling for multiple PVE and PBS nodes
- Automatic connection initialization and validation
- Separate client management for PVE and PBS
- Token-based authentication
- Connection health monitoring

**Key Methods**:
```python
get_pve_client(node_name)      # Get specific PVE API client
get_pbs_client(node_name)      # Get specific PBS API client
get_all_pve_clients()          # Get all PVE clients
get_all_pbs_clients()          # Get all PBS clients
get_clients_info()             # Get detailed client information
```

**Authentication**:
Uses Proxmox API tokens with three-part authentication:
- User (e.g., `root@pam`)
- Token name (e.g., `n8n-mcp-token`)
- Token value (secure token string)

### 4. EventDispatcher (`core/event_dispatcher.py`)

**Purpose**: Routes normalized events to all enabled output channels

**Operation**:
1. Receives events from input listeners (via MCPManager)
2. Asynchronously dispatches to all configured notifiers
3. Handles errors gracefully without blocking other notifiers

**Example Flow**:
```
Email Alert Received → MCPManager.on_event() → EventDispatcher.dispatch()
→ [Discord, Gotify, Webhook] (parallel async)
```

### 5. Input Listeners (`modules/input/`)

**Base Class**: `BaseListener` - Abstract interface for all input modules

**Available Listeners**:

#### WebSocketListener
- Connects to Proxmox WebSocket API
- Receives real-time cluster events
- Auto-reconnects on connection loss

#### EmailListener
- Polls email inbox for Proxmox alerts
- Parses email notifications
- Configurable poll interval

#### SyslogListener
- UDP syslog receiver
- Parses syslog messages from Proxmox nodes
- Configurable port (default: 514)

#### GotifyListener
- Polls Gotify server for messages
- Receives forwarded Proxmox notifications
- Bi-directional Gotify integration

#### DiscordListener
- Listens for Discord webhook events
- Enables Discord-based command triggers

**Common Interface**:
```python
async def start()       # Begin listening for events
async def stop()        # Gracefully stop listener
event_callback()        # Callback function for received events
```

### 6. Output Notifiers (`modules/output/`)

**Base Class**: `BaseNotifier` - Abstract interface for all output modules

**Available Notifiers**:

#### DiscordNotifier
- Sends notifications to Discord via webhooks
- Rich embed formatting
- Supports custom fields and metadata

#### GotifyNotifier
- Sends notifications to Gotify server
- Priority levels
- Message persistence

**Common Interface**:
```python
async def send(title, message, **kwargs)    # Send notification
```

### 7. MCP Protocol Servers

#### Standard MCP Server (`mcp_server.py`)
**Mode**: stdio (standard input/output)  
**Use Case**: Local n8n instance on same machine  
**Communication**: Process pipes  
**Initialization**: Immediate API connection on startup  

#### HTTP MCP Server (`mcp_server_http.py`)
**Mode**: HTTP/WebSocket  
**Use Case**: Remote n8n instances, network-accessible deployment  
**Communication**: HTTP REST + WebSocket  
**Initialization**: Lazy API connection (on first tool use)  
**Features**: CORS support, multiple concurrent clients  

**MCP Tools Exposed** (both servers):
- `get_cluster_status` - Cluster health and resources
- `get_nodes` - Node information
- `get_node_status` - Specific node details
- `get_vms` - Virtual machine inventory
- `execute_vm_command` - VM lifecycle operations
- `get_lxcs` - LXC container inventory
- `execute_lxc_command` - Container lifecycle operations
- `get_storage` - Storage information
- `get_recent_tasks` - Task history and status
- `run_diagnostic` - Health checks and diagnostics
- `test_connectivity` - Connection testing

---

## Data Flow

### Event Ingestion Flow

```
┌─────────────────────┐
│  Event Source       │  (e.g., Proxmox sends email alert)
│  (External System)  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Input Listener     │  (e.g., EmailListener polls inbox)
│  (Event Capture)    │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  MCPManager         │  (on_event() callback)
│  (Event Router)     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  EventDispatcher    │  (dispatch() to all notifiers)
│  (Fan-out)          │
└──────────┬──────────┘
           │
           ├─────────────────────┬─────────────────────┐
           ▼                     ▼                     ▼
    ┌────────────┐       ┌────────────┐       ┌────────────┐
    │  Discord   │       │   Gotify   │       │  Webhook   │
    │  Notifier  │       │  Notifier  │       │  Notifier  │
    └────────────┘       └────────────┘       └────────────┘
```

### MCP Tool Invocation Flow

```
┌──────────────────┐
│   AI Agent       │  (n8n workflow with LLM)
│   (n8n + LLM)    │
└────────┬─────────┘
         │ "Get VM status for node pve1"
         ▼
┌──────────────────┐
│   MCP Client     │  (n8n MCP node)
│   (n8n)          │
└────────┬─────────┘
         │ MCP Protocol: call_tool("get_vms", {node: "pve1"})
         ▼
┌──────────────────┐
│  MCP Server      │  (ProxmoxMCPServer)
│  (stdio/HTTP)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ ProxmoxAPI       │  (API call to Proxmox)
│ Manager          │
└────────┬─────────┘
         │ HTTPS API Request
         ▼
┌──────────────────┐
│  Proxmox VE/PBS  │  (Infrastructure)
│  (API Endpoint)  │
└────────┬─────────┘
         │ JSON Response
         ▼
    [Response flows back through stack]
```

### Complete Event Processing Example

**Scenario**: VM crashes and Proxmox sends email alert

1. **Event Generation**: Proxmox detects VM crash, sends email notification
2. **Event Capture**: EmailListener polls inbox, finds alert
3. **Event Parsing**: EmailListener extracts title, message, metadata
4. **Event Callback**: Calls `MCPManager.on_event(title, message, node=...)`
5. **Event Dispatch**: MCPManager forwards to EventDispatcher
6. **Notification Fan-out**: EventDispatcher sends to all enabled notifiers in parallel
7. **Discord Notification**: DiscordNotifier posts alert to Discord channel
8. **Gotify Notification**: GotifyNotifier pushes to Gotify app
9. **AI Agent Trigger**: n8n workflow receives Discord webhook
10. **MCP Tool Call**: AI agent calls `get_vms(node="pve1")` via MCP
11. **API Query**: ProxmoxAPIManager queries Proxmox API
12. **Response**: VM status returned to AI agent
13. **Automated Remediation**: AI agent decides action and calls `execute_vm_command("restart")`
14. **Verification**: AI agent confirms VM is running again

---

## Operational Modes

### Mode 1: Event Monitoring Only

**Purpose**: Passive monitoring and notification forwarding

**Configuration**:
```env
ENABLE_EVENT_LISTENERS=true
ENABLE_AGENT=false
# Enable desired input listeners
EVENT_EMAIL_ENABLED=true
# Enable desired output notifiers
DISCORD_OUT_ENABLED=true
```

**Use Case**: Alert consolidation, centralized notification hub

**Entry Point**: `main.py --test-connection` (validation only)

### Mode 2: MCP Server Only (Local)

**Purpose**: Provide MCP tools to local n8n instance

**Configuration**:
```env
ENABLE_EVENT_LISTENERS=false
# Configure Proxmox nodes only
```

**Command**: `python3 main.py --mcp-server`  
**Server**: `mcp_server.py` (stdio)

**Use Case**: Direct n8n integration on same machine, API-driven automation

### Mode 3: MCP Server Only (Remote)

**Purpose**: Network-accessible MCP server for remote n8n

**Configuration**: Same as Mode 2

**Command**: `python3 mcp_server_http.py --host 0.0.0.0 --port 8080`  
**Server**: `mcp_server_http.py` (HTTP/WebSocket)

**Use Case**: Remote n8n instances, multiple clients, Docker deployments

### Mode 4: Full Stack (Hybrid)

**Purpose**: Complete automation platform with event monitoring + AI agent

**Configuration**:
```env
ENABLE_EVENT_LISTENERS=true
ENABLE_AGENT=true
EVENT_EMAIL_ENABLED=true
EVENT_WS_ENABLED=true
DISCORD_OUT_ENABLED=true
GOTIFY_OUT_ENABLED=true
```

**Deployment**: 
1. Start MCP server: `python3 mcp_server_http.py`
2. Configure n8n to connect to MCP server
3. Events automatically trigger n8n workflows
4. AI agent uses MCP tools for remediation

**Use Case**: Production automation, autonomous infrastructure management

---

## Configuration System

### Lab Topologies

#### STANDALONE Mode
- Single Proxmox node (no cluster)
- Direct node configuration in `.env`
- Suitable for home labs, testing

**Example**:
```env
LAB_CONFIGURATION=STANDALONE
PVE_NODES=pve-main

PVE_MAIN_HOST=192.168.1.100
PVE_MAIN_USER=root@pam
PVE_MAIN_TOKEN_NAME=mcp-token
PVE_MAIN_TOKEN_VALUE=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### CLUSTERED Mode
- Proxmox cluster with multiple nodes
- Auto-discovery of cluster members
- Single primary node configuration

**Example**:
```env
LAB_CONFIGURATION=CLUSTERED
PVE_CLUSTER_PRIMARY_HOST=192.168.1.100
PVE_CLUSTER_PRIMARY_USER=root@pam
PVE_CLUSTER_PRIMARY_TOKEN_NAME=mcp-token
PVE_CLUSTER_PRIMARY_TOKEN_VALUE=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

#### MIXED Mode
- Both explicit node definitions and auto-discovery
- Mix of clustered and standalone nodes
- PBS nodes alongside PVE cluster

**Example**:
```env
LAB_CONFIGURATION=MIXED
PVE_NODES=pve-main,pve-edge
PBS_NODES=pbs-backup

# Cluster discovery from primary
PVE_CLUSTER_PRIMARY_HOST=192.168.1.100
...

# Additional standalone PBS
PBS_BACKUP_HOST=192.168.1.200
...
```

### Environment Variables Structure

**Node Definition Pattern**:
```
{NODE_NAME}_{PROPERTY}

Examples:
PVE_MAIN_HOST          → Hostname/IP for node "pve-main"
PVE_MAIN_USER          → User for authentication
PVE_MAIN_TOKEN_NAME    → API token name
PVE_MAIN_TOKEN_VALUE   → API token value
```

**List Configuration**:
```
COMMA_SEPARATED_VALUES

Examples:
PVE_NODES=node1,node2,node3
ENABLED_EVENT_LISTENERS=WEBSOCKET,EMAIL,SYSLOG
```

**Boolean Configuration**:
```
Truthy: 1, true, yes, on
Falsy:  0, false, no, off, <empty>
```

---

## Event Processing

### Event Normalization

All input listeners convert diverse event formats into a standardized structure:

```python
{
    "title": str,       # Event summary
    "message": str,     # Detailed message
    "source": str,      # Input listener name
    "timestamp": str,   # ISO 8601 timestamp
    "node": str,        # Proxmox node (if applicable)
    "severity": str,    # info|warning|error|critical
    "metadata": dict    # Additional context
}
```

### Event Filtering

Listeners can filter events before dispatching:
- Severity-based filtering
- Node-based filtering
- Keyword-based filtering
- Rate limiting

### Event Enrichment

EventDispatcher can enrich events with:
- Cluster context (from ProxmoxAPIManager)
- Historical data
- Correlation IDs
- Related events

---

## API Integration

### Proxmox API Connection

The system uses the `proxmoxer` library for API communication:

**Connection Parameters**:
```python
ProxmoxAPI(
    host="192.168.1.100:8006",
    user="root@pam",                    # User@realm
    token_name="mcp-token",             # Token name
    token_value="xxxx-xxxx-xxxx",       # Token secret
    verify_ssl=False,                   # SSL verification
    service="PVE"                       # PVE or PBS
)
```

### API Client Pool

ProxmoxAPIManager maintains a pool of API clients:
```python
{
    "pve-node1": ProxmoxAPI(...),
    "pve-node2": ProxmoxAPI(...),
    "pbs-backup": ProxmoxAPI(... service='PBS')
}
```

### API Call Pattern

**MCP Tool → API Manager → Proxmox**:
```python
# In MCP tool handler
async def handle_get_vms(node: str):
    api_manager = self._ensure_api_manager()
    client = api_manager.get_pve_client(node)
    
    # Direct API access
    vms = client.nodes(node).qemu.get()
    
    return format_vm_response(vms)
```

### API Error Handling

- Connection failures → Retry with exponential backoff
- Authentication errors → Logged and reported to notifiers
- API errors → Gracefully returned to MCP client
- Timeout errors → Configurable timeout with fallback

---

## Deployment Scenarios

### Scenario 1: Home Lab Monitoring

**Setup**:
- Single Proxmox node
- Email-based alerts
- Discord notifications
- No AI agent

**Configuration**:
```env
LAB_CONFIGURATION=STANDALONE
PVE_NODES=pve-main
EVENT_EMAIL_ENABLED=true
DISCORD_OUT_ENABLED=true
ENABLE_EVENT_LISTENERS=true
ENABLE_AGENT=false
```

**Command**: `python3 main.py` (runs listeners only)

### Scenario 2: Small Business Automation

**Setup**:
- Proxmox cluster (3 nodes)
- AI agent for automated responses
- Multiple notification channels
- Local n8n instance

**Configuration**:
```env
LAB_CONFIGURATION=CLUSTERED
EVENT_EMAIL_ENABLED=true
EVENT_WS_ENABLED=true
DISCORD_OUT_ENABLED=true
GOTIFY_OUT_ENABLED=true
ENABLE_AGENT=true
```

**Deployment**:
1. `python3 main.py --mcp-server` (stdio mode for local n8n)
2. Configure n8n with MCP integration
3. Event listeners run in same process

### Scenario 3: Enterprise Multi-Site

**Setup**:
- Multiple Proxmox clusters
- Remote n8n instance
- Centralized monitoring
- High availability

**Configuration**:
```env
LAB_CONFIGURATION=MIXED
PVE_NODES=site1-pve1,site1-pve2,site2-pve1
PBS_NODES=site1-pbs,site2-pbs
# ... all node configs
```

**Deployment**:
1. Run HTTP MCP server: `python3 mcp_server_http.py --host 0.0.0.0 --port 8080`
2. Configure remote n8n to connect via HTTP
3. Deploy behind reverse proxy (nginx/Caddy)
4. Use SSL/TLS for security

### Scenario 4: Docker Container

**Setup**:
- Containerized deployment
- Environment-based configuration
- Network-accessible MCP server

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["python3", "mcp_server_http.py", "--host", "0.0.0.0", "--port", "8080"]
```

**Docker Compose**:
```yaml
services:
  proxmox-mcp:
    build: .
    ports:
      - "8080:8080"
    env_file:
      - .env
    restart: unless-stopped
```

---

## Troubleshooting

### Common Issues

#### 1. API Connection Failures

**Symptoms**: "Failed to initialize Proxmox API" errors

**Diagnosis**:
```bash
python3 main.py --test-connection
```

**Solutions**:
- Verify node hostname/IP is reachable
- Check API token permissions
- Confirm token format (user, token_name, token_value are separate)
- Verify SSL settings match Proxmox configuration
- Check firewall rules (port 8006 for PVE)

#### 2. Event Listeners Not Receiving Events

**Symptoms**: No events in logs, notifications not sent

**Diagnosis**:
- Check `ENABLE_EVENT_LISTENERS=true`
- Verify specific listener is enabled (e.g., `EVENT_EMAIL_ENABLED=true`)
- Check listener is in `ENABLED_EVENT_LISTENERS` list

**Solutions**:
- Review email configuration (IMAP settings, credentials)
- Test WebSocket connectivity
- Verify syslog port is not blocked
- Check Gotify/Discord credentials

#### 3. MCP Server Not Responding

**Symptoms**: n8n cannot connect, MCP tools fail

**Diagnosis**:
```bash
# Test stdio server
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python3 mcp_server.py

# Test HTTP server
curl http://localhost:8080/health
```

**Solutions**:
- Ensure server process is running
- Check port availability (HTTP mode)
- Verify n8n configuration matches server mode
- Review logs for API initialization errors

#### 4. Events Not Triggering n8n Workflows

**Symptoms**: Events received but n8n workflows don't execute

**Solutions**:
- Verify webhook configuration in n8n
- Check n8n workflow activation status
- Review n8n execution logs
- Confirm event format matches n8n expectations

### Logging and Debugging

**Log Levels** (configured via `LOG_LEVEL` in `.env`):
- `DEBUG`: Verbose output, all events
- `INFO`: Normal operation (default)
- `WARNING`: Potential issues
- `ERROR`: Failures and exceptions

**Log Locations**:
- Console output (stdout/stderr)
- Configure external logging via Python logging handlers

**Debug Mode**:
```python
# In code, temporarily:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Checks

**System Health**:
```bash
python3 main.py --test-connection
```

**Component Tests**:
```bash
python3 modules/Test/test_connection.py      # API connectivity
python3 modules/Test/test_discord.py         # Discord integration
python3 modules/Test/test_mcp_server.py      # MCP protocol
```

### Performance Monitoring

**Key Metrics**:
- Event processing latency
- API response times
- Notifier success rates
- Listener uptime

**Monitoring Tools**:
- System logs for error rates
- Prometheus metrics (custom implementation)
- APM tools (e.g., Datadog, New Relic)

---

## Security Considerations

### API Token Security

✅ **Best Practices**:
- Use separate API tokens per application
- Grant minimal required permissions
- Rotate tokens periodically
- Never commit tokens to version control
- Use environment variables or secrets management

❌ **Avoid**:
- Using root user without token authentication
- Sharing tokens across services
- Embedding tokens in code

### Network Security

**Recommendations**:
- Run HTTP MCP server behind reverse proxy
- Use TLS/SSL for all external connections
- Implement firewall rules to restrict access
- Use VPN for remote administration
- Enable fail2ban for rate limiting

### Credential Management

**Options**:
1. `.env` file (development)
2. Docker secrets (Docker Swarm)
3. Kubernetes secrets (K8s)
4. HashiCorp Vault (enterprise)
5. AWS Secrets Manager (cloud)

---

## Maintenance

### Regular Tasks

**Daily**:
- Review logs for errors
- Monitor notification delivery
- Check API connectivity

**Weekly**:
- Review event volume and trends
- Update notification rules
- Test backup workflows

**Monthly**:
- Rotate API tokens
- Update dependencies
- Review and optimize configurations
- Test disaster recovery procedures

### Updates and Upgrades

**Updating MCP Server**:
```bash
git pull origin main
pip install -r requirements.txt --upgrade
systemctl restart proxmox-mcp  # If using systemd
```

**Compatibility**:
- Monitor Proxmox API changes
- Test with new Proxmox versions
- Update proxmoxer library as needed

---

## Conclusion

The Proxmox MCP Server provides a comprehensive bridge between Proxmox infrastructure and modern automation/AI platforms. Its modular architecture enables flexible deployment scenarios from simple monitoring to sophisticated AI-driven automation.

**Key Takeaways**:
- **Modular Design**: Mix and match components based on needs
- **Event-Driven**: Real-time response to infrastructure events
- **AI-Ready**: MCP protocol enables LLM-driven automation
- **Flexible Deployment**: From home labs to enterprise clusters
- **Production-Ready**: Robust error handling and monitoring

For specific use cases and advanced configurations, refer to:
- `README.md` - Getting started guide
- `modules/Enhanced_Files/ENHANCED_README.md` - Enhanced features
- `modules/Enhanced_Files/QUICK_START.md` - Quick start guide
- Example `.env` files in the repository

---

**Document Version**: 1.0  
**Last Updated**: October 16, 2025  
**Repository**: https://github.com/JerichoJack/Proxmox-MCP
