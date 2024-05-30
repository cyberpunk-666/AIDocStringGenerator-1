import os
import platform
import sys
from pathlib import Path
import argparse
from bots import BOTS
from DocStringGenerator.GoogleCommunicator import GoogleCommunicator
from DocStringGenerator.OpenAICommunicator import OpenAICommunicator
from DocStringGenerator.AnthropicCommunicator import AnthropicCommunicator
from DocStringGenerator.FileCommunicator import FileCommunicator

current = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f"{current}")
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.CommunicatorManager import CommunicatorManager

dependencies = DependencyContainer()

def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def switch_bot(bot, model):
    ConfigManager().set_config("bot", bot)
    ConfigManager().set_config("model", model)
    communicator_manager = dependencies.resolve(CommunicatorManager)
    communicator_manager.initialize_bot_communicator()

def display_available_bots():
    print("Available Chatbots:")
    for i, bot in enumerate(BOTS, 1):
        print(f" {i}. {bot}")

def capitalize_first(string):
    if not string:
        return string
    return string[0].upper() + string[1:]

def main():
    parser = argparse.ArgumentParser(description='DocString Generator Configuration')
    parser.add_argument('--bot', type=str, help='The bot to use')
    parser.add_argument('--model', type=str, help='The model to use')
    parser.add_argument('--source_path', type=str, help='Path to the source files')
    parser.add_argument('--output_path', type=str, help='Path to save the output files')

    args = parser.parse_args()

    config_manager = ConfigManager()
    config = config_manager.load_or_create_config()

    # Update config with command line arguments
    if args.bot:
        config['bot'] = args.bot
    if args.model:
        config['model'] = args.model
    if args.source_path:
        config['source_path'] = args.source_path
    if args.output_path:
        config['output_path'] = args.output_path

    # Ask for missing config values
    if 'bot' not in config or not config['bot']:
        display_available_bots()
        chosen_bot_index = int(input("Please choose a bot by entering its number: "))
        while chosen_bot_index < 1 or chosen_bot_index > len(BOTS):
            print("Invalid input. Please enter a valid number.")
            chosen_bot_index = int(input("Please choose a bot by entering its number: "))
        config['bot'] = list(BOTS.keys())[chosen_bot_index - 1]

    if 'model' not in config or not config['model']:
        chosen_bot_models = BOTS[config['bot']]
        print(f"Available models for {config['bot']}:")
        for i, model in enumerate(chosen_bot_models, 1):
            print(f" {i}. {model}")
        chosen_model_index = int(input("Please choose a model by entering its number: "))
        while chosen_model_index < 1 or chosen_model_index > len(chosen_bot_models):
            print("Invalid input. Please enter a valid number.")
            chosen_model_index = int(input("Please choose a model by entering its number: "))
        config['model'] = chosen_bot_models[chosen_model_index - 1]

    if 'source_path' not in config or not config['source_path']:
        config['source_path'] = input("Please enter the source path: ")
    if 'output_path' not in config or not config['output_path']:
        config['output_path'] = input("Please enter the output path: ")

    config_manager.update_config(config)

    enabled_bots = config.get('enabled_bots', [])

    if 'bot' in config and config['bot']:
        enabled_bots.append({'bot': config['bot'], 'model': config.get('model')})

    # Registering communicators
    dependencies.register(GoogleCommunicator, GoogleCommunicator())
    dependencies.register(OpenAICommunicator, OpenAICommunicator())
    dependencies.register(AnthropicCommunicator, AnthropicCommunicator())
    dependencies.register(FileCommunicator, FileCommunicator())

    code_processor = CodeProcessor()

    if enabled_bots:
        index = 0
        for bot_info in enabled_bots:
            if index < len(enabled_bots) - 1:
                config_manager.set_config('disable_log_processed_file', True)
            else:
                config_manager.set_config('disable_log_processed_file', False)
                
            bot = bot_info['bot']
            model = bot_info.get('model')
            switch_bot(bot, model)

            response = code_processor.process_folder_or_file(config['source_path'], config['output_path'])
            if not response.is_valid:
                failed_files = response.content
                for file in failed_files:
                    print(f"Failed to process {file.file_name}")
                    print(f"Error message: {file.response}")
            index += 1

if __name__ == '__main__':
    main()
