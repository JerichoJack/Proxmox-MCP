#!/usr/bin/env python3
"""
Test Proxmox API authentication to diagnose connection issues
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test configuration
print("=" * 60)
print("PROXMOX AUTHENTICATION TEST")
print("=" * 60)

# Check environment variables
print("\n📋 Environment Variables:")
print(f"  PROXIMO_HOST: {os.getenv('PROXIMO_HOST')}")
print(f"  PROXIMO_USER: {os.getenv('PROXIMO_USER')}")
print(f"  PROXIMO_TOKEN_NAME: {os.getenv('PROXIMO_TOKEN_NAME')}")
print(f"  PROXIMO_TOKEN_VALUE: {'***' + os.getenv('PROXIMO_TOKEN_VALUE', '')[-8:] if os.getenv('PROXIMO_TOKEN_VALUE') else 'NOT SET'}")

# Test network connectivity first
host = os.getenv('PROXIMO_HOST', '')
print(f"\n🌐 Testing network connectivity to {host}:8006...")
try:
    response = requests.get(f"https://{host}:8006", verify=False, timeout=5)
    print(f"✅ Host is reachable (HTTP {response.status_code})")
except requests.exceptions.Timeout:
    print(f"❌ Connection timeout - host may be down or unreachable")
    exit(1)
except requests.exceptions.ConnectionError as e:
    print(f"❌ Connection error: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️  Unexpected error: {e}")

# Try direct API call with token
print(f"\n🔑 Testing API Token Authentication...")
user = os.getenv('PROXIMO_USER', 'root@pam')
token_name = os.getenv('PROXIMO_TOKEN_NAME', '')
token_value = os.getenv('PROXIMO_TOKEN_VALUE', '')

# Format: PVEAPIToken=USER@REALM!TOKENID=UUID
auth_header = f"PVEAPIToken={user}!{token_name}={token_value}"

try:
    response = requests.get(
        f"https://{host}:8006/api2/json/version",
        headers={"Authorization": auth_header},
        verify=False,
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API Token authentication successful!")
        print(f"   Proxmox Version: {data['data'].get('version', 'unknown')}")
        print(f"   Release: {data['data'].get('release', 'unknown')}")
    elif response.status_code == 401:
        print(f"❌ Authentication failed (401 Unauthorized)")
        print(f"   The API token is invalid or doesn't have permissions")
        print(f"\n💡 Action needed:")
        print(f"   1. Log into Proxmox web UI: https://{host}:8006")
        print(f"   2. Go to: Datacenter → Permissions → API Tokens")
        print(f"   3. Find token: {user}!{token_name}")
        print(f"   4. If it doesn't exist, create a new one and update .env")
        print(f"   5. Ensure the token has 'Administrator' or appropriate privileges")
    else:
        print(f"⚠️  Unexpected response: HTTP {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ API call failed: {e}")

# Try to import proxmoxer
try:
    from proxmoxer import ProxmoxAPI
    print("\n✅ proxmoxer library imported successfully")
except ImportError:
    print("\n❌ proxmoxer library not installed")
    print("   Install with: pip install proxmoxer")
    exit(1)

# Test connection with API token using CORRECT proxmoxer syntax
print("\n🔄 Testing Proxmox API connection with proxmoxer library...")
print(f"   Host: {host}")
print(f"   User: {user}")
print(f"   Token Name: {token_name}")

try:
    print(f"\n🔑 ProxmoxAPI Authentication (CORRECT METHOD):")
    print(f"   Using token_name as separate parameter")
    
    # CORRECT way: pass user, token_name, and token_value separately
    proxmox = ProxmoxAPI(
        host,
        user=user,
        token_name=token_name,
        token_value=token_value,
        verify_ssl=False
    )
    
    # Test the connection by getting version
    version = proxmox.version.get()
    
    print(f"\n✅ Successfully connected to Proxmox with proxmoxer!")
    print(f"   Version: {version.get('version', 'unknown')}")
    print(f"   Release: {version.get('release', 'unknown')}")
    
    # Try to get node list
    try:
        nodes = proxmox.nodes.get()
        print(f"\n📊 Found {len(nodes)} node(s):")
        for node in nodes:
            status_icon = "🟢" if node['status'] == 'online' else "🔴"
            print(f"   {status_icon} {node['node']}: {node['status']} (uptime: {node.get('uptime', 0)}s)")
    except Exception as e:
        print(f"\n⚠️  Could not retrieve nodes: {e}")
    
except Exception as e:
    print(f"\n❌ proxmoxer connection failed!")
    print(f"   Error: {e}")
    print(f"\n💡 This means the MCP server needs to be fixed to pass")
    print(f"   user, token_name, and token_value as SEPARATE parameters")

print("\n" + "=" * 60)
