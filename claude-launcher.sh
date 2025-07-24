#!/bin/bash
# Script to launch Meep Research MCP for Claude Desktop

# Print debug info to stderr so it shows up in Claude Desktop logs
echo "Starting Claude Desktop launcher script..." >&2

# Set workspace directory - use absolute path, not ~
WORK_DIR="/Users/guillen/meep_research_workspace"

# Make sure the directories exist
if [ ! -d "$WORK_DIR" ]; then
    echo "Error: Workspace directory not found at $WORK_DIR" >&2
    echo "Please run setup.sh first" >&2
    exit 1
fi

if [ ! -d "$WORK_DIR/meep-research-mcp" ]; then
    echo "Error: MCP directory not found at $WORK_DIR/meep-research-mcp" >&2
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$WORK_DIR/meep-research-mcp/.venv" ]; then
    echo "Error: Virtual environment not found at $WORK_DIR/meep-research-mcp/.venv" >&2
    echo "Please run setup.sh first" >&2
    exit 1
fi

# Check if OpenSERP is running, start it if not
if ! curl -s http://localhost:7000 >/dev/null; then
    echo "OpenSERP is not running, starting it now..." >&2
    cd "$WORK_DIR/openserp"
    if [ -f "./openserp" ]; then
        ./openserp serve -a localhost -p 7000 &
        OPENSERP_PID=$!
        echo "Started OpenSERP with PID: $OPENSERP_PID" >&2
    elif command -v go >/dev/null; then
        go run main.go serve -a localhost -p 7000 &
        OPENSERP_PID=$!
        echo "Started OpenSERP with go run, PID: $OPENSERP_PID" >&2
    else
        echo "Warning: OpenSERP could not be started. Is Go installed?" >&2
    fi
    
    # Give OpenSERP time to start
    sleep 2
fi

# Set up environment for MCP server
echo "Activating virtual environment and setting up environment variables..." >&2
cd "$WORK_DIR/meep-research-mcp"
export OPENSERP_URL="http://localhost:7000"

# Run using the virtual environment Python
echo "Starting MCP server with venv Python..." >&2
exec "$WORK_DIR/meep-research-mcp/.venv/bin/python" -m meep_research_mcp 