"""
Configuration management for Meep Research MCP
"""

import json
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ConfigError(Exception):
    """Configuration related errors"""
    pass

class Config:
    """Configuration manager for Meep Research MCP"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to configuration file. If None, will look for config.json
        """
        self._config = {}
        self._config_file = config_file or self._find_config_file()
        self._load_config()
    
    def _find_config_file(self) -> str:
        """Find the configuration file in common locations"""
        possible_paths = [
            "config.json",
            "meep_research_mcp/config.json",
            os.path.join(os.path.dirname(__file__), "..", "config.json"),
            os.path.expanduser("~/.meep_research/config.json"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Found configuration file: {path}")
                return path
        
        # If no config file exists, create a default one
        default_path = "config.json"
        logger.warning(f"No configuration file found. Creating example at: {default_path}")
        self._create_example_config(default_path)
        raise ConfigError(
            f"No configuration file found. Created example at '{default_path}'. "
            "Please edit it with your Google Custom Search API credentials."
        )
    
    def _create_example_config(self, path: str):
        """Create an example configuration file"""
        example_config = {
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
        
        try:
            with open(path, 'w') as f:
                json.dump(example_config, f, indent=2)
            logger.info(f"Created example configuration file: {path}")
        except Exception as e:
            logger.error(f"Failed to create example configuration: {e}")
    
    def _load_config(self):
        """Load configuration from file"""
        try:
            with open(self._config_file, 'r') as f:
                self._config = json.load(f)
            logger.info(f"Loaded configuration from: {self._config_file}")
            self._validate_config()
        except FileNotFoundError:
            raise ConfigError(f"Configuration file not found: {self._config_file}")
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ConfigError(f"Error loading configuration: {e}")
    
    def _validate_config(self):
        """Validate required configuration fields"""
        required_fields = [
            ("google_custom_search", "api_key"),
            ("google_custom_search", "cse_id"),
        ]
        
        for section, field in required_fields:
            if section not in self._config:
                raise ConfigError(f"Missing configuration section: {section}")
            
            if field not in self._config[section]:
                raise ConfigError(f"Missing configuration field: {section}.{field}")
            
            value = self._config[section][field]
            if not value or value.startswith("your-"):
                raise ConfigError(
                    f"Configuration field {section}.{field} not set. "
                    f"Please edit {self._config_file} with your actual values."
                )
    
    def get(self, section: str, field: str, default: Any = None) -> Any:
        """
        Get a configuration value
        
        Args:
            section: Configuration section
            field: Field name
            default: Default value if not found
            
        Returns:
            Configuration value
        """
        return self._config.get(section, {}).get(field, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get an entire configuration section
        
        Args:
            section: Section name
            
        Returns:
            Dictionary with section values
        """
        return self._config.get(section, {})
    
    @property
    def google_api_key(self) -> str:
        """Get Google Custom Search API key"""
        return self.get("google_custom_search", "api_key")
    
    @property
    def google_cse_id(self) -> str:
        """Get Google Custom Search Engine ID"""
        return self.get("google_custom_search", "cse_id")
    
    @property
    def max_requests_per_day(self) -> int:
        """Get maximum requests per day"""
        return self.get("rate_limits", "max_requests_per_day", 100)
    
    @property
    def max_requests_per_minute(self) -> int:
        """Get maximum requests per minute"""
        return self.get("rate_limits", "max_requests_per_minute", 10)
    
    @property
    def default_max_results(self) -> int:
        """Get default maximum results"""
        return self.get("search_defaults", "max_results", 10)
    
    @property
    def timeout_seconds(self) -> int:
        """Get request timeout in seconds"""
        return self.get("search_defaults", "timeout_seconds", 30)
    
    def reload(self):
        """Reload configuration from file"""
        self._load_config()

# Global configuration instance
_config = None

def get_config(config_file: Optional[str] = None) -> Config:
    """
    Get the global configuration instance
    
    Args:
        config_file: Path to configuration file (only used on first call)
        
    Returns:
        Configuration instance
    """
    global _config
    if _config is None:
        _config = Config(config_file)
    return _config

def reload_config():
    """Reload the global configuration"""
    global _config
    if _config is not None:
        _config.reload() 