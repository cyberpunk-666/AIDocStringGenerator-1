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
dependencies = DependencyContainer()
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.Logger import Logger

class FileCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        self.logger : Logger = dependencies.resolve(Logger)        
        super().__init__()

    def ask(self, prompt, replacements) -> APIResponse:
        prompt_response = self.format_prompt(prompt, replacements)
        if not prompt_response.is_valid:
            return prompt_response
        self.logger.log_line("sending prompt: " + prompt_response.content)

        try:
            working_directory = os.getcwd()
            response_index: str = replacements.get('retry_count', '')
            example_retry: str = replacements.get('example_retry', 'False')
            ask_missing = replacements.get('ask_missing', 'False')

            base_bot_file: str = self.config.get('model', '')
            if ask_missing == 'True':
                bot_file = f'{base_bot_file}.missing.json'
            elif example_retry == 'True':
                bot_file = f'{base_bot_file}.example.json'
            else:
                response_index_str = '' if response_index == '1' else response_index
                bot_file = f'{base_bot_file}.response{response_index_str}.json'
            if not os.path.isabs(base_bot_file):
                bot_file = os.path.join(working_directory, f'responses/{bot_file}')
            with open(bot_file, 'r') as f:
                response_text = f.read()

            self.logger.log_line("Receiving response from File...")                
            return APIResponse(response_text, True)
        except Exception as e:
            return APIResponse('', False, str(e))
