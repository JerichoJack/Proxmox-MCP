# 🤖 n8n AI Agent Integration for Proxmox MCP Server

This integration enables an intelligent n8n AI Agent to consume events from your Proxmox MCP Server and take automated actions based on AI analysis.

## 🏗️ Architecture Overview

```plaintext
┌─────────────────┐    HTTP API    ┌──────────────────┐    Webhooks    ┌─────────────────┐
│  Proxmox MCP    │ ──────────────▶│  n8n_agent_      │ ─────────────▶ │   n8n AI Agent │
│  Server         │                │  interface.py    │                │   Workflow      │
│                 │                │                  │                │                 │
│ • Event Ingestion│               │ • HTTP Endpoints │                │ • Event Analysis│
│ • Notifications │               │ • Event History  │                │ • Smart Actions │
│ • Dispatching   │               │ • Status Monitor │                │ • Notifications │
└─────────────────┘                └──────────────────┘                └─────────────────┘
         │                                   │                                   │
         │                                   │                                   │
         ▼                                   ▼                                   ▼
┌─────────────────┐                ┌──────────────────┐                ┌─────────────────┐
│   Discord &     │                │   FastAPI Web    │                │   OpenAI GPT    │
│   Gotify        │                │   Server         │                │   Analysis      │
│   Notifications │                │   Port 8000      │                │   Engine        │
└─────────────────┘                └──────────────────┘                └─────────────────┘
```

## 🎯 Features

### AI Agent Capabilities
- **Event Analysis**: AI analyzes Proxmox events using GPT-4o-mini
- **Smart Notifications**: Context-aware notifications with severity assessment
- **Automated Actions**: Execute Proxmox commands based on AI decisions
- **Health Monitoring**: Continuous monitoring of MCP server status
- **Event History**: Maintains event context for better AI decision making

### HTTP API Endpoints
- `GET /status` - MCP system status
- `GET /events/recent` - Recent event history
- `POST /events/inject` - Inject custom events
- `POST /notifications/send` - Send notifications
- `POST /proxmox/action` - Execute Proxmox actions
- `POST /simulate/event` - Simulate events for testing

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install FastAPI and related packages
pip install fastapi uvicorn pydantic requests

# Or add to requirements.txt
echo "fastapi\nuvicorn\npydantic\nrequests" >> requirements.txt
pip install -r requirements.txt
```

### 2. Start the MCP Interface

```bash
# Start the HTTP API server
python n8n_agent_interface.py

# Server will be available at:
# - API: http://localhost:8000
# - Docs: http://localhost:8000/docs
```

### 3. Set Up n8n Workflow

1. **Import Workflow**:
   - Open n8n (local or cloud)
   - Go to "Workflows" → "Import from File"
   - Select `n8n_workflow_proxmox_ai_agent.json`

2. **Configure AI Integration**:
   - Open "AI Agent Analysis" node
   - Add your OpenAI API key
   - Adjust the AI model if needed (default: gpt-4o-mini)

3. **Update Endpoints**:
   - Verify HTTP Request nodes point to `http://localhost:8000`
   - Adjust if running on different host/port

4. **Activate Workflow**:
   - Click "Active" toggle in n8n
   - The workflow will now respond to events

### 4. Test the Integration

```bash
# Run the test suite
python setup_n8n_agent.py

# Or test manually:
curl -X POST "http://localhost:8000/simulate/event?event_type=vm_start"
```

## 📋 n8n Workflow Breakdown

### Core Workflow Nodes

1. **Webhook - Receive Event**
   - Receives Proxmox events via HTTP webhook
   - Triggers the AI analysis pipeline

2. **Get Recent Events**
   - Fetches recent event history for context
   - Helps AI make better decisions

3. **AI Agent Analysis**
   - **OpenAI GPT-4o-mini** analyzes the event
   - Determines severity and required actions
   - Returns JSON with recommendations

4. **Check if Notification Needed**
   - Routes events that require notifications
   - Based on AI analysis results

5. **Send AI Notification**
   - Sends enhanced notifications with AI analysis
   - Includes original event + AI insights

6. **Check if Critical Event**
   - Identifies critical events requiring immediate action
   - Routes to emergency response system

7. **Execute Emergency Action**
   - Executes automated Proxmox commands
   - For critical events only (mock implementation)

8. **Health Check Timer**
   - Monitors MCP server every 5 minutes
   - Ensures system availability

### AI Prompt Engineering

The AI agent uses a sophisticated system prompt:

```text
You are a Proxmox infrastructure AI agent. Analyze Proxmox events and determine appropriate automated responses.

Your capabilities:
1. Monitor VM states and performance
2. Respond to backup events  
3. Handle storage warnings
4. React to node failures
5. Send notifications for critical events

For each event, decide:
- Severity level (info/warning/critical)
- Required actions (none/restart/backup/notify)
- Notification channels needed
- Follow-up monitoring required
```

