# 🧠 MCP Server for Proxmox

The **MCP Server for Proxmox** is a true **real-time automation orchestrator** for your Proxmox environment.  
By ingesting **email** and **WebSocket events** directly from your PVE and PBS nodes, the MCP Server enables instant awareness and automated remediation of issues — before you even log in.

This project bridges the gap between **Proxmox’s event system** and your automation or AI layer, letting MCP Agents act immediately on node, VM, or backup events.

---

## 🚀 Why Event Ingestion Is Key

Proxmox generates valuable real-time data through:
- **Email notifications** (alerts, backup results, hardware events)
- **WebSocket events** (VM start/stop, migration progress, UI updates)
- **External integrations** (Gotify notifications, Discord webhooks)

The MCP Server ingests all these sources and provides:
- A **live state view** of all nodes, VMs, and PBS jobs.
- **Structured event forwarding** to MCP Agents for downstream processing.
- **Automated troubleshooting** and remediation via scripts or AI logic.
- **Multi-channel notifications** (Gotify, Discord, email, webhooks).
- A unified bridge between Proxmox's raw signals and your automation stack.

---

## 🧩 Architecture Overview

```plaintext
┌───────────────────────────────┐
│           MCP Server          │
│ proxmox-mcp-server            │
│                               │
│  ├── REST & WebSocket Client  │ ← Subscribes to PVE/PBS events
│  ├── Event Ingestion Engine   │ ← Parses, filters, normalizes events
│  ├── Event Dispatcher         │ ← Pushes structured events to MCP Agent
│  ├── Diagnostic Engine        │ ← Triggers auto-troubleshooting Agents
│  ├── Command Tools            │
└──────────────┬────────────────┘
               │
               ▼
┌───────────────────────────────┐
│             MCP Agent         │
│  Receives event stream,       │
│  sends notifications (Discord,│
│  Home Assistant, email),      │
│  or invokes troubleshooting.  │
└───────────────────────────────┘
```

---

## 🧱 Project Structure
```plaintext
Proxmox-MCP/
├── core/                                       # Core functionality
│   ├── api_tester.py                          # API connectivity testing
│   ├── config.py (MCPConfig)                  # Configuration management
│   ├── event_dispatcher.py                    # Event dispatching
│   ├── event_listener.py                      # Event listening base
│   ├── manager.py (MCPManager)                # MCP Manager
│   ├── proxmox_api.py                         # Proxmox API client wrapper
│   └── utils.py                               # Logging and helper utilities
├── modules/
│   ├── Enhanced_Files/                        # Enhanced documentation & examples
│   │   ├── Discord ChatBot.json               # n8n Discord ChatBot Workflow
│   │   ├── 🤖Proxmox MCP Agent Workflow - Enhanced.json # Advanced AI Agent Workflow
│   │   ├── ENHANCED_README.md                 # Enhanced features documentation
│   │   ├── QUICK_START.md                     # Quick start guide
│   │   └── roadmap.md                         # Project roadmap
│   ├── input/                                 # Event ingestion modules
│   │   ├── base.py                            # BaseListener class
│   │   ├── discord_listener.py                # Discord webhook listener
│   │   ├── email_listener.py                  # Email alert listener
│   │   ├── gotify_listener.py                 # Gotify stream listener
│   │   ├── syslog_listener.py                 # Syslog UDP listener
│   │   └── websocket_listener.py              # WebSocket event listener
│   ├── output/                                # Event dispatch / notification modules
│   │   ├── base.py                            # BaseNotifier class
│   │   ├── discord_notifier.py                # Discord notifier
│   │   └── gotify_notifier.py                 # Gotify notifier
│   └── Test/                                  # Test suite
│       ├── test_connection.py
│       ├── test_discord.py
│       ├── test_enhanced_server.py
│       ├── test_mcp_server.py
│       └── ... (additional test files)
├── main.py                                    # Unified Production Entry Point
├── mcp_server.py                              # MCP stdio Server (local n8n)
├── mcp_server_http.py                         # MCP HTTP/WebSocket Server (remote n8n)
├── .env.example                               # Example configuration file
├── requirements.txt                           # Python dependencies
└── README.md                                  # This file
```

---

## ⚙️ Configuration Overview

The `.env` file controls how the MCP Server connects to Proxmox and handles events.  
Each section can be toggled to match your deployment and notification preferences.
- **Standalone, Clustered, or Mixed Lab Support**
- **The key `LAB_CONFIGURATION` allows you to define if your lab consists of standalone nodes, clustered nodes, or a combination.**
- **Event Listeners can be toggled per type (WebSocket, Email, Syslog, Gotify, Discord).**
- **Notifiers can be toggled per backend (Discord, Gotify are currently supported).**
- **Node credentials, tokens, and host information are stored per-node using .env sections.**
> ⚠️ **Note:** See the full `.env.example` in the repository for structure and supported keys.

