import os
import io
from pathlib import Path
from typing import List
import ast
import json
import logging
from DocStringGenerator.APICommunicator import APICommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from typing import Dict
from DocStringGenerator.Spinner import Spinner
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.Utility import Utility

FILES_PROCESSED_LOG = "files_processed.log"
    
class FileProcessor:
    """The `FileProcessor` class is designed to handle the processing of Python source files for the purpose of generating, inserting, or removing docstrings. It utilizes an `APICommunicator` to communicate with an external API that provides the docstrings and a `DocstringProcessor` to handle the insertion of the generated docstrings into the source files. This class follows the Singleton design pattern, ensuring that only one instance of `FileProcessor` exists throughout the application's lifecycle.

The class provides methods to split source code into manageable parts, check if a file has been processed, process individual files or entire directories, and remove existing docstrings from source files. It also includes utility methods to find split points in the source code based on abstract syntax tree (AST) analysis and to list files in a directory with a specific extension.

The class is initialized with a configuration dictionary that contains settings for the docstring generation process, such as verbosity level and API endpoint. The configuration is used by the `APICommunicator` and `DocstringProcessor` to tailor the docstring generation and insertion process according to the user's preferences."""
    _instance = None
    def __new__(cls, config: dict):
        if cls._instance is None:
            cls._instance = super(FileProcessor, cls).__new__(cls)
            # Initialize the instance only once
            
        return cls._instance
        
    def __init__(self, config: dict):
        self._api_communicator = APICommunicator(config)
        self.config = config   

    def find_split_point(self, source_code: str, max_lines: int = 2048, start_node=None) -> int:
        """Finds a suitable point to split the source code into smaller parts."""
        try:
            if not start_node:        
                start_node = ast.parse(source_code)
            split_point = self.find_split_point_in_children(start_node, max_lines)
        except SyntaxError:
            # If invalid code, find split point in plain text
            split_point = min(max_lines, source_code.count("\n"))
        return split_point

    def find_end_line(self, node, max_lines):
        """Determines the end line number for a given AST node."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if max_lines >= node.end_lineno:
                return node.end_lineno
            else:
                return node.lineno - 1
        elif isinstance(node, ast.ClassDef):
            return node.lineno
        else:
            return -1

    def find_split_point_in_children(self, node, max_lines, recursive=True):
        """Recursively finds a split point within the children of an AST node."""
        end_line = max(self.find_end_line(node, max_lines), 0)
        child_split_point = 0
        if max_lines >= end_line:
            child_split_point = end_line
        if hasattr(node, "body"):
            for child_node in node.body:
                if child_node:
                    if recursive and (hasattr(child_node, "body") or hasattr(child_node, "orelse")):
                        child_split_point = max(child_split_point or 0,
                                            self.find_split_point_in_children(child_node, max_lines, recursive))
                                        
                    end_line = max(self.find_end_line(child_node, max_lines), 0)
                    if max_lines >= end_line and end_line > child_split_point:                  
                        child_split_point = max(child_split_point or 0, end_line)
        if hasattr(node, "orelse") and not child_split_point:
            for child_node in node.orelse:
                if child_node:
                    if recursive and (hasattr(child_node, "body") or hasattr(child_node, "orelse")):
                        child_split_point = max(child_split_point or 0,
                                            self.find_split_point_in_children(child_node, max_lines, recursive))
                    
                    end_line = max(self.find_end_line(child_node, max_lines), 0)
                    if max_lines >= end_line and end_line > child_split_point:                  
                        child_split_point = max(child_split_point or 0, end_line)
        return child_split_point

    

    def split_source_code(self, source_code: str, num_parts: int):
        """Splits the source code into a specified number of parts."""
        if num_parts == 0:
            return []
        lines = source_code.splitlines(True)
        if source_code.endswith("\n"):
            lines.append("")
        num_lines = len(lines)
        lines_per_part = num_lines // num_parts
        lines_per_part = max(lines_per_part, 1)
        current_line = 0
        output_parts = []

        for i in range(num_parts):
            next_split_line = (i+1) * lines_per_part
            next_split_line = self.find_split_point(source_code, next_split_line)
            if i == num_parts - 1 or next_split_line == -1:
                next_split_line = num_lines

            part_builder = io.StringIO()
            for line in lines[current_line:next_split_line]:
                part_builder.write(line)
            current_part = part_builder.getvalue()

            output_parts.append(current_part)
            current_line = min(next_split_line, num_lines)
        return output_parts

    def log_processed_file(self, file_path):
        filename = file_path.name
        with open(FILES_PROCESSED_LOG, 'a') as log_file:
            log_file.write(filename + '\n')

    def removed_from_processed_log(self, file_path):
        filename = file_path.name
        with open(FILES_PROCESSED_LOG, 'r') as log_file:
            processed_files = log_file.read().splitlines()
        if filename in processed_files:
            processed_files.remove(filename)
        with open(FILES_PROCESSED_LOG, 'w') as log_file:
            log_file.write('\n'.join(processed_files))


    def is_file_processed(self, file_name, log_file_path=None):
        """Checks if a file has already been processed by looking at a log file."""
        try:
            with open(log_file_path or FILES_PROCESSED_LOG, 'r') as log_file:
                processed_files = log_file.read().splitlines()
            return file_name in processed_files
        except FileNotFoundError:
            return False

    def process_folder_or_file(self, config):
        path = Path(config['path'])
        include_subfolders = config.get('include_subfolders', False)
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                if not include_subfolders and root != path:
                    continue
                for file in files:
                    full_file_path = Path(root, file)
                    if file.endswith('.py'):
                        if config['wipe_docstrings']:
                            self.wipe_docstrings(full_file_path)
                      
                        success = self.process_file(full_file_path.absolute(), config)
                        if not success:
                            print(f'Failed to process {str(full_file_path.absolute())}')
                                
        elif os.path.isfile(path) and str(path).endswith('.py'):
            if config['wipe_docstrings']:
                self.wipe_docstrings(path)

            success = self.process_file(path.absolute(), config)
            if not success:
                print(f'Failed to process {path}')
        else:
            print('Invalid path or file type. Please provide a Python file or directory.')

    def process_file(self, file_path, config):
        """Processes a single Python file to generate and insert docstrings."""
        from DocStringGenerator.APICommunicator import APICommunicator
        from DocStringGenerator.DocstringProcessor import DocstringProcessor
        file_name = os.path.basename(file_path)
        processed = self.is_file_processed(file_name)
        if processed:
            if config["verbose"]:
                print(f'File {str(file_path)} already processed. Skipping.')
            return True

        if config["verbose"]:
            print(f'Processing file: {file_path.name}')
        with open(str(file_path.absolute()), 'r') as file:
            source_code = file.read()

        file_path_str = str(file_path)
        task = ResultThread(target=APICommunicator(config).ask_for_docstrings, args=(source_code, config))
        task.start()
        if not config["verbose"]:
            spinner = Spinner()
            spinner.wait_for(task)
            spinner.stop()
        task.join()

        if task.result:
            responses = task.result
            docstrings_tuple = DocstringProcessor(config).extract_docstrings(responses, config)
            docstrings, success = docstrings_tuple
            if success:
                if config["keep_responses"]:
                    print(f'Extracted docstrings: {docstrings}')
                    self.save_response(file_path, docstrings)

                DocstringProcessor(config).insert_docstrings(file_path, docstrings)
                if config["verbose"]:
                    print(f'Inserted docstrings in {file_path_str}')

                parsed_examples = self.parse_examples_from_response(docstrings)
                success, failed_function_names = self.add_example_functions_to_classes(file_path, parsed_examples, config)
                if not success and config["verbose"]:
                    print(f'Failed to add example functions to classes: {failed_function_names}')
            else:
                if config["verbose"]:
                    print(f'Failed to generate docstrings for {file_path_str}')
                return False
        else:
            if config["verbose"]:
                print(f'No response received for file: {file_path_str}')
            return False
        
        self.log_processed_file(file_path)
        return True


    def wipe_docstrings(self, file_path: Path):
        """Removes all docstrings from a Python source file."""
        source = file_path.read_text()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            print(f"Failed parsing {file_path}")
            return

        tree = DocstringRemover().visit(tree)
        new_source = ast.unparse(tree)

        file_path.write_text(new_source)

    def save_response(self, file_path: Path,  docstrings):
        """
        Saves the response for a processed file in a separate JSON file.
        """
        response_file_path = file_path.with_suffix('.response.json')
        with open(response_file_path, 'w') as f:
            json.dump(docstrings, f, indent=4)

    def list_files(self, directory: Path, extension: str) -> List[Path]:
        """Lists all files in a directory with a given file extension."""
        return [f for f in directory.iterdir() if f.suffix == extension]  
    
    def parse_examples_from_response(self, docstrings: dict):
        parsed_examples = {}
        
        for class_or_func_name, content in docstrings.items():
            # Extract the example for the class or function
            class_example = content.get("example")
            if class_example:
                if class_or_func_name not in parsed_examples:
                    parsed_examples[class_or_func_name] = []
                parsed_examples[class_or_func_name] = class_example

        return parsed_examples

    


    def add_example_functions_to_classes(self, file_path, examples, config):
        success = True
        failed_class_names = []

        with open(file_path, 'r') as file:
            content = file.read()

        for class_name, example_code in examples.items():
            try:
                tree = ast.parse(content)  # Re-parse the content each time
                end_line_number = None
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        end_line_number = node.end_lineno if hasattr(node, 'end_lineno') else node.body[-1].lineno
                        break

                if end_line_number is not None:
                    content_lines = content.splitlines()
                    # Prepare the function definition for validation
                    validation_code = f"def example_function_{class_name}(self):\n{self.add_indentation(example_code, 1)}"
                    if not Utility.is_valid_python(validation_code):
                        if config["verbose"]:
                            print(f"Invalid example code for class {class_name}.")
                        success = False
                        failed_class_names.append(class_name)
                        continue

                    # Proper indentation for insertion
                    function_def_str = f"\n    def example_function_{class_name}(self):\n{self.add_indentation(example_code, 2)}"
                    content_lines.insert(end_line_number, function_def_str)
                    content = "\n".join(content_lines)
                else:
                    if config["verbose"]:
                        print(f"Class {class_name} not found.")
                    success = False
                    failed_class_names.append(class_name)
            except Exception as e:
                if config["verbose"]:
                    print(f"Failed to append example to class {class_name}: {e}")
                success = False
                failed_class_names.append(class_name)

        with open(file_path, 'w') as file:
            file.write(content)

        return success, failed_class_names


    def add_indentation(self, source_code: str, indent: int) -> str:
        """Adds indentation to a source code string."""
        indentation = "    " * indent
        return "\n".join([indentation + line for line in source_code.splitlines()])

class DocstringRemover(ast.NodeTransformer):
    """An AST node transformer that removes docstrings from function and class definitions."""
    def visit_FunctionDef(self, node):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, (ast.Str, ast.Constant)):
            node.body.pop(0)
        self.generic_visit(node)  # Visit children nodes
        return node

    def visit_ClassDef(self, node):
        if node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, (ast.Str, ast.Constant)):
            node.body.pop(0)
        self.generic_visit(node)  # Visit children nodes
        return node