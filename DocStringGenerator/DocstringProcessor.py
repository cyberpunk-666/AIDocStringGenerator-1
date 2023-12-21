from typing import Dict, Tuple
import ast
import logging
import json
from DocStringGenerator.Utility import Utility
from pathlib import Path
from json.decoder import JSONDecodeError
import tempfile

class DocstringProcessor:
    _instance = None
    
    def __new__(cls, config: dict):
        if cls._instance is None:
            cls._instance = super(DocstringProcessor, cls).__new__(cls)
            # Initialize the instance only once
            
        return cls._instance

    def __init__(self, config: dict):
        self.config = config


    def insert_docstrings(self, file_path: Path, docstrings: Dict[str, str]):
        """Insert docstrings into a Python source file."""

        content = file_path.read_text()
        content_lines = content.splitlines()
        tree = ast.parse(content)

        insertions = self._prepare_insertions(tree, content_lines, docstrings)

        new_content = []
        for i, line in enumerate(content_lines):
            new_content.append(line)
            if i in insertions:
                # Add the formatted docstring after the class/function definition line
                new_content.append(insertions[i])

        file_path.write_text("\n".join(new_content))


    def _prepare_insertions(self, tree, content_lines, docstrings):
        """Prepare the docstring insertions."""
        insertions = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                start_line = node.lineno - 1
                indent_level = self._get_indent(content_lines[start_line])
                docstring = docstrings.get(node.name)
                if docstring:
                    # Format the docstring with appropriate indentation
                    insertions[start_line] = self._format_docstring(docstring, indent_level)
        return insertions

    def _format_docstring(self, docstring: str, indent: int) -> str:
        """Format the docstring with appropriate indentation."""
        spaces = " " * (indent) + "    " # Additional indentation inside the class/function
        return f'{spaces}"""{docstring.strip()}"""'


    def _get_indent(self, line: str) -> int:
        return len(line) - len(line.lstrip())


    def _build_new_content(self, content: str, insertions: Dict[int, str]) -> str:
        lines = content.splitlines()
        new_content_lines = []

        for i, line in enumerate(lines):
            if i in insertions:
                new_content_lines.append(insertions[i])
            new_content_lines.append(line)

        return "\n".join(new_content_lines)


    def validate_response(self, response):
        try:
            json_str = Utility.extract_json(response)
            data = json.loads(json_str)

            if not isinstance(data["docstrings"], dict):
                return False
                
            keys = set(data.keys())
            if len(keys) != 2: 
                return False
        except (JSONDecodeError, KeyError):
            return False
        return True    
    
    def extract_docstrings(self, response, config):
        try:
            json_str = Utility.extract_json(response)
            if config["verbose"]:
                print(f"Extracted json string: {json_str}")
            data = json.loads(json_str)
            docstrings_dict = data["docstrings"]
            example = data["example"]
            return (docstrings_dict, example, True)
        except (IndexError, ValueError, SyntaxError) as e:
            if config["verbose"]:
                print(f'Error extracting docstrings: {e}')
            return ({}, {}, False)
