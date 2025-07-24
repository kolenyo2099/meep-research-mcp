# Meep Research MCP

A Model Context Protocol (MCP) server that provides advanced search capabilities for AI assistants through Google Custom Search API. Designed for Claude Desktop integration, it features intelligent query translation, robust error handling, and automatic rate limiting.

## Features

- **Direct Google Custom Search Integration**: 
  - Reliable access to Google's search index
  - Built-in rate limiting (100 free searches per day)
  - Automatic quota management and monitoring
  - Real-time API status tracking

- **Advanced Search Capabilities**:
  - Academic search (Google Scholar, arXiv, ResearchGate)
  - News search (Reuters, BBC, AP, NPR)
  - Technical documentation (Stack Overflow, GitHub, MDN)
  - OSINT-focused search strategies

- **Robust Error Handling**:
  - Graceful fallbacks for failed queries
  - Comprehensive error reporting
  - Automatic retry mechanisms
  - Clear troubleshooting messages

- **Natural Language Processing**:
  - Smart query translation
  - Entity extraction
  - Multiple fallback strategies
  - Context-aware search enhancement

## Quick Start

### Prerequisites

- Python 3.10 or higher
- Google Custom Search API credentials
  - API Key
  - Custom Search Engine ID
  - See `GOOGLE_SETUP.md` for detailed instructions

### Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/kolenyo2099/meep-research-mcp.git
   cd meep-research-mcp
   ```

2. **Run Setup Script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   This script will:
   - Install UV package manager (if not present)
   - Create a Python virtual environment
   - Install all required dependencies
   - Set up the project structure
   - Create configuration templates

3. **Configure Google Custom Search**:
   - Copy `config.json.example` to `config.json`
   - Add your Google Custom Search credentials
   - See `GOOGLE_SETUP.md` for detailed setup instructions

### Running the Server

```bash
chmod +x run.sh
./run.sh
```

The script will:
- Check for required dependencies
- Verify configuration files
- Start the MCP server with proper settings
- Handle graceful shutdown on Ctrl+C
- Provide Claude Desktop integration instructions

## Integration with Claude Desktop

1. Open Claude Desktop Settings → Developer → Edit Config
2. Add the configuration from `claude-desktop-config.json`
3. Save and restart Claude Desktop
4. The Meep Research capabilities will be available to Claude

## Search Types

### Academic Search
- Searches academic sources including:
  - Google Scholar
  - arXiv
  - ResearchGate
- Automatically filters for PDF documents
- Great for research papers and academic content

### News Search
- Focuses on reputable news sources:
  - Reuters
  - BBC
  - Associated Press
  - NPR
- Filter out social media noise
- Ideal for current events and fact-checking

### Technical Search
- Targets technical documentation and discussions:
  - Stack Overflow
  - GitHub
  - Python Documentation
  - MDN Web Docs
- Perfect for programming and technical research

### OSINT Search
- Optimized for open-source intelligence:
  - Excludes major social media platforms
  - Focuses on primary sources
  - Enhanced operator support
- Ideal for investigative work

## Rate Limiting

The service includes smart rate limiting to comply with Google Custom Search API limits:

- **Daily Quota**: 100 free searches per day
  - Automatic reset at midnight UTC
  - Real-time quota monitoring
  - Clear feedback when approaching limits

- **Per-Minute Rate**: 10 requests per minute
  - Automatic throttling
  - Queue management
  - Status monitoring

## Error Handling

Robust error handling ensures reliable operation:

1. **Query Translation**:
   - Multiple fallback strategies
   - Original query preservation
   - Clear error reporting

2. **API Interaction**:
   - Automatic retry on transient failures
   - Quota management
   - Clear error messages

3. **Results Processing**:
   - Graceful degradation
   - Partial results handling
   - Detailed error context

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

MIT License - see LICENSE file for details

# Install the package and dependencies
uv pip install -e .
```

#### Using traditional virtual environment

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Clone the repository
git clone https://github.com/yourusername/meep-research-mcp.git
cd meep-research-mcp

# Install the package and dependencies
pip install -e .
```
### Dependencies

The following dependencies will be installed automatically:
- `mcp` - Model Context Protocol library
- `asyncio` - Asynchronous I/O
- `aiohttp` - Async HTTP client for OpenSERP API
- `requests` - HTTP client for additional API calls

## Usage

### Running the server

```bash
# Make sure your virtual environment is activated
# On Windows:
.venv\Scripts\activate  # or venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate  # or source venv/bin/activate

# Basic usage with default settings
meep-research-mcp

# Using a specific transport
meep-research-mcp --transport streamable-http

