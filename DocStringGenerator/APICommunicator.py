from bardapi import Bard
from requests.exceptions import RequestException
from openai import APIError, APITimeoutError, BadRequestError, AuthenticationError  # and others as needed

import time
from dataclasses import dataclass
from typing import Dict
import requests
import json
import os
from openai import OpenAI
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.Utility import Utility
from DocStringGenerator.DocstringProcessor import DocstringProcessor


@dataclass
class APIResponse:
    content: str
    is_valid: bool

class APICommunicator:
    _instance = None

    def __new__(cls, config: dict):
        if cls._instance is None:
            cls._instance = super(APICommunicator, cls).__new__(cls)
        return cls._instance

    def __init__(self, config: dict):
        self.config = config
        self.claude_url = 'https://api.anthropic.com/v1/complete'

               

    def ask_claude(self, prompt_template, replacements, config):
        prompt = prompt_template
        for key, val in replacements.items():
            prompt = prompt.replace(f'{{{key}}}', val)
        claude_prompt = 'Human: ' + prompt + '\n\nAssistant:'
        url = 'https://api.anthropic.com/v1/complete'
        CLAUDE_API_KEY = config['CLAUDE_API_KEY'] or os.environ.get('CLAUDE_API_KEY')
        headers = {'anthropic-version': '2023-06-01', 'content-type': 'application/json', 'x-api-key': CLAUDE_API_KEY}
        model = ConfigManager.get_model(config['bot'])
        data = {'model': model, 'prompt': claude_prompt, 'max_tokens_to_sample': 4000, 'stream': True}

        if config['verbose']:
            Utility.print_long_string(f'Sending prompt to API: {claude_prompt}')
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data), stream=True)
            full_completion = ''
            first_block_received = False
            last_block_time = None
            timeout = 15  # Timeout in seconds after receiving the first block

            for line in response.iter_lines():
                if line:
                    current_time = time.time()

                    if not first_block_received:
                        first_block_received = True
                        last_block_time = current_time
                        continue

                    if current_time - last_block_time > timeout:
                        raise TimeoutError("Connection timed out after receiving initial data block")

                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data:'):
                        last_block_time = current_time  # Update time of last received block
                        event_data = json.loads(decoded_line[6:])
                        completion = event_data.get('completion', '')
                        full_completion += completion
                        if config['verbose']:
                            print(completion, end='')                        
                        if event_data.get('stop_reason') is not None:
                            if config['verbose']:
                                print("Received stop reason, breaking loop.")
                            break

            return full_completion
        except TimeoutError as e:
            if config['verbose']:
                print(f'Timeout error: {str(e)}')
            return f'Timeout error: {str(e)}'
        except RequestException as e:
            if config['verbose']:
                print(f'Error during API call: {str(e)}')
            return f'Error during Claude API call: {str(e)}'
        except ConnectionError as e:
            if config['verbose']:
                print(f'Error during API call: {str(e)}')
            return f'Error during Claude API call: {str(e)}'
        except Exception as e:
            if config['verbose']:
                print(f'Error during API call: {str(e)}')
            return f'Error during Claude API call: {str(e)}'
              
    def _parse_claude_response(self, response: requests.Response) -> APIResponse:
        content = ''
        for line in response.iter_lines():
            if line:
                content += self._process_claude_line(line)
        return APIResponse(content, True)

    def _process_claude_line(self, line: str) -> str:
        if line.startswith('data:'):
            event_data = json.loads(line[6:])
            completion = event_data.get('completion', '')
            if '\n' in completion:
                completion = completion.replace('\\n', '\n')
            return completion
        return ''

        
    def ask_openai(self, prompt_template, replacements, config, system_prompt='You are a helpful assistant.', verbose=False):
        prompt = prompt_template
        for key, val in replacements.items():
            prompt = prompt.replace(f'{{{key}}}', val)
        messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}]
        model = ConfigManager.get_model(config['bot'])
        OPENAI_API_KEY = config['OPENAI_API_KEY'] or os.environ.get('OPENAI_API_KEY')
        client = OpenAI(api_key=OPENAI_API_KEY)

        try:
            stream = client.chat.completions.create(model=model, messages=messages, temperature=0, stream=True)
            response = ''
            first_block_received = False
            last_block_time = None
            timeout = 15  # Timeout in seconds after receiving the first block

            for chunk in stream:
                current_time = time.time()

                if not first_block_received:
                    # Mark the receipt of the first block
                    first_block_received = True
                    last_block_time = current_time
                    continue

                if current_time - last_block_time > timeout:
                    # Timeout since last block
                    raise APITimeoutError()

                if config['verbose']:
                    print(Utility.convert_newlines(chunk.choices[0].delta.content or ''), end='')
                response += chunk.choices[0].delta.content or ''
                last_block_time = current_time  # Update time of last received block

            return response
        except APITimeoutError:
            return 'Timeout error: Request timed out after receiving initial data block.'
        except (BadRequestError, AuthenticationError):  # Catch specific API errors
            return 'Error: Bad request or authentication failed.'
        except APIError as e:  # Generic catch for other API errors
            return f'API error occurred: {e}'        



    def get_response(self, source_code, config):
        responses = []

        if config['bot'] == 'file':
            # Handling file-based responses
            working_directory = os.getcwd()
            base_bot_file = config['bot_response_file']

            # Check if it's a path or just a filename
            if not os.path.isabs(base_bot_file):
                base_bot_file = os.path.join(working_directory, f"responses/{base_bot_file}")

            # Remove file extension if present
            base_bot_file, _ = os.path.splitext(base_bot_file)

            bot_file = f"{base_bot_file}.response.json"
            while os.path.exists(bot_file):
                with open(bot_file, 'r') as f:
                    response_text = f.read()  # Read the raw string content
                    responses.append(response_text)
                bot_file = f"{base_bot_file}.response.json"
        else:
            # Handling bot-based responses
            responses = self.send_code_in_parts(source_code, config)

        return responses

    def ask(self, prompt, replacement):
        if self.config['bot'] == 'claude':
            return self.ask_claude(prompt, replacement, self.config)
        elif self.config['bot'] == 'bard':
            return self.ask_bard(prompt, replacement, self.config)
        elif self.config['bot'] == 'openai':
            return self.ask_openai(prompt, replacement, self.config)
        elif self.config['bot'] == 'file':
            return self.ask_file(prompt, replacement, self.config)


    def ask_retry(self, config):
        prompt_template = Utility.load_prompt('prompts/prompt_retry')
        return self.ask(prompt_template, {}, config)
  

    def ask_retry_examples(self, class_name, config):
        prompt_template = Utility.load_prompt('prompts/prompt_retry_example')
        replacements = {'class_name': class_name}
        self.ask(prompt_template, replacements, config)
        
    def ask_for_docstrings(self, source_code, config):
        prompt_template = Utility.load_prompt('prompts/prompt_docStrings')
        replacements = {'source_code': source_code, 
                        'verbosity_level': str(config.get('verbosity_level', 2)),
                        'max_line_length': str(config.get('max_line_length', 79)),
                        "class_docstrings_verbosity_level": str(config.get("class_docstrings_verbosity_level",5)),
                        "function_docstrings_verbosity_level":  str(config.get("function_docstrings_verbosity_level",2)),
                        "example_verbosity_level": str(config.get("example_verbosity_level",3))
                        }
                
        return self.ask(prompt_template, replacements, config)


    def send_code_in_parts(self, source_code, config):

        def make_request(code):
            return self.ask_for_docstrings(code, config)

        def attempt_send(code, iteration=0):
            from DocStringGenerator.FileProcessor import FileProcessor
            print(f'Sending code in {2 ** iteration} parts.')
            num_parts = 2 ** iteration
            parts = FileProcessor(self.config).split_source_code(code, num_parts)
            responses = []
            for part in parts:
                print(f'Sending part {parts.index(part) + 1} of {len(parts)}')
                #print(part)
                response = make_request(part)
                if 'context_length_exceeded' in response:
                    print('Context length exceeded. Trying again with more parts.')
                    return attempt_send(code, iteration + 1)
                responses.append(response)
            return responses
        
        return attempt_send(source_code)
    
    EXPECTED_KEYS = {'docstrings'}

    
    def ask_bard(self, prompt_template, replacements, config):
        prompt_template = prompt_template.replace('{verbosity_level}', str(config.get('verbosity_level', 2)))
        prompt = prompt_template
        for key, val in replacements.items():
            prompt = prompt.replace(f'{{{key}}}', val)

        bard = Bard(token_from_browser=True)
        response = bard.get_answer(prompt)
        return response['content']
    