## 🔧 Configuration

### Environment Variables (.env)

Ensure your MCP server has these configured:
```env
# Discord Integration
DISCORD_OUT_ENABLED=True
DISCORD_OUT_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook

# Gotify Integration  
GOTIFY_OUT_ENABLED=True
GOTIFY_OUT_SERVER_URL=http://your-gotify-server:port
GOTIFY_OUT_APP_TOKEN=your-app-token

# Event Listeners
EVENT_WS_ENABLED=True
EVENT_SYSLOG_ENABLED=True
DISCORD_IN_ENABLED=True
GOTIFY_IN_ENABLED=True
```

### n8n Configuration

1. **OpenAI API Key**: Required for AI analysis
2. **Webhook URLs**: Update if running on different ports
3. **Notification Channels**: Configure Discord/Gotify webhooks

## 🧪 Testing Scenarios

### 1. VM Lifecycle Events
```bash
# Simulate VM start
curl -X POST "http://localhost:8000/simulate/event?event_type=vm_start"

# Simulate VM stop  
curl -X POST "http://localhost:8000/simulate/event?event_type=vm_stop"
```

### 2. Storage Warnings
```bash
# Simulate storage warning
curl -X POST "http://localhost:8000/simulate/event?event_type=storage_warning"
```

### 3. Critical Events
```bash
# Simulate node error (triggers emergency actions)
curl -X POST "http://localhost:8000/simulate/event?event_type=node_error"
```

### 4. Custom Events
```bash
# Send custom event
curl -X POST "http://localhost:8000/events/inject" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Custom Alert",
    "message": "Custom test message",
    "severity": "warning",
    "vm_id": "999",
    "node": "test-node"
  }'
```

## 🔍 Monitoring & Debugging

### System Status
```bash
# Check MCP system status
curl http://localhost:8000/status

# Get configuration summary
curl http://localhost:8000/config/summary

# View recent events
curl http://localhost:8000/events/recent
```

### n8n Debugging
1. **Execution Log**: Check n8n execution history
2. **Node Outputs**: Inspect data flow between nodes
3. **AI Responses**: Review AI analysis results

### Log Files
- **MCP Server**: Check console output for event processing
- **Interface Server**: Monitor FastAPI logs for API calls
- **n8n**: Use built-in execution logging

## 🚨 Production Considerations

### Security
- **API Authentication**: Add API keys for production
- **Network Security**: Use HTTPS and proper firewall rules
- **Input Validation**: Validate all webhook inputs

### Scalability  
- **Rate Limiting**: Implement request rate limiting
- **Event Queue**: Use message queues for high-volume events
- **Database**: Store events in persistent database

### Reliability
- **Error Handling**: Comprehensive error handling and retries
- **Health Checks**: Implement proper health monitoring
- **Backup**: Regular backup of configuration and event history

## 🤝 Integration Examples

### Webhook Integration
Configure Proxmox to send events to n8n webhook:
```
Webhook URL: http://your-n8n-instance/webhook/proxmox-event
Method: POST
Content-Type: application/json
```

### Custom Automations
Extend the workflow with additional nodes:
- **Slack Notifications**: Add Slack integration nodes
- **Email Alerts**: Configure SMTP notifications  
- **Database Logging**: Store events in database
- **Custom Scripts**: Execute custom shell scripts

## 📊 Event Types & AI Responses

| Event Type | AI Analysis | Typical Actions |
|------------|-------------|-----------------|
| `vm_start` | Monitor resource usage | Info notification |
| `vm_stop` | Check if planned shutdown | Warning if unexpected |
| `backup_success` | Verify backup integrity | Info notification |
| `storage_warning` | Assess storage trends | Warning + monitoring |
| `node_error` | Critical infrastructure issue | Emergency notification + action |

## 🔮 Future Enhancements

- **Machine Learning**: Train custom models on event patterns
- **Predictive Analytics**: Predict failures before they occur
- **Auto-Remediation**: Fully automated problem resolution
- **Multi-Tenant**: Support multiple Proxmox clusters
- **Dashboard**: Real-time monitoring dashboard
- **Integration Hub**: Connect to more external systems

---

## 🆘 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if interface is running
   curl http://localhost:8000/status
   
   # Start interface if not running
   python n8n_agent_interface.py
   ```

2. **AI Analysis Fails**
   - Verify OpenAI API key in n8n
   - Check API quotas and limits
   - Review AI prompt configuration

3. **Notifications Not Sending**
   - Check Discord/Gotify webhook URLs
   - Verify MCP server configuration
   - Test notification endpoints directly

4. **Webhook Not Triggering**
   - Verify n8n workflow is active
   - Check webhook URL in workflow
   - Test webhook manually with curl

For more help, check the logs and use the test suite in `setup_n8n_agent.py`!