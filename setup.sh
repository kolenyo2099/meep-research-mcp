#!/bin/bash
set -e

echo "=== Meep Research MCP Setup Script ==="
echo "This script will install UV, create a virtual environment, and set up required dependencies."
echo ""

# Use current directory as the workspace
CURRENT_DIR=$(pwd)
echo "Setting up in current directory: ${CURRENT_DIR}"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "UV not found. Installing UV..."
    curl -fsSL https://astral.sh/uv/install.sh | bash
    
    # Source the profile to make UV available in this session
    if [ -f ~/.bashrc ]; then
        source ~/.bashrc
    elif [ -f ~/.zshrc ]; then
        source ~/.zshrc
    fi
    
    # Verify UV was installed
    if ! command -v uv &> /dev/null; then
        echo "UV installation failed. Please install UV manually from https://github.com/astral-sh/uv"
        echo "Then run this script again."
        exit 1
    fi
    echo "UV installed successfully!"
else
    echo "UV already installed!"
fi

# Create virtual environment with UV
echo "Creating virtual environment in the current directory..."
uv venv
source .venv/bin/activate

# Check if this is a Python project
if [ ! -f "pyproject.toml" ] && [ ! -f "setup.py" ]; then
    echo "No Python project files found. Creating a basic pyproject.toml file..."
    cat > pyproject.toml << EOF
