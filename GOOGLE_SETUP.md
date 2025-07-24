# Google Custom Search API Setup Guide

This guide will help you set up Google Custom Search API for the Meep Research MCP server.

## Overview

The Meep Research MCP uses Google Custom Search API for reliable web search functionality. Google Custom Search provides:

- **100 free searches per day**
- **$5 per 1,000 additional searches** (up to 10,000/day)
- **Reliable access** to Google's search index
- **Advanced search operators** support
- **Customizable search scope** with your own Custom Search Engine

## Features

- **Rate Limiting**
  - Automatic daily limit management (100 requests/day in free tier)
  - Per-minute request throttling (10 requests/minute by default)
  - Graceful error handling with informative messages
  - Real-time status monitoring via API

- **Error Handling**
  - Automatic retry on transient failures
  - Fallback strategies for query translation
  - Clear error messages with troubleshooting guidance
  - Status monitoring and reporting

## Prerequisites

1. **Google Account** - You need a Google account
2. **Google Cloud Console Access** - Free to set up
3. **Credit Card** - Required for Google Cloud (but free tier covers normal usage)

## Step-by-Step Setup

### 1. Set up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Create a new project or select an existing one:
   - Click the project dropdown at the top
   - Click "New Project"
   - Enter a project name (e.g., "Meep Research Search")
   - Click "Create"

### 2. Enable Custom Search API

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Custom Search API"
3. Click on "Custom Search API"
4. Click **"Enable"**

### 3. Create API Key

1. Go to **APIs & Services** → **Credentials**
2. Click **"+ Create Credentials"** → **"API key"**
3. **Important**: Copy and save your API key immediately
4. Click on the API key to edit it:
   - Give it a descriptive name (e.g., "Meep Research Search Key")
   - Under **"API restrictions"**, select **"Restrict key"**
   - Choose **"Custom Search API"** from the list
   - Click **"Save"**

### 4. Create Your Custom Search Engine

1. Go to [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click **"Add"** to create a new search engine
3. **Sites to search**: You can either:
   - Add specific websites you want to search
   - Or select **"Search the entire web"** for general web search
4. Give your search engine a name (e.g., "My Research Search")
5. Click **"Create"**
6. **Important**: Copy the **Search Engine ID** (it looks like: `017576662512468239146:omuauf_lfve`)

### 5. Configure the Application

1. **Copy the example configuration:**
   ```bash
   cp config.json.example config.json
   ```

2. **Edit config.json** with your credentials:
   ```json
   {
     "google_custom_search": {
       "api_key": "your-google-custom-search-api-key-here",
       "cse_id": "your-custom-search-engine-id-here"
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
   ```

3. **Replace the placeholder values:**
   - `api_key`: Your Google Custom Search API key from step 3
   - `cse_id`: Your Custom Search Engine ID from step 4

## Testing the Setup

1. **Test with the test script:**
   ```bash
   python test_google_search.py
   ```

2. **Test with the MCP server:**
   ```bash
   ./run.sh
   ```

3. **Check API status from within Claude:**
   Ask Claude to run the `google_search_status` tool to see your quota usage.

## Usage Limits & Costs

### Free Tier
- **100 searches per day** - completely free
- **10 searches per minute** - rate limited

### Paid Usage
- **$5 per 1,000 searches** (beyond the 100 free)
- **Maximum 10,000 searches per day**
- Billing is automatic if you exceed free limits

### Rate Limiting
The MCP server includes built-in rate limiting to:
- Track your daily usage
- Prevent exceeding minute limits
- Show clear error messages when limits are reached

## Troubleshooting

### "API key not configured" Error
1. Check that `config.json` exists in your project directory
2. Verify that the `api_key` field is properly set in the configuration
3. Make sure the API key doesn't contain the placeholder text "your-google-custom-search-api-key-here"

### "Access denied" Error
1. Make sure the Custom Search API is enabled in your Google Cloud project
2. Verify your API key has the correct restrictions (Custom Search API only)
3. Check that billing is enabled on your Google Cloud project

### "Rate limit exceeded" Error
1. Check your usage: run `python test_google_search.py`
2. Wait for the rate limit to reset (1 minute for minute limits, 24 hours for daily)
3. Consider optimizing your search queries to use fewer requests

### "Daily quota exceeded" Error
You've used your 100 free searches for the day. Options:
1. Wait until tomorrow for the quota to reset
2. Enable billing in Google Cloud Console to continue with paid searches

## Advanced Configuration

### Custom Rate Limits
You can modify the rate limits in `config.json`:
```json
{
  "rate_limits": {
    "max_requests_per_day": 100,
    "max_requests_per_minute": 10
  }
}
```

### Search Defaults
You can customize default search behavior:
```json
{
  "search_defaults": {
    "max_results": 10,
    "timeout_seconds": 30
  }
}
```

### Multiple API Keys
You can set up multiple API keys for different projects in Google Cloud Console.

### Monitoring Usage
- View usage in Google Cloud Console → APIs & Services → Dashboard
- The MCP server provides real-time usage tracking via the `google_search_status` tool

## Security Best Practices

1. **Restrict your API key** to only the Custom Search API
2. **Don't commit API keys** to version control
3. **Keep config.json secure** and add it to .gitignore
4. **Monitor usage** regularly in Google Cloud Console
5. **Set up billing alerts** to avoid unexpected charges
6. **Use the example file** for distribution (config.json.example)

## Support

If you encounter issues:

1. **Check the logs** when running `./run.sh`
2. **Test with** `python test_google_search.py`
3. **Verify API key** in Google Cloud Console
4. **Check billing status** in Google Cloud Console

The implementation includes comprehensive error handling and status reporting to help diagnose issues quickly. 