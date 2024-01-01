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

class AnthropicCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        self.anthropic_url = 'https://api.anthropic.com/v1/complete'

    def ask(self, prompt, replacements):
        for key, value in replacements.items():
            prompt = prompt.replace(f'{{{key}}}', value)
        anthropic_prompt = 'Human: ' + prompt + '\n\nAssistant:'
        headers = {'anthropic-version': '2023-06-01', 'content-type': 'application/json', 'x-api-key': self.config.get('ANTHROPIC_API_KEY')}
        model = self.config.get('model', '')
        models = BOTS[self.config.get('bot', '')]
        if model not in models:
            print(f'Invalid bot: {model}')
            return
        data = {'model': model, 'prompt': anthropic_prompt, 'max_tokens_to_sample': 4000, 'stream': True}
        try:
            response = requests.post(self.anthropic_url, headers=headers, data=json.dumps(data), stream=True)
            return self.handle_response(response)
        except Exception as e:
            raise e

    def handle_response(self, response):
        first_block_received = False
        full_completion = ''
        error_message = ''
        try:
            for line in response.iter_lines():
                if line:
                    current_time: float = time.time()
                    last_block_time = current_time
                    if not first_block_received:
                        first_block_received = True
                        last_block_time: float = current_time
                        continue
                    if current_time - last_block_time > 15:
                        raise TimeoutError('Connection timed out after receiving initial data block')
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data:'):
                        last_block_time = current_time
                        event_data = json.loads(decoded_line[6:])
                        completion = event_data.get('completion', '')
                        full_completion += completion
                        if self.config.get('verbose', False):
                            print(completion, end='')
                        if event_data.get('stop_reason') is not None:
                            if self.config.get('verbose', ''):
                                print('Received stop reason, breaking loop.')
                            break
        except Exception as e:
            full_completion = ''
            return APIResponse(None, is_valid=False, error_message=str(e))
        return APIResponse(content=full_completion, is_valid=True)
