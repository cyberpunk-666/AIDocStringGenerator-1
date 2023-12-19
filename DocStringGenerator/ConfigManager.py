from pathlib import Path
import logging
import json
import sys

class ConfigManager:
    _instance = None
    BOTS = {
        'gpt3.5': "gpt-3.5-turbo-1106",
        'gpt4': 'gpt-4',
        'gpt4-120k': "gpt-4-1106-preview", 
        'claude': 'claude-2.1',
        'file': "mock_bot"
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            # Initialize the instance only once
        return cls._instance

    DEFAULT_CONFIG = {'path': 'path/to/directory/or/file', 'wipe_docstrings': True, 'verbose': True, 'bot': 'GPT3.5', 'openai_api_key': 'my_key', 'claude_api_key': 'my_key', 'include_subfolders': False}
    def __init__(self, config_path: Path=Path('config.json'), default_config: dict=DEFAULT_CONFIG):
        self.config_path = config_path
        self.default_config = default_config

    def load_or_create_config(self) -> dict:
        if self.config_path.exists():
            return self.get_config() 
        else:
            self.config_path.write_text(json.dumps(self.default_config, indent=4))
            logging.info(f"Created default config at {self.config_path}")
            sys.exit(0)

    def get_config(self) -> dict:
        return json.loads(self.config_path.read_text())
    

    @staticmethod
    def get_model(bot):
        if bot not in ConfigManager.BOTS:
            print(f'Invalid bot: {bot}') 
            return  
        return ConfigManager.BOTS[bot]  