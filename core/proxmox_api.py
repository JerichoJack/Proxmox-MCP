#!/usr/bin/env python3
"""
Proxmox API Manager
Handles connections to multiple Proxmox VE and PBS nodes
"""
import logging
from typing import Dict, Optional, List
from proxmoxer import ProxmoxAPI
from core.config import MCPConfig

logger = logging.getLogger(__name__)


class ProxmoxAPIManager:
    """Manages Proxmox API connections for multiple nodes"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.pve_clients: Dict[str, ProxmoxAPI] = {}
        self.pbs_clients: Dict[str, ProxmoxAPI] = {}
        
        # Initialize connections
        self._initialize_pve_clients()
        self._initialize_pbs_clients()
    
    def _initialize_pve_clients(self):
        """Initialize Proxmox VE API clients"""
        if not self.config.pve_nodes:
            return
            
        for node_name in self.config.pve_nodes:
            try:
                node_info = self.config.get_pve_node(node_name)
                
                # ✅ CORRECT: Pass user, token_name, and token_value as SEPARATE parameters
                client = ProxmoxAPI(
                    node_info["host"],
                    user=node_info["user"],           # Just user@realm
                    token_name=node_info["token_name"],  # Separate token_name
                    token_value=node_info["token_value"], # Separate token_value
                    verify_ssl=self.config.verify_ssl
                )
                
                # Test the connection
                version = client.version.get()
                logger.info(f"✅ PVE client connected to {node_name} (v{version.get('version', 'unknown')})")
                self.pve_clients[node_name] = client
                
            except Exception as e:
                logger.error(f"Failed to initialize Proxmox API for {node_info['host']}: {e}")
                logger.error(f"❌ PVE client failed to connect to {node_name}")
    
    def _initialize_pbs_clients(self):
        """Initialize Proxmox Backup Server API clients"""
        if not self.config.pbs_nodes:
            return
            
        for node_name in self.config.pbs_nodes:
            try:
                node_info = self.config.get_pbs_node(node_name)
                
                # ✅ CORRECT: Pass user, token_name, and token_value as SEPARATE parameters
                client = ProxmoxAPI(
                    node_info["host"],
                    user=node_info["user"],           # Just user@realm
                    token_name=node_info["token_name"],  # Separate token_name
                    token_value=node_info["token_value"], # Separate token_value
                    verify_ssl=self.config.verify_ssl,
                    service='PBS'  # Important for PBS
                )
                
                # Test the connection
                version = client.version.get()
                logger.info(f"✅ PBS client connected to {node_name} (v{version.get('version', 'unknown')})")
                self.pbs_clients[node_name] = client
                
            except Exception as e:
                logger.error(f"Failed to initialize Proxmox API for {node_info['host']}: {e}")
                logger.error(f"❌ PBS client failed to connect to {node_name}")
    
    def get_pve_client(self, node_name: str) -> Optional[ProxmoxAPI]:
        """Get PVE API client for a specific node"""
        return self.pve_clients.get(node_name)
    
    def get_pbs_client(self, node_name: str) -> Optional[ProxmoxAPI]:
        """Get PBS API client for a specific node"""
        return self.pbs_clients.get(node_name)
    
    def get_all_pve_clients(self) -> Dict[str, ProxmoxAPI]:
        """Get all PVE API clients"""
        return self.pve_clients
    
    def get_all_pbs_clients(self) -> Dict[str, ProxmoxAPI]:
        """Get all PBS API clients"""
        return self.pbs_clients
    
    def get_client(self, node_name: str) -> Optional[ProxmoxAPI]:
        """Get API client for a node (checks both PVE and PBS)"""
        client = self.get_pve_client(node_name)
        if client:
            return client
        return self.get_pbs_client(node_name)

    def get_all_clients(self) -> Dict[str, ProxmoxAPI]:
        """Get all API clients (both PVE and PBS)"""
        return {**self.pve_clients, **self.pbs_clients}
    
    def get_clients_info(self) -> Dict[str, Dict]:
        """Get detailed information about all connected clients"""
        clients_info = {}
        
        # Add PVE clients info
        for node_name, client in self.pve_clients.items():
            try:
                version = client.version.get()
                clients_info[node_name] = {
                    "type": "PVE",
                    "node_name": node_name,
                    "host": self.config.get_pve_node(node_name)["host"],
                    "connected": True,
                    "version": version.get("version", "unknown"),
                    "api_version": version.get("repoid", "unknown")
                }
            except Exception as e:
                clients_info[node_name] = {
                    "type": "PVE",
                    "node_name": node_name,
                    "host": self.config.get_pve_node(node_name)["host"],
                    "connected": False,
                    "error": str(e)
                }
        
        # Add PBS clients info
        for node_name, client in self.pbs_clients.items():
            try:
                version = client.version.get()
                clients_info[node_name] = {
                    "type": "PBS",
                    "node_name": node_name,
                    "host": self.config.get_pbs_node(node_name)["host"],
                    "connected": True,
                    "version": version.get("version", "unknown"),
                    "api_version": version.get("repoid", "unknown")
                }
            except Exception as e:
                clients_info[node_name] = {
                    "type": "PBS",
                    "node_name": node_name,
                    "host": self.config.get_pbs_node(node_name)["host"],
                    "connected": False,
                    "error": str(e)
                }
        
        return clients_info