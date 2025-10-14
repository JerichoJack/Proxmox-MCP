# n8n Workflow Setup Guide

## Overview

This guide provides two n8n workflow files for the Proxmox MCP AI Agent:

1. **`n8n_workflow_proxmox_ai_agent.json`** - Full AI-powered workflow using OpenAI GPT-4o-mini
2. **`n8n_workflow_proxmox_ai_agent_simple.json`** - Rule-based workflow (no AI dependency)

## Quick Start (Recommended: Simple Workflow)

### 1. Import the Simple Workflow

1. Open n8n web interface
2. Click "+" to create new workflow
3. Click "..." menu → "Import from file"
4. Select `n8n_workflow_proxmox_ai_agent_simple.json`
5. Click "Save" to save the workflow

### 2. Configure Webhook URL

After importing, the webhook node will show a URL like:
```
https://your-n8n-instance.com/webhook/proxmox-event
```

Copy this URL - you'll need it for the MCP interface configuration.

### 3. Start MCP Interface

```powershell
# Start the n8n agent interface
python n8n_agent_interface.py
```

### 4. Test the Integration

```powershell
# Run the test suite
python setup_n8n_agent.py
```

## Advanced Setup (AI-Powered Workflow)

### Prerequisites

- OpenAI API account and API key
- n8n instance with HTTP Request node support

### 1. Setup OpenAI Credentials

1. In n8n, go to "Credentials" tab
2. Create new "Header Auth" credential:
   - Name: `OpenAI API Key`
   - Header Name: `Authorization`
   - Header Value: `Bearer YOUR_OPENAI_API_KEY`

### 2. Import AI Workflow

1. Import `n8n_workflow_proxmox_ai_agent.json`
2. Open "AI Agent Analysis" node
3. Configure credentials to use the OpenAI credential you created

### 3. Test AI Integration

The AI workflow provides more sophisticated analysis:
- Context-aware event analysis
- Intelligent severity assessment
- Adaptive response recommendations
- Pattern recognition across multiple events

## Workflow Features

### Both Workflows Include:

1. **Event Processing**
   - Webhook receiver for Proxmox events
   - Recent events context gathering
   - Intelligent analysis (AI or rule-based)

2. **Conditional Actions**
   - Notification routing based on severity
   - Emergency action execution for critical events
   - Webhook response with processing status

3. **Health Monitoring**
   - Periodic MCP status checks
   - System down detection and alerting
   - Automatic recovery simulation

### Simple Workflow Rules:

- **Critical**: Events containing "error" or "fail"
- **Warning**: Events containing "warning" or "warn"
- **Info**: Backup events and general notifications
- **Pattern Detection**: Multiple errors trigger emergency status

### AI Workflow Capabilities:

- **Contextual Analysis**: Considers event history and patterns
- **Adaptive Responses**: Learns from event patterns
- **Rich Reasoning**: Natural language analysis of complex scenarios
- **Proactive Actions**: Anticipates issues based on trends

## Integration with MCP Interface

### Webhook Configuration

Configure your MCP interface to send events to the n8n webhook:

```python
# In your MCP configuration
N8N_WEBHOOK_URL = "https://your-n8n-instance.com/webhook/proxmox-event"
```

### Event Format

The workflow expects events in this format:

```json
{
  "title": "VM 100 backup completed",
  "message": "Backup of VM 100 finished successfully",
  "node": "proxmox-node-01",
  "vm_id": "100",
  "severity": "info",
  "event_type": "backup",
  "timestamp": "2024-10-13T12:00:00Z"
}
```

## Troubleshooting

### Common Issues:

1. **Webhook not receiving events**
   - Check n8n webhook URL in MCP configuration
   - Ensure n8n workflow is activated
   - Verify network connectivity

2. **OpenAI API errors (AI workflow)**
   - Verify API key is correct
   - Check OpenAI API quota and billing
   - Ensure proper credential configuration

3. **MCP interface not responding**
   - Check if `python n8n_agent_interface.py` is running
   - Verify port 8000 is available
   - Check firewall settings

### Testing Commands:

```powershell
# Test webhook directly
curl -X POST "https://your-n8n-instance.com/webhook/proxmox-event" `
  -H "Content-Type: application/json" `
  -d '{
    "title": "Test Event",
    "message": "This is a test event",
    "severity": "info",
    "timestamp": "2024-10-13T12:00:00Z"
  }'

# Test MCP interface
curl http://localhost:8000/status

# Simulate an event
curl -X POST "http://localhost:8000/simulate/event?event_type=vm_start"
```

## Security Considerations

1. **API Keys**: Keep OpenAI API keys secure in n8n credentials
2. **Webhook URLs**: Consider authentication for production webhooks
3. **Network Access**: Restrict access to MCP interface port
4. **Data Privacy**: Review what data is sent to external AI services

## Next Steps

1. **Monitor Performance**: Check n8n execution logs for issues
2. **Customize Rules**: Modify the rule-based analysis for your environment
3. **Add Channels**: Configure additional notification channels (Discord, Gotify)
4. **Scale Up**: Consider multiple workflow instances for high availability

For additional help, refer to the main project documentation in `N8N_AI_AGENT_README.md`.