[build-system]
requires = ["setuptools>=42", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "meep-research-mcp"
version = "0.1.0"
description = "Meep Research MCP with Google Custom Search integration"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
dependencies = [
    "fastmcp",
    "asyncio",
    "aiohttp",
    "google-api-python-client",
]

[project.scripts]
meep-research-mcp = "meep_research_mcp.__main__:main"
EOF
    echo "Created pyproject.toml"
    
    # Ensure the package directory exists
    if [ ! -d "meep_research_mcp" ]; then
        echo "Creating meep_research_mcp package directory..."
        mkdir -p meep_research_mcp
        
        # Create an __init__.py file
        echo '"""Meep Research MCP Package"""' > meep_research_mcp/__init__.py
        
        # Create a skeleton server.py if it doesn't exist
        if [ ! -f "meep_research_mcp/server.py" ]; then
            echo "Creating skeleton server.py..."
            cat > meep_research_mcp/server.py << EOF
"""
Main server implementation for Meep Research MCP
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server.fastmcp import FastMCP, Context

try:
    from .search_strategies import translate_research_query, create_research_variations
    from .google_search import search_google_custom, validate_and_convert_query, get_api_status, GoogleCustomSearchError
except ImportError:
    # Fallback for when running as script
    from search_strategies import translate_research_query, create_research_variations
    from google_search import search_google_custom, validate_and_convert_query, get_api_status, GoogleCustomSearchError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("meep-research")

# Initialize the FastMCP server
mcp = FastMCP(
    "Meep Research",
    description="Advanced search capabilities with OSINT strategies for journalists and investigators",
    dependencies=["asyncio", "aiohttp"]
)

@mcp.tool()
async def search_with_operators(
    query: str,
    search_type: str = "general",
    ctx: Context = None
) -> Dict[str, Any]:
    """
    Search the web using advanced search operators.
    
    Args:
        query: The user's search query
        search_type: The type of search to perform (academic, news, general, technical, osint)
    
    Returns:
        Search results with enhanced query information
    """
    logger.info(f"Handling search: {query} (type: {search_type})")
    
    try:
        # Generate operators based on search_type
        enhanced_query = build_advanced_query(query, search_type)
        
        # Validate and convert query for Google Custom Search
        google_query = validate_and_convert_query(enhanced_query)
        
        # Perform search using Google Custom Search (uses max_results from config)
        results = await search_google_custom(google_query)
        
        # Get API status for monitoring
        api_status = get_api_status()
        
        return {
            "results": results,
            "enhanced_query": enhanced_query,
            "converted_query": google_query,
            "engine": "google_custom_search",
            "api_status": api_status
        }
        
    except (GoogleCustomSearchError, ValueError, Exception) as e:
        logger.error(f"Search error: {str(e)}")
        # Try to get enhanced_query for error response
        try:
            enhanced_query = build_advanced_query(query, search_type)
        except:
            enhanced_query = query
            
        return {
            "results": [],
            "enhanced_query": enhanced_query,
            "converted_query": query,
            "engine": "google_custom_search",
            "error": str(e),
            "api_status": get_api_status()
        }

def build_advanced_query(query: str, search_type: str) -> str:
    """Build advanced search query with operators based on search type"""
    
    # Enhanced query building for Google Custom Search
    if search_type == "academic":
        return f'{query} site:scholar.google.com OR site:arxiv.org OR site:researchgate.net OR filetype:pdf'
    elif search_type == "news":
        return f'{query} site:reuters.com OR site:bbc.com OR site:ap.org OR site:npr.org'
    elif search_type == "technical":
        return f'{query} site:stackoverflow.com OR site:github.com OR site:docs.python.org OR site:developer.mozilla.org'
    elif search_type == "osint":
        return f'{query} -site:facebook.com -site:twitter.com -site:instagram.com'
    else:
        # General search with basic enhancement
        return query

def main():
    """Run the server directly"""
    print("Starting Meep Research MCP Server using stdio transport")
    print("Press Ctrl+C to stop the server")
    
    try:
        mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        print("Server stopped")

if __name__ == "__main__":
    main()
EOF
        fi
        
        # Create a skeleton __main__.py if it doesn't exist
        if [ ! -f "meep_research_mcp/__main__.py" ]; then
            echo "Creating skeleton __main__.py..."
            # Create google_search.py
            # Create search_strategies.py
            cat > meep_research_mcp/search_strategies.py << EOF
"""
Simple Research Query Translator
Converts natural language research requests into precise Google search operators.
Designed for MCP integration with focus on user-controlled source restrictions.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import re
import logging

logger = logging.getLogger(__name__)

@dataclass
class SearchQuery:
    """Simple container for a search query and its purpose"""
    query: str
    purpose: str
    operator_breakdown: Dict[str, str]

class QueryTranslator:
    """
    Simple translator that converts natural language research requests 
    into precise Google search operators with user-specified restrictions.
    """
    
    def __init__(self):
        # Core Google operators
        self.operators = {
            'exact_phrase': lambda text: f'"{text}"',
            'site_restrict': lambda domain: f'site:{domain}',
            'exclude_site': lambda domain: f'-site:{domain}',
            'filetype': lambda ext: f'filetype:{ext}',
            'intitle': lambda text: f'intitle:"{text}"',
            'inurl': lambda text: f'inurl:{text}',
            'intext': lambda text: f'intext:"{text}"',
            'proximity': lambda term1, term2, distance: f'"{term1}" AROUND({distance}) "{term2}"',
            'date_after': lambda date: f'after:{date}',
            'date_before': lambda date: f'before:{date}',
            'exclude_term': lambda term: f'-{term}',
            'wildcard': lambda phrase: f'"{phrase}"',
            'or_operator': lambda terms: f'({" OR ".join(terms)})',
            'and_operator': lambda terms: f'{" ".join(terms)}'
        }
        
        # Common patterns in research requests
        self.patterns = {
            'proximity_request': re.compile(r'(.*?)\s+(mentioned|described|discussed|appear)\s+(close|together|near)\s+(.*?)'),
            'site_restriction': re.compile(r'(on|in|from)\s+([\w\.-]+\.\w+)'),
            'content_location': re.compile(r'in\s+(title|url|text|paragraphs?)'),
            'exclusion_request': re.compile(r'(but not|exclude|without|except)\s+(.*?)'),
            'time_restriction': re.compile(r'(after|since|before|until)\s+(\d{4}(?:/\d{1,2}(?:/\d{1,2})?)?)')
        }

    def translate_request(self, request: str, source_restrictions: Optional[str] = None) -> SearchQuery:
        """Main method: translate natural language request into Google search operators."""
        try:
            # Clean and prepare the request
            request = request.strip()
            operator_breakdown = {}
            query_parts = []
            
            # Add user-specified source restrictions first (highest priority)
            if source_restrictions:
                query_parts.append(source_restrictions)
                operator_breakdown['source_restrictions'] = source_restrictions
            
            # Extract entities and create query
            entities = self._extract_entities(request)
            if entities:
                query = ' '.join(f'"{entity}"' for entity in entities)
                query_parts.append(query)
                operator_breakdown['entities'] = entities
            else:
                # FIXED: Proper fallback if no entities found
                query_parts.append(request)
                operator_breakdown['fallback'] = "Used original request due to no entities found"
            
            final_query = ' '.join(query_parts)
            
            # FIXED: Another fallback check
            if not final_query.strip():
                final_query = request
                operator_breakdown['fallback'] = "Used original request due to empty translation"
            
            return SearchQuery(
                query=final_query,
                purpose=self._generate_purpose(request),
                operator_breakdown=operator_breakdown
            )
        except Exception as e:
            logger.error(f"Error translating request: {str(e)}")
            # Final fallback
            return SearchQuery(
                query=request.strip(),
                purpose=f"Fallback query: {request[:100]}",
                operator_breakdown={"error": str(e), "fallback": "Translation failed"}
            )
EOF

            cat > meep_research_mcp/google_search.py << EOF
"""
Google Custom Search API implementation for Meep Research MCP
"""
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
from datetime import datetime, timedelta
import logging
import time
import aiohttp

try:
    from .config import get_config, ConfigError
except ImportError:
    # Fallback for when running as script
    from config import get_config, ConfigError

logger = logging.getLogger(__name__)

# Google Custom Search API URL
GOOGLE_CUSTOM_SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

class GoogleCustomSearchError(Exception):
    """Custom exception for Google Custom Search API errors"""
    pass

class GoogleSearchRateLimiter:
    """Rate limiter for Google Custom Search API"""
    
    def __init__(self, config=None):
        if config is None:
            try:
                config = get_config()
            except ConfigError:
                # Use defaults if config not available
                self.max_requests_per_day = 100
                self.max_requests_per_minute = 10
            else:
                self.max_requests_per_day = config.max_requests_per_day
                self.max_requests_per_minute = config.max_requests_per_minute
        else:
            self.max_requests_per_day = config.max_requests_per_day
            self.max_requests_per_minute = config.max_requests_per_minute
            
        self.daily_count = 0
        self.minute_requests = []
        self.last_reset = time.time()

    def can_make_request(self) -> bool:
        """Check if we can make a request within rate limits"""
        current_time = time.time()
        
        # Reset daily counter if it's a new day
        if current_time - self.last_reset > 86400:  # 24 hours
            self.daily_count = 0
            self.last_reset = current_time
            
        # Clean old minute requests
        self.minute_requests = [req_time for req_time in self.minute_requests 
                               if current_time - req_time < 60]
        
        return (self.daily_count < self.max_requests_per_day and 
                len(self.minute_requests) < self.max_requests_per_minute)

    def record_request(self):
        """Record that a request was made"""
        current_time = time.time()
        self.daily_count += 1
        self.minute_requests.append(current_time)

# Global rate limiter instance
rate_limiter = None

def get_rate_limiter():
    """Get or create the global rate limiter instance"""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = GoogleSearchRateLimiter()
    return rate_limiter

def can_make_request() -> bool:
    """Check if we can make a request based on rate limits"""
    try:
        limiter = get_rate_limiter()
        return limiter.can_make_request()
    except Exception as e:
        logger.error(f"Error checking rate limits: {e}")
        return False

def get_reset_time() -> str:
    """Get human readable time until rate limit resets"""
    try:
        limiter = get_rate_limiter()
        current_time = time.time()
        
        # Check daily reset (resets at midnight UTC)
        if limiter.daily_count >= limiter.max_requests_per_day:
            tomorrow = datetime.fromtimestamp(current_time) + timedelta(days=1)
            midnight = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_until_reset = (midnight.timestamp() - current_time)
            hours = int(seconds_until_reset // 3600)
            minutes = int((seconds_until_reset % 3600) // 60)
            return f"{hours}h {minutes}m"
        
        # Check minute reset
        if len(limiter.minute_requests) >= limiter.max_requests_per_minute:
            oldest_request = min(limiter.minute_requests)
            seconds_until_reset = 60 - (current_time - oldest_request)
            return f"{int(seconds_until_reset)}s"
        
        return "now"
    except Exception as e:
        logger.error(f"Error getting reset time: {e}")
        return "unknown"

def _record_request():
    """Record a request for rate limiting"""
    try:
        limiter = get_rate_limiter()
        limiter.record_request()
    except Exception as e:
        logger.error(f"Error recording request: {e}")
EOF

            cat > meep_research_mcp/__main__.py << EOF
"""
Command-line entry point for Meep Research MCP.
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
EOF
        fi
    fi
fi

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

# Explicitly install required packages
echo "Installing required packages..."
uv add fastmcp aiohttp google-api-python-client

# Create configuration files if they don't exist
if [ ! -f "config.json.example" ]; then
    echo "Creating example configuration file..."
    cat > config.json.example << EOF
{
  "google_custom_search": {
    "api_key": "your-google-custom-search-api-key",
    "cse_id": "your-custom-search-engine-id"
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
    echo "Created config.json.example"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    echo "Creating .gitignore file..."
    cat > .gitignore << EOF
# Generated package directory - created by setup.sh
meep_research_mcp/

# User-specific configuration with sensitive data
config.json

# Generated files
*.pyc
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv/
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
*.log
logs/

# Runtime
*.pid
*.seed
*.pid.lock

# Coverage reports
htmlcov/
.coverage
.coverage.*
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json
EOF
    echo "Created .gitignore"
fi

# Check if run.sh exists
if [ ! -f "run.sh" ]; then
    echo "Creating basic run.sh script..."
    cat > run.sh << EOF
#!/bin/bash
set -e

echo "=== Meep Research MCP Runner Script ==="
echo "This script will start the MCP server with Google Custom Search integration."
echo ""

# Set current directory as workspace (where the script is located)
WORK_DIR="\$(pwd)"
MCP_PID=""

# Function to cleanup when the script is terminated
cleanup() {
    echo ""
    echo "Shutting down services..."
    
    # Kill MCP server if running
    if [ ! -z "\$MCP_PID" ]; then
        echo "Stopping MCP server (PID: \$MCP_PID)..."
        kill \$MCP_PID 2>/dev/null || true
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
    echo "Current directory: \$(pwd)"
    exit 1
fi

# Check for Python
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH."
    echo "Please install Python 3.10+ or ensure it's in your PATH."
    exit 1
fi

# Check if configuration file exists
if [ ! -f "config.json" ]; then
    echo "⚠️  Configuration file not found: config.json"
    echo ""
    echo "To enable search functionality:"
    echo "1. Copy config.json.example to config.json"
    echo "2. Edit config.json with your Google Custom Search credentials"
    echo "3. Refer to GOOGLE_SETUP.md for detailed setup instructions"
    echo ""
    echo "The server will start without search functionality."
    echo ""
else
    echo "✅ Configuration file found: config.json"
    echo ""
fi

echo "=== Starting Meep Research MCP Server ==="
echo "Using Google Custom Search API for search"
echo "Server will run using stdio transport for Claude Desktop integration"
echo ""

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
fi

# Run the MCP server
\$PYTHON_CMD -m meep_research_mcp &
MCP_PID=\$!
echo "MCP server started with PID: \$MCP_PID"

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
echo "      \"args\": [\"\$(pwd)/run.sh\"],"
echo "      \"cwd\": \"\$(pwd)\""
echo "    }"
echo "  }"
echo "}"
echo ""
echo "Press Ctrl+C to stop the server."

# Wait for user to press Ctrl+C
wait
EOF
    chmod +x run.sh
    echo "Created run.sh"
else
    echo "✅ run.sh already exists, keeping current version"
fi

# Create Claude Desktop configuration file
cat > claude-desktop-config.json << EOF
{
  "mcpServers": {
    "meep-research": {
      "command": "bash",
      "args": ["${CURRENT_DIR}/run.sh"],
      "cwd": "${CURRENT_DIR}",
      "description": "Meep Research MCP with Google Custom Search integration"
    }
  }
}
EOF

echo ""
echo "=== Setup completed successfully! ==="
echo ""
echo "Next steps:"
echo "1. Configure your Google Custom Search API:"
echo "   - Copy config.json.example to config.json"
echo "   - Edit config.json with your API credentials"
echo "   - See GOOGLE_SETUP.md for detailed instructions"
echo ""
echo "2. To run the MCP server:"
echo "   ./run.sh"
echo ""
echo "3. To configure Claude Desktop, copy the configuration from:"
echo "   ${CURRENT_DIR}/claude-desktop-config.json"
echo ""
echo "Current directory: ${CURRENT_DIR}" 