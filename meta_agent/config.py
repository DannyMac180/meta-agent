"""
Centralized configuration management for the meta-agent package.

This module provides a single point of access for all configuration settings
and handles environment variable loading with consistent error handling.
"""

import os
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

class Config:
    """Centralized configuration management class."""
    
    # Default configuration values
    _defaults = {
        "OPENAI_API_KEY": None,
        "OPENAI_MODEL": "gpt-4",
        "LOG_LEVEL": "INFO",
        "OUTPUT_DIR": "generated_agents",
        "DEBUG": False,
    }
    
    _instance = None
    _config: Dict[str, Any] = {}
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern to ensure only one config instance exists."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration if not already initialized."""
        if not self._initialized:
            self.load_config()
            Config._initialized = True
    
    def load_config(self) -> None:
        """
        Load configuration from environment variables and .env file.
        Environment variables take precedence over .env file values.
        """
        # Load from .env file first
        load_dotenv()
        
        # Populate config dictionary with defaults
        self._config = self._defaults.copy()
        
        # Override with environment variables
        for key in self._config.keys():
            env_value = os.environ.get(key)
            if env_value is not None:
                # Convert string boolean values
                if env_value.lower() == 'true':
                    self._config[key] = True
                elif env_value.lower() == 'false':
                    self._config[key] = False
                else:
                    self._config[key] = env_value
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key
            default: Default value if key is not found
            
        Returns:
            The configuration value or default
        """
        return self._config.get(key, default)
    
    def get_required(self, key: str) -> Any:
        """
        Get a required configuration value.
        
        Args:
            key: The configuration key
            
        Returns:
            The configuration value
            
        Raises:
            ConfigurationError: If the key is not found or has None value
        """
        value = self._config.get(key)
        if value is None:
            raise ConfigurationError(f"Required configuration '{key}' is missing")
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key
            value: The value to set
        """
        self._config[key] = value
    
    @property
    def openai_api_key(self) -> Optional[str]:
        """Get the OpenAI API key."""
        return self.get("OPENAI_API_KEY")
    
    @property
    def openai_model(self) -> str:
        """Get the OpenAI model to use."""
        return self.get("OPENAI_MODEL", "gpt-4")
    
    @property
    def debug(self) -> bool:
        """Get the debug flag."""
        return self.get("DEBUG", False)
    
    @property
    def output_dir(self) -> str:
        """Get the output directory."""
        return self.get("OUTPUT_DIR", "generated_agents")
    
    def check_api_key(self) -> bool:
        """
        Check if the OpenAI API key is set.
        
        Returns:
            True if the API key is set, False otherwise
        """
        return self.openai_api_key is not None
    
    def print_api_key_warning(self) -> None:
        """
        Print a warning message if the OpenAI API key is not set.
        """
        logger.warning("OPENAI_API_KEY environment variable not set.")
        logger.warning("Please set your OpenAI API key in the .env file or as an environment variable:")
        logger.warning("export OPENAI_API_KEY='your-api-key'")


# Create a global instance for easy importing
config = Config()


def load_config() -> None:
    """
    Load configuration from environment variables and .env file.
    This function exists for backward compatibility.
    """
    config.load_config()


def get_api_key() -> Optional[str]:
    """
    Get the OpenAI API key from environment variables.
    This function exists for backward compatibility.
    
    Returns:
        The API key if found, None otherwise
    """
    return config.openai_api_key


def check_api_key() -> bool:
    """
    Check if the OpenAI API key is set.
    This function exists for backward compatibility.
    
    Returns:
        True if the API key is set, False otherwise
    """
    return config.check_api_key()


def print_api_key_warning() -> None:
    """
    Print a warning message if the OpenAI API key is not set.
    This function exists for backward compatibility.
    """
    config.print_api_key_warning()
