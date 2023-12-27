import google.generativeai as genai
import json
import os
import time
import requests
from dataclasses import dataclass
from bots import *

from requests.exceptions import RequestException
from openai import APIError, APITimeoutError, BadRequestError, AuthenticationError  # and others as needed
from openai import OpenAI
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.Utility import Utility
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.Spinner import Spinner
from DocStringGenerator.APICommunicator import APICommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor


@dataclass
class APIResponse:
    content: str
    is_valid: bool
    error_message: str = None

class BaseBotCommunicator:
    def __init__(self, config):
        self.config = config

    def ask(self, prompt, replacements):
        """
        Sends a request to the respective bot API or file system. This method should be implemented by subclasses.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def handle_response(self, response):
        """
        Handles the response from the bot API or file system. This method can be overridden by subclasses for custom behavior.
        """
        return response

    def format_prompt(self, prompt_template, replacements):
        """
        Formats the prompt by replacing placeholders with actual values provided in 'replacements'.
        """
        for key, value in replacements.items():
            prompt_template = prompt_template.replace(f'{{{key}}}', value)
        return prompt_template
    
    def ask_retry(self):
        prompt_template = Utility.load_prompt('prompts/prompt_retry')
        return self.ask(prompt_template, {})

    def ask_retry_examples(self, class_name):
        prompt_template = Utility.load_prompt('prompts/prompt_retry_example')
        replacements = {'class_name': class_name}
        return self.ask(prompt_template, replacements)
        
    def ask_for_docstrings(self, source_code):
        prompt_template = Utility.load_prompt('prompts/prompt_docStrings')
        replacements = {'source_code': source_code,
                        'verbosity_level': str(self.config.get('verbosity_level', 2)),
                        'max_line_length': str(self.config.get('max_line_length', 79)),
                        "class_docstrings_verbosity_level": str(self.config.get("class_docstrings_verbosity_level",5)),
                        "function_docstrings_verbosity_level": str(self.config.get("function_docstrings_verbosity_level",2)),
                        "example_verbosity_level": str(self.config.get("example_verbosity_level",3))}
                
        return self.ask(prompt_template, replacements)    


def retry_decorator(retry_attempts=3, delay_seconds=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(retry_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < retry_attempts - 1:
                        time.sleep(delay_seconds)
                    else:
                        raise e
        return wrapper
    return decorator

class ClaudeCommunicator(BaseBotCommunicator):
    def __init__(self, config):
        self.config = config
        super().__init__(config)
        self.claude_url = 'https://api.anthropic.com/v1/complete'

    def ask(self, prompt, replacements):
        # Prepare the prompt
        for key, value in replacements.items():
            prompt = prompt.replace(f'{{{key}}}', value)

        claude_prompt = 'Human: ' + prompt + '\n\nAssistant:'
        headers = {
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
            'x-api-key': self.config.get('CLAUDE_API_KEY')
        }
        model = self.config['model']
        models = BOTS[self.config['bot']]
        if model not in models:
            print(f'Invalid bot: {model}') 
            return
        data = {
            'model': model,
            'prompt': claude_prompt,
            'max_tokens_to_sample': 4000,
            'stream': True
        }

        # Send request to Claude API
        try:
            response = requests.post(self.claude_url, headers=headers, data=json.dumps(data), stream=True)
            return self.handle_response(response)
        except Exception as e:
            # Add additional error handling if necessary
            raise e

    def handle_response(self, response):
        first_block_received = False
        full_completion = ''
        error_message = None

        try:
            for line in response.iter_lines():
                if line:
                    current_time = time.time()

                    if not first_block_received:
                        first_block_received = True
                        last_block_time = current_time
                        continue

                    if current_time - last_block_time > 15:
                        raise TimeoutError("Connection timed out after receiving initial data block")

                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data:'):
                        last_block_time = current_time  # Update time of last received block
                        event_data = json.loads(decoded_line[6:])
                        completion = event_data.get('completion', '')
                        full_completion += completion
                        if self.config.get('verbose', False):
                            print(completion, end='')                        
                        if event_data.get('stop_reason') is not None:
                            if self.config['verbose']:
                                print("Received stop reason, breaking loop.")
                            break
        except Exception as e:
            full_completion = ''
            error_message = str(e)

        return APIResponse(
            content=full_completion,
            is_valid=(error_message is None),
            error_message=error_message
        )               


class OpenAICommunicator(BaseBotCommunicator):
    def __init__(self, config):
        self.config = config
        super().__init__(config)
        self.client = OpenAI(api_key=config['OPENAI_API_KEY'])


    def ask(self, prompt, replacements):
        prompt = self.format_prompt(prompt, replacements)
        messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
                    {'role': 'user', 'content': prompt}]
        
        error_message = None
        try:

            model = self.config['model']
            models = BOTS[self.config['bot']]
            if model not in models:
                print(f'Invalid bot: {model}') 
                return
            stream = self.client.chat.completions.create(model=model,
                                                         messages=messages, temperature=0, stream=True)
            full_completion = self.handle_response(stream)
        except Exception as e:
            full_completion = ''
            error_message = str(e)

        return APIResponse(
            content=full_completion,
            is_valid=(error_message is None),
            error_message=error_message
        ) 

    def handle_response(self, stream):
        response = ''
        for chunk in stream:
            response += chunk.choices[0].delta.content or ''
        return response


class BardCommunicator(BaseBotCommunicator):
    def __init__(self, config):
        self.config = config
        super().__init__(config)
        genai.configure(api_key=self.config.get('BARD_API_KEY'))
        self.bard = genai.GenerativeModel('gemini-pro')


    def ask(self, prompt, replacements):
        formatted_prompt = self.format_prompt(prompt, replacements)
        full_completion = None
        error_message = None
        try:
            response = self.bard.generate_content(formatted_prompt, stream=True)
            full_completion =  self.handle_response(response)
        except Exception as e:
            full_completion = None
            error_message = str(e)

        return APIResponse(
            content=full_completion,
            is_valid=(error_message is None),
            error_message=error_message
        ) 
        
    def handle_response(self, stream):
        response = ''
        for response_chunk in stream:
            # Process each chunk
            response += response_chunk.text
        return response        


class FileCommunicator(BaseBotCommunicator):
    def __init__(self, config):
        self.config = config
        super().__init__(config)

    def ask(self, prompt, replacements):
        # Handling file-based responses
        working_directory = os.getcwd()
        base_bot_file = self.config['bot_response_file']

        # Check if it's a path or just a filename
        if not os.path.isabs(base_bot_file):
            base_bot_file = os.path.join(working_directory, f"responses/{base_bot_file}")

        # Remove file extension if present
        base_bot_file, _ = os.path.splitext(base_bot_file)
        responses = []
        bot_file = f"{base_bot_file}.response.json"
        with open(bot_file, 'r') as f:
            response_text = f.read()  # Read the raw string content
            responses.append(response_text)
        
        return responses
    
class CommunicatorManager:
    def __init__(self, config):
        self.config = config
        self.bot_communicator = self.initialize_bot_communicator()

    def initialize_bot_communicator(self):
        if self.config['bot'] == 'claude':
            return ClaudeCommunicator(self.config)
        elif self.config['bot'] == 'openai':
            return OpenAICommunicator(self.config)
        elif self.config['bot'] == 'bard':
            return BardCommunicator(self.config)
        elif self.config['bot'] == 'file':
            return FileCommunicator(self.config)
        else:
            raise ValueError(f"Unsupported bot type '{self.config['bot']}' specified in the configuration")

    def get_response(self, source_code):
        if isinstance(self.bot_communicator, FileCommunicator):
            return self.bot_communicator.handle_file_based_responses()
        else:
            return self.send_code_in_parts(source_code)

    def send_code_in_parts(self, source_code):
        def attempt_send(code, iteration=0):
            from DocStringGenerator.FileProcessor import FileProcessor
            print(f'Sending code in {2 ** iteration} parts.')
            num_parts = 2 ** iteration
            parts = FileProcessor(self.config).split_source_code(code, num_parts)
            responses = []
            for part in parts:
                print(f'Sending part {parts.index(part) + 1} of {len(parts)}')
                reponse = self.bot_communicator.ask_for_docstrings(source_code)
                
                if reponse.is_valid:
                    content = reponse.content
                    if 'length' in content and 'exceed' in content:
                        print('Context length exceeded. Trying again with more parts.')
                        return attempt_send(code, iteration + 1)
                    responses.append(content)
                else:
                    return content
            return APIResponse(content,True)

        return attempt_send(source_code)


    def handle_file_based_responses(self):
        responses = []
        working_directory = os.getcwd()
        base_bot_file = self.config['bot_response_file']

        if not os.path.isabs(base_bot_file):
            base_bot_file = os.path.join(working_directory, f"responses/{base_bot_file}")

        base_bot_file, _ = os.path.splitext(base_bot_file)

        counter = 1
        bot_file = f"{base_bot_file}.response.json"
        while os.path.exists(bot_file):
            with open(bot_file, 'r') as f:
                response_text = f.read()
                responses.append(response_text)

            counter += 1
            bot_file = f"{base_bot_file}.response{counter}.json"

        return responses               
    

