from typing import Optional
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
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam

class OpenAICommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        api_key = self.config.get('OPENAI_API_KEY', '')
        self.client = OpenAI(api_key=api_key)
        self.messages = []
        self.messages.append(ChatCompletionSystemMessageParam({'role': 'system', 'content': 'You are a helpful assistant.'}))


    def ask(self, prompt, replacements) -> APIResponse:
        prompt_response = self.format_prompt(prompt, replacements)
        if not prompt_response.is_valid:
            return prompt_response
                
        try:
            new_prompt= prompt_response.content
            if self.config.get('verbose', False):
                print("sending prompt: " + new_prompt) 

            self.messages.append(ChatCompletionUserMessageParam(content=new_prompt,role='user'))
            model = self.config.get('model', '')
            models = BOTS[self.config.get('bot', '')]
            if model not in models:
                print(f'Invalid bot: {model}')
                return APIResponse('', False, 'Invalid bot')
            
            stream = self.client.chat.completions.create(model=model, messages=self.messages, temperature=0, stream=True)
            response = self.handle_response(stream)
            if response.is_valid:
                self.messages.append(ChatCompletionAssistantMessageParam(content=response.content,role='assistant'))
            return response
        except Exception as e:
            return APIResponse("", is_valid=False, error_message=str(e))

    def handle_response(self, stream) -> APIResponse:
        response = ''
        if self.config.get('verbose', False):
            print("Receiving response from OpenAI API...")
        try:
            for chunk in stream:
                content = chunk.choices[0].delta.content or ''
                if self.config.get('verbose', False):
                    print(content, end='')
                response += content
            return APIResponse(response, True)            
        except Exception as e:
            return APIResponse('', is_valid=False, error_message=str(e))