---

## 🏗️ Key Features

- **Unified Production Environment** – ✅ Single entry point with `main.py`
- **Comprehensive Testing** – ✅ Full connectivity validation with `--test-connection`
- **MCP Protocol Integration** – ✅ Production-ready MCP server for n8n
- **AI Agent Workflows** – ✅ Complete n8n examples for intelligent automation
- **Multi-Node Support** – ✅ Standalone, clustered, and mixed Proxmox environments
- **Real-time Event Processing** – ✅ WebSocket, Email, Syslog, and API event ingestion
- **Smart Notifications** – ✅ Discord, Gotify integration with intelligent routing
- **Natural Language Interface** – ✅ Discord ChatBot for conversational Proxmox management
- **Approval Workflows** – ✅ AI agents with human oversight for critical operations

---

## 🧰 Available MCP Tools

Both the stdio (`mcp_server.py`) and HTTP/WebSocket (`mcp_server_http.py`) servers provide comprehensive tools for managing your Proxmox infrastructure:

### Core Infrastructure Management
- **`get_cluster_status`** - Get comprehensive status of Proxmox cluster including nodes, resources, and health
- **`get_nodes`** - Get detailed information about all Proxmox nodes including status and resources
- **`get_node_status`** - Get detailed status of a specific Proxmox node including CPU, memory, storage usage
- **`check_node_health`** - Perform comprehensive health check on Proxmox nodes including connectivity and resource status

### Virtual Machine Operations
- **`get_vms`** - Get comprehensive VM information including status, configuration, and performance
- **`execute_vm_command`** - Execute commands on VMs (start, stop, shutdown, restart, reboot, suspend, resume, reset, status, config)

### Container Management
- **`get_lxcs`** - Get comprehensive LXC container information including status and configuration
- **`execute_lxc_command`** - Execute commands on LXC containers (start, stop, shutdown, restart, reboot, suspend, resume, status, config)

### Storage & Backup Management
- **`get_storage`** - Get detailed storage information including usage, content, and health status
- **`get_backup_info`** - Get backup job information and status

### Advanced Operations
- **`get_node_tasks`** - Get recent tasks and operations for nodes
- **`get_network_info`** - Get network configuration and interface information

### Notifications
- **`send_notification`** - Send notification through configured channels (Discord, Gotify)

**Total Tools Available:** 13 comprehensive tools for complete Proxmox management

> 🔄 **Feature Parity:** Both server implementations (stdio and HTTP) provide identical tool functionality, ensuring consistent experience regardless of deployment method.

---

## 🚀 Getting Started

### Quick Start (Production Environment)

```bash
# Clone repository and setup
git clone https://github.com/JerichoJack/Proxmox-MCP.git
cd Proxmox-MCP
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your Proxmox credentials and preferences

# Test all connections
python3 main.py --test-connection

# Start MCP server for n8n integration
python3 main.py --mcp-server
```

### Production Usage

The unified `main.py` serves as the single entry point with two primary modes:

**🔍 Connection Testing:**
```bash
python3 main.py --test-connection
```
- Tests all configured PVE/PBS node connectivity
- Validates input/output module functionality
- Verifies MCP server protocol initialization
- Provides comprehensive system health check

**🔌 MCP Server Mode (stdio):**
```bash
python3 main.py --mcp-server
```
- Starts enhanced MCP server for n8n integration
- Uses stdio interface for local MCP Client connections
- Comprehensive Proxmox infrastructure management
- Full suite of advanced tools and capabilities

**🌐 MCP HTTP Server Mode (remote):**
```bash
python3 main.py --mcp-http --host 0.0.0.0 --port 8000
```
- Starts enhanced HTTP/WebSocket MCP server
- Supports remote n8n connections via network
- **Same comprehensive functionality as stdio server**
- Ideal for distributed deployments

---

## 🛠️ Enhanced MCP Tools & Capabilities

Both the stdio and HTTP MCP servers now provide **identical comprehensive functionality**:

### 🏗️ Core Infrastructure Management
- **`get_cluster_status`** - Comprehensive cluster health and resource overview
- **`get_nodes`** - Detailed node information with performance metrics
- **`get_node_status`** - Specific node status including CPU, memory, storage
- **`check_node_health`** - Connectivity and API health validation

