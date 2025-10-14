# modules/input/syslog_listener.py
import asyncio
import re
import socket
from datetime import datetime

from core.utils import setup_logger

logger = setup_logger()


class SyslogListener:
    """
    MCP input listener for syslog messages from Proxmox nodes.
    Listens on a UDP port for syslog messages and parses Proxmox-specific events.
    """
    
    def __init__(self, config, event_callback):
        self.listen_port = getattr(config, 'event_syslog_listen_port', 514)
        self.parse_format = getattr(config, 'event_syslog_parse_format', 'proxmox')
        self.event_callback = event_callback
        self._running = False
        self._server = None
        self._transport = None
        
        # Proxmox syslog patterns for common events
        self.proxmox_patterns = {
            'vm_start': re.compile(r'starting VM (\d+) \(([^)]+)\)'),
            'vm_stop': re.compile(r'VM (\d+) \(([^)]+)\) stopped'),
            'vm_migrate': re.compile(r'migration finished successfully, old VM (\d+) \(([^)]+)\)'),
            'backup_start': re.compile(r'starting backup of VM (\d+) to (.+)'),
            'backup_finish': re.compile(r'backup finished \(VM (\d+)\): (.+)'),
            'node_fence': re.compile(r'node (\S+) fenced'),
            'cluster_join': re.compile(r'node (\S+) joined cluster'),
            'cluster_leave': re.compile(r'node (\S+) left cluster'),
            'storage_error': re.compile(r'storage \'(\S+)\' is not available'),
            'task_error': re.compile(r'TASK ERROR: (.+)'),
            'corosync': re.compile(r'corosync.*membership changed'),
        }

    async def start(self):
        """Start the syslog UDP server."""
        if self._running:
            logger.warning("[SyslogListener] Already running, ignoring start request.")
            return
            
        logger.info(f"[SyslogListener] Starting syslog server on UDP port {self.listen_port}...")
        self._running = True
        
        try:
            loop = asyncio.get_running_loop()
            
            # Create UDP endpoint
            self._transport, self._server = await loop.create_datagram_endpoint(
                lambda: SyslogProtocol(self._process_message),
                local_addr=('0.0.0.0', self.listen_port)
            )
            
            logger.info(f"[SyslogListener] Syslog server listening on UDP port {self.listen_port}")
            
        except Exception as e:
            logger.error(f"[SyslogListener] Failed to start syslog server: {e}")
            self._running = False
            raise

    async def stop(self):
        """Stop the syslog server."""
        self._running = False
        
        if self._transport:
            self._transport.close()
            self._transport = None
            
        logger.info("[SyslogListener] Syslog server stopped.")

    async def _process_message(self, data, addr):
        """Process incoming syslog message."""
        if not self._running:
            return
            
        try:
            message = data.decode('utf-8', errors='ignore').strip()
            logger.debug(f"[SyslogListener] Received from {addr[0]}: {message}")
            
            # Parse syslog message
            parsed_event = self._parse_syslog_message(message, addr[0])
            
            if parsed_event:
                title = parsed_event.get('title', 'Proxmox Syslog Event')
                content = parsed_event.get('message', message)
                
                # Add source information
                enhanced_message = f"Source: {addr[0]}\nEvent: {content}"
                if parsed_event.get('vm_id'):
                    enhanced_message = f"VM ID: {parsed_event['vm_id']}\n{enhanced_message}"
                if parsed_event.get('node'):
                    enhanced_message = f"Node: {parsed_event['node']}\n{enhanced_message}"
                
                await self.event_callback(title, enhanced_message)
            else:
                # Forward unrecognized messages as generic events
                await self.event_callback(
                    "Proxmox Syslog Message", 
                    f"Source: {addr[0]}\nRaw: {message}"
                )
                
        except Exception as e:
            logger.error(f"[SyslogListener] Error processing message from {addr[0]}: {e}")

    def _parse_syslog_message(self, message, source_ip):
        """
        Parse syslog message and extract Proxmox-specific event information.
        Returns dict with parsed event info or None if not a recognized Proxmox event.
        """
        if self.parse_format != 'proxmox':
            # For non-Proxmox formats, return basic parsing
            return {
                'title': 'Syslog Event',
                'message': message,
                'source': source_ip,
                'timestamp': datetime.now().isoformat()
            }
        
        # Extract standard syslog components (RFC 3164 format)
        # Format: <priority>timestamp hostname tag: message
        syslog_pattern = re.compile(
            r'^(?:<(\d+)>)?'  # Priority (optional)
            r'(\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+'  # Timestamp
            r'(\S+)\s+'  # Hostname
            r'([^:]+):\s*'  # Tag/Process
            r'(.*)$'  # Message
        )
        
        match = syslog_pattern.match(message)
        if not match:
            return None
            
        priority, timestamp, hostname, tag, msg_content = match.groups()
        
        # Try to match Proxmox-specific patterns
        for event_type, pattern in self.proxmox_patterns.items():
            event_match = pattern.search(msg_content)
            if event_match:
                return self._create_proxmox_event(event_type, event_match, {
                    'hostname': hostname,
                    'tag': tag,
                    'timestamp': timestamp,
                    'source': source_ip,
                    'raw_message': msg_content
                })
        
        # Return generic Proxmox event if no specific pattern matched
        return {
            'title': f'Proxmox Event - {hostname}',
            'message': msg_content,
            'hostname': hostname,
            'tag': tag,
            'timestamp': timestamp,
            'source': source_ip,
            'event_type': 'generic'
        }

    def _create_proxmox_event(self, event_type, match, metadata):
        """Create structured event data for recognized Proxmox events."""
        events = {
            'vm_start': {
                'title': 'VM Started',
                'message': f"VM {match.group(1)} ({match.group(2)}) started successfully",
                'vm_id': match.group(1),
                'vm_name': match.group(2),
                'severity': 'info'
            },
            'vm_stop': {
                'title': 'VM Stopped',
                'message': f"VM {match.group(1)} ({match.group(2)}) stopped",
                'vm_id': match.group(1),
                'vm_name': match.group(2),
                'severity': 'info'
            },
            'vm_migrate': {
                'title': 'VM Migration Completed',
                'message': f"Migration of VM {match.group(1)} ({match.group(2)}) completed successfully",
                'vm_id': match.group(1),
                'vm_name': match.group(2),
                'severity': 'info'
            },
            'backup_start': {
                'title': 'Backup Started',
                'message': f"Backup of VM {match.group(1)} started to {match.group(2)}",
                'vm_id': match.group(1),
                'backup_target': match.group(2),
                'severity': 'info'
            },
            'backup_finish': {
                'title': 'Backup Completed',
                'message': f"Backup of VM {match.group(1)} completed: {match.group(2)}",
                'vm_id': match.group(1),
                'backup_result': match.group(2),
                'severity': 'info' if 'successful' in match.group(2).lower() else 'warning'
            },
            'node_fence': {
                'title': 'Node Fenced',
                'message': f"Node {match.group(1)} has been fenced",
                'node': match.group(1),
                'severity': 'critical'
            },
            'cluster_join': {
                'title': 'Node Joined Cluster',
                'message': f"Node {match.group(1)} joined the cluster",
                'node': match.group(1),
                'severity': 'info'
            },
            'cluster_leave': {
                'title': 'Node Left Cluster',
                'message': f"Node {match.group(1)} left the cluster",
                'node': match.group(1),
                'severity': 'warning'
            },
            'storage_error': {
                'title': 'Storage Error',
                'message': f"Storage '{match.group(1)}' is not available",
                'storage': match.group(1),
                'severity': 'critical'
            },
            'task_error': {
                'title': 'Task Error',
                'message': f"Task failed: {match.group(1)}",
                'error_details': match.group(1),
                'severity': 'error'
            },
            'corosync': {
                'title': 'Cluster Membership Changed',
                'message': "Corosync cluster membership has changed",
                'severity': 'warning'
            }
        }
        
        event_data = events.get(event_type, {})
        event_data.update(metadata)
        event_data['event_type'] = event_type
        
        return event_data

    async def test_connection(self, timeout: int = 5) -> bool:
        """
        Test if syslog listener can bind to the configured port.
        Returns True if successful, False otherwise.
        """
        try:
            # Try to bind to the port temporarily
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            test_socket.bind(('0.0.0.0', self.listen_port))
            test_socket.close()
            
            logger.info(f"[SyslogListener] Port {self.listen_port} is available for binding.")
            return True
            
        except OSError as e:
            logger.error(f"[SyslogListener] Cannot bind to port {self.listen_port}: {e}")
            return False
        except Exception as e:
            logger.error(f"[SyslogListener] Test connection failed: {e}")
            return False


class SyslogProtocol(asyncio.DatagramProtocol):
    """UDP protocol handler for syslog messages."""
    
    def __init__(self, message_handler):
        self.message_handler = message_handler
        
    def connection_made(self, transport):
        self.transport = transport
        
    def datagram_received(self, data, addr):
        """Handle incoming UDP datagram."""
        asyncio.create_task(self.message_handler(data, addr))
        
    def error_received(self, exc):
        logger.error(f"[SyslogProtocol] UDP error: {exc}")