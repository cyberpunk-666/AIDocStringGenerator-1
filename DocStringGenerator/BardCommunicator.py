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

class BardCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        api_key = self.config.get('BARD_API_KEY', '')
        genai.configure(api_key=api_key)
        self.bard = genai.GenerativeModel('gemini-pro')

    def ask(self, prompt, replacements):
        formatted_prompt = self.format_prompt(prompt, replacements)
        full_completion = ''
        error_message = ''
        try:
            response = self.bard.generate_content(formatted_prompt, stream=True)
            full_completion = self.handle_response(response)
        except Exception as e:
            full_completion = ''
            error_message = str(e)
            return APIResponse(None, is_valid=False, error_message=str(e))
        return APIResponse(content=full_completion, is_valid=True)

    def handle_response(self, stream):
        response = ''
        for response_chunk in stream:
            response += response_chunk.text
        return response
