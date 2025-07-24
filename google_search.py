"""
Google Custom Search API implementation for Meep Research MCP
"""

import logging
try:
    import aiohttp
except ImportError as e:
    aiohttp = None
    logging.error("aiohttp package is required for Google Custom Search")
    raise
import asyncio
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus
import time
import json
from datetime import datetime, timedelta

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
    limiter = get_rate_limiter()
    return limiter.can_make_request()

def get_reset_time() -> str:
    """Get human readable time until rate limit resets"""
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

def _record_request():
    """Record a request for rate limiting"""
    limiter = get_rate_limiter()
    limiter.record_request()

async def search_google_custom(
    query: str, 
    max_results: Optional[int] = None,
    start_index: int = 1
) -> List[Dict[str, Any]]:
    """
    Search using Google Custom Search API.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (from config if not provided)
        start_index: Starting index for results (1-based)
    
    Returns:
        List of search results
    """
    
    try:
        config = get_config()
    except ConfigError as e:
        logger.error(f"Configuration error: {e}")
        raise GoogleCustomSearchError(f"Configuration error: {e}")
    
    if max_results is None:
        max_results = config.default_max_results
    
    # Check rate limits
    if not can_make_request():
        remaining_time = get_reset_time()
        raise GoogleCustomSearchError(f"Rate limit exceeded. Try again in {remaining_time}")
    
    all_results = []
    current_start = start_index
    
    try:
        # Google Custom Search API allows max 10 results per request
        # For more results, we need to make multiple requests
        results_needed = max_results
        
        while results_needed > 0 and current_start <= 100:  # Google limits to 100 total results
            # Google API allows max 10 results per request
            current_batch_size = min(results_needed, 10)
            
            # Make API request
            params = {
                "q": query,
                "cx": config.google_cse_id,
                "key": config.google_api_key,
                "num": current_batch_size,
                "start": current_start,
                "safe": "medium",
                "fields": "items(title,link,snippet,displayLink,formattedUrl)"
            }
            
            logger.info(f"Making Google Custom Search request: query='{query}', num={current_batch_size}, start={current_start}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(GOOGLE_CUSTOM_SEARCH_URL, params=params) as response:
                    
                    # Update rate limiting
                    _record_request()
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract results
                        items = data.get("items", [])
                        
                        for item in items:
                            all_results.append({
                                "title": item.get("title", ""),
                                "url": item.get("link", ""),
                                "snippet": item.get("snippet", ""),
                                "domain": item.get("displayLink", ""),
                                "formatted_url": item.get("formattedUrl", ""),
                                "rank": len(all_results) + 1
                            })
                        
                        # Update for next iteration
                        results_needed -= len(items)
                        current_start += len(items)
                        
                        # If we got fewer results than requested, we've reached the end
                        if len(items) < current_batch_size:
                            break
                            
                        # Add small delay between requests to be respectful
                        if results_needed > 0:
                            await asyncio.sleep(0.1)
                        
                    elif response.status == 429:
                        # Rate limited
                        raise GoogleCustomSearchError("Rate limit exceeded by Google API")
                    
                    elif response.status == 403:
                        error_data = await response.json()
                        error_msg = error_data.get("error", {}).get("message", "API key invalid or quota exceeded")
                        raise GoogleCustomSearchError(f"API Error: {error_msg}")
                    
                    else:
                        error_text = await response.text()
                        raise GoogleCustomSearchError(f"API request failed with status {response.status}: {error_text[:200]}")
        
        logger.info(f"Google Custom Search returned {len(all_results)} results for query: '{query}'")
        return all_results
        
    except aiohttp.ClientError as e:
        logger.error(f"Network error during Google Custom Search: {str(e)}")
        raise GoogleCustomSearchError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during Google Custom Search: {str(e)}")
        raise GoogleCustomSearchError(f"Unexpected error: {str(e)}")

def parse_google_results(data: Dict[str, Any], original_query: str) -> List[Dict[str, Any]]:
    """
    Parse Google Custom Search API response
    
    Args:
        data: Raw API response data
        original_query: The original search query
    
    Returns:
        List of parsed search results
    """
    results = []
    
    # Check if we have search results
    items = data.get('items', [])
    if not items:
        logger.info(f"No results found for query: {original_query}")
        return results
    
    search_info = data.get('searchInformation', {})
    total_results = search_info.get('totalResults', '0')
    search_time = search_info.get('searchTime', 0)
    
    logger.info(f"Found {total_results} total results in {search_time} seconds")
    
    for item in items:
        try:
            result = {
                'title': item.get('title', 'No title'),
                'url': item.get('link', ''),
                'snippet': item.get('snippet', 'No description available'),
                'display_url': item.get('displayLink', ''),
                'formatted_url': item.get('formattedUrl', ''),
                'cache_id': item.get('cacheId', ''),
                'search_engine': 'google_custom_search'
            }
            
            # Add additional metadata if available
            if 'pagemap' in item:
                pagemap = item['pagemap']
                
                # Extract images if available
                if 'cse_image' in pagemap:
                    images = pagemap['cse_image']
                    if images:
                        result['image'] = images[0].get('src', '')
                
                # Extract meta description if available
                if 'metatags' in pagemap:
                    metatags = pagemap['metatags']
                    if metatags:
                        meta = metatags[0]
                        result['meta_description'] = meta.get('og:description', meta.get('description', ''))
                        result['meta_keywords'] = meta.get('keywords', '')
                        result['og_title'] = meta.get('og:title', '')
                        result['og_type'] = meta.get('og:type', '')
            
            results.append(result)
            
        except Exception as e:
            logger.warning(f"Error parsing search result: {str(e)}")
            continue
    
    logger.info(f"Successfully parsed {len(results)} results")
    return results

def validate_and_convert_query(query: str) -> str:
    """
    Validate and convert query for Google Custom Search
    
    Args:
        query: The search query
    
    Returns:
        Validated query string
    """
    if not query or not query.strip():
        raise ValueError("Query cannot be empty")
    
    # Google Custom Search supports most operators natively
    # Just clean up the query a bit
    query = query.strip()
    
    # Remove excessive whitespace
    query = ' '.join(query.split())
    
    # Google Custom Search has a 2048 character limit
    if len(query) > 2048:
        query = query[:2048]
        logger.warning("Query truncated to 2048 characters for Google Custom Search")
    
    return query

def get_api_status() -> Dict[str, Any]:
    """
    Get current API usage status
    
    Returns:
        Dictionary with current rate limiting status
    """
    limiter = get_rate_limiter()
    current_time = time.time()
    
    # Clean old minute requests
    limiter.minute_requests = [req_time for req_time in limiter.minute_requests 
                              if current_time - req_time < 60]
    
    return {
        'daily_requests_used': limiter.daily_count,
        'daily_requests_limit': limiter.max_requests_per_day,
        'minute_requests_used': len(limiter.minute_requests),
        'minute_requests_limit': limiter.max_requests_per_minute,
        'can_make_request': limiter.can_make_request(),
        'time_until_daily_reset': 86400 - (current_time - limiter.last_reset)
    } 