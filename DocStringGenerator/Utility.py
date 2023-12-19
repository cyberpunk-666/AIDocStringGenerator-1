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
        # Use a different pattern to capture escaped newlines
        pattern = r'\{((?:[^{}]+|{(?:[^{}]+)*})*)\}'
        match = re.search(pattern, input_string, re.DOTALL)
        if match:
            return match.group()
        else:
            return "{}"
            