# With debug logging enabled
meep-research-mcp --debug

# With a custom OpenSERP URL
OPENSERP_URL=http://custom-openserp:8080 meep-research-mcp
```

### Command-line options

- `--transport`: Transport protocol to use (options: stdio, sse, streamable-http; default: stdio)
- `--debug`: Enable debug logging
- `--host`: Host to bind the server to (default: localhost) - only applicable for HTTP transports
- `--port`: Port to bind the server to (default: 8000) - only applicable for HTTP transports

## Claude Desktop Integration

### Setting up in Claude Desktop

1. Install [Claude Desktop](https://claude.ai/desktop) if you haven't already
2. Open Claude Desktop
3. Go to Settings (gear icon)
4. Navigate to the "MCP Servers" section
5. Click "Add Server"
6. Create a configuration based on this template, replacing the paths with your actual installation paths:

```json
{
  "mcpServers": {
    "meepResearch": {
      "name": "Meep Research",
      "command": "/path/to/your/.venv/bin/python",
      "args": ["/path/to/your/minimal_mcp.py"],
      "cwd": "/path/to/your/meep-research-mcp",
      "description": "Meep Research MCP Server"
    }
  }
}
```

Important path replacements:
- `/path/to/your/.venv/bin/python`: Full path to the Python executable in your virtual environment
- `/path/to/your/minimal_mcp.py`: Full path to the minimal_mcp.py script
- `/path/to/your/meep-research-mcp`: Full path to your project directory

To find these paths:
1. Virtual environment Python path: Run `which python` while your virtual environment is activated
2. Project directory: Use the full path to where you cloned the repository
3. minimal_mcp.py: This file should be in your project root directory

7. Click "Save"

### Example configurations for different systems

Here are examples for different operating systems (remember to adjust paths for your system):

For macOS/Linux:
```json
{
  "mcpServers": {
    "meepResearch": {
      "name": "Meep Research",
      "command": "~/meep-research-mcp/.venv/bin/python",
      "args": ["~/meep-research-mcp/minimal_mcp.py"],
      "cwd": "~/meep-research-mcp",
      "description": "Meep Research MCP Server"
    }
  }
}
```

For Windows:
```json
{
  "mcpServers": {
    "meepResearch": {
      "name": "Meep Research",
      "command": "C:\\Users\\YourUsername\\meep-research-mcp\\.venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\YourUsername\\meep-research-mcp\\minimal_mcp.py"],
      "cwd": "C:\\Users\\YourUsername\\meep-research-mcp",
      "description": "Meep Research MCP Server"
    }
  }
}
```

### Troubleshooting Claude Desktop Connection Issues

If you see errors like "MCP meepResearch: spawn python ENOENT" or "Could not connect to MCP server meepResearch", try these solutions:

#### 1. Python Path Issues (ENOENT Errors)

The "ENOENT" error means Claude Desktop can't find the Python executable in your system PATH.

**Solution:** Use the full path to Python in your configuration:

```json
{
  "mcpServers": {
    "meepResearch": {
      "name": "Meep Research",
      "command": "/usr/local/bin/python3",  // Use full path to Python
      "args": ["-m", "meep_research_mcp"],
      "description": "OSINT search capabilities with sophisticated operators"
    }
  }
}
```

Find your Python path by running this in Terminal:
```bash
which python3  # macOS/Linux
where python   # Windows
```

#### 2. Virtual Environment Setup

If you're using a virtual environment, you need to point Claude Desktop to that Python:

```json
{
  "mcpServers": {
    "meepResearch": {
      "name": "Meep Research",
      "command": "~/meep_research_workspace/meep-research-mcp/.venv/bin/python",
      "args": ["-m", "meep_research_mcp"],
      "cwd": "~/meep_research_workspace/meep-research-mcp",
      "description": "OSINT search capabilities with sophisticated operators"
    }
  }
}
```

#### 3. Working Directory Issues

Make sure Claude Desktop can find your package:

```json
{
  "mcpServers": {
    "meepResearch": {
      "name": "Meep Research",
      "command": "python3",
      "args": ["-m", "meep_research_mcp"],
      "cwd": "~/meep_research_workspace/meep-research-mcp", // Important!
      "description": "OSINT search capabilities with sophisticated operators"
    }
  }
}
```

#### 4. Using the Run Script Directly

Instead of having Claude Desktop run Python directly, have it run your script:

```json
{
  "mcpServers": {
    "meepResearch": {
      "name": "Meep Research",
      "command": "~/meep_research_workspace/run-simple.sh",
      "args": [],
      "description": "OSINT search capabilities with sophisticated operators"
    }
  }
}
```

Make sure the script is executable: `chmod +x ~/meep_research_workspace/run-simple.sh`

#### 5. Check if Services Are Running

Make sure both OpenSERP and the MCP server are running:

```bash
# Check if OpenSERP is running
curl http://localhost:7000

