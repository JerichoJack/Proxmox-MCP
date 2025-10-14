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
├── core/
│   ├── config.py (MCPConfig)                   ✅ Implemented
│   ├── event_dispatcher.py (EventDispatcher)   ✅ Implemented
│   ├── event_listener.py (EventListener)       ⚙ In Work
│   ├── manager.py (MCPManager)                 ⚙ In Work
│   └── utils.py (logging, helpers)             ⚙ In Work
├── modules/
│   ├── input/                                  # Event ingestion modules
│   │   ├── base.py                             # BaseListener class
│   │   ├── discord_listener.py                 # DiscordListener ✅ Implemented
│   │   ├── email_listener.py                   # EmailListener ✅ Implemented
│   │   ├── gotify_listener.py                  # GotifyListener ✅ Implemented  
│   │   ├── syslog_listener.py                  # SyslogListener ✅ Implemented
│   │   └── websocket_listener.py               # WebSocketListener ✅ Standalone & clustered support
│   ├── output/                                 # Event dispatch / notification modules
│   │   ├── base.py                             # BaseNotifier class
│   │   ├── discord_notifier.py                 # DiscordNotifier ✅ Implemented
│   │   ├── gotify_notifier.py                  # GotifyNotifier ✅ Implemented
│   │   ├── ntfy_notifier.py                    # NtfyNotifier
│   │   └── email_notifier.py                   # EmailNotifier (future)
├── main.py                                     ✅ Demo Implementation with --test-connection
├── n8n_agent_interface.py                     ✅ n8n AI Agent HTTP API
├── n8n_workflow_proxmox_ai_agent.json         ✅ Complete n8n AI Agent Workflow
├── setup_n8n_agent.py                         ✅ Setup & Test Suite
├── .env.example                                ✅ Added
├── requirements.txt                            ✅ Added
└── README.md                                   ✅ Updated
```

---

## ⚙️ Configuration Overview

The `.env` file controls how the MCP Server connects to Proxmox and handles events.  
Each section can be toggled to match your deployment and notification preferences.
- **Standalone, Clustered, or Mixed Lab Support**
- **The key `LAB_CONFIGURATION` allows you to define if your lab consists of standalone nodes, clustered nodes, or a combination.**
- **Event Listeners can be toggled per type (WebSocket, Email, Syslog).**
- **Notifiers can be toggled per backend (Discord, Gotify, Ntfy, Email).**
- **Node credentials, tokens, and host information are stored per-node using .env sections.**
> ⚠️ **Note:** See the full `.env.example` in the repository for structure and supported keys.

---

## 🏗️ Key Features (Progress So Far)

- **Full PVE/PBS API control** – ✅ API testing implemented with `--test-connection`
- **Real-time event handling** – ✅ Email, WebSocket & Gotify ingestion implemented
- **Clustered & standalone node support** – ✅ WebSocket and dispatcher updated for clusters
- **Agent notifications and automation** – ✅ Dispatcher & Gotify notifier implemented
- **Pluggable architecture** – ✅ Easy to extend with custom notifiers or handlers
- **Connection validation** – ✅ Comprehensive testing via `python main.py --test-connection`

---

## 🧩 Example Use Cases

- **AI-Powered Automation**: n8n AI Agent analyzes events and takes intelligent actions
- **Smart Notifications**: AI-enhanced notifications with context and severity analysis
- **Automate backups** via PBS and report results in real time.
- **Monitor VM migrations**, restarts, or failed tasks instantly.
- **Detect and fix** node or disk errors before they escalate.
- **Forward structured** Proxmox events to AI agents for analysis and response.

---

## 🏗️ Setup & Installation

## 📦 requirements.txt (recommended)

```
mcp
proxmoxer
requests
aiohttp
python-dotenv
configparser
apscheduler
```

- Python 3.10+  
- `pip` or `uv` for dependency management  
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

Once all tests pass, you can start the full MCP server:

```bash
# Start MCP Server with real-time event processing
python main.py
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

## 🧠 Future Steps / Remaining Work for Demo

1. **Finish MCP Agent** – receives events and triggers notifications or remediation scripts.
2. **Finalize Event Listeners** – make Email & WebSocket listeners fully async, handle clustered node events correctly.
3. **Complete Gotify/Discord/Ntfy notifiers** – fully async, include error handling.
4. **Manager/Command tools** – orchestrate backups, VM tasks, storage actions.
5. **Logging & Diagnostics** – central log, optional database support.
6. **Optional Web UI/Dashboard** – show live events, node states, and notifications.

> With these steps completed, the MCP server will be a fully working demo, ingesting live events from PVE/PBS nodes and pushing them to notifiers in real time.

---

## 🤝 Contributing

Contributions welcome! Open an issue or submit a pull request.
Discuss major changes in the Issues section first.

---

## 📄 License

MIT License

---

> **MCP Server for Proxmox** — A real-time automation orchestrator bringing intelligence and autonomy to your Proxmox infrastructure.

