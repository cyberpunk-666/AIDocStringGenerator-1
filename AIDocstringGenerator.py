import os
import platform
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.FileProcessor import FileProcessor
from pathlib import Path
import argparse


def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def main():
    parser = argparse.ArgumentParser(description='DocString Generator Configuration')
    parser.add_argument('--path', type=str, help='Path to process')
    parser.add_argument('--wipe_docstrings', action='store_true', help='Wipe existing docstrings')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--bot', type=str, choices=['claude', 'other_bot'], help='Choose the bot for processing')
    parser.add_argument('--bot_response_file', type=str, help='File for storing bot responses')
    parser.add_argument('--include_subfolders', action='store_true', help='Process subfolders')
    parser.add_argument('--verbosity_level', type=str, help='Set verbosity level')
    parser.add_argument('--bard_api_key', type=str, help='API key for Bard')
    parser.add_argument('--openai_api_key', type=str, help='API key for OpenAI')
    parser.add_argument('--claude_api_key', type=str, help='API key for Claude')

    args = parser.parse_args()

    config_manager = ConfigManager()
    config = config_manager.load_or_create_config()

    # Override configurations with command line arguments
    if args.path:
        config['path'] = args.path
    if args.wipe_docstrings is not None:
        config['wipe_docstrings'] = args.wipe_docstrings
    if args.verbose is not None:
        config['verbose'] = args.verbose
    if args.bot:
        config['bot'] = args.bot
    if args.bot_response_file:
        config['bot_response_file'] = args.bot_response_file
    if args.include_subfolders is not None:
        config['include_subfolders'] = args.include_subfolders
    if args.verbosity_level:
        config['verbosity_level'] = args.verbosity_level
    if args.bard_api_key:
        config['bard_api_key'] = args.bard_api_key
    if args.openai_api_key:
        config['openai_api_key'] = args.openai_api_key
    if args.claude_api_key:
        config['claude_api_key'] = args.claude_api_key

    file_processor = FileProcessor(config)
    file_processor.process_folder_or_file(config)

if __name__ == '__main__':
    main()
