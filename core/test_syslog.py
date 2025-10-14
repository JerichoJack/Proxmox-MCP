#!/usr/bin/env python3
"""
Simple test script to verify SyslogListener functionality.
This script sends sample syslog messages to test the parser.
"""
import asyncio
import socket
from datetime import datetime

# Sample Proxmox syslog messages for testing
TEST_MESSAGES = [
    # VM Operations
    b"<30>Oct 13 10:15:32 pve-node1 pvestatd[1234]: starting VM 100 (test-vm)",
    b"<30>Oct 13 10:16:45 pve-node1 pvestatd[1234]: VM 100 (test-vm) stopped",
    b"<30>Oct 13 10:17:22 pve-node1 pve-ha-manager[5678]: migration finished successfully, old VM 100 (test-vm)",
    
    # Backup Operations
    b"<30>Oct 13 11:00:05 pve-node1 pvebackup[9999]: starting backup of VM 100 to storage 'backup-pool'",
    b"<30>Oct 13 11:15:30 pve-node1 pvebackup[9999]: backup finished (VM 100): successful, archive '/backup/vzdump-qemu-100-2025_10_13-11_00_05.vma.zst'",
    
    # Cluster Events
    b"<30>Oct 13 12:00:01 pve-node1 pve-cluster[2468]: node pve-node2 joined cluster",
    b"<31>Oct 13 12:30:15 pve-node1 pve-ha-manager[1357]: node pve-node3 fenced",
    
    # Storage Events
    b"<27>Oct 13 13:45:22 pve-node1 pvestatd[1234]: storage 'shared-nfs' is not available",
    
    # Task Errors
    b"<27>Oct 13 14:15:18 pve-node1 pvedaemon[4321]: TASK ERROR: command 'vzdump 101' failed: exit code 2",
    
    # Generic message
    b"<30>Oct 13 15:00:00 pve-node1 kernel[0]: some generic kernel message",
]

async def send_test_messages(port=514):
    """Send test syslog messages to the specified port."""
    print(f"Sending {len(TEST_MESSAGES)} test syslog messages to localhost:{port}")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    try:
        for i, message in enumerate(TEST_MESSAGES, 1):
            print(f"Sending message {i}: {message.decode('utf-8', errors='ignore')}")
            sock.sendto(message, ('127.0.0.1', port))
            await asyncio.sleep(0.5)  # Small delay between messages
            
    except Exception as e:
        print(f"Error sending messages: {e}")
    finally:
        sock.close()
        
    print("All test messages sent!")

async def main():
    print("=== Syslog Listener Test ===")
    print("This script sends test syslog messages to test the SyslogListener.")
    print("Make sure your SyslogListener is running on port 514 (or configured port).")
    print()
    
    port = input("Enter syslog port (default 514): ").strip() or "514"
    try:
        port = int(port)
    except ValueError:
        print("Invalid port number, using default 514")
        port = 514
    
    print(f"Targeting port: {port}")
    input("Press Enter to start sending test messages...")
    
    await send_test_messages(port)
    
    print()
    print("Test complete! Check your MCP server logs to see if events were processed.")

if __name__ == "__main__":
    asyncio.run(main())