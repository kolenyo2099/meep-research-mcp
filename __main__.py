"""
Main entry point for the Meep Research MCP package.
"""

import argparse
import logging
from .server import mcp

def main():
    """Main entry point for the package."""
    # Configure argument parser
    parser = argparse.ArgumentParser(description="Meep Research MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--transport", choices=["stdio", "sse", "streamable-http"], default="stdio", 
                       help="Transport protocol to use (stdio, sse, or streamable-http)")
    
    args = parser.parse_args()
    
    # Configure logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Start the server
    print(f"Starting Meep Research MCP Server using {args.transport} transport")
    print("Press Ctrl+C to stop the server")
    
    try:
        mcp.run(transport=args.transport)
    except KeyboardInterrupt:
        print("\nShutting down server...")
        print("Server stopped")

if __name__ == "__main__":
    main() 