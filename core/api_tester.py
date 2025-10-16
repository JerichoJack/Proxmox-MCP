# core/api_tester.py
import asyncio
import requests
from core.utils import setup_logger
from core.proxmox_api import ProxmoxAPIManager

logger = setup_logger()

def test_proxmox_connection(host, user, token_name, token_value, verify_ssl=False, is_pbs=False):
    """
    Test API connectivity to a PVE or PBS node.
    Returns True if successful, False otherwise.
    """
    base_port = 8007 if is_pbs else 8006
    base_url = f"https://{host}:{base_port}/api2/json/version"

    # Correct token prefix and format for PVE vs PBS
    if is_pbs:
        headers = {"Authorization": f"PBSAPIToken={user}!{token_name}:{token_value}"}
    else:
        headers = {"Authorization": f"PVEAPIToken={user}!{token_name}={token_value}"}

    try:
        response = requests.get(base_url, headers=headers, verify=verify_ssl, timeout=5)
        if response.status_code == 200:
            version = response.json().get("data", {}).get("version", "Unknown")
            logger.info(f"✅ Connected to {'PBS' if is_pbs else 'PVE'} node '{host}' (version: {version})")
            return True, {"success": True, "host": host, "version": version, "type": "PBS" if is_pbs else "PVE"}
        else:
            logger.error(f"❌ Failed to connect to {'PBS' if is_pbs else 'PVE'} node '{host}': HTTP {response.status_code}")
            return False, {"success": False, "host": host, "error": f"HTTP {response.status_code}", "type": "PBS" if is_pbs else "PVE"}
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Connection to {'PBS' if is_pbs else 'PVE'} node '{host}' failed: {e}")
        return False, {"success": False, "host": host, "error": str(e), "type": "PBS" if is_pbs else "PVE"}

async def test_nodes(config, target_nodes=None):
    """
    Enhanced node testing with detailed results.
    Returns (overall_success, list_of_results)
    """
    results = []
    overall_success = True

    # Test PVE nodes
    if config.pve_nodes:
        logger.info("🔗 Testing PVE nodes...")
        for node_name in config.pve_nodes:
            if target_nodes and node_name not in target_nodes:
                continue
                
            node_info = config.get_pve_node(node_name)
            if not all(node_info.values()):
                result = {
                    "success": False,
                    "node_name": node_name,
                    "host": node_info.get("host", "unknown"),
                    "error": "Incomplete node configuration",
                    "type": "PVE"
                }
                results.append(result)
                overall_success = False
                continue
                
            success, result = test_proxmox_connection(
                host=node_info["host"],
                user=node_info["user"],
                token_name=node_info["token_name"],
                token_value=node_info["token_value"],
                verify_ssl=config.verify_ssl,
                is_pbs=False,
            )
            
            result["node_name"] = node_name
            results.append(result)
            
            if not success:
                overall_success = False

    # Test PBS nodes
    if config.pbs_nodes:
        logger.info("🔗 Testing PBS nodes...")
        for node_name in config.pbs_nodes:
            if target_nodes and node_name not in target_nodes:
                continue
                
            node_info = config.get_pbs_node(node_name)
            if not all(node_info.values()):
                result = {
                    "success": False,
                    "node_name": node_name,
                    "host": node_info.get("host", "unknown"),
                    "error": "Incomplete node configuration",
                    "type": "PBS"
                }
                results.append(result)
                overall_success = False
                continue
                
            success, result = test_proxmox_connection(
                host=node_info["host"],
                user=node_info["user"],
                token_name=node_info["token_name"],
                token_value=node_info["token_value"],
                verify_ssl=config.verify_ssl,
                is_pbs=True,
            )
            
            result["node_name"] = node_name
            results.append(result)
            
            if not success:
                overall_success = False

    if overall_success:
        logger.info("🎉 All nodes connected successfully!")
    else:
        logger.warning("⚠ Some nodes failed to connect. Check credentials and network.")

    return overall_success, results

# Legacy function for backward compatibility
def test_nodes_legacy(config):
    """Legacy synchronous wrapper"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        success, _ = loop.run_until_complete(test_nodes(config))
        return success
    finally:
        loop.close()
