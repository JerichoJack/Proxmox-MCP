#!/usr/bin/env python3
"""
Setup and test script for n8n AI Agent integration with Proxmox MCP Server.
This script helps you set up the complete AI agent workflow.
"""
import asyncio
import json
import time
from datetime import datetime

import requests


def print_header(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def check_requirements():
    """Check if required dependencies are available."""
    print_header("Checking Requirements")
    
    requirements = []
    
    try:
        import fastapi
        print("✅ FastAPI available")
    except ImportError:
        requirements.append("fastapi")
        print("❌ FastAPI not installed")
    
    try:
        import uvicorn
        print("✅ Uvicorn available")
    except ImportError:
        requirements.append("uvicorn")
        print("❌ Uvicorn not installed")
    
    try:
        import pydantic
        print("✅ Pydantic available")
    except ImportError:
        requirements.append("pydantic")
        print("❌ Pydantic not installed")
    
    if requirements:
        print(f"\n📦 Install missing packages:")
        print(f"   pip install {' '.join(requirements)}")
        return False
    
    print("\n✅ All requirements satisfied!")
    return True

def test_mcp_interface():
    """Test the MCP interface endpoints."""
    print_header("Testing MCP Interface")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/status",
        "/config/summary",
        "/events/recent"
    ]
    
    print("🔍 Testing MCP interface endpoints...")
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {endpoint}: OK")
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Connection refused (Is the interface running?)")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")

def simulate_events():
    """Simulate various Proxmox events for testing."""
    print_header("Simulating Proxmox Events")
    
    base_url = "http://localhost:8000"
    events = [
        "vm_start",
        "backup_success", 
        "storage_warning",
        "node_error"
    ]
    
    for event_type in events:
        try:
            response = requests.post(
                f"{base_url}/simulate/event",
                params={"event_type": event_type},
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Simulated {event_type}: {data['message']}")
            else:
                print(f"❌ Failed to simulate {event_type}")
                
            time.sleep(1)  # Delay between events
            
        except Exception as e:
            print(f"❌ Error simulating {event_type}: {e}")

def send_test_notification():
    """Send a test notification through the MCP system."""
    print_header("Testing Notification System")
    
    base_url = "http://localhost:8000"
    
    notification = {
        "title": "n8n AI Agent Test",
        "message": "🤖 This is a test notification from the n8n AI Agent integration!",
        "channels": ["discord", "gotify"],
        "priority": "info",
        "metadata": {
            "source": "n8n_test",
            "test_type": "integration_test"
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/notifications/send",
            json=notification,
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Test notification sent successfully!")
            print(f"   Response: {response.json()['message']}")
        else:
            print(f"❌ Failed to send notification: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error sending notification: {e}")

def create_n8n_webhook_test():
    """Create a test that mimics n8n webhook calls."""
    print_header("Testing n8n Webhook Integration")
    
    # This simulates what n8n would send to the webhook
    webhook_data = {
        "title": "VM Migration Alert",
        "message": "VM 150 (production-web) migration from pve-node1 to pve-node2 completed",
        "severity": "info",
        "vm_id": "150",
        "node": "pve-node2",
        "event_type": "vm_migrate",
        "timestamp": datetime.now().isoformat()
    }
    
    print("📡 Simulating n8n webhook call...")
    print(f"   Event: {webhook_data['title']}")
    print(f"   VM ID: {webhook_data['vm_id']}")
    print(f"   Node: {webhook_data['node']}")
    
    # In a real scenario, this would be the webhook endpoint that n8n calls
    # For testing, we'll inject it directly
    try:
        response = requests.post(
            "http://localhost:8000/events/inject",
            json=webhook_data,
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Webhook event processed successfully!")
            print(f"   Event ID: {result['data']['id']}")
        else:
            print(f"❌ Webhook test failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Webhook test error: {e}")

def show_setup_instructions():
    """Show setup instructions for the complete integration."""
    print_header("Setup Instructions")
    
    print("""
🚀 Complete n8n AI Agent Setup:

1. Install Required Dependencies:
   pip install fastapi uvicorn pydantic

2. Start the MCP Interface Server:
   python n8n_agent_interface.py
   
   This will start the HTTP API at http://localhost:8000
   API docs will be available at http://localhost:8000/docs

3. Import n8n Workflow:
   - Open n8n (local or cloud instance)
   - Go to Workflows > Import from File
   - Import: n8n_workflow_proxmox_ai_agent.json
   
4. Configure n8n Workflow:
   - Update the HTTP Request node URLs if needed
   - Add your OpenAI API key to the AI Agent Analysis node
   - Activate the workflow

5. Test the Integration:
   - Use the webhook endpoint in the workflow to send test events
   - Monitor the MCP interface logs
   - Check Discord/Gotify for AI-generated notifications

6. Configure Webhook Integration:
   - Copy the webhook URL from n8n workflow
   - Configure your Proxmox systems to send events to this webhook
   - Or use the MCP interface to inject events programmatically

📊 Monitoring:
   - MCP Status: http://localhost:8000/status
   - Recent Events: http://localhost:8000/events/recent
   - API Documentation: http://localhost:8000/docs
""")

def main():
    print("🤖 Proxmox MCP Server - n8n AI Agent Setup & Test")
    
    while True:
        print(f"\n{'='*40}")
        print("Choose an option:")
        print("1. Check requirements")
        print("2. Test MCP interface")
        print("3. Simulate Proxmox events")
        print("4. Send test notification")
        print("5. Test n8n webhook integration")
        print("6. Show setup instructions")
        print("7. Exit")
        
        choice = input("\nEnter your choice (1-7): ").strip()
        
        if choice == "1":
            check_requirements()
        elif choice == "2":
            test_mcp_interface()
        elif choice == "3":
            simulate_events()
        elif choice == "4":
            send_test_notification()
        elif choice == "5":
            create_n8n_webhook_test()
        elif choice == "6":
            show_setup_instructions()
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()