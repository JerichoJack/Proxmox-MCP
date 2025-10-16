#!/usr/bin/env python3
"""Quick test of MCP server"""
import requests
import json

print("Testing MCP Server at http://localhost:8888/mcp")
print("=" * 60)

# Test get_node_status tool
print("\n1. Testing get_node_status tool...")
response = requests.post(
    'http://localhost:8888/mcp',
    json={
        'jsonrpc': '2.0',
        'id': 1,
        'method': 'tools/call',
        'params': {
            'name': 'get_node_status',
            'arguments': {'node_type': 'all'}
        }
    }
)

print(f"   Status Code: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"   Response:")
    print(json.dumps(result, indent=2))
else:
    print(f"   Error: {response.text}")

print("\n" + "=" * 60)
