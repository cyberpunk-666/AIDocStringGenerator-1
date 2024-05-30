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

class ChunkData:
    def __init__(self, bot_name: str, chunk: str):      
        self.bot_name = bot_name
        self.chunk = chunk
class GoogleCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        api_key = self.config.get('GOOGLE_API_KEY', '')
        if api_key:
            genai.configure(api_key=api_key)
        self.google = genai.GenerativeModel('gemini-pro')
        self.logger : Logger = dependencies.resolve(Logger)         

    def ask(self, prompt, replacements) -> APIResponse:
        formatted_prompt_response = self.format_prompt(prompt, replacements)
        if not formatted_prompt_response.is_valid:
            return formatted_prompt_response

        try:
            new_prompt= formatted_prompt_response.content
            self.logger.log_line("sending prompt: " + new_prompt)            
            chat = self.google.start_chat()
            response = chat.send_message(new_prompt, stream=True)
            response_handled = self.handle_response(response)
            return response_handled
        except Exception as e:
            return APIResponse(None, is_valid=False, error_message=str(e))

    def handle_response(self, stream)-> APIResponse:
        response = ''
        self.logger.log_line("Receiving response from Google API...")
        try:
            for response_chunk in stream:
                self.logger.log(response_chunk.text)
                response += response_chunk.text
            return APIResponse(content=response, is_valid=True)
        except Exception as e:
            return APIResponse("", is_valid=False, error_message=str(e))
