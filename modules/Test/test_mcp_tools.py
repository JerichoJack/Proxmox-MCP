#!/usr/bin/env python3
"""
Test MCP tools functionality
"""
import requests
import json

def test_mcp_tools():
    """Test MCP server tools"""
    
    base_url = "http://192.168.4.14:8888/mcp"
    
    print("🧪 Testing MCP Tools on 192.168.4.14:8888")
    print("=" * 50)
    
    # Step 1: Initialize
    print("1. Initializing MCP connection...")
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize", 
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "n8n-test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = requests.post(base_url, json=init_request)
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Initialization successful")
        print(f"   📊 Server: {result['result']['serverInfo']['name']}")
    else:
        print(f"   ❌ Initialization failed: {response.status_code}")
        return
    
    # Step 2: List available tools
    print("\n2. Listing available tools...")
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = requests.post(base_url, json=tools_request)
    if response.status_code == 200:
        result = response.json()
        tools = result.get('result', {}).get('tools', [])
        print(f"   ✅ Found {len(tools)} tools:")
        for tool in tools:
            print(f"      • {tool['name']}: {tool['description']}")
    else:
        print(f"   ❌ Tools list failed: {response.status_code}")
        return
    
    # Step 3: Test get_node_status tool
    print("\n3. Testing get_node_status tool...")
    node_status_request = {
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
    
    response = requests.post(base_url, json=node_status_request)
    if response.status_code == 200:
        result = response.json()
        if 'result' in result:
            content = result['result']['content'][0]['text']
            print(f"   ✅ Node status retrieved successfully")
            print(f"   📊 Response: {content}")
            
            # Try to parse as JSON if possible
            try:
                nodes_data = json.loads(content)
                if isinstance(nodes_data, dict):
                    print(f"   📊 Found {len(nodes_data)} nodes:")
                    for node_name, node_info in nodes_data.items():
                        status_icon = "🟢" if node_info.get('status') == 'online' else "🔴"
                        print(f"      {status_icon} {node_name} ({node_info.get('type', 'unknown')})")
                else:
                    print(f"   📋 Node data: {nodes_data}")
            except json.JSONDecodeError:
                # Content might be plain text response
                print(f"   📋 Raw response: {content}")
        else:
            print(f"   ⚠️ Unexpected response format: {result}")
    else:
        print(f"   ❌ Node status failed: {response.status_code}")
        print(f"   📄 Response: {response.text}")

    print(f"\n✅ MCP server is ready for n8n integration!")
    print(f"📋 Use endpoint: http://192.168.4.14:8888/mcp")

if __name__ == "__main__":
    test_mcp_tools()