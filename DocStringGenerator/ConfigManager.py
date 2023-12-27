from pathlib import Path
import logging
import json
import sys

class ConfigManager:
    """The ConfigManager class is a singleton designed to manage configuration settings for an application. It ensures that only one instance of the ConfigManager can exist at any given time. The class provides methods to load or create a default configuration file and retrieve specific configurations, such as API keys and bot settings.\n\nAt verbosity level 5, the class docstring would include a comprehensive explanation of the class's purpose, its singleton nature, the structure of the default configuration, and the methods provided for interacting with the configuration file. It would also cover potential edge cases, such as what happens if the configuration file is missing or corrupted, and how the class handles different types of bots specified in the configuration."""
    _instance = None




    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            # Initialize the instance only once
        return cls._instance

    DEFAULT_CONFIG = {'path': 'path/to/directory/or/file', 'wipe_docstrings': True, 'verbose': True, 'bot': 'GPT3.5', 'OPENAI_API_KEY': 'my_key', 'CLAUDE_API_KEY': 'my_key', 'include_subfolders': False}
    def __init__(self, config_path: Path=Path('config.json'), default_config: dict=DEFAULT_CONFIG):
        self.config_path = config_path
        self.default_config = default_config

    def load_or_create_config(self) -> dict:
        """Load the configuration from a file or create a default configuration if the file does not exist."""
        if self.config_path.exists():
            return self.get_config() 
        else:
            self.config_path.write_text(json.dumps(self.default_config, indent=4))
            logging.info(f"Created default config at {self.config_path}")
            sys.exit(0)

    def get_config(self) -> dict:
        """Retrieve the configuration as a dictionary from the configuration file."""
        return json.loads(self.config_path.read_text())
    

    @staticmethod
    def get_model(bot):
        """Return the model identifier for a given bot name."""
        if bot not in ConfigManager.BOTS:
            print(f'Invalid bot: {bot}') 
            return  
        return ConfigManager.BOTS[bot]  