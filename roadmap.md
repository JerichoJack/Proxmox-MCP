# 🛣️ MCP Server for Proxmox - Roadmap

This roadmap tracks progress on the MCP Server for Proxmox project, including event ingestion, dispatch, and notification modules, as well as the integration plan for a working demo.

---

## ✅ Completed

* [x] Initial project skeleton with `core` and `modules` directories
* [x] `.env.example` added with detailed standalone & clustered node examples
* [x] `requirements.txt` added
* [x] `README.md` added and updated
* [x] `core/config.py` (MCPConfig) implemented
* [x] `core/event_dispatcher.py` implemented
* [x] `modules/input/email_listener.py` implemented
* [x] `modules/input/gotify_listener.py` implemented with streaming support
* [x] `modules/input/syslog_listener.py` implemented with UDP server and Proxmox pattern matching
* [x] `modules/input/discord_listener.py` implemented with webhook monitoring
* [x] `modules/input/websocket_listener.py` updated for standalone & clustered support
* [x] `modules/output/gotify_notifier.py` implemented
* [x] `modules/output/discord_notifier.py` implemented with rich embeds
* [x] `main.py` demo implementation with --test-connection feature
* [x] `core/api_tester.py` comprehensive node connectivity testing
* [x] Gotify input/output integration and testing
* [x] `n8n_agent_interface.py` HTTP API for n8n integration
* [x] `n8n_workflow_proxmox_ai_agent.json` complete AI agent workflow
* [x] `setup_n8n_agent.py` setup and testing suite
* [x] Roadmap & demo integration plan drafted

---

## ⚙ In Progress

* [⚙] `core/event_listener.py` fully async, cluster-aware
* [⚙] `core/manager.py` orchestration logic
* [⚙] `core/utils.py` logging & helper functions
* [⚙] Notifiers: Ntfy, Email output modules
* [⚙] MCP Agent integration (event-driven actions)
* [⚙] Optional Web UI / Dashboard
* [⚙] Logging & diagnostics (central log, optional database)

---

## 🎉 Working Demo Status

The **MCP Server Demo** is now functional with core features implemented:

✅ **Completed Demo Features:**
1. **Configuration Loading** - `.env` parsing with LAB_CONFIGURATION support
2. **Event Dispatcher** - Initialized with active notifiers  
3. **Event Listeners** - WebSocket, Email, Gotify, Syslog, and Discord input streams
4. **Connection Testing** - `--test-connection` validates all PVE/PBS nodes and I/O modules
5. **Gotify Integration** - Full bidirectional support (input stream + output notifications)
6. **Discord Integration** - Full bidirectional support (webhook monitoring + rich embed notifications)  
7. **n8n AI Agent Integration** - Complete AI-powered automation with OpenAI analysis
6. **Graceful Shutdown** - Proper SIGINT/SIGTERM handling
7. **Clustered Node Support** - Both PVE & PBS cluster configurations

**Current Status:** `python main.py --test-connection` successfully validates:
- PVE/PBS API connectivity and credentials
- Gotify input/output module functionality  
- Discord input/output webhook connectivity
- Syslog input listener port binding capability
- WebSocket event stream subscriptions
- Configuration file parsing and validation

## 🚀 Next Steps / Future Enhancements

**Immediate Priorities:**
8. **Additional Notifiers** - Complete Ntfy and Email output modules
9. **Enhanced Logging** - Structured logging with optional database storage
10. **Production Hardening** - Authentication, rate limiting, error handling

**Future Features:**
11. **Web UI Dashboard** - Live event monitoring and system status
12. **Advanced Event Filtering** - Rule-based event processing and routing  
13. **Backup Automation** - PBS integration for automated backup workflows
14. **Performance Monitoring** - Resource usage and event throughput metrics
15. **Multi-Tenant Support** - Support multiple Proxmox clusters
16. **Machine Learning** - Predictive analytics and failure prevention

---

## 📦 Project Structure (Current)

```plaintext
PROXMOX-MCP/
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
│   │   └── websocket_listener.py               # WebSocketListener ✅ Implemented
│   ├── output/                                 # Event dispatch / notification modules
│   │   ├── base.py                             # BaseNotifier class
│   │   ├── discord_notifier.py                 # DiscordNotifier ✅ Implemented
│   │   ├── gotify_notifier.py                  # GotifyNotifier ✅ Implemented
│   │   ├── ntfy_notifier.py                    # NtfyNotifier (future)
│   │   └── email_notifier.py                   # EmailNotifier (future)
├── main.py                                     ✅ Implemented with --test-connection
├── .env.example                                ✅ Added
├── requirements.txt                            ✅ Added
└── README.md                                   ✅ Added
```

---

## 📌 Notes

* The roadmap is **dynamic**: tasks marked ✅ are implemented and tested, ⚙ are in progress.
* The demo integration plan ensures the MCP server can be launched with a **single command**, supporting real-time event ingestion and notifications.
* Clustered and standalone nodes are fully supported via the `LAB_CONFIGURATION` and per-node `.env` settings.

---