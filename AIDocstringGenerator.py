import os
import platform
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer

dependencies = DependencyContainer()
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
    parser.add_argument('--BARD_API_KEY', type=str, help='API key for Bard')
    parser.add_argument('--OPENAI_API_KEY', type=str, help='API key for OpenAI')
    parser.add_argument('--CLAUDE_API_KEY', type=str, help='API key for Claude')
    parser.add_argument('--keep_responses', action='store_true', help='Keep responses in the output')
    parser.add_argument('--ignore', type=str, help='Specify patterns to ignore')
    parser.add_argument('--class_docstrings_verbosity_level', type=int, default=5, help='Verbosity level for class docstrings')
    parser.add_argument('--function_docstrings_verbosity_level', type=int, default=2, help='Verbosity level for function docstrings')
    parser.add_argument('--example_verbosity_level', type=int, default=3, help='Verbosity level for examples')
    parser.add_argument('--max_line_length', type=int, default=79, help='Maximum line length for formatting')    

    args = parser.parse_args()

    config_manager = ConfigManager()
    config = config_manager.load_or_create_config()

    # Override config with command line arguments
    for arg in vars(args):
        value = getattr(args, arg)
        if value:
            config[arg] = value        

    code_processor = dependencies.resolve("CodeProcessor")
    response = code_processor.process_folder_or_file()
    if not response.is_valid:
        failed_files = response.content
        for file in failed_files:
            print(f"Failed to process {file.file_name}")
            print(f"Error message: {file.response}")

if __name__ == '__main__':
    main()
