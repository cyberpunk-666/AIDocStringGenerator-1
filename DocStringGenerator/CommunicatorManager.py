from bots import *
from DocStringGenerator.DependencyContainer import DependencyContainer, Scope
dependencies = DependencyContainer()
from DocStringGenerator.GlobalConfig import GlobalConfig
global_config = dependencies.resolve(GlobalConfig)

from DocStringGenerator.Utility import *
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.EmptyCommunicator import EmptyCommunicator
from DocStringGenerator.AnthropicCommunicator import AnthropicCommunicator
from DocStringGenerator.GoogleCommunicator import GoogleCommunicator
from DocStringGenerator.OpenAICommunicator import OpenAICommunicator
from DocStringGenerator.FileCommunicator import FileCommunicator
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.Logger import Logger

class CommunicatorManager:

    def __init__(self):
        self.logger : Logger = dependencies.resolve(Logger)        
        self.config = ConfigManager().config
        self.initialize_bot_communicator()
        self.bot_communicator = EmptyCommunicator()

    def resolve_bot_communicator(self, bot: str) -> BaseBotCommunicator:
        class_name = f'{bot}Communicator'
        communicator_class = globals().get(class_name)
        if communicator_class:
            return dependencies.resolve(communicator_class)
        else:
            raise ValueError(f"Communicator class not found: {class_name}")


    def initialize_bot_communicator(self):
        if not 'bot' in self.config:
            return
        bot = self.config.get('bot', '')
        if not bot in BOTS:
            raise ValueError(f"Unsupported bot type '{bot}' specified in the configuration")
        if global_config.mode == "web":
            dependencies.register(AnthropicCommunicator, AnthropicCommunicator, Scope.SCOPED)
            dependencies.register(OpenAICommunicator, OpenAICommunicator, Scope.SCOPED)
            dependencies.register(GoogleCommunicator, GoogleCommunicator, Scope.SCOPED)
            dependencies.register(FileCommunicator, FileCommunicator, Scope.SCOPED)
        else:
            dependencies.register(AnthropicCommunicator, AnthropicCommunicator, Scope.SINGLETON)
            dependencies.register(OpenAICommunicator, OpenAICommunicator, Scope.SINGLETON)
            dependencies.register(GoogleCommunicator, GoogleCommunicator, Scope.SINGLETON)
            dependencies.register(FileCommunicator, FileCommunicator, Scope.SINGLETON)

        self.resolve_bot_communicator(bot)
        self.bot_communicator: BaseBotCommunicator = dependencies.resolve(bot)
        if not self.bot_communicator:
            raise ValueError(f"Error initializing bot communicator for '{bot}'")

    def send_code_in_parts(self, source_code: str, retry_count: int=1) -> APIResponse:
        from DocStringGenerator.CodeProcessor import CodeProcessor

        def attempt_send(code: str, iteration:int=0) -> APIResponse:
            self.logger.log_line(f'Sending code in {2 ** iteration} parts.')
            num_parts = 2 ** iteration
            code_processor: CodeProcessor = dependencies.resolve(CodeProcessor)
            parts = code_processor.split_source_code(code, num_parts)
            responses: list[Any] = []
            response = None
            for part in parts:
                self.logger.log_line(f'Sending part {parts.index(part) + 1} of {len(parts)}')
                response = self.bot_communicator.ask_for_docstrings(part, retry_count)
                if response:
                    if response.is_valid:
                        content = response.content
                        if 'length' in content and 'exceed' in content:
                            self.logger.log_line('Context length exceeded. Trying again with more parts.')
                            return attempt_send(code, iteration + 1)
                        responses.append({'content': content, 'source_code': part})
                    else:
                        return response
            return APIResponse(responses, True)
        return attempt_send(source_code)
        
if global_config.mode == "web":
    dependencies.register(CommunicatorManager, CommunicatorManager, Scope.SCOPED)
else:
    dependencies.register(CommunicatorManager, CommunicatorManager, Scope.SINGLETON)