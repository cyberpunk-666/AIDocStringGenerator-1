import os
import ast
from pathlib import Path
from typing import Dict
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.Spinner import Spinner
import json
import re

class Utility:
    """
    Utility class providing static methods for common helper tasks like
    reading configurations, loading prompts from files, parsing
    JSON strings, etc.
    """

    @staticmethod
    def extract_json(input_string):
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
        found_json_string = None
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
        return (found_json_string, is_valid, error_message)

    @staticmethod
    def parse_json(text):
        """
        Tries to parse a JSON string from given text input. Handles
        errors and returns tuple with parsed object or None, 
        validity boolean and error message if any.
        """
        json_object = None
        is_valid = True
        error_message = None
        try:
            json_string, is_valid, error_message = Utility.extract_json(text)
            if is_valid:
                json_object = json.loads(json_string)
            else:
                print(f'Invalid JSON: {error_message}')
                is_valid = False
        except json.JSONDecodeError as e:
            error_message = str(e)
            print(f'Invalid JSON: {json_string}\nError: {e}')
            is_valid = False
        return (json_object, is_valid, error_message)

    @staticmethod
    def read_config(config_path: Path) -> dict:
        """
        Reads given config file path as JSON and returns
        parsed config dict.
        """
        return json.loads(config_path.read_text())

    @staticmethod
    def load_prompt(file, base_path='.'):
        """
        Loads text content from a file in base path, handling
        new lines.
        """
        file_path = os.path.join(base_path, file)
        with open(f'{file_path}.txt', 'r') as file:
            return file.read()

    @staticmethod
    def convert_newlines(content):
        """
        Converts new line escapes in a string to actual
        new line characters.
        """
        try:
            return ast.literal_eval(f"'{content}'")
        except (ValueError, SyntaxError):
            return content

    @staticmethod
    def is_valid_python(code, config=None):
        """Checks if given Python code text is valid syntactically."""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError as e:
            if config and config['verbose']:
                print(f'Invalid Python code: {e}')
            return False

    def example_function_Utility(self):
        prompt = Utility.load_prompt('prompt_file')
        print(Utility.convert_newlines(prompt))

    def print_long_string(self, long_string):
        n = 1000  # number of characters to display at a time

        for i in range(0, len(long_string), n):
            print(long_string[i:i+n], "")         