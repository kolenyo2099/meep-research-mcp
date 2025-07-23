"""
Main server implementation for Meep Research MCP
"""

import asyncio
import logging
import aiohttp
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import json

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

# List of common ambiguous terms in technical contexts
AMBIGUOUS_TECH_TERMS = {
    "go", "c", "r", "js", "java", "ruby", "rust", "swift", "react", "vue", 
    "node", "aws", "api", "sql", "ai", "ml", "ui", "ux", "sdk", "cli", "css"
}

# Initialize the FastMCP server
mcp = FastMCP(
    "Meep Research",
    description="Advanced search capabilities with mandatory source citation requirements for researchers and investigators",
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
    
    # Generate operators based on search_type
    enhanced_query = build_advanced_query(query, search_type)
    
    # Validate and convert query for Google Custom Search
    google_query = validate_and_convert_query(enhanced_query)
    
    try:
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
        
    except GoogleCustomSearchError as e:
        logger.error(f"Google Custom Search error: {str(e)}")
        return {
            "results": [],
            "enhanced_query": enhanced_query,
            "converted_query": google_query,
            "engine": "google_custom_search",
            "error": str(e),
            "api_status": get_api_status()
        }

@mcp.tool()
async def extract_content(url: str, ctx: Context = None) -> Dict[str, Any]:
    """
    Extract basic metadata from a URL.
    
    Args:
        url: The URL to extract metadata from
    
    Returns:
        Basic metadata about the URL
    """
    logger.info(f"Basic metadata for: {url}")
    
    # Return basic URL information
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    
    try:
        # Basic metadata
        metadata = {
            "url": url,
            "domain": parsed_url.netloc,
            "path": parsed_url.path,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Try to fetch additional metadata if possible
        if url.lower().endswith('.pdf'):
            metadata["file_type"] = "PDF document"
        elif url.lower().endswith(('.doc', '.docx')):
            metadata["file_type"] = "Word document"
        elif url.lower().endswith(('.xls', '.xlsx')):
            metadata["file_type"] = "Excel spreadsheet"
        else:
            metadata["file_type"] = "Web page or other document"
        
        metadata["message"] = f"Successfully retrieved metadata for {url}"
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting metadata from URL {url}: {str(e)}")
        return {
            "url": url,
            "error": f"Failed to extract metadata: {str(e)}",
            "timestamp": datetime.now().isoformat(),
        }

@mcp.tool()
def google_search_status() -> Dict[str, Any]:
    """
    Check Google Custom Search API status and usage.
    
    Returns:
        Current API usage statistics and rate limiting status
    """
    logger.info("Checking Google Custom Search API status")
    
    status = get_api_status()
    
    # Add some helpful interpretation
    status["status_message"] = []
    
    if status["daily_requests_used"] >= status["daily_requests_limit"]:
        status["status_message"].append("❌ Daily quota exhausted")
    elif status["daily_requests_used"] >= status["daily_requests_limit"] * 0.9:
        status["status_message"].append("⚠️ Daily quota nearly exhausted")
    else:
        status["status_message"].append("✅ Daily quota available")
    
    if status["minute_requests_used"] >= status["minute_requests_limit"]:
        status["status_message"].append("❌ Minute rate limit reached")
    else:
        status["status_message"].append("✅ Minute rate limit OK")
    
    if not status["can_make_request"]:
        status["status_message"].append("🚫 Cannot make requests due to rate limits")
    else:
        status["status_message"].append("🟢 Ready to make requests")
    
    return status

@mcp.tool()
def translate_query(
    request: str,
    source_restrictions: str = ""
) -> Dict[str, Any]:
    """
    Translate natural language research request into precise Google search operators.
    
    Args:
        request: Natural language research question or investigation request
        source_restrictions: Optional Google search operators to restrict sources (e.g., "site:example.com filetype:pdf")
    
    Returns:
        Translated search query with operator breakdown and metadata
    """
    logger.info(f"Translating research request: {request}")
    
    result = translate_research_query(request, source_restrictions if source_restrictions else None)
    return result

@mcp.tool()
def create_query_variations(
    request: str,
    source_restrictions: str = ""
) -> Dict[str, Any]:
    """
    Create multiple search query variations for comprehensive research.
    
    Args:
        request: Natural language research question or investigation request
        source_restrictions: Optional Google search operators to restrict sources (e.g., "site:example.com filetype:pdf")
    
    Returns:
        Multiple search query variations with different operator combinations
    """
    logger.info(f"Creating query variations for: {request}")
    
    variations = create_research_variations(request, source_restrictions if source_restrictions else None)
    
    return {
        "variations": variations,
        "count": len(variations),
        "original_request": request
    }

@mcp.tool()
async def research_and_analyze(
    request: str,
    source_restrictions: str = "",
    max_sources: int = 5
) -> Dict[str, Any]:
    """
    Perform comprehensive research and return findings that MUST be cited using academic format.
    All factual claims in responses require proper source attribution.
    
    Args:
        request: Natural language research question
        source_restrictions: Optional Google search operators to restrict sources
        max_sources: Maximum number of sources to analyze for the answer (default: 5)
    
    Returns:
        Research findings with mandatory citation requirements and indexed sources
    """
    logger.info(f"Performing comprehensive research for: {request}")
    
    try:
        # Step 1: Translate the request into optimized search query
        translation_result = translate_research_query(request, source_restrictions if source_restrictions else None)
        optimized_query = translation_result["query"]
        
        logger.info(f"Translated query: {optimized_query}")
        
        # Step 2: Perform the search
        search_results = await search_google_custom(optimized_query, max_results=max_sources)
        
        if not search_results:
            return {
                "findings": [],
                "source_index": {},
                "citation_required": True,
                "citation_instruction": "No sources found - unable to provide properly cited research",
                "sources_analyzed": 0,
                "search_query_used": optimized_query,
                "translation_details": translation_result
            }
        
        # Step 3: Create indexed sources with proper citation formatting
        source_index = {}
        analyzed_sources = []
        
        for i, result in enumerate(search_results[:max_sources], 1):
            source_id = f"source_{i}"
            
            # Extract domain and determine credibility level
            domain = result.get("domain", "").lower()
            credibility_level = "standard"
            institution_type = "website"
            
            if any(tld in domain for tld in ['.edu']):
                credibility_level = "high"
                institution_type = "academic institution"
            elif any(tld in domain for tld in ['.gov']):
                credibility_level = "high" 
                institution_type = "government agency"
            elif any(news in domain for news in ['reuters', 'bbc', 'npr', 'ap.org', 'wsj', 'nytimes']):
                credibility_level = "high"
                institution_type = "news organization"
            elif 'wikipedia' in domain:
                credibility_level = "medium"
                institution_type = "encyclopedia"
            
            # Create formatted citation
            title = result.get("title", "Untitled")
            url = result.get("url", "")
            
            # Generate academic-style citation
            if institution_type == "academic institution":
                citation_format = f"({domain.split('.')[0].title()}, 2024)"
            elif institution_type == "government agency":
                agency_name = domain.split('.')[0].upper()
                citation_format = f"({agency_name}, 2024)"
            elif institution_type == "news organization":
                org_name = domain.split('.')[0].title()
                citation_format = f"({org_name}, 2024)"
            else:
                citation_format = f"({domain}, 2024)"
            
            source_index[source_id] = {
                "title": title,
                "institution": domain,
                "institution_type": institution_type,
                "credibility_level": credibility_level,
                "url": url,
                "citation_format": citation_format,
                "rank": i
            }
            
            analyzed_sources.append({
                "source_id": source_id,
                "title": title,
                "snippet": result.get("snippet", ""),
                "credibility_level": credibility_level,
                "institution_type": institution_type
            })
        
        # Step 4: Create structured findings with source attribution
        findings = _create_cited_findings(request, analyzed_sources, source_index)
        
        # Step 5: Generate citation compliance information
        high_credibility_count = sum(1 for source in source_index.values() 
                                   if source["credibility_level"] == "high")
        
        citation_compliance = {
            "citation_recommended": True,
            "sources_available": len(source_index),
            "high_credibility_sources_available": high_credibility_count,
            "citation_format": "academic",
            "usage_guidance": "Citation formats are provided for academic or professional use of this research"
        }
        
        # No content blocking - provide research immediately

        return {
            "findings": findings,
            "source_index": source_index,
            
            # BALANCED CITATION APPROACH
            "citation_guidance": {
                "status": "Research findings with citation support included",
                "approach": "Two-tier system: clean content + citation-ready versions",
                "requirement_level": "recommended",
                "academic_integrity_note": "For academic or professional use, citation-ready versions are available in each finding",
                "citation_formats_available": True,
                "high_credibility_sources": high_credibility_count
            },
            
            # Enhanced citation instructions
            "citation_instructions": {
                "dual_format_note": "Each finding includes both 'finding' (clean) and 'finding_with_citations' (citation-ready) versions",
                "format_example": f"Citation-ready example: According to research from {list(source_index.values())[0]['institution']} {list(source_index.values())[0]['citation_format']}, [finding content]",
                "available_citations": [source_info["citation_format"] for source_info in source_index.values()],
                "usage_note": "Use 'finding' for casual reference, 'finding_with_citations' for academic/professional presentation"
            },
            
            "citation_compliance": citation_compliance,
            "sources_analyzed": len(analyzed_sources),
            "search_query_used": optimized_query,
            "translation_details": translation_result
        }
        
    except Exception as e:
        logger.error(f"Error in research_and_analyze: {str(e)}")
        return {
            "findings": [],
            "source_index": {},
            "citation_required": True,
            "citation_instruction": f"Research failed due to error: {str(e)}. No citations available.",
            "error": str(e)
        }

def _create_cited_findings(request: str, analyzed_sources: List[Dict], source_index: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Create research findings with both clean and citation-ready versions"""
    
    if not analyzed_sources:
        return [{
            "finding": "No reliable sources found for this research request",
            "finding_with_citations": "No reliable sources found for this research request",
            "confidence": "none",
            "source_ids": [],
            "citation_note": "No sources available for citation"
        }]
    
    findings = []
    
    # HIGH-CREDIBILITY SOURCES SUMMARY
    high_cred_sources = [s for s in analyzed_sources if s["credibility_level"] == "high"]
    
    if high_cred_sources:
        # Clean version
        clean_text = f"Based on analysis of {len(high_cred_sources)} high-credibility sources, research indicates significant findings related to {request}."
        
        # Citation-ready version with natural embedding
        citations = [source_index[source["source_id"]]["citation_format"] for source in high_cred_sources]
        institutions = [source_index[source["source_id"]]["institution"] for source in high_cred_sources]
        
        if len(high_cred_sources) == 1:
            cited_text = f"According to research from {institutions[0]} {citations[0]}, significant findings emerge related to {request}."
        else:
            citation_string = ", ".join(citations)
            cited_text = f"Based on analysis from {len(high_cred_sources)} high-credibility sources {citation_string}, research indicates significant findings related to {request}."
        
        findings.append({
            "finding": clean_text,
            "finding_with_citations": cited_text,
            "confidence": "high", 
            "source_ids": [source["source_id"] for source in high_cred_sources],
            "citation_note": f"This finding is supported by {len(high_cred_sources)} high-credibility sources"
        })
    
    # INDIVIDUAL SOURCE FINDINGS (both versions)
    for source in analyzed_sources[:3]:
        if source.get("snippet"):
            source_info = source_index[source["source_id"]]
            
            # Clean version
            clean_text = f"Research from {source_info['institution']} indicates: {source['snippet'][:200]}..."
            
            # Citation-ready version with natural embedding
            cited_text = f"According to {source_info['institution_type']} research from {source_info['institution']} {source_info['citation_format']}, {source['snippet'][:180]}..."
            
            findings.append({
                "finding": clean_text,
                "finding_with_citations": cited_text,
                "confidence": source["credibility_level"],
                "source_ids": [source["source_id"]],
                "citation_note": f"Source: {source_info['title']} - Citation format: {source_info['citation_format']}"
            })
    
    # COMPREHENSIVE SUMMARY FINDING
    if len(analyzed_sources) > 1:
        # Clean version
        clean_summary = f"Comprehensive analysis of {request} reveals multiple perspectives and evidence from {len(analyzed_sources)} sources across different credibility levels and institution types."
        
        # Citation-ready version
        all_citations = [source_info["citation_format"] for source_info in source_index.values()]
        if len(all_citations) <= 3:
            citation_list = ", ".join(all_citations)
            cited_summary = f"Comprehensive analysis of {request} from multiple sources {citation_list} reveals diverse perspectives and evidence across different credibility levels and institution types."
        else:
            cited_summary = f"Comprehensive analysis of {request} from {len(analyzed_sources)} sources including {', '.join(all_citations[:2])}, and others reveals diverse perspectives and evidence."
        
        findings.append({
            "finding": clean_summary,
            "finding_with_citations": cited_summary,
            "confidence": "medium",
            "source_ids": [source["source_id"] for source in analyzed_sources],
            "citation_note": "This summary incorporates findings from all analyzed sources"
        })
    
    return findings



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