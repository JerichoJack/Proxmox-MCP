# core/config.py
import os
from pathlib import Path
from dotenv import load_dotenv
import requests


class MCPConfig:
    """
    Loads and manages configuration for the MCP Server from a .env file.
    Supports standalone, clustered, and mixed node topologies.
    """

    def __init__(self, env_path: str | Path = ".env"):
        env_path = Path(env_path)
        if not env_path.exists():
            raise FileNotFoundError(f"Missing configuration file: {env_path}")
        load_dotenv(env_path)

        # -----------------------
        # General settings
        # -----------------------
        self.verify_ssl = self._get_bool("VERIFY_SSL", default=False)
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.enable_event_listeners = self._get_bool("ENABLE_EVENT_LISTENERS", default=True)

        # -----------------------
        # Lab Configuration
        # -----------------------
        self.lab_mode = os.getenv("LAB_CONFIGURATION", "STANDALONE").upper()
        if self.lab_mode not in ["STANDALONE", "CLUSTERED", "MIXED"]:
            raise ValueError(f"Invalid LAB_CONFIGURATION: {self.lab_mode}")

        # -----------------------
        # Nodes
        # -----------------------
        self.pve_nodes = self._get_list("PVE_NODES")
        self.pbs_nodes = self._get_list("PBS_NODES")

        # Clustered nodes (auto-discovery)
        self.cluster_pve_nodes = []
        if self.lab_mode in ["CLUSTERED", "MIXED"]:
            self._discover_cluster_nodes()

        # -----------------------
        # Event listeners (Input)
        # -----------------------
        self.enabled_event_listeners = self._get_list("ENABLED_EVENT_LISTENERS")
        self.event_ws_enabled = self._get_bool("EVENT_WS_ENABLED", default=False)
        self.event_email_enabled = self._get_bool("EVENT_EMAIL_ENABLED", default=False)
        self.event_syslog_enabled = self._get_bool("EVENT_SYSLOG_ENABLED", default=False)

        # Gotify input
        self.gotify_in_enabled = self._get_bool("GOTIFY_IN_ENABLED", default=False)
        self.gotify_in_server_url = os.getenv("GOTIFY_IN_SERVER_URL")
        self.gotify_in_client_token = os.getenv("GOTIFY_IN_CLIENT_TOKEN")
        self.gotify_in_poll_interval = self._get_int("GOTIFY_IN_POLL_INTERVAL", default=15)

        # Discord input (optional)
        self.discord_in_enabled = self._get_bool("DISCORD_IN_ENABLED", default=False)
        self.discord_in_webhook = os.getenv("DISCORD_IN_WEBHOOK_URL")

        # -----------------------
        # Notification providers (Output)
        # -----------------------
        self.enabled_notifiers = self._get_list("ENABLED_NOTIFIERS")
        self.gotify_out_enabled = self._get_bool("GOTIFY_OUT_ENABLED", default=False)
        self.gotify_out_server_url = os.getenv("GOTIFY_OUT_SERVER_URL")
        self.gotify_out_app_token = os.getenv("GOTIFY_OUT_APP_TOKEN")

        self.discord_out_enabled = self._get_bool("DISCORD_OUT_ENABLED", default=False)
        self.discord_out_webhook = os.getenv("DISCORD_OUT_WEBHOOK_URL")

        self.ntfy_enabled = self._get_bool("NTFY_ENABLED", default=False)
        self.notify_email_enabled = self._get_bool("NOTIFY_EMAIL_ENABLED", default=False)

        # Event listener config
        self.ws_interval = self._get_int("EVENT_WS_RECONNECT_INTERVAL", default=30)
        self.email_poll_interval = self._get_int("EVENT_EMAIL_POLL_INTERVAL", default=60)

        # Agent
        self.agent_enabled = self._get_bool("ENABLE_AGENT", default=False)
        self.agent_server_url = os.getenv("AGENT_SERVER_URL", "http://localhost:8090")

    # -----------------------
    # Utility Accessors
    # -----------------------
    def _get_bool(self, key: str, default: bool = False) -> bool:
        value = os.getenv(key)
        if value is None:
            return default
        return str(value).strip().lower() in ("1", "true", "yes", "on")

    def _get_list(self, key: str, default=None) -> list[str]:
        value = os.getenv(key)
        if not value:
            return default or []
        return [v.strip() for v in value.split(",") if v.strip()]

    def _get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(os.getenv(key, default))
        except (TypeError, ValueError):
            return default

    # -----------------------
    # Node Access Helpers
    # -----------------------
    def get_pve_node(self, node_name: str) -> dict:
        prefix = node_name.upper().replace("-", "_")
        return {
            "host": os.getenv(f"{prefix}_HOST"),
            "user": os.getenv(f"{prefix}_USER"),
            "token_name": os.getenv(f"{prefix}_TOKEN_NAME"),
            "token_value": os.getenv(f"{prefix}_TOKEN_VALUE"),
        }

    def get_pbs_node(self, node_name: str) -> dict:
        prefix = node_name.upper().replace("-", "_")
        return {
            "host": os.getenv(f"{prefix}_HOST"),
            "user": os.getenv(f"{prefix}_USER"),
            "token_name": os.getenv(f"{prefix}_TOKEN_NAME"),
            "token_value": os.getenv(f"{prefix}_TOKEN_VALUE"),
        }

    # -----------------------
    # Cluster Node Discovery
    # -----------------------
    def _discover_cluster_nodes(self):
        primary_host = os.getenv("PVE_CLUSTER_PRIMARY_HOST")
        user = os.getenv("PVE_CLUSTER_PRIMARY_USER")
        token_name = os.getenv("PVE_CLUSTER_PRIMARY_TOKEN_NAME")
        token_value = os.getenv("PVE_CLUSTER_PRIMARY_TOKEN_VALUE")
        if not all([primary_host, user, token_name, token_value]):
            print("[MCP] Cluster primary node info incomplete, skipping discovery.")
            return

        url = f"https://{primary_host}:8006/api2/json/cluster/resources"
        headers = {"Authorization": f"PVEAPIToken={user}!{token_name}={token_value}"}

        try:
            resp = requests.get(url, headers=headers, verify=self.verify_ssl, timeout=5)
            resp.raise_for_status()
            data = resp.json().get("data", [])
            for node in data:
                if node.get("type") == "node":
                    node_name = node["name"]
                    self.cluster_pve_nodes.append(node_name)
                    if f"PVE_{node_name.upper()}_HOST" not in os.environ:
                        print(f"[MCP] Node {node_name} detected in cluster but no host defined in .env")
            if self.lab_mode == "CLUSTERED":
                self.pve_nodes = self.cluster_pve_nodes
            elif self.lab_mode == "MIXED":
                self.pve_nodes = list(set(self.pve_nodes + self.cluster_pve_nodes))
            print(f"[MCP] Cluster nodes discovered: {self.cluster_pve_nodes}")
        except Exception as e:
            print(f"[MCP] Error discovering cluster nodes: {e}")

    # -----------------------
    # Display Utilities
    # -----------------------
    def summary(self) -> str:
        return (
            f"🔧 MCP Server Configuration\n"
            f" ├─ Log Level: {self.log_level}\n"
            f" ├─ Verify SSL: {self.verify_ssl}\n"
            f" ├─ Lab Mode: {self.lab_mode}\n"
            f" ├─ PVE Nodes: {', '.join(self.pve_nodes) or 'None'}\n"
            f" ├─ PBS Nodes: {', '.join(self.pbs_nodes) or 'None'}\n"
            f" ├─ Enabled Listeners: {', '.join(self.enabled_event_listeners) or 'None'}\n"
            f" ├─ Gotify Input Enabled: {self.gotify_in_enabled}\n"
            f" ├─ Gotify Output Enabled: {self.gotify_out_enabled}\n"
            f" ├─ Discord Input Enabled: {self.discord_in_enabled}\n"
            f" ├─ Discord Output Enabled: {self.discord_out_enabled}\n"
            f" ├─ Agent Enabled: {self.agent_enabled}\n"
        )


if __name__ == "__main__":
    config = MCPConfig(".env")
    print(config.summary())
