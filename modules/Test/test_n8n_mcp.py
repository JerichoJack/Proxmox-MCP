#!/usr/bin/env python3
"""
Test MCP server specifically for n8n compatibility
"""
import requests
import json
import time

def test_n8n_mcp_flow():
    """Test the exact MCP flow that n8n would use"""
    
    base_url = "http://192.168.4.14:8888/mcp"
    
    print("🧪 Testing n8n MCP Client Compatibility")
    print("=" * 50)
    
    # Test 1: Initialize connection (what n8n does first)
    print("1. Testing MCP initialization (n8n style)...")
    
    init_request = {
        "jsonrpc": "2.0",
        "id": "init-1",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "experimental": {},
                "sampling": {}
            },
            "clientInfo": {
                "name": "@n8n/n8n-nodes-langchain",
                "version": "1.2.0"
            }
        }
    }
    
    try:
        response = requests.post(base_url, 
                               json=init_request,
                               headers={
                                   'Content-Type': 'application/json',
                                   'Accept': 'application/json',
                                   'User-Agent': 'n8n/1.0.0'
                               },
                               timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Initialize successful")
            print(f"   📄 Response: {json.dumps(result, indent=2)}")
            
            # Check if response has expected structure
            if 'result' in result and 'capabilities' in result['result']:
                print(f"   ✅ Response structure is correct")
            else:
                print(f"   ⚠️  Response structure may be incompatible with n8n")
                
        else:
            print(f"   ❌ Initialize failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return False
    
    # Test 2: Send initialized message (n8n does this after init)
    print("\n2. Testing initialized acknowledgment...")
    
    initialized_request = {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {}
    }
    
    try:
        response = requests.post(base_url,
                               json=initialized_request,
                               headers={
                                   'Content-Type': 'application/json',
                                   'Accept': 'application/json'
                               },
                               timeout=10)
        
        print(f"   Status Code: {response.status_code}")
        if response.status_code == 200:
            print(f"   ✅ Initialized acknowledgment successful")
        else:
            print(f"   ⚠️  Initialized response: {response.status_code}")
            
    except Exception as e:
        print(f"   ⚠️  Initialized error (may be normal): {e}")
    
    # Test 3: List tools (n8n does this to discover available tools)
    print("\n3. Testing tools/list...")
    
    tools_request = {
        "jsonrpc": "2.0",
        "id": "tools-1",
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(base_url,
                               json=tools_request,
                               headers={
                                   'Content-Type': 'application/json',
                                   'Accept': 'application/json'
                               },
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if 'result' in result and 'tools' in result['result']:
                tools = result['result']['tools']
                print(f"   ✅ Tools list successful - found {len(tools)} tools")
                for tool in tools[:3]:  # Show first 3 tools
                    print(f"      • {tool['name']}")
                if len(tools) > 3:
                    print(f"      ... and {len(tools)-3} more")
            else:
                print(f"   ❌ Tools list format error: {result}")
                return False
        else:
            print(f"   ❌ Tools list failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Tools list error: {e}")
        return False
    
    # Test 4: Call a simple tool (test actual tool execution)
    print("\n4. Testing tool execution...")
    
    tool_call_request = {
        "jsonrpc": "2.0",
        "id": "call-1", 
        "method": "tools/call",
        "params": {
            "name": "get_node_status",
            "arguments": {
                "node_type": "all"
            }
        }
    }
    
    try:
        response = requests.post(base_url,
                               json=tool_call_request,
                               headers={
                                   'Content-Type': 'application/json',
                                   'Accept': 'application/json'
                               },
                               timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if 'result' in result and 'content' in result['result']:
                print(f"   ✅ Tool execution successful")
                content = result['result']['content'][0]['text']
                print(f"   📊 Tool response (first 200 chars): {content[:200]}...")
            else:
                print(f"   ❌ Tool execution format error: {result}")
                return False
        else:
            print(f"   ❌ Tool execution failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Tool execution error: {e}")
        return False
    
    print(f"\n✅ All MCP tests passed! n8n should be able to connect.")
    print(f"🔧 If n8n still fails, the issue may be:")
    print(f"   • n8n version compatibility")
    print(f"   • Network firewall/proxy issues")  
    print(f"   • n8n MCP Client node configuration")
    
    return True

def test_alternative_endpoints():
    """Test if alternative endpoints work better for n8n"""
    
    endpoints = [
        "http://192.168.4.14:8888/mcp",
        "http://192.168.4.14:8888/ws",
    ]
    
    print(f"\n🔍 Testing alternative endpoints...")
    
    for endpoint in endpoints:
        print(f"\n   Testing: {endpoint}")
        try:
            response = requests.post(endpoint,
                                   json={
                                       "jsonrpc": "2.0",
                                       "id": 1,
                                       "method": "initialize",
                                       "params": {
                                           "protocolVersion": "2024-11-05",
                                           "capabilities": {},
                                           "clientInfo": {"name": "test", "version": "1.0.0"}
                                       }
                                   },
                                   timeout=5)
            
            if response.status_code == 200:
                print(f"      ✅ {endpoint} works")
            else:
                print(f"      ❌ {endpoint} failed: {response.status_code}")
                
        except Exception as e:
            print(f"      ❌ {endpoint} error: {e}")

if __name__ == "__main__":
    test_n8n_mcp_flow()
    test_alternative_endpoints()