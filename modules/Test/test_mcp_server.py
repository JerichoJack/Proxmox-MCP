#!/usr/bin/env python3
"""
Test script for the Proxmox MCP HTTP Server
This script tests the basic connectivity and tool functionality
"""
import asyncio
import aiohttp
import json
import sys

async def test_mcp_server():
    """Test the MCP server connectivity and basic functionality"""
    base_url = "http://0.0.0.0:8888"
    
    print("🧪 Testing Proxmox MCP Server")
    print(f"📡 Target: {base_url}")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Health Check
            print("1️⃣ Testing health endpoint...")
            async with session.get(f"{base_url}/health") as response:
                if response.status == 200:
                    health_data = await response.json()
                    print("✅ Health check passed")
                    print(f"   Status: {health_data.get('status')}")
                    print(f"   Server: {health_data.get('server')}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False
            
            # Test 2: MCP Initialize
            print("\n2️⃣ Testing MCP initialization...")
            init_payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "test-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            async with session.post(f"{base_url}/mcp", json=init_payload) as response:
                if response.status == 200:
                    init_data = await response.json()
                    print("✅ MCP initialization successful")
                    print(f"   Protocol: {init_data.get('result', {}).get('protocolVersion')}")
                    print(f"   Server: {init_data.get('result', {}).get('serverInfo', {}).get('name')}")
                else:
                    print(f"❌ MCP initialization failed: {response.status}")
                    print(f"   Response: {await response.text()}")
                    return False
            
            # Test 3: List Tools
            print("\n3️⃣ Testing tools list...")
            tools_payload = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            async with session.post(f"{base_url}/mcp", json=tools_payload) as response:
                if response.status == 200:
                    tools_data = await response.json()
                    tools = tools_data.get('result', {}).get('tools', [])
                    print(f"✅ Found {len(tools)} tools:")
                    for tool in tools:
                        print(f"   📋 {tool.get('name')}: {tool.get('description')}")
                else:
                    print(f"❌ Tools list failed: {response.status}")
                    print(f"   Response: {await response.text()}")
                    return False
            
            # Test 4: Call get_node_status tool
            print("\n4️⃣ Testing get_node_status tool...")
            node_status_payload = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_node_status",
                    "arguments": {
                        "node_type": "all"
                    }
                }
            }
            
            async with session.post(f"{base_url}/mcp", json=node_status_payload) as response:
                if response.status == 200:
                    status_data = await response.json()
                    content = status_data.get('result', {}).get('content', [])
                    if content:
                        result_text = content[0].get('text', '')
                        print("✅ Node status retrieved:")
                        print(f"   📊 Result: {result_text[:200]}{'...' if len(result_text) > 200 else ''}")
                    else:
                        print("⚠️ Node status returned empty content")
                else:
                    print(f"❌ Node status failed: {response.status}")
                    print(f"   Response: {await response.text()}")
                    return False
            
            print("\n🎉 All tests passed! MCP server is working correctly.")
            return True
            
        except aiohttp.ClientConnectorError as e:
            print(f"❌ Connection failed: {e}")
            print("💡 Make sure the MCP server is running with:")
            print(f"   python mcp_server_http.py --host 192.168.4.14 --port 8888")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False

async def main():
    """Main test function"""
    success = await test_mcp_server()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())