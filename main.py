#!/usr/bin/env python3
"""
Proxmox MCP Server - Unified Production Entry Point

This is the single entry point for the Proxmox MCP Server system.
Supports two primary modes:
  --test-connection: Comprehensive connectivity testing
  --mcp-server: Production MCP server for n8n integration

Usage Examples:
  python3 main.py --test-connection    # Test all connections
  python3 main.py --mcp-server         # Start MCP server for n8n
"""
import argparse
import asyncio
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

from core.config import MCPConfig
from core.manager import MCPManager


def print_banner():
    """Display startup banner"""
    print("🧠 Proxmox MCP Server - Production Environment")
    print("=" * 55)


def print_config_summary(config: MCPConfig):
    """Display configuration summary"""
    print(f"📊 Configuration: {config.lab_mode} mode")
    print(f"🖥️  PVE Nodes: {len(config.pve_nodes)}")
    print(f"💾 PBS Nodes: {len(config.pbs_nodes)}")
    
    # Show enabled features
    features = []
    if config.gotify_out_enabled:
        features.append("Gotify")
    if config.discord_out_enabled:
        features.append("Discord")
    if config.enable_event_listeners:
        features.append("Event Listeners")
        
    if features:
        print(f"🔔 Enabled: {', '.join(features)}")
    print()


