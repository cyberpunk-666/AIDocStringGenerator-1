import os
from pathlib import Path
import json
from dataclasses import dataclass
from typing import Any

@dataclass
class APIResponse:
    content: Any
    is_valid: bool
    error_message: str = ""

class Utility:
    """
    Utility class providing static methods for common helper tasks like
    reading configurations, loading prompts from files, parsing
    JSON strings, etc.
    """

    @staticmethod
    def extract_json(input_string: str) -> APIResponse:
        """
        Extracts valid JSON string from input text, checking for
        balanced braces and valid JSON format. Returns tuple
        with JSON string, boolean validity indicator and error
        message.
        """
        brace_count = 0
        in_string = False
        escape = False
        start_index = None
        found_json_string = ""
        is_valid = True
        error_message = ''
        for i, char in enumerate(input_string):
            if char == '"' and (not escape):
                in_string = not in_string
            elif char == '\\' and in_string:
                escape = not escape
                continue
            elif char == '{' and (not in_string):
                brace_count += 1
                if brace_count == 1:
                    start_index = i
            elif char == '}' and (not in_string):
                brace_count -= 1
                if brace_count == 0 and start_index is not None:
                    found_json_string = input_string[start_index:i + 1]
                    try:
                        json.loads(found_json_string)
                    except json.JSONDecodeError as e:
                        is_valid = False
                        error_message = str(e)
                    break
            if char != '\\':
                escape = False
        if brace_count != 0:
            is_valid = False
            error_message = 'Unbalanced curly braces in JSON string.'
        if not found_json_string or found_json_string.strip() == '':
            is_valid = False
            error_message = 'No JSON string found.'
        return APIResponse(found_json_string, is_valid, error_message)

    @staticmethod
    def parse_json(text: str) -> APIResponse:
        """
        Tries to parse a JSON string from given text input. Handles
        errors and returns tuple with parsed object or None, 
        validity boolean and error message if any.
        """
        json_object = None
        error_message = None
        json_string = ""
        try:
            
            response = Utility.extract_json(text)
            json_string = response.content
            if response.is_valid:
                json_object = json.loads(json_string)
                return APIResponse(json_object, True)
            else:
                return APIResponse(None, False, response.error_message)
        except json.JSONDecodeError as e:
            error_message = str(e)
            return APIResponse(None, False, error_message)
        

    @staticmethod
    def read_config(config_path: Path) -> dict[str, Any]:
        """
        Reads given config file path as JSON and returns
        parsed config dict.
        """
        return json.loads(config_path.read_text())

    @staticmethod
    def load_prompt(file_name: str, base_path: str='.') -> str:
        """
        Loads text content from a file in base path, handling
        new lines.
        """
        file_path = os.path.join(base_path, file_name)
        with open(f'{file_path}.txt', 'r') as file:
            return file.read()


    @staticmethod
    def is_valid_python(code: str) -> APIResponse:
        """Checks if given Python code text is valid syntactically."""
        try:
            compile(code, '<string>', 'exec')
            return APIResponse(True, True)
        except SyntaxError as e:
            return APIResponse(False, False, str(e))
