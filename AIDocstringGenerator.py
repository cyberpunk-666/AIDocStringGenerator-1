import os
import platform
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.CommunicatorManager import CommunicatorManager

dependencies = DependencyContainer()
from pathlib import Path
import argparse



def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')


def switch_bot(bot, model):
    # Set bot and model configuration
    ConfigManager().set_config("bot", bot)
    ConfigManager().set_config("model", model)
    communicator_manager = dependencies.resolve("CommunicatorManager")
    communicator_manager.initialize_bot_communicator()

def main():
    parser = argparse.ArgumentParser(description='DocString Generator Configuration')
    # Add argument definitions here (if any)

    args = parser.parse_args()

    config_manager = ConfigManager()
    config = config_manager.load_or_create_config()
    config_manager.update_config(config)

    # Override config with command line arguments
    for arg in vars(args):
        value = getattr(args, arg)
        if value:
            config[arg] = value

    # Handling enabled_bots
    enabled_bots = config.get('enabled_bots', [])

    # Include 'bot' and 'model' from command line args if provided
    if 'bot' in config and config['bot']:
        enabled_bots.append({'bot': config['bot'], 'model': config.get('model')})

    code_processor = CodeProcessor()

    if enabled_bots:
        # If multiple bots are enabled, we will process the code with each of them
        # and then compare the results to find the best one
        index = 0
        for bot_info in enabled_bots:
            if index < len(enabled_bots) - 1:
                config_manager.set_config('disable_log_processed_file', True)
            else:
                config_manager.set_config('disable_log_processed_file', False)
                
            bot = bot_info['bot']
            model = bot_info.get('model')
            switch_bot(bot, model)
            # code_processor.remove_from_processed_log()
            response = code_processor.process_folder_or_file()
            if not response.is_valid:
                failed_files = response.content
                for file in failed_files:
                    print(f"Failed to process {file.file_name}")
                    print(f"Error message: {file.response}")
            index += 1
    
if __name__ == '__main__':
    main()