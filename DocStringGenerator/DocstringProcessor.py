from typing import Dict, Tuple
import ast
import logging
import json
from DocStringGenerator.Utility import Utility
from pathlib import Path
from json.decoder import JSONDecodeError
import tempfile

class DocstringProcessor:
    """The `DocstringProcessor` class is a singleton that provides functionality to insert docstrings into a Python source file.
    It is designed to read a file, parse its abstract syntax tree (AST), and insert docstrings at the appropriate locations based on the provided configuration.
    The class ensures that only one instance is created, and subsequent instantiations return the existing instance.
    The class methods include functionality to prepare and format docstring insertions, determine indentation levels, and validate and extract docstrings from a JSON response.
    The class requires a configuration dictionary upon instantiation, which dictates certain behaviors such as verbosity during extraction of docstrings.
    """
    _instance = None
    
    def __new__(cls, config: dict):
        if cls._instance is None:
            cls._instance = super(DocstringProcessor, cls).__new__(cls)
            # Initialize the instance only once
            
        return cls._instance

    def __init__(self, config: dict):
        self.config = config


    def insert_docstrings(self, file_path: Path, docstrings: Dict[str, Dict[str, str]]):
        content = file_path.read_text()
        content_lines = content.splitlines()
        tree = ast.parse(content)

        insertions = self._prepare_insertions(tree, content_lines, docstrings)

        new_content = []
        for i, line in enumerate(content_lines):
            new_content.append(line)
            if i in insertions:
                new_content.append(insertions[i])

        file_path.write_text("\n".join(new_content))

    def _prepare_insertions(self, tree, content_lines, docstrings):
        insertions = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                start_line = node.lineno - 1
                indent_level = self._get_indent(content_lines[start_line])
                class_or_func_name = node.name
                if class_or_func_name in docstrings:
                    class_or_func_doc = docstrings[class_or_func_name]
                    if "docstring" in class_or_func_doc:
                        insertions[start_line] = self._format_docstring(class_or_func_doc["docstring"], indent_level)
                    for item_name, item_doc in class_or_func_doc.items():
                        if item_name != "docstring":  # handle method or nested function
                            # additional logic to find the right line number and indentation for nested items
                            pass
        return insertions


    def _format_docstring(self, docstring: str, indent: int) -> str:
        """Format the docstring with appropriate indentation."""
        spaces = " " * (indent) + "    " # Additional indentation inside the class/function
        return f'{spaces}"""{docstring.strip()}"""'


    def _get_indent(self, line: str) -> int:
        """Determine the indentation level of a line of code."""
        return len(line) - len(line.lstrip())


    def _build_new_content(self, content: str, insertions: Dict[int, str]) -> str:
        """Build the new content for a file with docstring insertions."""
        lines = content.splitlines()
        new_content_lines = []

        for i, line in enumerate(lines):
            if i in insertions:
                new_content_lines.append(insertions[i])
            new_content_lines.append(line)

        return "\n".join(new_content_lines)


    def validate_response(self, responses):
        for response in responses:
            try:
                json_objects = Utility.extract_json(response)
                for data in json_objects:
                    if not isinstance(data.get("docstrings", {}), dict):
                        return False
                    for class_name, class_doc in data["docstrings"].items():
                        if not isinstance(class_doc, dict) or "docstring" not in class_doc:
                            return False
                    if "examples" not in data:
                        return False
            except json.JSONDecodeError:
                return False
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

    def extract_docstrings(self, responses, config):
        json_objects = []

        for response in responses:
            try:
                if config["verbose"]:
                    print(f"Extracted json string: {response}")
                data = json.loads(response)
                json_objects.append(data)
            except (IndexError, ValueError, SyntaxError) as e:
                if config["verbose"]:
                    print(f'Error extracting docstrings: {e}')
                continue

        merged_data = self.merge_json_objects(json_objects)
        return merged_data["docstrings"], merged_data["examples"], True
