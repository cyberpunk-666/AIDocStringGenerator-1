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
        configManager.set_config("verbose", True)
        configManager.set_config("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
        configManager.set_config("CLAUDE_API_KEY", os.getenv("CLAUDE_API_KEY"))
        configManager.set_config("BARD_API_KEY", os.getenv("BARD_API_KEY"))

    def ask(self, prompt, replacements)-> APIResponse:
        """
        Sends a request to the respective bot API or file system. This method should be implemented by subclasses.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def handle_response(self, response):
        """
        Handles the response from the bot API or file system. This method can be overridden by subclasses for custom behavior.
        """
        return response

    def format_prompt(self, prompt_template, replacements)-> APIResponse:
        """
        Formats the prompt by replacing placeholders with actual values provided in 'replacements'.
        """
        for key, value in replacements.items():
            prompt_template = prompt_template.replace(f'{{{key}}}', value)
        return prompt_template
    
    def ask_retry(self):
        prompt_template = Utility.load_prompt('prompts/prompt_retry')
        return self.ask(prompt_template, {})

    def ask_retry_examples(self, class_name)-> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_retry_example')
        replacements = {'class_name': class_name}
        return self.ask(prompt_template, replacements)
        
    def ask_for_docstrings(self, source_code) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_docStrings')
        replacements = {'source_code': source_code,
                        'max_line_length': str(self.config.get('max_line_length', 79)),
                        "class_docstrings_verbosity_level": str(self.config.get("class_docstrings_verbosity_level",5)),
                        "function_docstrings_verbosity_level": str(self.config.get("function_docstrings_verbosity_level",2)),
                        "example_verbosity_level": str(self.config.get("example_verbosity_level",3))}
                
        return self.ask(prompt_template, replacements)    

    
class ClaudeCommunicator(BaseBotCommunicator):
    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
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
        model = self.config.get('model', "")
        models = BOTS[self.config.get('bot', "")]
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
        error_message = ""

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
                            if self.config.get('verbose', ""):
                                print("Received stop reason, breaking loop.")
                            break
        except Exception as e:
            full_completion = ''
            return APIResponse(
                None,
                is_valid=False,
                error_message=str(e)
            ) 
        return APIResponse(
            content=full_completion,
            is_valid=True
        )             


class OpenAICommunicator(BaseBotCommunicator):
    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        api_key = self.config.get('OPENAI_API_KEY', "")
        self.client = OpenAI(api_key=api_key)


    def ask(self, prompt, replacements):
        prompt = self.format_prompt(prompt, replacements)
        messages = [{'role': 'system', 'content': 'You are a helpful assistant.'},
                    {'role': 'user', 'content': prompt}]
        
        error_message = ""
        try:

            model = self.config.get('model', "")
            models = BOTS[self.config.get('bot', "")]
            if model not in models:
                print(f'Invalid bot: {model}') 
                return
            stream = self.client.chat.completions.create(model=model,
                                                         messages=messages, temperature=0, stream=True)
            full_completion = self.handle_response(stream)
        except Exception as e:
            full_completion = ''
            return APIResponse(
                None,
                is_valid=False,
                error_message=str(e)
            ) 
        return APIResponse(
            content=full_completion,
            is_valid=True
        ) 

    def handle_response(self, stream):
        response = ''
        for chunk in stream:
            response += chunk.choices[0].delta.content or ''
        return response


class BardCommunicator(BaseBotCommunicator):
    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        api_key = self.config.get('BARD_API_KEY', "")
        genai.configure(api_key=api_key)
        self.bard = genai.GenerativeModel('gemini-pro')


    def ask(self, prompt, replacements):
        formatted_prompt = self.format_prompt(prompt, replacements)
        full_completion = ""
        error_message = ""
        try:
            response = self.bard.generate_content(formatted_prompt, stream=True)
            full_completion =  self.handle_response(response)
        except Exception as e:
            full_completion = ""
            error_message = str(e)
            return APIResponse(
                None,
                is_valid=False,
                error_message=str(e)
            ) 
        return APIResponse(
            content=full_completion,
            is_valid=True
        ) 
        
    def handle_response(self, stream):
        response = ''
        for response_chunk in stream:
            # Process each chunk
            response += response_chunk.text
        return response        


class FileCommunicator(BaseBotCommunicator):
    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()

    def ask(self, prompt, replacements) -> APIResponse:
        # Handling file-based responses
        working_directory = os.getcwd()
        base_bot_file = self.config.get('model', "")
        try:
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
        except Exception as e:
            return APIResponse("", False, str(e))
        return APIResponse(responses, True)
    
class CommunicatorManager:
    def __init__(self):
        #DependencyContainer().resolve('CommunicatorManager').bot_communicator
        self.config = ConfigManager().config
        self.bot_communicator:Optional[BaseBotCommunicator] = self.initialize_bot_communicator()
 
    def initialize_bot_communicator(self) -> Optional[BaseBotCommunicator]:
        if not 'bot' in self.config:
            if self.config.get('verbose', ""):
                print("No bot specified in the configuration. Aborting.")
            return None
        bot_communicator_class = dependencies.resolve(f"{self.config.get('bot', "")}_Communicator")
        if not bot_communicator_class:
            raise ValueError(f"Unsupported bot type '{self.config.get('bot', "")}' specified in the configuration")
        return bot_communicator_class       

    def send_code_in_parts(self, source_code) -> APIResponse:
        from DocStringGenerator.FileProcessor import FileProcessor
        
        def attempt_send(code, iteration=0) -> APIResponse:
            print(f'Sending code in {2 ** iteration} parts.')
            num_parts = 2 ** iteration
            file_processor: FileProcessor = dependencies.resolve("FileProcessor")
            parts = file_processor.split_source_code(code, num_parts)
            responses = []
            response = None
            for part in parts:
                print(f'Sending part {parts.index(part) + 1} of {len(parts)}')
                if self.bot_communicator is not None:
                    response = self.bot_communicator.ask_for_docstrings(part)                
                if response:
                    if response.is_valid:
                        content = response.content
                        if 'length' in content and 'exceed' in content:
                            print('Context length exceeded. Trying again with more parts.')
                            return attempt_send(code, iteration + 1)
                        responses.append(content)
                    else:
                        return response
            aggregated_content = ' '.join(responses)  # Adjust as needed for correct formatting
            return APIResponse(aggregated_content, True)        
        return attempt_send(source_code)


    def handle_file_based_responses(self):
        responses = []
        working_directory = os.getcwd()
        base_bot_file = self.config.get('model', "")

        if not os.path.isabs(base_bot_file):
            base_bot_file = os.path.join(working_directory, f"responses/{base_bot_file}")

        base_bot_file, _ = os.path.splitext(base_bot_file)

        counter = 1
        try:
            bot_file = f"{base_bot_file}.response.json"
            while os.path.exists(bot_file):
                with open(bot_file, 'r') as f:
                    response_text = f.read()
                    responses.append(response_text)

                counter += 1
                bot_file = f"{base_bot_file}.response{counter}.json"
            return APIResponse(responses, True)
        except Exception as e:
            return APIResponse("", False, str(e))
              
    

dependencies = DependencyContainer()
dependencies.register('CommunicatorManager', CommunicatorManager)
dependencies.register('claude_Communicator', ClaudeCommunicator)
dependencies.register('openai_Communicator', OpenAICommunicator)
dependencies.register('bard_Communicator', BardCommunicator)
dependencies.register('file_Communicator', FileCommunicator)