### 🖥️ Virtual Machine Operations
- **`get_vms`** - List VMs with status, configuration, and performance data
- **`execute_vm_command`** - Complete VM lifecycle management:
  - `start`, `stop`, `shutdown` (graceful/forced)
  - `restart`, `reboot`, `suspend`, `resume`, `reset`
  - `status`, `config` - Query current state and configuration

### 📦 Container Management
- **`get_lxcs`** - LXC container information and status
- **`execute_lxc_command`** - Full container lifecycle operations:
  - Same command set as VMs with container-specific optimizations

### 💾 Storage & Backup Monitoring
- **`get_storage`** - Storage utilization, health, and capacity analysis
- **`get_backup_info`** - Backup job status and scheduling information
- **`get_node_tasks`** - Recent operations, task history, and error tracking

### 🌐 Network & Operations
- **`get_network_info`** - Network configuration and interface status
- **`send_notification`** - Multi-channel notifications (Discord, Gotify)

### 🤖 AI-Ready Prompts
- **`proxmox_health_check`** - Guided infrastructure health assessment
- **`proxmox_status_report`** - Comprehensive reporting with recommendations
- **`proxmox_vm_management`** - VM operations best practices
- **`proxmox_storage_analysis`** - Storage optimization guidance
- **`proxmox_incident_response`** - Systematic troubleshooting procedures

### 📚 Resources
- **`proxmox://config`** - Current Proxmox MCP Server configuration
- **`proxmox://nodes`** - List of configured nodes with connection status
- **`proxmox://capabilities`** - Server capabilities and tool descriptions
- **`proxmox://status`** - Current server status and health

**Summary:** 13 Tools + 5 AI Prompts + 4 Resources = Comprehensive Proxmox Management Platform

---

## 🧩 n8n AI Agent Integration

This project includes complete n8n workflow examples for intelligent Proxmox management:

### 🎯 Workflow Examples

**1. Discord ChatBot** (`modules/Enhanced_Files/Discord ChatBot.json`)
- Natural language interface for Proxmox queries
- Processes user commands via Discord
- Routes complex requests to specialized AI agents
- Supports both simple queries and complex infrastructure management

**2. Proxmox MCP Agent** (`modules/Enhanced_Files/🤖Proxmox MCP Agent Workflow - Enhanced.json`)
- Advanced AI agent for Proxmox infrastructure management
- Uses MCP tools for real-time system monitoring
- Intelligent decision making with user approval workflows
- Comprehensive status reporting and automated remediation

### 🔄 Integration Flow

```plaintext
Discord User → ChatBot Agent → Proxmox MCP Agent → MCP Server → Proxmox Infrastructure
     ↑                                ↓
     └─────────── Response & Status Updates ──────────┘
```

### 📋 n8n MCP Client Configuration

There are two ways to connect n8n to your Proxmox MCP Server:

#### Option 1: Local Installation (stdio) - **Same Enhanced Features**

If you can install the MCP server on the same machine as n8n:

```bash
# On your n8n server
git clone https://github.com/JerichoJack/Proxmox-MCP.git /opt/Proxmox-MCP
cd /opt/Proxmox-MCP
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Proxmox server credentials

# Start enhanced stdio server
python3 main.py --mcp-server
```

Configure your MCP Client node:
```json
{
  "parameters": {
    "options": {
      "connection": {
        "type": "stdio",
        "command": "python3",
        "args": ["/opt/Proxmox-MCP/mcp_server.py"],
        "workingDirectory": "/opt/Proxmox-MCP"
      }
    }
  }
}
```

#### Option 2: Remote Server (WebSocket) ⭐ **Same Enhanced Features**

If your n8n and Proxmox MCP server are on different machines:

```bash
# On your Proxmox MCP server machine
git clone https://github.com/JerichoJack/Proxmox-MCP.git /root/Proxmox-MCP
cd /root/Proxmox-MCP
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Proxmox server credentials

# Start enhanced HTTP/WebSocket server
python3 main.py --mcp-http --host 0.0.0.0 --port 8000
```

Configure your MCP Client node:
```json
{
  "parameters": {
    "options": {
      "connection": {
        "type": "websocket",
        "endpoint": "ws://YOUR-SERVER-IP:8000/ws"
      }
    }
  }
}
```

> 🎯 **Both server modes now provide identical comprehensive functionality** - choose based on your deployment architecture, not feature differences!

**Replace `YOUR-SERVER-IP` with the actual IP address of your MCP server machine.**

#### Connection Examples

