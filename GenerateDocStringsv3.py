import os
import platform
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.FileProcessor import FileProcessor
from pathlib import Path


def clear_screen():
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def main():
    clear_screen()
    config_manager = ConfigManager()
    config = config_manager.load_or_create_config()
    file_processor = FileProcessor(config)
    file_processor.process_folder_or_file(config)


if __name__ == '__main__':
    main()
