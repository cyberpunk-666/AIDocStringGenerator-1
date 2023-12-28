from unittest.mock import MagicMock, patch, ANY

import re
from typing import Dict, Tuple
import ast
import logging
import json
from DocStringGenerator.Utility import APIResponse, Utility
from pathlib import Path
from json.decoder import JSONDecodeError
import tempfile
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.DependencyContainer import DependencyContainer

class DocstringProcessor:
    """The `DocstringProcessor` class is a singleton that provides functionality to insert docstrings into a Python source file.
    It is designed to read a file, parse its abstract syntax tree (AST), and insert docstrings at the appropriate locations based on the provided configuration.
    The class ensures that only one instance is created, and subsequent instantiations return the existing instance.
    The class methods include functionality to prepare and format docstring insertions, determine indentation levels, and validate and extract docstrings from a JSON response.
    The class requires a configuration dictionary upon instantiation, which dictates certain behaviors such as verbosity during extraction of docstrings.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DocstringProcessor, cls).__new__(cls)
            # Initialize the instance only once
            
        return cls._instance

    def __init__(self):
        self.config = ConfigManager().config

    def insert_docstrings(self, content, docstrings: Dict[str, Dict[str, str]]):

        content_lines = content.splitlines()
        tree = ast.parse(content)

        insertions = self._prepare_insertions(tree, content_lines, docstrings)

        new_content = []
        for i, line in enumerate(content_lines):
            new_content.append(line)
            if i in insertions:
                new_content.append(insertions[i])  # Properly extend the list with the docstring lines

        new_content = '\n'.join(new_content)
        return new_content

    def _prepare_insertions(self, tree, content_lines, docstrings):
        insertions = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                start_line = node.lineno - 1
                indent_level = 4 + self._get_indent(content_lines[start_line])
                class_or_func_name = node.name

                if isinstance(node, ast.ClassDef) and class_or_func_name in docstrings:
                    class_doc = docstrings[class_or_func_name]
                    if "docstring" in class_doc:
                        insertions[start_line] = self._format_docstring(class_doc["docstring"], indent_level)

                    if "methods" in class_doc:
                        for method_name, method_doc in class_doc["methods"].items():
                            for inner_node in node.body:
                                if isinstance(inner_node, ast.FunctionDef) and inner_node.name == method_name:
                                    inner_start_line = inner_node.lineno - 1
                                    inner_indent_level = 4 + self._get_indent(content_lines[inner_start_line])
                                    insertions[inner_start_line] = self._format_docstring(method_doc, inner_indent_level)

                elif isinstance(node, ast.FunctionDef) and 'global_functions' in docstrings:
                    if class_or_func_name in docstrings['global_functions']:
                        func_doc = docstrings['global_functions'][class_or_func_name]
                        insertions[start_line] = self._format_docstring(func_doc, indent_level)

        return insertions

    def _get_indent(self, line):
        return len(line) - len(line.lstrip())

    def _format_docstring(self, docstring, indent_level):
        indent = ' ' * indent_level

        # Replace escaped newlines with actual newlines
        docstring = docstring.replace('\\n', '\n')
        docstring_lines = docstring.splitlines()

        # If the docstring is multiline
        if len(docstring_lines) > 1:
            # Start the docstring with opening triple quotes on a new line
            formatted_docstring = [f'{indent}\"\"\"']
            # Add each line of the docstring, indented
            formatted_docstring.extend(f'{indent}{line}' for line in docstring_lines)
            # Append closing triple quotes on a new line
            formatted_docstring.append(f'{indent}\"\"\"')
        else:
            # If the docstring is a single line, keep it on one line with the closing triple quotes
            formatted_docstring = [f'{indent}"""{docstring}"""']

        return '\n'.join(formatted_docstring)

            
    def validate_response(self, json_object):
        try:

            if self.config.get('verbose', ""):
                print("Validating docstrings...")

            # Validate docstrings
            docstrings = json_object.get("docstrings", {})
            if not isinstance(docstrings, dict):
                if self.config.get('verbose', ""):
                    print("Invalid format: 'docstrings' should be a dictionary.")
                return False

            # Validate each class and global functions
            for key, value in docstrings.items():
                if key == "global_functions":
                    if not isinstance(value, dict):
                        if self.config.get('verbose', ""):
                            print(f"Invalid format: Global functions under '{key}' should be a dictionary.")
                        return False
                else:
                    if not isinstance(value, dict) or "docstring" not in value:
                        if self.config.get('verbose', ""):
                            print(f"Invalid format: Class '{key}' should contain a 'docstring'.")
                        return False
                    if "methods" in value and not isinstance(value["methods"], dict):
                        if self.config.get('verbose', ""):
                            print(f"Invalid format: Methods under class '{key}' should be a dictionary.")
                        return False

            if self.config.get('verbose', ""):
                print("Validating examples...")

            # Validate examples
            if "examples" in json_object and not isinstance(json_object["examples"], dict):
                if self.config.get('verbose', ""):
                    print("Invalid format: 'examples' should be a dictionary.")
                return False

            if self.config.get('verbose', ""):
                print(f"Validation successful for response: {json_object}")

        except json.JSONDecodeError:
            if self.config.get('verbose', ""):
                print(f"JSON decoding error encountered for response: {json_object}")
            return False

        if self.config.get('verbose', ""):
            print("Response validated successfully.")

        return True


    
    def deep_merge_dict(self, dct1, dct2):
        """
        Recursively merge two dictionaries, including nested dictionaries.
        """
        merged = dct1.copy()
        for key, value in dct2.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self.deep_merge_dict(merged[key], value)
            else:
                merged[key] = value
        return merged

    def merge_json_objects(self, json_objects):
        """
        Merge a list of JSON objects, deeply merging nested dictionaries.
        """
        merged_data = {}

        for obj in json_objects:
            merged_data = self.deep_merge_dict(merged_data, obj)

        return merged_data

    def extract_docstrings(self, responses) -> APIResponse:
        # Merge responses before validity check
        json_responses = []
        for response in responses:
            json_object, is_valid, error_message = Utility.parse_json(response)
            if not is_valid:
                message: str = f"Invalid response: {response}\nError: {error_message}"
                if self.config.get('verbose', ""):                    
                    print(message)
                return APIResponse("", False, message)
            json_responses.append(json_object)

        merged_response = self.merge_json_objects(json_responses)

        # Check the validity of the merged response
        is_valid = self.validate_response(merged_response)
        if not is_valid:
            message: str = f"Invalid response after merging. Aborting extraction."
            if self.config.get('verbose', ""):                    
                print(message)
            return APIResponse("", False, message)            

        # Extract docstrings from merged data
        docstrings = merged_response.get("docstrings", {})
        if docstrings:
            return APIResponse(docstrings, True)
        
        return APIResponse("", False, "No docstrings found in response.")               


dependencies = DependencyContainer()
dependencies.register('DocstringProcessor', DocstringProcessor)