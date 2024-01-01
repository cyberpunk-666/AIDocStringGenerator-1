from typing import Optional
import google.generativeai as genai
import json
import os
import time
import requests
from bots import *
from dotenv import load_dotenv
from openai import OpenAI
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.EmptyCommunicator import EmptyCommunicator
from DocStringGenerator.AnthropicCommunicator import AnthropicCommunicator
from DocStringGenerator.GoogleCommunicator import GoogleCommunicator
from DocStringGenerator.OpenAICommunicator import OpenAICommunicator
from DocStringGenerator.FileCommunicator import FileCommunicator

class CommunicatorManager:

    def __init__(self):
        self.config = ConfigManager().config
        self.initialize_bot_communicator()
        self.bot_communicator = EmptyCommunicator()

    def initialize_bot_communicator(self):
        if not 'bot' in self.config:
            return
        bot = self.config.get('bot', '')
        if not bot in BOTS:
            raise ValueError(f"Unsupported bot type '{bot}' specified in the configuration")
        dependencies.register('anthropic_Communicator', AnthropicCommunicator)
        dependencies.register('openai_Communicator', OpenAICommunicator)
        dependencies.register('google_Communicator', GoogleCommunicator)
        dependencies.register('file_Communicator', FileCommunicator)
        self.bot_communicator = dependencies.resolve(f'{bot}_Communicator')
        if not self.bot_communicator:
            raise ValueError(f"Error initializing bot communicator for '{bot}'")

    def send_code_in_parts(self, source_code, retry_count=1) -> APIResponse:
        from DocStringGenerator.CodeProcessor import CodeProcessor

        def attempt_send(code, iteration=0) -> APIResponse:
            print(f'Sending code in {2 ** iteration} parts.')
            num_parts = 2 ** iteration
            code_processor: CodeProcessor = dependencies.resolve('CodeProcessor')
            parts = code_processor.split_source_code(code, num_parts)
            responses = []
            response = None
            for part in parts:
                print(f'Sending part {parts.index(part) + 1} of {len(parts)}')
                if self.bot_communicator is not None:
                    response = self.bot_communicator.ask_for_docstrings(part, retry_count)
                if response:
                    if response.is_valid:
                        content = response.content
                        if 'length' in content and 'exceed' in content:
                            if self.config.get('verbose', ''):
                                print('Context length exceeded. Trying again with more parts.')
                            return attempt_send(code, iteration + 1)
                        responses.append({'content': content, 'source_code': part})
                    else:
                        return response
            return APIResponse(responses, True)
        return attempt_send(source_code)
        
dependencies = DependencyContainer()
dependencies.register('CommunicatorManager', CommunicatorManager)        