#!/bin/bash
set -e

echo "=== Meep Research MCP Runner Script ==="
echo "This script will start the MCP server with Google Custom Search integration."
echo ""

# Set current directory as workspace (where the script is located)
WORK_DIR="$(pwd)"
MCP_PID=""

# Function to cleanup when the script is terminated
cleanup() {
    echo ""
    echo "Shutting down services..."
    
    # Kill MCP server if running
    if [ ! -z "$MCP_PID" ]; then
        echo "Stopping MCP server (PID: $MCP_PID)..."
        kill $MCP_PID 2>/dev/null || true
    fi
    
    echo "Cleanup complete!"
    exit 0
}

# Set up trap to call cleanup function on script termination
trap cleanup EXIT INT TERM

# Check if we're in the right directory (should contain meep_research_mcp)
if [ ! -d "meep_research_mcp" ]; then
    echo "Error: meep_research_mcp directory not found in current directory."
    echo "Please run this script from the root of the Meep Research project."
    echo "Current directory: $(pwd)"
    exit 1
fi

# Check for Python
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH."
    echo "Please install Python 3.10+ or ensure it's in your PATH."
    exit 1
fi

# Check Python version
python_version=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$python_version < 3.10" | bc -l) == 1 ]]; then
    echo "Error: Python 3.10 or higher is required. Current version: $python_version"
    exit 1
fi

# Function to setup configuration interactively
setup_configuration() {
    echo ""
    echo "=== Google Custom Search Configuration Setup ==="
    echo ""
    echo "This will help you set up your Google Custom Search API credentials."
    echo "If you haven't set up Google Custom Search yet, please refer to GOOGLE_SETUP.md"
    echo ""
    
    # Get API key
    while true; do
        echo -n "Enter your Google Custom Search API key: "
        read -r api_key
        if [ -z "$api_key" ]; then
            echo "❌ API key cannot be empty. Please try again."
        else
            break
        fi
    done
    
    # Get CSE ID
    while true; do
        echo -n "Enter your Custom Search Engine ID: "
        read -r cse_id
        if [ -z "$cse_id" ]; then
            echo "❌ CSE ID cannot be empty. Please try again."
        else
            break
        fi
    done
    
    # Create config.json
    cat > config.json << EOF
{
  "google_custom_search": {
    "api_key": "$api_key",
    "cse_id": "$cse_id"
  },
  "rate_limits": {
    "max_requests_per_day": 100,
    "max_requests_per_minute": 10
  },
  "search_defaults": {
    "max_results": 10,
    "timeout_seconds": 30
  }
}
EOF
    
    echo ""
    echo "✅ Configuration saved to config.json"
    
    # Test the configuration
    echo "🔍 Testing your configuration..."
    if python -c "
import sys
sys.path.append('meep_research_mcp')
from config import Config
try:
    config = Config()
    print('✅ Configuration loaded successfully!')
    print(f'   API Key: {config.google_api_key[:8]}...')
    print(f'   CSE ID: {config.google_cse_id}')
    print(f'   Rate limits: {config.max_requests_per_day}/day, {config.max_requests_per_minute}/min')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"; then
        echo "✅ Configuration test passed!"
    else
        echo "❌ Configuration test failed. Please check your credentials."
        exit 1
    fi
    
    echo ""
}

# Check for uv (recommended package manager)
if command -v uv &> /dev/null; then
    echo "Using uv for package management..."
    PYTHON_CMD="uv run python"
    
    # Install dependencies with uv if needed
    echo "Ensuring dependencies are installed..."
    uv sync --quiet
else
    echo "uv not found. Using standard Python..."
    PYTHON_CMD="python"
    
    # Check if dependencies are installed
    echo "Checking dependencies..."
    if ! python -c "import fastmcp, google.cloud" &> /dev/null; then
        echo "Installing dependencies..."
        if [ -f "requirements.txt" ]; then
            pip install -r requirements.txt
        else
            echo "Error: requirements.txt not found and dependencies not installed."
            exit 1
        fi
    fi
fi

echo ""

# Check if configuration file exists
if [ ! -f "config.json" ]; then
    echo "⚠️  Configuration file not found: config.json"
    echo ""
    echo "Would you like to set up the configuration now? (y/n)"
    read -r setup_choice
    
    if [[ "$setup_choice" == "y" || "$setup_choice" == "Y" || "$setup_choice" == "yes" ]]; then
        setup_configuration
    else
        echo ""
        echo "To enable search functionality later:"
        echo "1. Copy config.json.example to config.json"
        echo "2. Edit config.json with your Google Custom Search credentials"
        echo "3. Refer to GOOGLE_SETUP.md for detailed setup instructions"
        echo ""
        echo "The server will start without search functionality."
        echo ""
    fi
else
    echo "✅ Configuration file found: config.json"
    
    # Validate configuration
    if python -c "
import sys
sys.path.append('meep_research_mcp')
from config import Config
try:
    config = Config()
    print('✅ Configuration validated successfully!')
except Exception as e:
    print(f'❌ Configuration error: {e}')
    sys.exit(1)
"; then
        echo "✅ Configuration validated!"
    else
        echo "❌ Configuration validation failed."
        echo "Would you like to reconfigure? (y/n)"
        read -r reconfig_choice
        
        if [[ "$reconfig_choice" == "y" || "$reconfig_choice" == "Y" || "$reconfig_choice" == "yes" ]]; then
            setup_configuration
        else
            echo "Continuing with existing configuration..."
        fi
    fi
    echo ""
fi

echo "=== Starting Meep Research MCP Server ==="
echo "Using Google Custom Search API for search"
echo "Server will run using stdio transport for Claude Desktop integration"
echo ""

# Run the MCP server
$PYTHON_CMD -m meep_research_mcp &
MCP_PID=$!
echo "MCP server started with PID: $MCP_PID"

echo ""
echo "=== MCP Server is running ==="
echo "Server is ready for Claude Desktop integration"
echo "Google Custom Search API integration active"
echo ""
echo "To connect to Claude Desktop:"
echo "1. Open Claude Desktop Settings → Developer → Edit Config"
echo "2. Add this configuration:"
echo "{"
echo "  \"mcpServers\": {"
echo "    \"meep-research\": {"
echo "      \"command\": \"bash\","
echo "      \"args\": [\"$(pwd)/run.sh\"],"
echo "      \"cwd\": \"$(pwd)\""
echo "    }"
echo "  }"
echo "}"
echo ""
echo "Press Ctrl+C to stop the server."

# Wait for user to press Ctrl+C
wait 