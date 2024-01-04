import json
import time
import requests
from requests.models import Response

from bots import *
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.Logger import Logger
dependencies = DependencyContainer()

class ChunkData:
    def __init__(self, bot_name: str, chunk: str):
        self.bot_name = bot_name
        self.chunk = chunk
class AnthropicCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        self.logger : Logger = dependencies.resolve(Logger)
        self.anthropic_url = 'https://api.anthropic.com/v1/complete'
        self.prompt = ''

    def ask(self, prompt: str, replacements: dict[str, str]) -> APIResponse:

        prompt_response = self.format_prompt(prompt, replacements)
        if not prompt_response.is_valid:
            return prompt_response
        
        try:            
            new_prompt = '\n\nHuman: ' + prompt_response.content + '\n\nAssistant:'
            self.logger.log_line("sending prompt: " + new_prompt)
            
            self.prompt += new_prompt
            api_key = self.config.get('ANTHROPIC_API_KEY')
            headers: dict[str, str] = {'anthropic-version': '2023-06-01', 'content-type': 'application/json', 'x-api-key': api_key if api_key else ''}
            model = self.config.get('model', '')
            models: list[str] = BOTS[self.config.get('bot', '')]
            if model not in models:
                return APIResponse('', False, f'Invalid bot: {model}')
            data = {'model': model, 'prompt': self.prompt, 'max_tokens_to_sample': 4000, 'stream': True}
            response: Response = requests.post(self.anthropic_url, headers=headers, data=json.dumps(data), stream=True)
            response_handled: APIResponse = self.handle_response(response)
            return response_handled
        except Exception as e:
            return APIResponse(None, is_valid=False, error_message=str(e))

    def handle_response(self, response: Response) -> APIResponse:
        first_block_received = False
        full_completion = ''
        try:
            self.logger.log_line("Receiving response from Anthropic API...")
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
                        self.logger.log(completion)
                        if event_data.get('stop_reason') is not None:
                            break
        except Exception as e:
            full_completion = ''
            return APIResponse(None, is_valid=False, error_message=str(e))
        return APIResponse(content=full_completion, is_valid=True)
