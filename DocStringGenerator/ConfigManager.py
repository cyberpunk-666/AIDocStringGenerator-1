from pathlib import Path
import logging
import json
import sys
from typing import Any

class ConfigManager:
    """The ConfigManager class is a singleton designed to manage configuration settings for an application. It ensures that only one instance of the ConfigManager can exist at any given time. The class provides methods to load or create a default configuration file and retrieve specific configurations, such as API keys and bot settings.\n\nAt verbosity level 5, the class docstring would include a comprehensive explanation of the class's purpose, its singleton nature, the structure of the default configuration, and the methods provided for interacting with the configuration file. It would also cover potential edge cases, such as what happens if the configuration file is missing or corrupted, and how the class handles different types of bots specified in the configuration."""
    _instance = None
    _is_initialized = False
    DEFAULT_CONFIG = {'verbose': True}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def update_config(self, new_config: dict[str, Any]) -> None:
        """Update the configuration with values from the provided dictionary."""
        self.config.update(new_config)

    def set_config(self, key, value):
        """Set a configuration value."""
        self.config[key] = value

    def __init__(self, config_path: Path = Path('config.json'), initial_config: dict = DEFAULT_CONFIG):
        if not self._is_initialized:
            self.config_path = config_path
            self.config:dict[str, Any] = initial_config
            self._is_initialized = True

    def load_or_create_config(self) -> dict:
        """Load the configuration from a file or create a default configuration if the file does not exist."""
        if self.config_path.exists():
            return self.get_config() 
        else:
            self.config_path.write_text(json.dumps(self.config, indent=4))
            logging.info(f"Created default config at {self.config_path}")
            sys.exit(0)

    def get_config(self) -> dict:
        """Retrieve the configuration as a dictionary from the configuration file."""
        return json.loads(self.config_path.read_text())
    