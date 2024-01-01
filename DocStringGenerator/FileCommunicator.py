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
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator

class FileCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()

    def ask(self, prompt, replacements) -> APIResponse:
        formatted_prompt = self.format_prompt(prompt, replacements)
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
        try:
            if not os.path.isabs(base_bot_file):
                bot_file = os.path.join(working_directory, f'responses/{bot_file}')
            with open(bot_file, 'r') as f:
                response_text = f.read()
        except Exception as e:
            return APIResponse('', False, str(e))
        return APIResponse(response_text, True)
