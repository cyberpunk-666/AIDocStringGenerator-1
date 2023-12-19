from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.FileProcessor import FileProcessor
from pathlib import Path


# Constants
DEFAULT_CONFIG = {
    'path': 'path/to/directory/or/file',
    'wipe_docstrings': True,
    'verbose': True,
    'bot': 'GPT3.5',
    'openai_api_key': 'my_key',
    'claude_api_key': 'my_key',
    'include_subfolders': False
}
CONFIG_FILE = 'config.json'
PROMPT_FILE = 'chatbot_prompt.txt'

EXPECTED_KEYS = {'docstrings'}
BOTS = {
    'gpt3.5': "gpt-3.5-turbo-1106",
    'gpt4': 'gpt-4',
    'gpt4-120k': "gpt-4-1106-preview",
    'claude': 'claude-2.1',
    'file': "mock_bot"
}


def main():
    config_manager = ConfigManager()
    config = config_manager.load_or_create_config()
    file_processor = FileProcessor(config)
    path = config.get("path")
    file_processor.process_folder_or_file(Path(path), config)


if __name__ == '__main__':
    main()
