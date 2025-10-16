#!/usr/bin/env python3
"""
Test script for the Enhanced Proxmox MCP Server
This script verifies that all enhanced functionality works correctly.
"""
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from core.config import MCPConfig
from core.proxmox_api import ProxmoxAPIManager, ProxmoxAPIClient
from core.api_tester import test_nodes

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("test_enhanced_mcp")

async def test_basic_connectivity():
    """Test basic connectivity to all configured nodes"""
    print("\n🔗 Testing Basic Connectivity")
    print("=" * 50)
    
    try:
        config = MCPConfig(".env")
        success, results = await test_nodes(config)
        
        print(f"Overall Success: {success}")
        print(f"Nodes Tested: {len(results)}")
        
        for result in results:
            status = "✅" if result.get("success") else "❌"
            node_name = result.get("node_name", "unknown")
            host = result.get("host", "unknown")
            node_type = result.get("type", "unknown")
            
            print(f"  {status} {node_name} ({node_type}) - {host}")
            if not result.get("success"):
                print(f"    Error: {result.get('error', 'Unknown error')}")
        
        return success, results
    except Exception as e:
        print(f"❌ Connectivity test failed: {e}")
        return False, []

async def test_api_manager():
    """Test the ProxmoxAPIManager functionality"""
    print("\n🔧 Testing API Manager")
    print("=" * 50)
    
    try:
        config = MCPConfig(".env")
        api_manager = ProxmoxAPIManager(config)
        
        print(f"PVE Clients Connected: {len(api_manager.pve_clients)}")
        print(f"PBS Clients Connected: {len(api_manager.pbs_clients)}")
        print(f"Total Clients: {len(api_manager.get_all_clients())}")
        
        # Test getting nodes
        if api_manager.get_all_clients():
            print("\n📋 Testing get_nodes operation...")
            
            async def get_nodes_from_client(client):
                return await client.get_nodes()
            
            results = await api_manager.aggregate_results(get_nodes_from_client)
            print(f"Nodes retrieved: {len(results)}")
            
            for i, result in enumerate(results[:3]):  # Show first 3 results
                if "error" not in result:
                    print(f"  Node {i+1}: {result.get('host', 'unknown')}")
                else:
                    print(f"  Node {i+1}: Error - {result.get('error')}")
        
        return True
    except Exception as e:
        print(f"❌ API Manager test failed: {e}")
        return False

async def test_vm_operations():
    """Test VM-related operations"""
    print("\n🖥️  Testing VM Operations")
    print("=" * 50)
    
    try:
        config = MCPConfig(".env")
        api_manager = ProxmoxAPIManager(config)
        
        if not api_manager.pve_clients:
            print("❌ No PVE clients available for VM testing")
            return False
        
        # Test getting VMs
        print("📋 Testing get_vms operation...")
        
        async def get_vms_from_client(client):
            return await client.get_vms()
        
        vm_results = await api_manager.aggregate_results(get_vms_from_client)
        
        vm_count = len([vm for vm in vm_results if "vmid" in vm])
        print(f"Total VMs found: {vm_count}")
        
        # Show first few VMs
        for vm in vm_results[:5]:
            if "vmid" in vm:
                vmid = vm.get("vmid")
                name = vm.get("name", "unnamed")
                status = vm.get("status", "unknown")
                node = vm.get("node", "unknown")
                print(f"  VM {vmid}: {name} ({status}) on {node}")
        
        return True
    except Exception as e:
        print(f"❌ VM operations test failed: {e}")
        return False

async def test_lxc_operations():
    """Test LXC-related operations"""
    print("\n📦 Testing LXC Operations")
    print("=" * 50)
    
    try:
        config = MCPConfig(".env")
        api_manager = ProxmoxAPIManager(config)
        
        if not api_manager.pve_clients:
            print("❌ No PVE clients available for LXC testing")
            return False
        
        # Test getting LXCs
        print("📋 Testing get_lxcs operation...")
        
        async def get_lxcs_from_client(client):
            return await client.get_lxcs()
        
        lxc_results = await api_manager.aggregate_results(get_lxcs_from_client)
        
        lxc_count = len([lxc for lxc in lxc_results if "vmid" in lxc])
        print(f"Total LXCs found: {lxc_count}")
        
        # Show first few LXCs
        for lxc in lxc_results[:5]:
            if "vmid" in lxc:
                vmid = lxc.get("vmid")
                name = lxc.get("name", "unnamed")
                status = lxc.get("status", "unknown")
                node = lxc.get("node", "unknown")
                print(f"  LXC {vmid}: {name} ({status}) on {node}")
        
        return True
    except Exception as e:
        print(f"❌ LXC operations test failed: {e}")
        return False

async def test_storage_operations():
    """Test storage-related operations"""
    print("\n💾 Testing Storage Operations")
    print("=" * 50)
    
    try:
        config = MCPConfig(".env")
        api_manager = ProxmoxAPIManager(config)
        
        if not api_manager.get_all_clients():
            print("❌ No clients available for storage testing")
            return False
        
        # Test getting storage
        print("📋 Testing get_storage operation...")
        
        async def get_storage_from_client(client):
            return await client.get_storage()
        
        storage_results = await api_manager.aggregate_results(get_storage_from_client)
        
        storage_count = len([s for s in storage_results if "storage" in s])
        print(f"Total storage entries found: {storage_count}")
        
        # Show first few storage entries
        for storage in storage_results[:5]:
            if "storage" in storage:
                name = storage.get("storage")
                storage_type = storage.get("type", "unknown")
                node = storage.get("node", "unknown")
                print(f"  Storage: {name} ({storage_type}) on {node}")
        
        return True
    except Exception as e:
        print(f"❌ Storage operations test failed: {e}")
        return False

async def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 Enhanced Proxmox MCP Server Test Suite")
    print("=" * 60)
    
    tests = [
        ("Connectivity", test_basic_connectivity),
        ("API Manager", test_api_manager),
        ("VM Operations", test_vm_operations),
        ("LXC Operations", test_lxc_operations),
        ("Storage Operations", test_storage_operations)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Print summary
    print("\n📊 Test Summary")
    print("=" * 30)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced MCP Server is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check configuration and connectivity.")
        return False

if __name__ == "__main__":
    # Check if .env file exists
    if not Path(".env").exists():
        print("❌ .env file not found. Please create one based on the configuration example.")
        sys.exit(1)
    
    # Run tests
    try:
        result = asyncio.run(run_all_tests())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)