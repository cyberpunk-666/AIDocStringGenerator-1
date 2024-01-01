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

class OpenAICommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        api_key = self.config.get('OPENAI_API_KEY', '')
        self.client = OpenAI(api_key=api_key)

    def ask(self, prompt, replacements):
        prompt = self.format_prompt(prompt, replacements)
        messages = [{'role': 'system', 'content': 'You are a helpful assistant.'}, {'role': 'user', 'content': prompt}]
        error_message = ''
        try:
            model = self.config.get('model', '')
            models = BOTS[self.config.get('bot', '')]
            if model not in models:
                print(f'Invalid bot: {model}')
                return
            stream = self.client.chat.completions.create(model=model, messages=messages, temperature=0, stream=True)
            full_completion = self.handle_response(stream)
        except Exception as e:
            full_completion = ''
            return APIResponse(None, is_valid=False, error_message=str(e))
        return APIResponse(content=full_completion, is_valid=True)

    def handle_response(self, stream):
        response = ''
        for chunk in stream:
            response += chunk.choices[0].delta.content or ''
        return response
