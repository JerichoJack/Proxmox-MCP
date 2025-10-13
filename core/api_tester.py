# core/api_tester.py
import requests
from core.utils import setup_logger

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
            return True
        else:
            logger.error(f"❌ Failed to connect to {'PBS' if is_pbs else 'PVE'} node '{host}': HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Connection to {'PBS' if is_pbs else 'PVE'} node '{host}' failed: {e}")
        return False

def test_nodes(config):
    """
    Iterate through all configured PVE and PBS nodes and test connectivity.
    Returns True if all nodes are reachable, False if any fail.
    """
    success = True

    if config.pve_nodes:
        logger.info("🔗 Testing PVE nodes...")
        for node_name in config.pve_nodes:
            node_info = config.get_pve_node(node_name)
            if not test_proxmox_connection(
                host=node_info["host"],
                user=node_info["user"],
                token_name=node_info["token_name"],
                token_value=node_info["token_value"],
                verify_ssl=config.verify_ssl,
                is_pbs=False,
            ):
                success = False

    if config.pbs_nodes:
        logger.info("🔗 Testing PBS nodes...")
        for node_name in config.pbs_nodes:
            node_info = config.get_pbs_node(node_name)
            if not test_proxmox_connection(
                host=node_info["host"],
                user=node_info["user"],
                token_name=node_info["token_name"],
                token_value=node_info["token_value"],
                verify_ssl=config.verify_ssl,
                is_pbs=True,
            ):
                success = False

    if success:
        logger.info("🎉 All nodes connected successfully!")
    else:
        logger.warning("⚠ Some nodes failed to connect. Check credentials and network.")

    return success
