from typing import Any
from DocStringGenerator.DependencyContainer import DependencyContainer, Scope
from DocStringGenerator.ConfigManager import ConfigManager
dependencies = DependencyContainer()
from DocStringGenerator.GlobalConfig import GlobalConfig
global_config = dependencies.resolve(GlobalConfig)

class ChunkData:
    def __init__(self, bot_name: str, chunk: str):
        self.logger : Logger = dependencies.resolve(Logger)        
        self.bot_name = bot_name
        self.chunk = chunk

class Logger:
    def __init__(self, chunk_received_callback=None):
        config_manager = dependencies.resolve(ConfigManager)
        config: dict[str, Any] = config_manager.config
        self.config: dict[str, Any] = config
        self.chunk_received_callback = chunk_received_callback

    def log_line(self, message: str):
        self.log(message + '\n')

    def log(self, message: str):
        if self.config.get('verbose', False):
            bot = self.config.get('bot', '')
            if self.chunk_received_callback:
                # Send log to chunk_received_callback
                self.chunk_received_callback(ChunkData(bot, message))
            else:
                # Default to terminal output
                print(message)

if global_config.mode == "web":
    dependencies.register(Logger, Logger, scope=Scope.SCOPED)
else:
    dependencies.register(Logger, Logger, scope=Scope.SINGLETON)