**For your current setup (n8n on separate server):**
```json
{
  "nodes": [
    {
      "parameters": {
        "options": {
          "connection": {
            "type": "websocket",
            "endpoint": "ws://192.168.1.100:8000/ws"
          }
        }
      },
      "type": "@n8n/n8n-nodes-langchain.mcpClientTool",
      "typeVersion": 1.2,
      "position": [1200, 592],
      "id": "bcc9b8b5-9b94-4f73-81de-ea00dd4c9ba6",
      "name": "MCP Client"
    }
  ]
}
```

#### Server Management Commands

**Start enhanced stdio server (local n8n):**
```bash
python3 main.py --mcp-server
```
*Comprehensive feature set: 13 tools + 5 AI prompts + 4 resources*

**Start enhanced HTTP server (remote n8n):**
```bash
python3 main.py --mcp-http --host 0.0.0.0 --port 8000
```
*Identical feature set: 13 tools + 5 AI prompts + 4 resources*

**Test connectivity and validate setup:**
```bash
python3 main.py --test-connection
```

**Health check (HTTP server):**
```bash
curl http://YOUR-SERVER-IP:8000/health
```

> ✨ **Feature Parity Achieved**: Both servers now provide identical comprehensive Proxmox management capabilities!

## 🧩 Enhanced Use Cases

### 🤖 AI-Powered Infrastructure Management
- **Intelligent Health Monitoring**: AI agents continuously assess cluster health using `check_node_health`
- **Predictive Maintenance**: Automated analysis of `get_node_tasks` to identify potential issues
- **Smart Resource Allocation**: AI-driven VM/LXC management using comprehensive `get_vms`/`get_lxcs` data

### 📊 Advanced Operations & Analytics  
- **Capacity Planning**: AI analysis of `get_storage` trends for expansion recommendations
- **Performance Optimization**: Intelligent VM placement using detailed node resource data
- **Backup Strategy**: AI-enhanced backup monitoring via `get_backup_info` with failure prediction

### 🔔 Intelligent Notification & Response
- **Context-Aware Alerts**: Smart notifications using severity analysis and historical data
- **Natural Language Interface**: Discord ChatBot answers complex queries like "Which VMs need attention?"
- **Automated Remediation**: AI agents execute safe recovery procedures with human approval

### 🌐 Cross-Platform Integration
- **Multi-Channel Communications**: Unified notifications across Discord, Gotify, and other platforms
- **Event-Driven Workflows**: Automatic responses to Proxmox events with intelligent escalation
- **Distributed Management**: Remote HTTP server enables management from anywhere

---

## 🏗️ Setup & Installation

## 📦 requirements.txt

The following Python packages are required:

```
mcp
proxmoxer
requests
aiohttp
aiohttp-cors
python-dotenv
configparser
apscheduler
gotify
websockets
fastapi
uvicorn
pydantic
```

Install all dependencies with:
```bash
pip install -r requirements.txt
```

### Prerequisites

- Python 3.10+  
- `pip` for dependency management  
- Proxmox VE environment with API access or event hooks enabled

### Clone the Repository

