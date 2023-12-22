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
    def extract_json(input_string):
        json_objects = []
        brace_count = 0
        in_string = False
        escape = False
        start_index = None

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
                    try:
                        json_obj = json.loads(input_string[start_index:i+1])
                        json_objects.append(json_obj)
                    except json.JSONDecodeError:
                        pass
                    start_index = None
            if char != '\\':
                escape = False

        return json_objects
            
