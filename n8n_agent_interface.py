# n8n_agent_interface.py
"""
n8n AI Agent interface for Proxmox MCP Server.
This provides HTTP endpoints that n8n can call to interact with the MCP server.
"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our MCP components
from core.config import MCPConfig
from core.event_dispatcher import EventDispatcher
from modules.output.discord_notifier import DiscordNotifier
from modules.output.gotify_notifier import GotifyNotifier

app = FastAPI(
    title="Proxmox MCP Server - n8n Agent Interface",
    description="HTTP API interface for n8n AI Agent integration with Proxmox MCP Server",
    version="1.0.0"
)

# Enable CORS for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MCP components
config = None
dispatcher = None
event_history = []

# Pydantic models for API requests/responses
class EventModel(BaseModel):
    title: str
    message: str
    severity: Optional[str] = "info"
    vm_id: Optional[str] = None
    node: Optional[str] = None
    event_type: Optional[str] = None

class NotificationRequest(BaseModel):
    title: str
    message: str
    channels: List[str] = ["discord", "gotify"]
    priority: Optional[str] = "info"
    metadata: Optional[Dict] = {}

class ProxmoxAction(BaseModel):
    action: str  # "start_vm", "stop_vm", "backup_vm", "reboot_node"
    target: str  # VM ID or node name
    parameters: Optional[Dict] = {}

class AgentResponse(BaseModel):
    status: str
    message: str
    data: Optional[Dict] = None
    timestamp: str = datetime.now().isoformat()

# Initialize MCP components
@app.on_event("startup")
async def startup_event():
    global config, dispatcher
    
    try:
        config = MCPConfig(".env")
        
        # Initialize notifiers
        notifiers = []
        if config.gotify_out_enabled:
            notifiers.append(GotifyNotifier(config))
        if config.discord_out_enabled:
            notifiers.append(DiscordNotifier(config))
            
        dispatcher = EventDispatcher(notifiers)
        print("✅ MCP n8n Agent Interface started successfully")
        
    except Exception as e:
        print(f"❌ Failed to initialize MCP components: {e}")

# Event endpoints
@app.get("/events/recent", response_model=List[Dict])
async def get_recent_events(limit: int = 10):
    """Get recent events from the MCP server for n8n agent analysis."""
    return event_history[-limit:] if event_history else []

@app.post("/events/inject", response_model=AgentResponse)
async def inject_event(event: EventModel):
    """Allow n8n agent to inject events into the MCP system."""
    try:
        # Store event in history
        event_data = {
            "id": len(event_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "title": event.title,
            "message": event.message,
            "severity": event.severity,
            "vm_id": event.vm_id,
            "node": event.node,
            "event_type": event.event_type,
            "source": "n8n_agent"
        }
        event_history.append(event_data)
        
        # Dispatch event through MCP system
        if dispatcher:
            await dispatcher.dispatch(
                title=event.title,
                message=event.message,
                severity=event.severity,
                vm_id=event.vm_id,
                node=event.node,
                event_type=event.event_type
            )
        
        return AgentResponse(
            status="success",
            message="Event injected successfully",
            data=event_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to inject event: {str(e)}")

# Notification endpoints
@app.post("/notifications/send", response_model=AgentResponse)
async def send_notification(notification: NotificationRequest):
    """Send notification through MCP dispatcher."""
    try:
        if not dispatcher:
            raise HTTPException(status_code=503, detail="MCP dispatcher not initialized")
            
        await dispatcher.dispatch(
            title=notification.title,
            message=notification.message,
            priority=notification.priority,
            **notification.metadata
        )
        
        return AgentResponse(
            status="success",
            message=f"Notification sent via {', '.join(notification.channels)}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

# Proxmox action endpoints (mock implementation for demo)
@app.post("/proxmox/action", response_model=AgentResponse)
async def execute_proxmox_action(action: ProxmoxAction):
    """Execute Proxmox action (mock implementation for n8n agent testing)."""
    try:
        # In a real implementation, this would use proxmoxer to execute actual commands
        result = {
            "action": action.action,
            "target": action.target,
            "parameters": action.parameters,
            "executed_at": datetime.now().isoformat(),
            "status": "simulated"  # Change to "executed" in real implementation
        }
        
        # Log the action as an event
        event_data = {
            "id": len(event_history) + 1,
            "timestamp": datetime.now().isoformat(),
            "title": f"Proxmox Action: {action.action}",
            "message": f"Action '{action.action}' executed on '{action.target}'",
            "severity": "info",
            "event_type": "proxmox_action",
            "source": "n8n_agent",
            "action_details": result
        }
        event_history.append(event_data)
        
        return AgentResponse(
            status="success",
            message=f"Action '{action.action}' executed on '{action.target}'",
            data=result
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute action: {str(e)}")

# System status endpoints
@app.get("/status", response_model=Dict)
async def get_system_status():
    """Get MCP system status for n8n agent monitoring."""
    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "config_loaded": config is not None,
            "dispatcher_ready": dispatcher is not None,
            "notifiers_count": len(dispatcher.notifiers) if dispatcher else 0,
            "events_processed": len(event_history)
        },
        "configuration": {
            "gotify_enabled": config.gotify_out_enabled if config else False,
            "discord_enabled": config.discord_out_enabled if config else False,
            "lab_mode": config.lab_mode if config else "unknown"
        }
    }

@app.get("/config/summary")
async def get_config_summary():
    """Get configuration summary for n8n agent."""
    if not config:
        raise HTTPException(status_code=503, detail="Configuration not loaded")
    
    return {
        "lab_mode": config.lab_mode,
        "pve_nodes": config.pve_nodes,
        "pbs_nodes": config.pbs_nodes,
        "listeners": {
            "websocket": config.event_ws_enabled,
            "email": config.event_email_enabled,
            "syslog": config.event_syslog_enabled,
            "gotify": config.gotify_in_enabled,
            "discord": config.discord_in_enabled
        },
        "notifiers": {
            "gotify": config.gotify_out_enabled,
            "discord": config.discord_out_enabled
        }
    }

# Event simulation for testing
@app.post("/simulate/event", response_model=AgentResponse)
async def simulate_proxmox_event(event_type: str = "vm_start"):
    """Simulate common Proxmox events for n8n agent testing."""
    
    event_templates = {
        "vm_start": {
            "title": "VM Started",
            "message": "VM 100 (test-server) started successfully on node pve-main",
            "severity": "info",
            "vm_id": "100",
            "node": "pve-main",
            "event_type": "vm_start"
        },
        "vm_stop": {
            "title": "VM Stopped", 
            "message": "VM 101 (database) stopped on node pve-main",
            "severity": "info",
            "vm_id": "101",
            "node": "pve-main",
            "event_type": "vm_stop"
        },
        "backup_success": {
            "title": "Backup Completed",
            "message": "Backup of VM 100 completed successfully",
            "severity": "info",
            "vm_id": "100",
            "event_type": "backup_success"
        },
        "storage_warning": {
            "title": "Storage Warning",
            "message": "Storage 'local-lvm' usage is above 80%",
            "severity": "warning",
            "node": "pve-main",
            "event_type": "storage_warning"
        },
        "node_error": {
            "title": "Node Error",
            "message": "Node pve-backup is unreachable",
            "severity": "critical",
            "node": "pve-backup",
            "event_type": "node_error"
        }
    }
    
    template = event_templates.get(event_type)
    if not template:
        raise HTTPException(status_code=400, detail=f"Unknown event type: {event_type}")
    
    # Inject the simulated event
    event = EventModel(**template)
    return await inject_event(event)

if __name__ == "__main__":
    print("🚀 Starting Proxmox MCP Server - n8n Agent Interface")
    print("📡 Available at: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)