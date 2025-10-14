#!/usr/bin/env python3
"""
Simple test script to verify Discord integration functionality.
This script tests both Discord input and output capabilities.
"""
import asyncio
from datetime import datetime

import aiohttp


async def test_discord_webhook(webhook_url, test_type="output"):
    """Test Discord webhook functionality."""
    print(f"=== Testing Discord {test_type.title()} Webhook ===")
    
    if not webhook_url:
        print("❌ No webhook URL provided")
        return False
        
    # Create test payload based on type
    if test_type == "output":
        payload = {
            "embeds": [{
                "title": "🧪 Discord Output Test",
                "description": "This is a test message from the Proxmox MCP Discord notifier.",
                "color": 0x00FF00,  # Green
                "fields": [
                    {
                        "name": "Test Type",
                        "value": "Output Notifier Test",
                        "inline": True
                    },
                    {
                        "name": "Source",
                        "value": "Proxmox MCP Server",
                        "inline": True
                    },
                    {
                        "name": "VM ID",
                        "value": "100",
                        "inline": True
                    },
                    {
                        "name": "Node",
                        "value": "pve-test",
                        "inline": True
                    }
                ],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Proxmox MCP Test | Host: test-server"
                }
            }],
            "username": "Proxmox MCP Test",
            "content": "🔔 **Test Notification**: Discord output integration successful!"
        }
    else:  # input test
        payload = {
            "embeds": [{
                "title": "🧪 Discord Input Test",
                "description": "This message tests Discord input listener connectivity.",
                "color": 0x0099FF,  # Blue
                "timestamp": datetime.utcnow().isoformat()
            }],
            "username": "Proxmox MCP Input Test",
            "content": "📥 **Input Test**: Testing Discord webhook for input monitoring..."
        }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status in [200, 204]:
                    print(f"✅ Discord {test_type} webhook test successful!")
                    print(f"   Status: {response.status}")
                    return True
                else:
                    text = await response.text()
                    print(f"❌ Discord {test_type} webhook test failed!")
                    print(f"   Status: {response.status}")
                    print(f"   Response: {text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Discord {test_type} webhook test failed with error: {e}")
        return False

async def send_sample_proxmox_events(webhook_url):
    """Send sample Proxmox events to test Discord formatting."""
    print("\n=== Sending Sample Proxmox Events ===")
    
    sample_events = [
        {
            "title": "VM Started",
            "message": "VM 100 (web-server) started successfully on node pve-main",
            "color": 0x00FF00,  # Green
            "fields": [
                {"name": "VM ID", "value": "100", "inline": True},
                {"name": "VM Name", "value": "web-server", "inline": True},
                {"name": "Node", "value": "pve-main", "inline": True},
                {"name": "Event Type", "value": "VM Start", "inline": True}
            ]
        },
        {
            "title": "Backup Completed",
            "message": "Backup of VM 101 (database) completed successfully",
            "color": 0x00FF00,  # Green
            "fields": [
                {"name": "VM ID", "value": "101", "inline": True},
                {"name": "VM Name", "value": "database", "inline": True},
                {"name": "Status", "value": "Success", "inline": True},
                {"name": "Duration", "value": "45 minutes", "inline": True}
            ]
        },
        {
            "title": "Storage Warning", 
            "message": "Storage 'local-lvm' usage is above 80%",
            "color": 0xFFA500,  # Orange
            "fields": [
                {"name": "Storage", "value": "local-lvm", "inline": True},
                {"name": "Usage", "value": "85%", "inline": True},
                {"name": "Node", "value": "pve-main", "inline": True}
            ]
        },
        {
            "title": "Node Fenced",
            "message": "Node pve-node2 has been fenced due to network issues",
            "color": 0xFF0000,  # Red
            "fields": [
                {"name": "Node", "value": "pve-node2", "inline": True},
                {"name": "Reason", "value": "Network timeout", "inline": True},
                {"name": "Severity", "value": "Critical", "inline": True}
            ]
        }
    ]
    
    for i, event in enumerate(sample_events, 1):
        payload = {
            "embeds": [{
                "title": event["title"],
                "description": event["message"],
                "color": event["color"],
                "fields": event["fields"],
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": f"Proxmox MCP | Event {i}/4"
                }
            }],
            "username": "Proxmox MCP"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as resp:
                    if resp.status in [200, 204]:
                        print(f"✅ Event {i}: {event['title']}")
                    else:
                        print(f"❌ Event {i} failed: HTTP {resp.status}")
                        
            await asyncio.sleep(2)  # Delay between messages
            
        except Exception as e:
            print(f"❌ Event {i} error: {e}")

async def main():
    print("🧪 Discord Integration Test Script")
    print("=" * 50)
    
    # Get webhook URLs from user
    print("\n📝 Please provide your Discord webhook URLs:")
    print("(You can create webhooks in Discord: Server Settings > Integrations > Webhooks)")
    
    output_webhook = input("Discord Output Webhook URL (press Enter to skip): ").strip()
    input_webhook = input("Discord Input Webhook URL (press Enter to skip): ").strip()
    
    results = []
    
    # Test output webhook
    if output_webhook:
        print(f"\n🔍 Testing output webhook...")
        result = await test_discord_webhook(output_webhook, "output")
        results.append(("Output", result))
        
        # Send sample events if output test passed
        if result:
            print(f"\n📤 Sending sample Proxmox events...")
            await send_sample_proxmox_events(output_webhook)
    
    # Test input webhook  
    if input_webhook:
        print(f"\n🔍 Testing input webhook...")
        result = await test_discord_webhook(input_webhook, "input")
        results.append(("Input", result))
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print("=" * 30)
    for test_type, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_type} Webhook: {status}")
    
    if not output_webhook and not input_webhook:
        print("⚠️  No webhook URLs provided - no tests performed")
        print("\nTo test Discord integration:")
        print("1. Create Discord webhooks in your server")
        print("2. Configure DISCORD_OUT_WEBHOOK_URL and DISCORD_IN_WEBHOOK_URL in .env")
        print("3. Run: python main.py --test-connection")
    
    print(f"\n🎯 Next steps:")
    print("1. Update your .env file with working webhook URLs")
    print("2. Enable Discord in configuration: DISCORD_OUT_ENABLED=True")
    print("3. Test with: python main.py --test-connection")

if __name__ == "__main__":
    asyncio.run(main())