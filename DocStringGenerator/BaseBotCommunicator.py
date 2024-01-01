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

class BaseBotCommunicator:

    def __init__(self):
        configManager = ConfigManager()
        self.config = configManager.config
        load_dotenv()
        configManager.set_config('verbose', True)
        configManager.set_config('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))
        configManager.set_config('CLAUDE_API_KEY', os.getenv('CLAUDE_API_KEY'))
        configManager.set_config('BARD_API_KEY', os.getenv('BARD_API_KEY'))

    def ask(self, prompt, replacements) -> APIResponse:
        """
        Sends a request to the respective bot API or file system. This method should be implemented by subclasses.
        """
        raise NotImplementedError('This method should be implemented by subclasses')

    def handle_response(self, response):
        """
        Handles the response from the bot API or file system. This method can be overridden by subclasses for custom behavior.
        """
        return response

    def format_prompt(self, prompt_template, replacements) -> APIResponse:
        """
        Formats the prompt by replacing placeholders with actual values provided in 'replacements'.
        """
        for key, value in replacements.items():
            prompt_template = prompt_template.replace(f'{{{key}}}', value)
        return prompt_template

    def ask_retry(self, last_error_message, retry_count) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_retry')
        replacements: dict[str, str] = {'last_error_message': last_error_message, 'retry_count': str(retry_count)}
        return self.ask(prompt_template, replacements)

    def ask_retry_examples(self, class_name) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_retry_example')
        replacements: dict[str, str] = {'class_name': class_name, 'example_retry': 'True'}
        return self.ask(prompt_template, replacements)

    def ask_for_docstrings(self, source_code, retry_count=1) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_docStrings')
        replacements: dict[str, str] = {'source_code': source_code, 'max_line_length': str(self.config.get('max_line_length', 79)), 'class_docstrings_verbosity_level': str(self.config.get('class_docstrings_verbosity_level', 5)), 'function_docstrings_verbosity_level': str(self.config.get('function_docstrings_verbosity_level', 2)), 'example_verbosity_level': str(self.config.get('example_verbosity_level', 3)), 'retry_count': str(retry_count)}
        return self.ask(prompt_template, replacements)

    def ask_missing_docstrings(self, class_names, retry_count=1) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_missingDocStrings')
        replacements: dict[str, str] = {'function_names': json.dumps(class_names), 'retry_count': str(retry_count)}
        return self.ask(prompt_template, replacements)

