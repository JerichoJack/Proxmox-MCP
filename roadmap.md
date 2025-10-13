# 🛣️ MCP Server for Proxmox - Roadmap

This roadmap tracks progress on the MCP Server for Proxmox project, including event ingestion, dispatch, and notification modules, as well as the integration plan for a working demo.

---

## ✅ Completed

* [x] Initial project skeleton with `core` and `modules` directories
* [x] `.env.example` added with detailed standalone & clustered node examples
* [x] `requirements.txt` added
* [x] `README.md` added
* [x] `core/config.py` (MCPConfig) implemented
* [x] `core/event_dispatcher.py` implemented
* [x] `modules/input/email_listener.py` implemented
* [x] `modules/input/websocket_listener.py` updated for standalone & clustered support
* [x] `modules/output/gotify_notifier.py` implemented
* [x] `modules/output/discord_notifier.py` implemented
* [x] `main.py` skeleton prepared for integration
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

## 🧠 Future / Demo Steps

The **MCP Demo Integration Plan** ensures a fully working demo for testing.

1. **Load configuration** from `.env` (LAB_CONFIGURATION, nodes, listeners, notifiers)
2. **Initialize Event Dispatcher** with active notifiers
3. **Start Event Listeners** (WebSocket, Email, future: Syslog)
4. **Test connection mode** (`--test-connection`) to validate PVE/PBS access
5. **Dispatch events** from listeners to configured notifiers
6. **Support clustered nodes** for both PVE & PBS
7. **Graceful shutdown** handling (SIGINT / SIGTERM)
8. **Integration with MCP Agent** for automated actions
9. **Optional:** Add additional listeners and notifiers as needed

> After these steps, the MCP server demo will be able to ingest live events from PVE/PBS nodes and push them to configured notifiers in real time.

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
│   │   ├── email_listener.py                   # EmailListener
│   │   ├── websocket_listener.py               # WebSocketListener
│   │   └── syslog_listener.py                  # SyslogListener (future)
│   ├── output/                                 # Event dispatch / notification modules
│   │   ├── base.py                             # BaseNotifier class
│   │   ├── discord_notifier.py                 # DiscordNotifier
│   │   ├── gotify_notifier.py                  # GotifyNotifier
│   │   ├── ntfy_notifier.py                    # NtfyNotifier (future)
│   │   └── email_notifier.py                   # EmailNotifier (future)
├── main.py                                     ⚙ In Work
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