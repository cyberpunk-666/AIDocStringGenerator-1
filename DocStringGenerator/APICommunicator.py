from dataclasses import dataclass
from typing import Dict
import requests
import json
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
    MOCK_RESPONSES_FILE = 'mock_bot.txt'
    def __new__(cls, config: dict):
        if cls._instance is None:
            cls._instance = super(APICommunicator, cls).__new__(cls)
            # Initialize the instance only once
            
        return cls._instance
        
    def __init__(self, config: dict):
        self.config = config
        self.claude_url = "https://api.anthropic.com/v1/complete"         

    def ask_claude(self, prompt_template, replacements, config):    
        prompt_template = prompt_template.replace("{verbosity_level}", str(config.get("verbosity_level", 2)))
        prompt = prompt_template
        for key, val in replacements.items():
            prompt = prompt.replace(f"{{{key}}}", val)
            
        claude_prompt = 'Human: ' + prompt + '\n\nAssistant:'
        
        url = 'https://api.anthropic.com/v1/complete'
        headers = {'anthropic-version': '2023-06-01', 
                'content-type': 'application/json',
                'x-api-key': config['claude_api_key']}
                
        model = ConfigManager.get_model(config['bot'])
        data = {'model': model, 
                'prompt': claude_prompt, 
                'max_tokens_to_sample': 4000,
                'stream': True}
                
        try:
            response = requests.post(url, 
                                    headers=headers, 
                                    data=json.dumps(data), 
                                    stream=True,)
                                    
            full_completion = ''
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data:'):
                        event_data = json.loads(decoded_line[6:])
                        completion = event_data.get('completion', '')
                        if config["verbose"]:
                            print(completion, end='')
                        full_completion += completion
                        if event_data.get('stop_reason') is not None:
                            break
                            
            return full_completion
        except Exception as e:
            return f'Error during Claude API call: {str(e)}'

    def ask_claude_for_docstrings(self, source_code, config):
        import sys


        prompt_template = Utility.load_prompt("prompts/prompt_docStrings")
        replacements = {
            "source_code": source_code
        }
        
        return self.ask_claude(prompt_template, replacements, config)

    def _parse_claude_response(self, response: requests.Response) -> APIResponse:
        content = ""
        for line in response.iter_lines():
            if line:
                content += self._process_claude_line(line) 
        return APIResponse(content, True)

    def _process_claude_line(self, line: str) -> str:
        if line.startswith('data:'):
            event_data = json.loads(line[6:])
            completion = event_data.get('completion', '')
            if "\n" in completion:
                completion = completion.replace("\\n", "\n")

            return completion
        
        return ""


    def ask_openai(self, prompt_template, replacements, config, system_prompt="You are a helpful assistant.", verbose=False):       
        prompt_template = prompt_template.replace("{verbosity_level}", str(config.get("verbosity_level", 2)))    
        prompt = prompt_template
        for key, val in replacements.items():
            prompt = prompt.replace(f"{{{key}}}", val)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        client = OpenAI(api_key=config['openai_api_key'])
        try:
            stream = client.chat.completions.create(
                model=config["model"], 
                messages=messages, 
                temperature=0,
                stream=True
            )
            
            response = ''
            for chunk in stream:
                if config["verbose"]:
                    print(Utility.convert_newlines(chunk.choices[0].delta.content or ''), end='')
                response += chunk.choices[0].delta.content or ''
                
            return response
        
        except Exception as e:
            return f'Error during OpenAI API call: {e}'
        
    def ask_openai_for_docstrings(self, source_code, config):
        prompt_template = Utility.load_prompt("prompts/prompt_docStrings")
        replacements = {
            "source_code": source_code
        }
        return self.ask_openai(prompt_template, replacements, config)     

    def ask_for_docstrings(self, source_code, config):
    
        if config['bot'] == 'file':
            with open(APICommunicator.MOCK_RESPONSES_FILE) as f:
                response = f.read()
            is_valid = True    
        else:
            response = self.send_code_in_parts(source_code, config)
            context_exceeded, has_docstrings, is_valid = self.get_response_validity(response, config)
            
            if not is_valid and not context_exceeded:
                prompt_retry = Utility.load_prompt("prompts/prompt_retry")         
                if config['bot'] == 'claude':
                    return self.ask_claude(prompt_retry, {}, config) 
                else:
                    return self.ask_openai(prompt_retry, {}, config)
                
            
        return (response, is_valid)   
    
    def send_code_in_parts(self, source_code, config):

        def make_request(code):
            if config["bot"] == 'claude':
                return self.ask_claude_for_docstrings(code, config)
            else:
                return self.ask_openai_for_docstrings(code, config)



        def attempt_send(code, iteration=0):
            from DocStringGenerator.FileProcessor import FileProcessor
            print(f'Sending code in {2 ** iteration} parts.')
            num_parts = 2 ** iteration
            parts = FileProcessor(self.config).split_source_code(code, num_parts)
            responses = []
            for part in parts:
                print(f'Sending part {parts.index(part) + 1} of {len(parts)}')
                print(part)
                response = make_request(part)
                if 'context_length_exceeded' in response:
                    print('Context length exceeded. Trying again with more parts.')
                    return attempt_send(code, iteration + 1)
                responses.append(response)
            return '\n'.join(responses)
        
        return attempt_send(source_code)    
    
    EXPECTED_KEYS = {'docstrings'}

    def get_response_validity(response, config):
        context_exceeded = 'context_length_exceeded' in response
        has_docstrings = 'docstrings = {' in response
        is_valid = DocstringProcessor().validate_response(response)
        
        if not is_valid and not context_exceeded and not has_docstrings and config["verbose"]:
            print('Retrying with the full code as the response format was incorrect.')
            
        return (context_exceeded, has_docstrings, is_valid)