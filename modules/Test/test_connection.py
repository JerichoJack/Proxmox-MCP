#!/usr/bin/env python3
"""
Test connectivity to the MCP server from different hosts/IPs
"""
import requests
import json
import sys
import time

def test_endpoint(url, description):
    """Test a specific endpoint URL"""
    print(f"\n🧪 Testing {description}")
    print(f"   URL: {url}")
    
    try:
        # Test health endpoint first
        health_url = url.replace('/mcp', '/health')
        print(f"   Health check: {health_url}")
        
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Health check successful: {response.text.strip()}")
        else:
            print(f"   ❌ Health check failed: HTTP {response.status_code}")
            return False
            
        # Test MCP endpoint
        print(f"   MCP endpoint: {url}")
        mcp_request = {
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
        
        response = requests.post(url, 
                               json=mcp_request, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                print(f"   ✅ MCP connection successful!")
                print(f"   📊 Server capabilities: {result['result'].get('capabilities', {})}")
                return True
            else:
                print(f"   ⚠️  MCP response unexpected: {result}")
                return False
        else:
            print(f"   ❌ MCP connection failed: HTTP {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection refused - server not reachable")
        return False
    except requests.exceptions.Timeout:
        print(f"   ❌ Connection timeout - server not responding")
        return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def main():
    print("🔌 MCP Server Connection Test")
    print("=" * 50)
    
    # List of potential endpoints to test
    endpoints = [
        ("http://localhost:8888/mcp", "Local connection (localhost)"),
        ("http://127.0.0.1:8888/mcp", "Local connection (127.0.0.1)"),
        ("http://GPU-Server:8888/mcp", "Hostname connection (GPU-Server)"),
    ]
    
    # Try to guess local IP if running on Windows
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        endpoints.append((f"http://{local_ip}:8888/mcp", f"Local IP connection ({local_ip})"))
    except:
        pass
    
    # Add common private network ranges
    common_ips = [
        "192.168.1.100", "192.168.1.10", "192.168.1.20",
        "192.168.4.14", "192.168.0.100", "192.168.0.10",
        "10.0.0.10", "10.0.0.100", "172.16.0.10"
    ]
    
    for ip in common_ips:
        endpoints.append((f"http://{ip}:8888/mcp", f"Common IP ({ip})"))
    
    successful_endpoints = []
    
    for url, description in endpoints:
        if test_endpoint(url, description):
            successful_endpoints.append(url)
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    
    if successful_endpoints:
        print(f"✅ Found {len(successful_endpoints)} working endpoint(s):")
        for endpoint in successful_endpoints:
            print(f"   • {endpoint}")
        
        print(f"\n🔧 UPDATE N8N CONFIGURATION:")
        print(f"   Set MCP Client endpoint to: {successful_endpoints[0]}")
        
    else:
        print("❌ No working endpoints found!")
        print("\n💡 TROUBLESHOOTING TIPS:")
        print("   1. Ensure the MCP server is running on GPU-Server")
        print("   2. Check firewall settings (port 8888)")
        print("   3. Verify the server is binding to 0.0.0.0:8888")
        print("   4. Run this test from the same network as n8n")
        print("\n🔍 MANUAL CHECK:")
        print("   Run on GPU-Server: netstat -tlnp | grep 8888")
        print("   Should show: 0.0.0.0:8888 LISTEN")

if __name__ == "__main__":
    main()