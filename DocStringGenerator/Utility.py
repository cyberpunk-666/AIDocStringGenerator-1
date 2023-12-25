import os
import ast
from pathlib import Path
from typing import Dict
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.Spinner import Spinner

import json
import re

class Utility:
  
    @staticmethod                   
    def extract_json(input_string):
        brace_count = 0
        in_string = False
        escape = False
        start_index = None
        found_json_string = None
        is_valid = True
        error_message = ""

        for i, char in enumerate(input_string):
            if char == '"' and not escape:
                in_string = not in_string
            elif char == '\\' and in_string:
                escape = not escape
                continue
            elif char == '{' and not in_string:
                brace_count += 1
                if brace_count == 1:
                    start_index = i
            elif char == '}' and not in_string:
                brace_count -= 1
                if brace_count == 0 and start_index is not None:
                    found_json_string = input_string[start_index:i+1]
                    # Check if the found string is a valid JSON
                    try:
                        json.loads(found_json_string)
                    except json.JSONDecodeError as e:
                        is_valid = False
                        error_message = str(e)
                    break
            if char != '\\':
                escape = False

        # Check if the brackets are unbalanced
        if brace_count != 0:
            is_valid = False
            error_message = "Unbalanced curly braces in JSON string."
        if not found_json_string or found_json_string.trim() == "":
            is_valid = False
            error_message = "No JSON string found."

        return found_json_string, is_valid, error_message

    @staticmethod 
    def parse_json(text):
        json_object= None
        is_valid = True
        error_message = None
        try:
            json_string, is_valid, error_message =Utility.extract_json(text)
            if is_valid:
                json_object = json.loads(json_string)
            else:
                print(f"Invalid JSON: {error_message}")
                is_valid = False
        except json.JSONDecodeError as e:
            error_message = str(e)
            print(f"Invalid JSON: {json_string}\nError: {e}")
            is_valid = False

        return json_object, is_valid, error_message

    @staticmethod
    def read_config(config_path: Path) -> dict:
        return json.loads(config_path.read_text())
    
    @staticmethod
    def load_prompt(file, base_path="."):
        file_path = os.path.join(base_path, file)
        with open(f"{file_path}.txt", 'r') as file:
            return file.read()
        
    @staticmethod
    def convert_newlines(content):
        try:
            return ast.literal_eval(f"'{content}'")
        except (ValueError, SyntaxError):
            return content
        

    
    @staticmethod
    def is_valid_python(code):
        try:
            # Attempt to compile the code
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError:
            # The code has syntax errors
            return False    
            