```bash
git clone https://github.com/JerichoJack/Proxmox-MCP.git
cd Proxmox-MCP
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 🧩 Proxmox API Setup

To allow the MCP Server to receive data and interact with your Proxmox environment, you’ll need to create a dedicated **API user** with restricted permissions.  
This process should be repeated for both **Proxmox VE (PVE)** and **Proxmox Backup Server (PBS)** if you’re using both.

---

#### 🧠 Step 1: Create a Dedicated API User (PVE)

1. Log in to your **Proxmox VE Web UI**.
2. Navigate to **Datacenter → Permissions → Users**.
3. Click **Add** → **User**.
4. Enter a username, for example:
   ```
   mcp@pve
   ```
5. Choose **Realm:** `Proxmox VE authentication server` (or another if you use LDAP).
6. Set a **secure password** and click **Add**.

---

#### 🧩 Step 2: Create an API Token (Optional but Recommended)

If you prefer **token-based authentication** (safer for services):

1. Navigate to **Datacenter → Permissions → API Tokens**.
2. Click **Add**.
3. Choose the user you just created (`mcp@pve`).
4. Give the token an ID, e.g. `mcp-token`.
5. Uncheck **Privilege Separation** if your MCP server needs full access to the assigned roles.
6. Copy the **Token ID** and **Secret** — you’ll need these for your `.env` file.

---

#### 🔐 Step 3: Assign Permissions

1. Go to **Datacenter → Permissions → Add → User Permission**.
2. Choose:
   - **Path:** `/` (or restrict to a specific node if you prefer)
   - **User:** `mcp@pve`
   - **Role:** `PVEAuditor` *(read-only)*  
     or `PVEAdmin` *(for full event and control access)*.
3. Click **Add**.

---

> ⚠️ **Note:** If your MCP server runs on the same host as PVE, you can use `localhost` for the host address.  
> Ensure the MCP process user has network access to the Proxmox API port (default `8006`).

---

### 🗄️ Proxmox Backup Server (PBS) API Setup

If you also want MCP to listen for backup-related events from your **Proxmox Backup Server**, create a similar user there.

#### Step 1: Create a User on PBS

1. Log in to your **PBS Web UI**.
2. Go to **Access Control → Users** → **Add**.
3. Create a user:
   ```
   mcp@pbs
   ```
4. Set a secure password.

#### Step 2: Assign Role and Permissions

1. Go to **Access Control → Permissions → Add**.
2. Choose:
   - **Path:** `/`  
   - **User:** `mcp@pbs`  
   - **Role:** `Audit` *(read-only)* or `Admin` *(full access)*.

#### Step 3: (Optional) Create an API Token

Similar to PVE:
- Go to **Access Control → API Tokens**.
- Click **Add**.
- Create token for `mcp@pbs`.
- Copy the token and secret for `.env`.

---

### ✅ Final Step: Test Connectivity

After configuring your `.env` file, validate your setup with the built-in connection tester:

```bash
# Test all configured nodes and IO modules
python main.py --test-connection
```

**What `--test-connection` validates:**
- ✅ **PVE/PBS API Access** – Tests credentials and connectivity for each configured node
- ✅ **WebSocket Endpoints** – Verifies subscription capability to live event streams  
- ✅ **Input Listeners** – Tests Gotify stream, Discord webhook, and Syslog port binding
- ✅ **Output Notifiers** – Sends test notifications via Gotify and Discord (if enabled)
- ✅ **Configuration Parsing** – Validates `.env` structure and required parameters

**Expected Output:**
```
🔗 Testing connectivity to configured nodes...
✅ PVE Node 'pve-main' connectivity test passed
✅ PBS Node 'pbs-main' connectivity test passed
🔔 Testing Gotify output notifier...
✅ Gotify output test sent successfully
🔔 Testing Gotify input listener (stream)...
✅ Gotify input test stream succeeded

🎉 All nodes and IO modules are reachable and ready!
```

Once all tests pass, you can start the MCP server in your preferred mode:

```bash
# Start MCP stdio server (for local n8n)
python3 main.py --mcp-server

# OR start MCP HTTP server (for remote n8n)
python3 main.py --mcp-http --host 0.0.0.0 --port 8000
```

---

## 🔔 Notification System

* [x] **Email** – reads Proxmox email alerts
* [x] **WebSocket** – subscribes to live Proxmox event streams
* [x] **Syslog** – listens for UDP syslog messages from Proxmox nodes
* [x] **Gotify** – ✅ Full input/output implementation with streaming and notifications
* [x] **Discord** – ✅ Full input/output implementation with webhooks and rich embeds
* [⚙] **Ntfy** – planned

> All notification backends use a unified interface; adding a new notifier only requires implementing `.send(title, message)`.

---

## 🛠️ Troubleshooting

### Common Issues

**❌ Configuration file '.env' not found**
```bash
# Copy the example configuration
cp .env.example .env
# Edit with your Proxmox credentials
nano .env
```

**❌ MCP Server connection issues in n8n**
- Ensure working directory is set to the Proxmox-MCP folder
- Use absolute paths for the Python command
- Verify python3 is in your PATH: `which python3`
- Test manually: `python3 mcp_server.py` (should show connection info)

**❌ Some connectivity tests failed**
- Check network connectivity to Proxmox nodes
- Verify API credentials in `.env`
- Ensure firewall allows connections to required ports
- Check Discord/Gotify tokens and webhook URLs

**❌ n8n workflow execution errors**
- Ensure MCP server is running: `python3 main.py --mcp-server`
- Check n8n MCP Client node configuration
- Verify channelId is being passed correctly from Discord
- Test individual MCP tools in n8n test mode

### Getting Help

1. **Run diagnostics**: `python3 main.py --test-connection`
2. **Check logs**: Look for error messages in terminal output
3. **Validate configuration**: Review `.env` file settings
4. **Review documentation**: See `modules/Enhanced_Files/QUICK_START.md` for quick setup guide
5. **Test MCP tools**: Use n8n's test mode to verify individual tool functionality

---

## 🤝 Contributing

Contributions welcome! Open an issue or submit a pull request.
Discuss major changes in the Issues section first.

---

## 📄 License

MIT License

---

> **MCP Server for Proxmox** — A real-time automation orchestrator bringing intelligence and autonomy to your Proxmox infrastructure.

