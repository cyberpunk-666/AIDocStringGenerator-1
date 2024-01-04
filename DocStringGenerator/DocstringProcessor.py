from unittest.mock import MagicMock, patch, ANY

import re
from typing import Any, Dict, Tuple
import ast
import logging
import json
from DocStringGenerator.Utility import APIResponse, Utility
from pathlib import Path
from json.decoder import JSONDecodeError
import tempfile
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.DependencyContainer import DependencyContainer, Scope
dependencies = DependencyContainer()
from DocStringGenerator.GlobalConfig import GlobalConfig
global_config = dependencies.resolve(GlobalConfig)

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

    def insert_docstrings(self, content: str, docstrings: Dict[str, Dict[str, str]]):

        content_lines = content.splitlines()
        tree = ast.parse(content)

        insertions = self._prepare_insertions(tree, content_lines, docstrings)

        new_content: list[str] = []
        for i, line in enumerate(content_lines):
            new_content.append(line)
            if i in insertions:
                new_content.append(insertions[i])  # Properly extend the list with the docstring lines

        new_content_str: str = '\n'.join(new_content)
        return new_content_str

    def _prepare_insertions(self, tree: ast.AST, content_lines: list[str], docstrings: dict[str, Any]) -> dict[int, str]:
        insertions: dict[int, str] = {}
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

    def _get_indent(self, line: str) -> int:
        return len(line) - len(line.lstrip())

    def _format_docstring(self, docstring_str: str, indent_level: int):
        indent = ' ' * indent_level

        # Replace escaped newlines with actual newlines
        docstring_str = docstring_str.replace('\\n', '\n')
        docstring_lines = docstring_str.splitlines()

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
            formatted_docstring = [f'{indent}"""{docstring_str}"""']

        return '\n'.join(formatted_docstring)

    def _validate_function_docstring(self, methods: dict[str, str], max_length: int=999) -> APIResponse:
        for method_name, method_doc in methods.items():
            for line in method_doc.splitlines():
                if len(line) > max_length:
                    return APIResponse(None, False, f"Docstring line in '{method_name}' exceeds maximum length of {max_length} characters.")

        return APIResponse(None, True)
        

    def validate_response(self, json_object: Any, example_only: bool=False, ask_missing: bool=False, max_length: int=999) -> APIResponse:
        try:            
            docstrings: dict[str, Any] = {}
            # Validate docstrings
            if not ask_missing:
                docstrings = json_object.get("docstrings", {})
                if not isinstance(docstrings, dict):
                    return APIResponse(json_object, False, "Invalid format: 'docstrings' should be a dictionary.")
            
            if not example_only:
                # Validate each class and global functions
                for key, value in docstrings.items():
                    if key == "global_functions":
                        if not isinstance(value, dict):
                            return APIResponse(json_object, False, f"Invalid format: Global functions under '{key}' should be a dictionary.")
                        else:
                            response = self._validate_function_docstring(value)
                            if not response.is_valid:
                                return response
                        
                    else:
                        if not isinstance(value, dict) or "docstring" not in value:
                            return APIResponse(json_object, False, f"Invalid format: Class '{key}' should contain a 'docstring'.")
                        methods: str = value["methods"]
                        if "methods" in value and not isinstance(methods, dict):
                            return APIResponse(json_object, False, f"Invalid format: Methods under class '{key}' should be a dictionary.")
                        response = self._validate_function_docstring(value.get("methods", {}))
                        if not response.is_valid:
                            return response
                    # Check docstring length
                    docstring = value.get('docstring', "")
                    for line in docstring.splitlines():
                        if len(line) > max_length:
                            return APIResponse(json_object, False, f"Docstring line in '{key}' exceeds maximum length of {max_length} characters.")


            # Validate examples
            if "examples" in json_object and not isinstance(json_object["examples"], dict):
                return APIResponse(json_object, False, "Invalid format: 'examples' should be a dictionary.")

        except json.JSONDecodeError as e:
            return APIResponse(json_object, False, f"JSON decoding error encountered. {e}")

        return APIResponse(json_object, True, "Response validated successfully.")

    
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

    def extract_docstrings(self, responses: list[dict[str, Any]] | str, example_only: bool = False, ask_missing: bool=False) -> APIResponse:
        # Merge responses before validity check
        json_responses = []
        if isinstance(responses, list):
            for response in responses:
                content = response["content"]
                parse_json_response: APIResponse = Utility.parse_json(content)
                json_object = parse_json_response.content
                if not parse_json_response.is_valid:
                    return parse_json_response

                json_responses.append(json_object)
        elif isinstance(responses, str):
            content = responses
            parse_json_response: APIResponse = Utility.parse_json(content)
            json_object = parse_json_response.content
            if not parse_json_response.is_valid:
                return parse_json_response

            json_responses.append(json_object)

        merged_response = self.merge_json_objects(json_responses)

        # Check the validity of the merged response
        max_length=self.config.get('max_line_length', 999)
        response = self.validate_response(merged_response, example_only, ask_missing, max_length)
        if not response.is_valid:
            return response           

        # Extract docstrings from merged data
        docstrings = merged_response.get("docstrings", {})
        if docstrings:
            return APIResponse(docstrings, True)
        
        return APIResponse("", False, "No docstrings found in response.")               


if global_config.mode == "web":
    dependencies.register(DocstringProcessor, DocstringProcessor, Scope.SCOPED)
else:
    dependencies.register(DocstringProcessor, DocstringProcessor, Scope.SINGLETON)