def validate_environment():
    """Validate that all required files exist"""
    required_files = [
        ".env",
        "core/config.py",
        "core/manager.py", 
        "mcp_server.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("\nPlease ensure all files are present and try again.")
        sys.exit(1)


async def run_connectivity_tests():
    """Run comprehensive connectivity tests"""
    print("🔗 CONNECTIVITY TEST MODE")
    print("=" * 50)
    print("Testing all configured connections, I/O modules, and MCP functionality...")
    print()
    
    try:
        # Initialize manager
        manager = MCPManager()
        manager.setup()
        
        # Run comprehensive tests
        success = await manager.test_connectivity()
        
        # Test MCP server functionality
        print("🔌 Testing MCP Server Protocol...")
        try:
            # Test if mcp_server.py can be imported and initialized
            mcp_test_result = subprocess.run([
                sys.executable, "-c", 
                "from mcp_server import ProxmoxMCPServer; server = ProxmoxMCPServer(); print('✅ MCP Server initialization successful')"
            ], capture_output=True, text=True, timeout=10)
            
            if mcp_test_result.returncode == 0:
                print("✅ MCP Server protocol test passed")
            else:
                print(f"❌ MCP Server protocol test failed: {mcp_test_result.stderr}")
                success = False
        except subprocess.TimeoutExpired:
            print("❌ MCP Server protocol test timed out")
            success = False
        except Exception as e:
            print(f"❌ MCP Server protocol test error: {e}")
            success = False
        
        print()
        if success:
            print("🎉 ALL TESTS PASSED!")
            print("✅ System is ready for production use")
            print("💡 Start MCP server with: python3 main.py --mcp-server")
        else:
            print("⚠️  SOME TESTS FAILED")
            print("❌ Please check configuration and network connectivity")
            print("📖 See README.md for troubleshooting guidance")
        
        return success
        
    except Exception as e:
        print(f"❌ Test runner error: {e}")
        return False


def start_mcp_server():
    """Start the MCP server process"""
    print("🔌 MCP SERVER MODE - n8n Integration")
    print("=" * 50)
    print()
    print("📋 N8N MCP CLIENT CONFIGURATION:")
    print("   Connection Type: stdio")
    print("   Command: python")
    print("   Arguments: ['mcp_server.py']")
    print()
    print("   OR use absolute path:")
    print("   Command: /usr/bin/python3")
    print(f"   Arguments: ['{os.path.abspath('mcp_server.py')}']")
    print()
    
    print("🎯 Starting MCP Server (Model Context Protocol)...")
    print("📡 Server will accept connections from n8n MCP Client nodes")
    print()
    
    # Signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 MCP Server shutdown signal received")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start MCP server subprocess
        result = subprocess.run([
            sys.executable, "mcp_server.py"
        ], check=True)
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 MCP Server shutdown requested")
        return 0
    except Exception as e:
        print(f"\n❌ MCP Server error: {e}")
        return 1


def start_mcp_http_server(host: str = "0.0.0.0", port: int = 8000):
    """Start the HTTP/WebSocket MCP server"""
    print("🌐 MCP HTTP SERVER MODE - Remote n8n Integration")
    print("=" * 55)
    print()
    print("📋 N8N MCP CLIENT CONFIGURATION:")
    print("   Connection Type: websocket")
    print(f"   Endpoint: ws://{host}:{port}/ws")
    print("   (Use your server's IP address instead of 0.0.0.0)")
    print()
    
    print("🎯 Starting HTTP/WebSocket MCP Server...")
    print("🌍 Server accessible from remote machines")
    print()
    
    # Signal handler for graceful shutdown
    def signal_handler(signum, frame):
        print("\n🛑 HTTP MCP Server shutdown signal received")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start HTTP MCP server subprocess
        result = subprocess.run([
            sys.executable, "mcp_server_http.py",
            "--host", host,
            "--port", str(port)
        ], check=True)
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 HTTP MCP Server shutdown requested")
        return 0
    except Exception as e:
        print(f"\n❌ HTTP MCP Server error: {e}")
        return 1    # Start the MCP server using subprocess to maintain stdio connection
    try:
        return subprocess.call([sys.executable, "mcp_server.py"])
    except KeyboardInterrupt:
        print("\n🛑 MCP Server shutdown requested")
        return 0
    except Exception as e:
        print(f"\n❌ MCP Server error: {e}")
        return 1


def main():
    """Main entry point"""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Proxmox MCP Server - Production Environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  python3 main.py --test-connection    # Test all connections and exit
  python3 main.py --mcp-server         # Start MCP server for n8n

For n8n integration, use the MCP Client node with:
  Connection Type: stdio
  Command: python
  Arguments: ['mcp_server.py']
        """
    )
    parser.add_argument(
        "--test-connection",
        action="store_true",
        help="Test connectivity to all configured PVE/PBS nodes, I/O modules, and MCP server functionality"
    )
    parser.add_argument(
        "--mcp-server",
        action="store_true", 
        help="Start MCP Server for n8n integration (Model Context Protocol)"
    )
    parser.add_argument(
        "--mcp-http",
        action="store_true",
        help="Start HTTP/WebSocket MCP Server for remote n8n integration"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind HTTP server to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int,
        default=8000,
        help="Port to bind HTTP server to (default: 8000)"
    )
    
    args = parser.parse_args()
    
    # Validate environment
    validate_environment()
    
    # Load and display configuration
    try:
        config = MCPConfig(".env")
    except FileNotFoundError:
        print("❌ Configuration file '.env' not found")
        print("📋 Please copy '.env.example' to '.env' and configure your Proxmox credentials")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    print_banner()
    print_config_summary(config)
    
    # Route to appropriate mode
    if args.test_connection:
        # Test mode - run comprehensive connectivity tests
        success = asyncio.run(run_connectivity_tests())
        sys.exit(0 if success else 1)
        
    elif args.mcp_server:
        # MCP server mode - start server for n8n integration
        exit_code = start_mcp_server()
        sys.exit(exit_code)
        
    elif args.mcp_http:
        # HTTP MCP server mode - start HTTP/WebSocket server for remote n8n
        exit_code = start_mcp_http_server(host=args.host, port=args.port)
        sys.exit(exit_code)
        
    else:
        # No mode specified - show help
        print("❓ No operation mode specified")
        print()
        print("Available modes:")
        print("  --test-connection    Test all connections and configuration")
        print("  --mcp-server         Start MCP server for n8n integration (local)")
        print("  --mcp-http           Start HTTP MCP server for remote n8n integration")
        print()
        print("💡 For n8n integration:")
        print("   Local n8n:")
        print("   1. First run: python3 main.py --test-connection")
        print("   2. Then start: python3 main.py --mcp-server")
        print("   3. Configure n8n MCP Client with stdio connection to 'mcp_server.py'")
        print()
        print("   Remote n8n:")
        print("   1. First run: python3 main.py --test-connection")
        print("   2. Then start: python3 main.py --mcp-http --host 0.0.0.0 --port 8000")
        print("   3. Configure n8n MCP Client with WebSocket connection to ws://YOUR-IP:8000/ws")
        print()
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()