# Check if MCP is running separately (if not using the run script)
ps aux | grep meep_research_mcp
```

#### 6. Restart Claude Desktop

After making any changes to your configuration:

1. Close Claude Desktop completely
2. Start Claude Desktop again
3. Check if the connection is established

#### 7. Verify Log Messages

Check Claude Desktop logs for more detailed error messages:

1. Open Claude Desktop
2. Press `Cmd+Option+I` (Mac) or `Ctrl+Shift+I` (Windows) to open Developer Tools
3. Go to the "Console" tab to view error logs

## Available Tools

When connected, the MCP server provides the following tools:

### 1. search_with_operators

Performs a Google web search (via OpenSERP) using advanced search operators tailored to the search type.

**Parameters:**
- `query`: The user's search query
- `search_type`: The type of search to perform
  - `academic`: Optimizes for scholarly sources and educational content
  - `news`: Focuses on recent news articles from reputable sources
  - `technical`: Tailored for programming and technical documentation
  - `general`: Default search with basic quality filters
  - `osint`: Focused on documents with investigation-relevant file types

**Example usage in Claude:**
```
I need to search for academic papers on climate change.
```

### 2. investigation_search

Generates specialized OSINT search queries for specific investigation types.

**Parameters:**
- `topic`: The subject to investigate (person, company, domain, etc.)
- `investigation_type`: The type of investigation to perform
  - `person`: Background check on an individual
  - `company`: Corporate intelligence research
  - `document_leak`: Search for leaked sensitive documents
  - `financial_fraud`: Financial crime investigation
  - `environmental`: Environmental violations research
  - `conflict`: War/conflict verification search
  - `cyber`: Data breach investigation
  - `username`: Username enumeration across platforms
  - `domain`: Domain and DNS investigation

**Example usage in Claude:**
```
Help me investigate Theranos using corporate intelligence searches.
```

### 3. search_strategy_generator

Generates tailored search strategies for researching a topic based on specified perspective.

**Parameters:**
- `topic`: The topic to generate search strategies for
- `perspective`: The perspective to generate strategies from
  - `academic`: Research-oriented strategies
  - `business`: Business intelligence focus
  - `technical`: Technical documentation and implementation
  - `general`: Balanced general research
  - `data`: Data-focused research strategies

**Example usage in Claude:**
```
Generate search strategies for researching "renewable energy" from a business perspective.
```

### 4. extract_content

Provides basic metadata about a URL.

**Parameters:**
- `url`: The URL to extract metadata from

**Example usage in Claude:**
```
Get information about https://example.com/article
```

## Example Workflows

### Journalistic Investigation

```
User: I need to investigate a company called Theranos for potential fraud.

Claude: I'll help you investigate Theranos using specialized OSINT search strategies.

[Claude uses investigation_search with investigation_type=company and topic=Theranos]

Based on my searches, I've found multiple SEC filings showing regulatory actions, several lawsuits from investors, and numerous news articles about their questionable blood testing technology. Let me share the key findings...
```

### Person Background Check

```
User: Can you help me research the background of John Smith who claims to be a cybersecurity expert?

Claude: Let me search for information about John Smith using specialized person search strategies.

[Claude uses investigation_search with investigation_type=person and topic="John Smith cybersecurity"]

I've found John Smith's LinkedIn profile showing his employment history, several conference presentations he's given on cybersecurity topics, and publications in industry journals. Here's what I can tell you about his credentials...
```

## Development

### Project structure

- `meep_research_mcp/server.py`: Core server implementation
- `meep_research_mcp/search_strategies.py`: OSINT search strategies
- `meep_research_mcp/__main__.py`: Command-line interface

## Troubleshooting

### Common issues

1. **OpenSERP connection error**
   
   Solution: Make sure the enhanced OpenSERP is running and accessible at the configured URL. Check the OPENSERP_URL environment variable.

2. **MCP server not showing in Claude**
   
   Solution: Make sure the server is configured correctly in Claude Desktop settings and that it's using the "stdio" transport.

3. **Search returns error responses**
   
   Solution: Check that your query is valid and that OpenSERP is functioning correctly.

4. **Virtual environment issues**

   Solution: If facing issues with the virtual environment, ensure you've activated it properly before running commands. Try creating a fresh environment if problems persist.

## License

MIT

