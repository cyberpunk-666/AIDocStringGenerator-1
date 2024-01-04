
import os
import io
import sys
from pathlib import Path
from typing import List
import ast
import json
from DocStringGenerator.DependencyContainer import DependencyContainer, Scope
dependencies = DependencyContainer()
from DocStringGenerator.GlobalConfig import GlobalConfig
global_config = dependencies.resolve(GlobalConfig)

from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.ConfigManager import ConfigManager

FILES_PROCESSED_LOG = "files_processed.log"
MAX_RETRY_LIMIT = 3

class ChunkData:
    def __init__(self, bot_name: str, chunk: str):
        self.bot_name = bot_name
        self.chunk = chunk

class DocstringChecker(ast.NodeVisitor):
    """AST visitor that checks for the presence of docstrings in functions."""

    def __init__(self):
        self.missing_docstrings: list[str] = []

    def visit_FunctionDef(self, node:ast.AST):
        """Visit a function definition and check if it has a docstring."""
        if isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef, ast.ClassDef)):
            # These node types have a 'name' attribute
            if not ast.get_docstring(node) and not "example_" in node.name:
                self.missing_docstrings.append(node.name)
            self.generic_visit(node)  # Continue traversing child nodes

class CodeProcessor:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CodeProcessor, cls).__new__(cls)
        return cls._instance
        
    def __init__(self):
        if not hasattr(self, '_initialized'):  # Prevent reinitialization
            self.communicator_manager: CommunicatorManager = dependencies.resolve(CommunicatorManager)
            self.docstring_processor: DocstringProcessor = dependencies.resolve(DocstringProcessor)
            self.config: dict[str, Any]  = ConfigManager().config
            self._initialized = True


    def find_split_point(self, source_code: str, max_lines: int=sys.maxsize , start_node: ast.AST | None = None) -> int:
        """Finds a suitable point to split the source code into smaller parts."""
        try:
            if not start_node:        
                start_node = ast.parse(source_code)
            split_point = self.find_split_point_in_children(start_node, max_lines)
        except SyntaxError:
            # If invalid code, find split point in plain text
            split_point = min(max_lines, source_code.count("\n"))
        return split_point

    def find_end_line(self, node: ast.AST, max_lines: int) -> int:
        """Determines the end line number for a given AST node."""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.end_lineno and max_lines >= node.end_lineno:
                return node.end_lineno
            else:
                return node.lineno - 1
        elif isinstance(node, ast.ClassDef):
            return node.lineno
        else:
            return -1


    def find_split_point_in_children(self, node: ast.AST, max_lines: int, recursive: bool=True) -> int:
        """Recursively finds a split point within the children of an AST node."""

        def safe_end_line(node: ast.AST, max_lines: int) -> int:
            """ Safely get the end line or return 0 if None. """
            end_line = self.find_end_line(node, max_lines)
            return max(end_line, 0) if end_line >= 0 else 0

        child_split_point = safe_end_line(node, max_lines)
        if max_lines < child_split_point:
            child_split_point = 0

        def process_node(child_node: ast.AST):
            nonlocal child_split_point
            if child_node:
                if recursive and (hasattr(child_node, "body") or hasattr(child_node, "orelse")):
                    child_split_point = max(child_split_point,
                                            self.find_split_point_in_children(child_node, max_lines, recursive))
                
                end_line = safe_end_line(child_node, max_lines)
                if max_lines >= end_line and end_line > child_split_point:
                    child_split_point = end_line

        if hasattr(node, "body"):
            for child_node in getattr(node, "body", []):
                process_node(child_node)

        if hasattr(node, "orelse"):
            for child_node in getattr(node, "orelse", []):
                process_node(child_node)

        return child_split_point


    def split_source_code(self, source_code: str, num_parts: int) -> list[str]:
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
        output_parts: list[str] = []

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

    def log_processed_file(self, file_path: Path):
        filename = file_path.name
        with open(FILES_PROCESSED_LOG, 'a') as log_file:
            log_file.write(filename + '\n')

    def remove_from_processed_log(self, file_path: Path):
        filename = file_path.name
        with open(FILES_PROCESSED_LOG, 'r') as log_file:
            processed_files = log_file.read().splitlines()
        if filename in processed_files:
            processed_files.remove(filename)
        with open(FILES_PROCESSED_LOG, 'w') as log_file:
            log_file.write('\n'.join(processed_files))


    def is_file_processed(self, file_name: str, log_file_path: str=''):
        """Checks if a file has already been processed by looking at a log file."""
        try:
            with open(log_file_path or FILES_PROCESSED_LOG, 'r') as log_file:
                processed_files = log_file.read().splitlines()
            return file_name in processed_files
        except FileNotFoundError:
            return False

    def process_folder_or_file(self) -> APIResponse:
        path = Path(self.config.get('path', ""))
        include_subfolders = self.config.get('include_subfolders', False)
        ignore_list: list[str] = self.config.get('ignore', [])

        failed_files: list[Any] = []
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                if not include_subfolders and root != str(path):
                    continue

                # Filter out ignored directories
                dirs[:] = [d for d in dirs if d not in ignore_list]

                for file in files:
                    # Check if the file is in the ignore list
                    if file in ignore_list:
                        continue

                    full_file_path = Path(root, file)
                    if file.endswith('.py'):
                        response = self.process_file(full_file_path.absolute())
                        if not response.is_valid:
                            failed_files.append({"file_name":full_file_path.name, "response":response})

        elif os.path.isfile(path) and str(path).endswith('.py'):
            if path.name not in ignore_list:
                success = self.process_file(path.absolute())
                if not success:
                    failed_files.append(str(path))
        else:
            return APIResponse([], False, 'Invalid path or file type. Please provide a Python file or directory.')

        return APIResponse(failed_files, not failed_files, "" if not failed_files else "Some files failed to process.")


    def process_file(self, file_path: Path) -> APIResponse:
        file_name = os.path.basename(file_path)
        processed = self.is_file_processed(file_name)
        if processed:
            message = f'File {file_name} already processed. Skipping.'
            return APIResponse("", False, message)
                # Read the source code from the file
        with open(file_path, 'r') as file:
            source_code = file.read() 
            
        process_code_response = self.process_code(source_code)
        if process_code_response.is_valid:
            if not ConfigManager().config.get('dry_run', False):
                self.write_new_code(file_path, process_code_response)

        return process_code_response

        
    def process_code(self, source_code: str) -> APIResponse:
        ask_count = 0
        if self.config.get('wipe_docstrings', False):
            wipe_docstrings_response = self.wipe_docstrings(source_code)
            if wipe_docstrings_response.is_valid:
                source_code = wipe_docstrings_response.content
            else:
                return wipe_docstrings_response



        last_error_message = ""
        while True:
            ask_count += 1
            response_docstrings: APIResponse = self.try_generate_docstrings(source_code, ask_count, last_error_message)
            if response_docstrings.is_valid:
                source_code = self.docstring_processor.insert_docstrings(source_code, response_docstrings.content)
                break
            else:
                last_error_message = response_docstrings.error_message
                if ask_count == MAX_RETRY_LIMIT:
                    break
            

        if response_docstrings.is_valid:
            final_code_response = self.process_examples(source_code, response_docstrings)
        else:
            return response_docstrings
        
        if final_code_response.is_valid:
            source_code = final_code_response.content
            verify_response = self.verify_code_docstrings(source_code)
            if verify_response.is_valid:
                return final_code_response
            else:
                missing_docstrings_response: APIResponse = self.communicator_manager.bot_communicator.ask_missing_docstrings(verify_response.content, 1)
                if missing_docstrings_response.is_valid:
                    extract_docstrings_response : APIResponse = self.docstring_processor.extract_docstrings(missing_docstrings_response.content, ask_missing=True)
                    if extract_docstrings_response.is_valid:
                        source_code = self.docstring_processor.insert_docstrings(source_code, extract_docstrings_response.content)
                    return APIResponse(source_code, True)

                else:
                    return final_code_response
        else:
            return final_code_response
        
    def write_new_code(self, file_path: Path, final_code_response: APIResponse):
        file_name = Path(file_path).name
        bot_path = Path(Path(file_path).parent, self.config.get("bot", ""))
        if not bot_path.exists():
            bot_path.mkdir(exist_ok=True)
        bot_path = Path(bot_path, file_name)
        if final_code_response.is_valid:
            with open(bot_path, 'w') as file:
                file.write(final_code_response.content)
            if not ConfigManager().config.get('disable_log_processed_file', False):                
                self.log_processed_file(bot_path)

    def process_examples(self, source_code: str, response_docstrings: APIResponse) -> APIResponse:
        if response_docstrings.is_valid:
            parsed_examples = self.parse_examples_from_docstrings(response_docstrings.content)
            if parsed_examples.is_valid:
                response = self.add_example_functions_to_classes(source_code, parsed_examples.content)

                if response.is_valid:
                    return APIResponse(response.content, True)
                else:
                    ask_count = 0
                    bot_communicator = self.communicator_manager.bot_communicator 
                    while True:
                        if bot_communicator:
                            response = bot_communicator.ask_retry_examples(response.content)
                            if response.is_valid:
                                response: APIResponse = self.docstring_processor.extract_docstrings(response.content, True)
                                if response.is_valid:
                                    response = self.parse_examples_from_docstrings(response.content)
                                    if response.is_valid:
                                        response = self.add_example_functions_to_classes(source_code, response.content)
                                        if response.is_valid:
                                            return APIResponse(response.content, True)
                                        else:
                                            ask_count += 1
                                    else:
                                        ask_count += 1
                                else:
                                    ask_count += 1
                            else:
                                ask_count += 1

                            if ask_count == MAX_RETRY_LIMIT:
                                break

                    return response                      
            else:
                return parsed_examples                    
        else:
            return response_docstrings


    def try_generate_docstrings(self, source_code: str, retry_count: int=1, last_error_message:str="") -> APIResponse:
        """Attempts to generate docstrings, retrying if necessary."""
        bot_communicator: BaseBotCommunicator | None = self.communicator_manager.bot_communicator        
        if not bot_communicator:
            return APIResponse("", False, "Bot communicator not initialized.")

        if retry_count == 1:
            result = self.communicator_manager.send_code_in_parts(source_code, retry_count)
        else:
            if self.communicator_manager.bot_communicator:
                result = self.communicator_manager.bot_communicator.ask_retry(last_error_message, retry_count)                
            else:
                return APIResponse("", False)

        if result.is_valid:
            docstring_response: APIResponse = self.docstring_processor.extract_docstrings(result.content)
            return docstring_response
        else:
            return result


    def save_response(self, file_path: Path,  docstrings: dict[str, Any]):
        """
        Saves the response for a processed file in a separate JSON file.
        """
        response_file_path = file_path.with_suffix('.response.json')
        folder_path = Path("./responses")
        folder_path.mkdir(parents=True, exist_ok=True)
        stem = Path(file_path).stem
        response_file_path = Path(folder_path, stem + '.response.json')
        with open(response_file_path, 'w') as f:
            json.dump(docstrings, f, indent=4)


    def verify_code_docstrings(self, source: str) -> APIResponse:
        """Checks all functions in a Python source file for docstrings."""

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return APIResponse("", False, f"Invalid Python code: {e}")

        checker = DocstringChecker()
        checker.visit(tree)

        if checker.missing_docstrings:
            message = f"Functions without docstrings: {', '.join(checker.missing_docstrings)}"
            return APIResponse(checker.missing_docstrings, False, message)
        else:
            return APIResponse([], True, "All functions have docstrings.")


    def wipe_docstrings(self, source: str) -> APIResponse:
        """Removes all docstrings from a Python source file."""

        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return APIResponse("", False, f"Invalid Python code: {e}")
            

        tree = DocstringRemover().visit(tree)
        new_source = ast.unparse(tree)

        return APIResponse(new_source, True)

    def list_files(self, directory: Path, extension: str) -> List[Path]:
        """Lists all files in a directory with a given file extension."""
        return [f for f in directory.iterdir() if f.suffix == extension]  
    
    def parse_examples_from_docstrings(self, docstrings: dict[str, Any]) -> APIResponse:
        parsed_examples = {}
        try:
            for class_or_func_name, content in docstrings.items():
                if class_or_func_name == "global_functions":
                    continue
                # Extract the example for the class or function
                class_example = content.get("example")
                if class_example:
                    if class_or_func_name not in parsed_examples:
                        parsed_examples[class_or_func_name] = []
                    parsed_examples[class_or_func_name] = class_example
            return APIResponse(parsed_examples, True)
        except Exception as e:
            return APIResponse("", False, f"Failed to parse examples from response: {e}")


    def add_example_functions_to_classes(self, code_source: str, examples:dict[str, str]) -> APIResponse:
        success = True
        failed_class_names: list[Any] = []

        for class_name, example_code in examples.items():
            try:
                tree = ast.parse(code_source)
                end_line_number = None
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef) and node.name == class_name:
                        end_line_number = node.end_lineno if hasattr(node, 'end_lineno') else node.body[-1].lineno
                        break

                if end_line_number is not None:
                    content_lines = code_source.splitlines()
                    example_code = example_code.replace("\\n", "\n")
                    validation_code = f"def example_function_{class_name}(self):\n{self.add_indentation(example_code, 1)}"
                    is_valid_response = Utility.is_valid_python(validation_code)
                    if not is_valid_response.is_valid:
                        success = False
                        failed_class_names.append({"class": class_name, "error": is_valid_response.error_message})
                        continue  # Keep processing other classes

                    function_def_str = f"\n    def example_function_{class_name}(self):\n{self.add_indentation(example_code, 2)}"
                    content_lines.insert(end_line_number, function_def_str)
                    code_source = "\n".join(content_lines)
                else:
                    error_message = f"Class {class_name} not found."
                    success = False
                    failed_class_names.append({"class": class_name, "error": error_message})

            except Exception as e:
                error_message = f"Failed to append example to class {class_name}: {e}"
                success = False
                failed_class_names.append({"class": class_name, "error": error_message})  
                      
        if not success:
            return APIResponse(failed_class_names, False, "Failed to add example functions to some classes.")
        return APIResponse(code_source, True)



    def add_indentation(self, source_code: str, indent: int) -> str:
        """Adds indentation to a source code string."""
        indentation = "    " * indent
        return "\n".join([indentation + line for line in source_code.splitlines()])

class DocstringRemover(ast.NodeTransformer):
    """An AST node transformer that removes docstrings from function and class definitions."""
    def visit_FunctionDef(self, node: ast.AST):
        if hasattr(node, "body"):
            body: list[ast.stmt] = getattr(node, "body", [])            
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                body.pop(0)
            self.generic_visit(node)  # Visit children nodes
            return node

    def visit_ClassDef(self, node: ast.AST):
        if hasattr(node, "body"):
            body: list[ast.stmt] = getattr(node, "body", [])         
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, (ast.Constant)):
                body.pop(0)
            self.generic_visit(node)  # Visit children nodes
            return node
    
if global_config.mode == "web":
    dependencies.register(DocstringRemover, DocstringRemover, Scope.SCOPED)
    dependencies.register(CodeProcessor, CodeProcessor,Scope.SCOPED)
else:
    dependencies.register(DocstringRemover, DocstringRemover, Scope.SINGLETON)
    dependencies.register(CodeProcessor, CodeProcessor, Scope.SINGLETON)
