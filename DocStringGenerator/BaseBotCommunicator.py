import json
import os
from bots import *
from dotenv import load_dotenv
from DocStringGenerator.Utility import *
from DocStringGenerator.ConfigManager import ConfigManager

class BaseBotCommunicator:

    def __init__(self):
        configManager = ConfigManager()
        self.config = configManager.config
        load_dotenv()
        configManager.set_config('verbose', True)
        configManager.set_config('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))
        configManager.set_config('ANTHROPIC_API_KEY', os.getenv('ANTHROPIC_API_KEY'))
        configManager.set_config('GOOGLE_API_KEY', os.getenv('GOOGLE_API_KEY'))

    def ask(self, prompt: str, replacements: dict[str, str]) -> APIResponse:
        """
        Sends a request to the respective bot API or file system. This method should be implemented by subclasses.
        """
        raise NotImplementedError('This method should be implemented by subclasses')

    def format_prompt(self, prompt_template: str, replacements: dict[str, str]) -> APIResponse:
        """
        Formats the prompt by replacing placeholders with actual values provided in 'replacements'.
        """
        try:
            for key, value in replacements.items():
                prompt_template = prompt_template.replace(f'{{{key}}}', value)
            return APIResponse(prompt_template, True)
        except Exception as e:
            return APIResponse('', False, str(e))

    def ask_retry(self, last_error_message: str, retry_count: int) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_retry')
        replacements: dict[str, str] = {
            'last_error_message': last_error_message,
            'retry_count': str(retry_count)
        }
        return self.ask(prompt_template, replacements)

    def _format_class_errors(self, class_errors: list[dict[str, str]]) -> str:
        error_string = ''
        for class_error in class_errors:         
            error_string += f'{class_error["class"]}: {class_error["error"]}\n'
        return error_string
    
    def ask_retry_examples(self, class_errors: list[dict[str, str]]) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_retry_example')
        replacements = {
            'class_errors': self._format_class_errors(class_errors),
            'example_retry': 'True'
        }
        return self.ask(prompt_template, replacements)

    def ask_for_docstrings(self, source_code: str, retry_count: int=1) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_docStrings')
        replacements: dict[str, str] = {
            'source_code': source_code,
            'max_line_length': str(self.config.get('max_line_length', 79)),
            'class_docstrings_verbosity_level': str(self.config.get('class_docstrings_verbosity_level', 5)),
            'function_docstrings_verbosity_level': str(self.config.get('function_docstrings_verbosity_level', 2)),
            'example_verbosity_level': str(self.config.get('example_verbosity_level', 3)),
            'retry_count': str(retry_count)
        }

        return self.ask(prompt_template, replacements)

    def ask_missing_docstrings(self, class_names: str, retry_count: int=1) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_missingDocStrings')
        replacements: dict[str, str] = {
            'function_names': json.dumps(class_names),
            'retry_count': str(retry_count),
            'ask_missing': 'True'
        }
        return self.ask(prompt_template, replacements)

