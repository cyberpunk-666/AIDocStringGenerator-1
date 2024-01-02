
from typing import Optional
import google.generativeai as genai
import json
import os
import time
import requests
from bots import *
from dotenv import load_dotenv
from openai import OpenAI
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator

class AnthropicCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        self.anthropic_url = 'https://api.anthropic.com/v1/complete'
        self.prompt = ''

    def ask(self, prompt, replacements) -> APIResponse:

        prompt_response = self.format_prompt(prompt, replacements)
        if not prompt_response.is_valid:
            return prompt_response
        
        try:            
            new_prompt = '\n\nHuman: ' + prompt_response.content + '\n\nAssistant:'
            if self.config.get('verbose', False):
                print("sending prompt: " + new_prompt)
            
            self.prompt += new_prompt
            headers = {'anthropic-version': '2023-06-01', 'content-type': 'application/json', 'x-api-key': self.config.get('ANTHROPIC_API_KEY')}
            model = self.config.get('model', '')
            models = BOTS[self.config.get('bot', '')]
            if model not in models:
                print(f'Invalid bot: {model}')
                return APIResponse('', False, 'Invalid bot')
            data = {'model': model, 'prompt': self.prompt, 'max_tokens_to_sample': 4000, 'stream': True}
            response = requests.post(self.anthropic_url, headers=headers, data=json.dumps(data), stream=True)
            response_handled = self.handle_response(response)
            return response_handled
        except Exception as e:
            return APIResponse(None, is_valid=False, error_message=str(e))

    def handle_response(self, response) -> APIResponse:
        first_block_received = False
        full_completion = ''
        error_message = ''
        try:
            if self.config.get('verbose', False):
                print("Receiving response from Anthropic API...")
            for line in response.iter_lines():
                if line:
                    current_time: float = time.time()
                    last_block_time = current_time
                    if not first_block_received:
                        first_block_received = True
                        last_block_time: float = current_time
                        continue
                    if current_time - last_block_time > 15:
                        raise TimeoutError('Connection timed out after receiving initial data block')
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data:'):
                        last_block_time = current_time
                        event_data = json.loads(decoded_line[6:])
                        completion = event_data.get('completion', '')
                        full_completion += completion
                        if self.config.get('verbose', False):
                            print(completion, end='')
                        if event_data.get('stop_reason') is not None:
                            if self.config.get('verbose', ''):
                                print('Received stop reason, breaking loop.')
                            break
        except Exception as e:
            full_completion = ''
            return APIResponse(None, is_valid=False, error_message=str(e))
        return APIResponse(content=full_completion, is_valid=True)

from typing import Optional
import google.generativeai as genai
import json
import os
import time
import requests
from bots import *
from dotenv import load_dotenv
from openai import OpenAI
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread

class BaseBotCommunicator:

    def __init__(self):
        configManager = ConfigManager()
        self.config = configManager.config
        load_dotenv()
        configManager.set_config('verbose', True)
        configManager.set_config('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY'))
        configManager.set_config('ANTHROPIC_API_KEY', os.getenv('ANTHROPIC_API_KEY'))
        configManager.set_config('GOOGLE_API_KEY', os.getenv('GOOGLE_API_KEY'))

    def ask(self, prompt, replacements) -> APIResponse:
        """
        Sends a request to the respective bot API or file system. This method should be implemented by subclasses.
        """
        raise NotImplementedError('This method should be implemented by subclasses')

    def handle_response(self, response)->APIResponse:
        """
        Handles the response from the bot API or file system. This method can be overridden by subclasses for custom behavior.
        """
        return response

    def format_prompt(self, prompt_template, replacements) -> APIResponse:
        """
        Formats the prompt by replacing placeholders with actual values provided in 'replacements'.
        """
        try:
            for key, value in replacements.items():
                prompt_template = prompt_template.replace(f'{{{key}}}', value)
            return APIResponse(prompt_template, True)
        except Exception as e:
            return APIResponse('', False, str(e))

    def ask_retry(self, last_error_message, retry_count) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_retry')
        replacements: dict[str, str] = {
            'last_error_message': last_error_message,
            'retry_count': str(retry_count)
        }
        return self.ask(prompt_template, replacements)

    def _format_class_errors(self, class_errors) -> str:
        error_string = ''
        for class_error in class_errors:
            error_string += f'{class_error["class"]}: {class_error["error"]}\n'
        return error_string
    
    def ask_retry_examples(self, class_errors, last_error_message) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_retry_example')
        replacements = {
            'class_errors': self._format_class_errors(class_errors),
            'example_retry': 'True'
        }
        return self.ask(prompt_template, replacements)

    def ask_for_docstrings(self, source_code, retry_count=1) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_docStrings')
        replacements: dict[str, str] = {
            'source_code': source_code,
            'max_line_length': str(self.config.get('max_line_length', 79)),
            'class_docstrings_verbosity_level': str(self.config.get('class_docstrings_verbosity_level', 5)),
            'function_docstrings_verbosity_level': str(self.config.get('function_docstrings_verbosity_level', 2)),
            'example_verbosity_level': str(self.config.get('example_verbosity_level', 3)),
            'retry_count': str(retry_count)
        }

        return self.ask(prompt_template, replacements)

    def ask_missing_docstrings(self, class_names, retry_count=1) -> APIResponse:
        prompt_template = Utility.load_prompt('prompts/prompt_missingDocStrings')
        replacements: dict[str, str] = {
            'function_names': json.dumps(class_names),
            'retry_count': str(retry_count),
            'ask_missing': 'True'
        }
        if self.config.get('verbose', False):
            print("sending prompt: " + prompt_template)
        return self.ask(prompt_template, replacements)


from math import e
import os
import io
from pathlib import Path
from typing import List
from typing import cast, Any
import ast
import json
import logging

from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from typing import Dict
from DocStringGenerator.Spinner import Spinner
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager

FILES_PROCESSED_LOG = "files_processed.log"
MAX_RETRY_LIMIT = 3

class DocstringChecker(ast.NodeVisitor):
    """AST visitor that checks for the presence of docstrings in functions."""

    def __init__(self):
        self.missing_docstrings = []

    def visit_FunctionDef(self, node):
        """Visit a function definition and check if it has a docstring."""
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
            self.communicator_manager: CommunicatorManager = dependencies.resolve("CommunicatorManager")
            self.docstring_processor: DocstringProcessor = dependencies.resolve("DocstringProcessor")
            self.config: dict[str, str]  = ConfigManager().config
            self._initialized = True


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

    def find_end_line(self, node, max_lines) -> int:
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


    def find_split_point_in_children(self, node: ast.AST, max_lines: int, recursive=True):
        """Recursively finds a split point within the children of an AST node."""

        def safe_end_line(node: ast.AST, max_lines: int) -> int:
            """ Safely get the end line or return 0 if None. """
            end_line = self.find_end_line(node, max_lines)
            return max(end_line, 0) if end_line is not None else 0

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

    def remove_from_processed_log(self, file_path):
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

    def process_folder_or_file(self) -> APIResponse:
        path = Path(self.config.get('path', ""))
        include_subfolders = self.config.get('include_subfolders', False)
        ignore_list = set(self.config.get('ignore', []))  # Convert ignore list to a set for faster lookup

        failed_files = []
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
                            print(f'Failed to process {str(full_file_path)}')

        elif os.path.isfile(path) and str(path).endswith('.py'):
            if path.name not in ignore_list:
                success = self.process_file(path.absolute())
                if not success:
                    failed_files.append(str(path))
        else:
            return APIResponse([], False, 'Invalid path or file type. Please provide a Python file or directory.')

        return APIResponse(failed_files, not failed_files, "" if not failed_files else "Some files failed to process.")

    

    def process_file(self, file_path) -> APIResponse:
        file_name = os.path.basename(file_path)
        processed = self.is_file_processed(file_name)
        if processed:
            message = f'File {file_name} already processed. Skipping.'
            if self.config.get('verbose', ""):
                print(message)
            return APIResponse("", False, message)
                # Read the source code from the file
        with open(file_path, 'r') as file:
            source_code = file.read() 
            
        process_code_response = self.process_code(source_code)
        if process_code_response.is_valid:
            if not ConfigManager().config.get('dry_run', False):
                self.write_new_code(file_path, process_code_response)

        return process_code_response

        
    def process_code(self, source_code) -> APIResponse:
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
                missing_docstrings_response = self.communicator_manager.bot_communicator.ask_missing_docstrings(verify_response.content)
                if missing_docstrings_response.is_valid:
                    extract_docstrings_response : APIResponse = self.docstring_processor.extract_docstrings(missing_docstrings_response.content, ask_missing=True)
                    if extract_docstrings_response.is_valid:
                        source_code = self.docstring_processor.insert_docstrings(source_code, extract_docstrings_response.content)
                    return APIResponse(source_code, True)

                else:
                    return final_code_response
        else:
            return final_code_response
        
    def write_new_code(self, file_path, final_code_response):
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

    def process_examples(self, source_code, response_docstrings: APIResponse) -> APIResponse:
        if response_docstrings.is_valid:
            parsed_examples = self.parse_examples_from_docstrings(response_docstrings.content)
            if parsed_examples.is_valid:
                response = self.add_example_functions_to_classes(source_code, parsed_examples.content)

                if response.is_valid:
                    return APIResponse(response.content, True)
                else:
                    ask_count = 0
                    last_error_message = response.error_message
                    bot_communicator = self.communicator_manager.bot_communicator 
                    while True:
                        if bot_communicator:
                            response = bot_communicator.ask_retry_examples(response.content, last_error_message)
                            if response.is_valid:
                                response: APIResponse = self.docstring_processor.extract_docstrings(response.content, True)
                                if response.is_valid:
                                    response = self.parse_examples_from_docstrings(response.content)
                                    if response.is_valid:
                                        response = self.add_example_functions_to_classes(source_code, response.content)
                                        if response.is_valid:
                                            return APIResponse(response.content, True)
                                        else:
                                            last_error_message = response.error_message
                                            ask_count += 1
                                    else:
                                        last_error_message = response.error_message
                                        ask_count += 1
                                else:
                                    last_error_message = response.error_message
                                    ask_count += 1
                            else:
                                last_error_message = response.error_message
                                ask_count += 1

                            if ask_count == MAX_RETRY_LIMIT:
                                break

                    return response                      
            else:
                return parsed_examples                    
        else:
            return response_docstrings


    def try_generate_docstrings(self, source_code, retry_count=1, last_error_message="") -> APIResponse:
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


    def save_response(self, file_path: Path,  docstrings):
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


    def verify_code_docstrings(self, source) -> APIResponse:
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


    def wipe_docstrings(self, source) -> APIResponse:
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
    
    def parse_examples_from_docstrings(self, docstrings: dict) -> APIResponse:
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


    def add_example_functions_to_classes(self, code_source, examples) -> APIResponse:
        success = True
        failed_class_names = []

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
                    if not Utility.is_valid_python(validation_code):
                        error_message = f"Invalid example code for class {class_name}."
                        success = False
                        failed_class_names.append({"class": class_name, "error": error_message})
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
    
dependencies = DependencyContainer()
dependencies.register('DocstringRemover', DocstringRemover)
dependencies.register('CodeProcessor', CodeProcessor)

from typing import Optional
import google.generativeai as genai
import json
import os
import time
import requests
from bots import *
from dotenv import load_dotenv
from openai import OpenAI
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.EmptyCommunicator import EmptyCommunicator
from DocStringGenerator.AnthropicCommunicator import AnthropicCommunicator
from DocStringGenerator.GoogleCommunicator import GoogleCommunicator
from DocStringGenerator.OpenAICommunicator import OpenAICommunicator
from DocStringGenerator.FileCommunicator import FileCommunicator

class CommunicatorManager:

    def __init__(self):
        self.config = ConfigManager().config
        self.initialize_bot_communicator()
        self.bot_communicator = EmptyCommunicator()

    def initialize_bot_communicator(self):
        if not 'bot' in self.config:
            return
        bot = self.config.get('bot', '')
        if not bot in BOTS:
            raise ValueError(f"Unsupported bot type '{bot}' specified in the configuration")
        dependencies.register('anthropic_Communicator', AnthropicCommunicator)
        dependencies.register('openai_Communicator', OpenAICommunicator)
        dependencies.register('google_Communicator', GoogleCommunicator)
        dependencies.register('file_Communicator', FileCommunicator)
        self.bot_communicator = dependencies.resolve(f'{bot}_Communicator')
        if not self.bot_communicator:
            raise ValueError(f"Error initializing bot communicator for '{bot}'")

    def send_code_in_parts(self, source_code, retry_count=1) -> APIResponse:
        from DocStringGenerator.CodeProcessor import CodeProcessor

        def attempt_send(code, iteration=0) -> APIResponse:
            print(f'Sending code in {2 ** iteration} parts.')
            num_parts = 2 ** iteration
            code_processor: CodeProcessor = dependencies.resolve('CodeProcessor')
            parts = code_processor.split_source_code(code, num_parts)
            responses = []
            response = None
            for part in parts:
                print(f'Sending part {parts.index(part) + 1} of {len(parts)}')
                if self.bot_communicator is not None:
                    response = self.bot_communicator.ask_for_docstrings(part, retry_count)
                if response:
                    if response.is_valid:
                        content = response.content
                        if 'length' in content and 'exceed' in content:
                            if self.config.get('verbose', ''):
                                print('Context length exceeded. Trying again with more parts.')
                            return attempt_send(code, iteration + 1)
                        responses.append({'content': content, 'source_code': part})
                    else:
                        return response
            return APIResponse(responses, True)
        return attempt_send(source_code)
        
dependencies = DependencyContainer()
dependencies.register('CommunicatorManager', CommunicatorManager)        
from pathlib import Path
import logging
import json
import sys
from typing import Any

class ConfigManager:
    """The ConfigManager class is a singleton designed to manage configuration settings for an application. It ensures that only one instance of the ConfigManager can exist at any given time. The class provides methods to load or create a default configuration file and retrieve specific configurations, such as API keys and bot settings.\n\nAt verbosity level 5, the class docstring would include a comprehensive explanation of the class's purpose, its singleton nature, the structure of the default configuration, and the methods provided for interacting with the configuration file. It would also cover potential edge cases, such as what happens if the configuration file is missing or corrupted, and how the class handles different types of bots specified in the configuration."""
    _instance = None
    _is_initialized = False
    DEFAULT_CONFIG = {'verbose': True}

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance

    def update_config(self, new_config) -> None:
        """Update the configuration with values from the provided dictionary."""
        self.config.update(new_config)

    def set_config(self, key, value):
        """Set a configuration value."""
        self.config[key] = value

    def __init__(self, config_path: Path = Path('config.json'), initial_config: dict = DEFAULT_CONFIG):
        if not self._is_initialized:
            self.config_path = config_path
            self.config:dict[str, Any] = initial_config
            self._is_initialized = True

    def load_or_create_config(self) -> dict:
        """Load the configuration from a file or create a default configuration if the file does not exist."""
        if self.config_path.exists():
            return self.get_config() 
        else:
            self.config_path.write_text(json.dumps(self.config, indent=4))
            logging.info(f"Created default config at {self.config_path}")
            sys.exit(0)

    def get_config(self) -> dict:
        """Retrieve the configuration as a dictionary from the configuration file."""
        return json.loads(self.config_path.read_text())
    
import threading
from typing import Type, Any, Callable, Dict, Tuple

class DependencyNotRegisteredError(KeyError):
    """Exception raised when a dependency is not registered."""
    pass

class DependencyContainer:


    def register(self, interface: Type, implementation: Callable, singleton: bool = True) -> None:
        """Register a dependency.

        Args:
            interface (Type): The interface or key under which to register the implementation.
            implementation (Callable): The implementation to register.
            singleton (bool): Whether to treat the implementation as a singleton.
        """
        self.dependencies[interface] = (implementation, singleton)

    def resolve(self, interface: Type, *args: Any, **kwargs: Any) -> Any:
        """Resolve a dependency.

        Args:
            interface (Type): The interface or key to resolve.

        Returns:
            Any: The resolved implementation.

        Raises:
            DependencyNotRegisteredError: If no implementation is registered for the interface.
        """
        implementation_info = self.dependencies.get(interface)
        if implementation_info:
            implementation, singleton = implementation_info
            if singleton:
                if not hasattr(implementation, "_singleton_instance"):
                    implementation._singleton_instance = implementation(*args, **kwargs)
                return implementation._singleton_instance
            else:
                return implementation(*args, **kwargs)
        else:
            raise DependencyNotRegisteredError(f"No implementation registered for {interface}")


class DependencyContainer:
    """
    A thread-safe singleton class used for dependency injection.

    The DependencyContainer class provides a centralized registry for managing dependencies. 
    It ensures that only one instance of the container is created (singleton pattern), 
    even in a multi-threaded environment. The container allows for registering dependencies 
    under a specific interface and later resolving them. This aids in decoupling the creation 
    and usage of objects, facilitating better testability and adherence to SOLID principles.

    Attributes:
        _instance (DependencyContainer): A private class-level attribute that stores the 
                                        single instance of the class.
        _lock (threading.Lock): A private class-level lock used to synchronize the creation 
                                of the singleton instance across multiple threads.
        dependencies (Dict[Type, Tuple[Callable, bool]]): A dictionary holding the registered 
                                                          dependencies. Each key is an interface or type, 
                                                          and the value is a tuple containing the 
                                                          implementation (Callable) and a boolean 
                                                          indicating if it should be treated as a singleton.

    Methods:
        __new__(cls): Overrides the default object creation mechanism to implement the singleton pattern.
        __init__(): Initializes the instance; called only once during the first instantiation.
        register(interface, implementation, singleton=True): Registers a dependency with the container.
        resolve(interface, *args, **kwargs): Resolves and returns an instance of the registered dependency.

    Raises:
        DependencyNotRegisteredError: If an attempt is made to resolve a dependency that hasn't been registered.
    """
    _instance: 'DependencyContainer' = None
    _lock = threading.Lock()


    def __new__(cls):
        """ 
        Create a new instance of DependencyContainer (singleton).

        This method ensures that only one instance of the DependencyContainer is created. 
        If an instance already exists, it returns that existing instance. Otherwise, 
        it creates a new instance. This method is thread-safe.

        Returns:
            DependencyContainer: The singleton instance of the DependencyContainer.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DependencyContainer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize the DependencyContainer instance.

        This method initializes the dependencies dictionary for the container. It is 
        designed to run only once; subsequent calls after the first instantiation 
        do not reinitialize the container.

        Note: 
            The __init__ method is not the typical constructor as it is only executed 
            once due to the singleton nature of the DependencyContainer.
        """
        if not hasattr(self, '_is_initialized') or not self._is_initialized:
            self.dependencies: Dict[Type, Tuple[Callable, bool]] = {}
            self._is_initialized = True

    def register(self, interface, implementation, singleton=True):
        """
        Register a dependency in the container.

        This method allows registering an implementation under a specific interface. 
        The implementation can be registered as a singleton or as a non-singleton (new 
        instance on each resolution).

        Args:
            interface (Type): The interface or type under which the implementation is to be registered.
            implementation (Callable): The concrete implementation of the interface.
            singleton (bool, optional): Whether the implementation should be treated as a singleton. 
                                        Defaults to True.

        Example:
            container.register(SomeInterface, SomeImplementation)
        """
        self.dependencies[interface] = (implementation, singleton)

    def resolve(self, interface, *args, **kwargs):
        """
        Resolve and return an instance of the registered dependency.

        This method returns an instance of the implementation registered under the provided interface. 
        If the implementation is registered as a singleton, it returns the same instance on each call. 
        If not, a new instance is created for each call. Additional arguments and keyword arguments 
        are passed to the constructor of the implementation.

        Args:
            interface (Type): The interface or type to resolve.
            *args: Variable length argument list passed to the implementation's constructor.
            **kwargs: Arbitrary keyword arguments passed to the implementation's constructor.

        Returns:
            Any: An instance of the registered implementation.

        Raises:
            DependencyNotRegisteredError: If no implementation is registered for the given interface.

        Example:
            instance = container.resolve(SomeInterface)
        """
        # Method implementation ...



    def example_1():
        # Import necessary classes and modules
        # from dependency_container import DependencyContainer, DependencyNotRegisteredError

        # Step 1: Define an Interface and its Implementation
        # ---------------------------------------------------

        # Define a simple interface (or abstract class) for demonstration
        class Communicator:
            def send_message(self, message):
                raise NotImplementedError

        # Define an implementation of the Communicator interface
        class EmailCommunicator(Communicator):
            def send_message(self, message):
                print(f"Sending email: {message}")

        # Step 2: Register the Implementation with DependencyContainer
        # ------------------------------------------------------------

        # Create an instance of the DependencyContainer
        container = DependencyContainer()

        # Register the EmailCommunicator as the implementation for the Communicator interface
        # Here, we specify that EmailCommunicator should be treated as a singleton
        container.register(Communicator, EmailCommunicator)

        # Step 3: Resolve the Dependency and Use It
        # ------------------------------------------

        # Resolve the dependency from the container
        # This will return an instance of EmailCommunicator
        email_communicator = container.resolve(Communicator)

        # Use the resolved communicator instance to send a message
        email_communicator.send_message("Hello World!")

        # Note: The following line will raise an exception if uncommented, 
        # as no implementation is registered for the 'str' type.
        # container.resolve(str)

        # Additional Usage: Registering Non-Singleton Implementations
        # -----------------------------------------------------------

        # Define another implementation of the Communicator interface
        class SMSCommunicator(Communicator):
            def send_message(self, message):
                print(f"Sending SMS: {message}")

        # Register SMSCommunicator as a non-singleton implementation
        container.register(Communicator, SMSCommunicator, singleton=False)

        # Resolving this will give a new instance each time
        sms_communicator = container.resolve(Communicator)
        sms_communicator.send_message("Text Message")


# Example usage:
# container = DependencyContainer()
# container.register(SomeInterface, SomeImplementation)
# instance = container.resolve(SomeInterface)

from typing import Optional
import threading
from typing import Type, Callable, Dict, Tuple

class DependencyNotRegisteredError(KeyError):
    """Exception raised when a dependency is not registered."""
    pass

class DependencyContainer:
    _instance: Optional['DependencyContainer'] = None
    _lock = threading.Lock()


    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DependencyContainer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, '_is_initialized') or not self._is_initialized:
            self.dependencies: Dict[Type, Tuple[Callable, bool]] = {}
            self._is_initialized = True

    def register(self, interface, implementation, singleton=True):
        self.dependencies[interface] = (implementation, singleton)

    def resolve(self, interface, *args, **kwargs):      
        implementation_info = self.dependencies.get(interface)
        if implementation_info:
            implementation, singleton = implementation_info
            if singleton:
                if not hasattr(implementation, "_singleton_instance"):
                    implementation._singleton_instance = implementation(*args, **kwargs)
                return implementation._singleton_instance
            else:
                return implementation(*args, **kwargs)
        else:
            raise DependencyNotRegisteredError(f"No implementation registered for {interface}")




    def example_1(self):
        # Import necessary classes and modules
        # from dependency_container import DependencyContainer, DependencyNotRegisteredError

        # Step 1: Define an Interface and its Implementation
        # ---------------------------------------------------

        # Define a simple interface (or abstract class) for demonstration
        class Communicator:
            def send_message(self, message):
                raise NotImplementedError

        # Define an implementation of the Communicator interface
        class EmailCommunicator(Communicator):
            def send_message(self, message):
                print(f"Sending email: {message}")

        # Step 2: Register the Implementation with DependencyContainer
        # ------------------------------------------------------------

        # Create an instance of the DependencyContainer
        container = DependencyContainer()

        # Register the EmailCommunicator as the implementation for the Communicator interface
        # Here, we specify that EmailCommunicator should be treated as a singleton
        container.register(Communicator, EmailCommunicator)

        # Step 3: Resolve the Dependency and Use It
        # ------------------------------------------

        # Resolve the dependency from the container
        # This will return an instance of EmailCommunicator
        email_communicator = container.resolve(Communicator)

        # Use the resolved communicator instance to send a message
        email_communicator.send_message("Hello World!")

        # Note: The following line will raise an exception if uncommented, 
        # as no implementation is registered for the 'str' type.
        # container.resolve(str)

        # Additional Usage: Registering Non-Singleton Implementations
        # -----------------------------------------------------------

        # Define another implementation of the Communicator interface
        class SMSCommunicator(Communicator):
            def send_message(self, message):
                print(f"Sending SMS: {message}")

        # Register SMSCommunicator as a non-singleton implementation
        container.register(Communicator, SMSCommunicator, singleton=False)

        # Resolving this will give a new instance each time
        sms_communicator = container.resolve(Communicator)
        sms_communicator.send_message("Text Message")


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

    def _validate_function_docstring(self, methods, max_length=999) -> APIResponse:
        for method_name, method_doc in methods.items():
            if not isinstance(method_doc, str):
                return APIResponse(None, False, f"Invalid format: Method '{method_name}' docstring should be a string.")
            for line in method_doc.splitlines():
                if len(line) > max_length:
                    return APIResponse(None, False, f"Docstring line in '{method_name}' exceeds maximum length of {max_length} characters.")

        return APIResponse(None, True)
        

    def validate_response(self, json_object, example_only=False, ask_missing=False, max_length=999) -> APIResponse:
        try:
            if self.config.get('verbose', ""):
                print("Validating docstrings...")
            
            docstrings = {}
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
                        if "methods" in value and not isinstance(value["methods"], dict):
                            return APIResponse(json_object, False, f"Invalid format: Methods under class '{key}' should be a dictionary.")
                        response = self._validate_function_docstring(value.get("methods", {}))
                        if not response.is_valid:
                            return response
                    # Check docstring length
                    docstring = value.get('docstring', "")
                    for line in docstring.splitlines():
                        if len(line) > max_length:
                            return APIResponse(json_object, False, f"Docstring line in '{key}' exceeds maximum length of {max_length} characters.")

            if self.config.get('verbose', ""):
                print("Validating examples...")

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

    def extract_docstrings(self, responses, example_only = False, ask_missing=False) -> APIResponse:
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
        else:
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


dependencies = DependencyContainer()
dependencies.register('DocstringProcessor', DocstringProcessor)
from typing import Optional
import google.generativeai as genai
import json
import os
import time
import requests
from bots import *
from dotenv import load_dotenv
from openai import OpenAI
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator

class EmptyCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()

    def ask(self, prompt, replacements) -> APIResponse:
        return APIResponse('Ok', True)

from typing import Optional
import google.generativeai as genai
import json
import os
import time
import requests
from bots import *
from dotenv import load_dotenv
from openai import OpenAI
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator

class FileCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()

    def ask(self, prompt, replacements) -> APIResponse:
        prompt_response = self.format_prompt(prompt, replacements)
        if not prompt_response.is_valid:
            return prompt_response
        if self.config.get('verbose', False):
            print("sending prompt: " + prompt_response.content)

        try:
            working_directory = os.getcwd()
            response_index: str = replacements.get('retry_count', '')
            example_retry: str = replacements.get('example_retry', 'False')
            ask_missing = replacements.get('ask_missing', 'False')

            base_bot_file: str = self.config.get('model', '')
            if ask_missing == 'True':
                bot_file = f'{base_bot_file}.missing.json'
            elif example_retry == 'True':
                bot_file = f'{base_bot_file}.example.json'
            else:
                response_index_str = '' if response_index == '1' else response_index
                bot_file = f'{base_bot_file}.response{response_index_str}.json'
            if not os.path.isabs(base_bot_file):
                bot_file = os.path.join(working_directory, f'responses/{bot_file}')
            with open(bot_file, 'r') as f:
                response_text = f.read()

            if self.config.get('verbose', False):
                print("Receiving response from File...")                
            return APIResponse(response_text, True)
        except Exception as e:
            return APIResponse('', False, str(e))

from typing import Optional
import google.generativeai as genai
import json
import os
import time
import requests
from bots import *
from dotenv import load_dotenv
from openai import OpenAI
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator

class GoogleCommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        api_key = self.config.get('GOOGLE_API_KEY', '')
        genai.configure(api_key=api_key)
        self.google = genai.GenerativeModel('gemini-pro')

    def ask(self, prompt, replacements) -> APIResponse:
        formatted_prompt_response = self.format_prompt(prompt, replacements)
        if not formatted_prompt_response.is_valid:
            return formatted_prompt_response

        try:
            new_prompt= formatted_prompt_response.content
            if self.config.get('verbose', False):
                print("sending prompt: " + new_prompt)            
            chat = self.google.start_chat()
            response = chat.send_message(new_prompt, stream=True)
            response_handled = self.handle_response(response)
            return response_handled
        except Exception as e:
            return APIResponse(None, is_valid=False, error_message=str(e))

    def handle_response(self, stream)-> APIResponse:
        response = ''
        if self.config.get('verbose', False):
            print("Receiving response from Google API...")
        try:
            for response_chunk in stream:
                if self.config.get('verbose', False):
                    print(response_chunk.text, end='')
                response += response_chunk.text
            return APIResponse(content=response, is_valid=True)
        except Exception as e:
            return APIResponse("", is_valid=False, error_message=str(e))

from typing import Optional
import json
import os
import time
import requests
from bots import *
from dotenv import load_dotenv
from openai import OpenAI
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.Utility import *
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam

class OpenAICommunicator(BaseBotCommunicator):

    def __init__(self):
        self.config = ConfigManager().config
        super().__init__()
        api_key = self.config.get('OPENAI_API_KEY', '')
        self.client = OpenAI(api_key=api_key)
        self.messages = []
        self.messages.append(ChatCompletionSystemMessageParam({'role': 'system', 'content': 'You are a helpful assistant.'}))


    def ask(self, prompt, replacements) -> APIResponse:
        prompt_response = self.format_prompt(prompt, replacements)
        if not prompt_response.is_valid:
            return prompt_response
                
        try:
            new_prompt= prompt_response.content
            if self.config.get('verbose', False):
                print("sending prompt: " + new_prompt) 

            self.messages.append(ChatCompletionUserMessageParam(content=new_prompt,role='user'))
            model = self.config.get('model', '')
            models = BOTS[self.config.get('bot', '')]
            if model not in models:
                print(f'Invalid bot: {model}')
                return APIResponse('', False, 'Invalid bot')
            
            stream = self.client.chat.completions.create(model=model, messages=self.messages, temperature=0, stream=True)
            response = self.handle_response(stream)
            if response.is_valid:
                self.messages.append(ChatCompletionAssistantMessageParam(content=response.content,role='assistant'))
            return response
        except Exception as e:
            return APIResponse("", is_valid=False, error_message=str(e))

    def handle_response(self, stream) -> APIResponse:
        response = ''
        if self.config.get('verbose', False):
            print("Receiving response from OpenAI API...")
        try:
            for chunk in stream:
                content = chunk.choices[0].delta.content or ''
                if self.config.get('verbose', False):
                    print(content, end='')
                response += content
            return APIResponse(response, True)            
        except Exception as e:
            return APIResponse('', is_valid=False, error_message=str(e))

import threading

class ResultThread(threading.Thread):    
    def __init__(self, target=None, *args, **kwargs):
        super(ResultThread, self).__init__(*args, **kwargs)
        self.result = None
        self._custom_target = target
        self._custom_args = args
        self._custom_kwargs = kwargs

    def run(self):
        """Executes the thread's target function and stores the result."""
        if self._custom_target is not None:
            self.result = self._custom_target(*self._custom_args, **self._custom_kwargs)

import time
import sys
import itertools
from threading import Thread

class Spinner:
    """
    This class implements a text-based spinner for indicating progress in the console.
    It follows the singleton design pattern, ensuring that only one instance of the Spinner class exists throughout the runtime of the program.
      
    At verbosity level 5, the class is described in great detail.
    The Spinner class is initialized with a line length to keep track of the output's length and an iterator that cycles through a set of spinner characters ('-', '/', '|', '\\').
    The iterator is created using itertools.cycle, which allows the spinner to loop indefinitely through the spinner characters.
    
    The class provides methods to start the spinner, update the spinner's appearance with the next character, stop the spinner, and clear the current line in the console.
    Additionally, there is a method to keep the spinner spinning while a given thread is alive, which is useful for providing a visual indication that a background process is running.
    
    Usage of this class involves creating an instance (or getting the existing one), starting the spinner, and then periodically calling the spin method to update the spinner's appearance.
    When the operation is complete, the stop method should be called to clear the spinner and move the cursor to the next line.
    
    Edge cases, such as attempting to create multiple instances of the class,
    are handled by the __new__ method, which ensures that the _instance class variable holds only one instance of the Spinner class.
    If an attempt is made to create another instance, the existing one is returned instead.
    
    This class is particularly useful for command-line interfaces where long-running operations may lead to a perception of unresponsiveness.
    By providing a visual cue that work is being done, the spinner can improve the user experience by indicating that the program is actively processing.
    """
    _instance = None
    
    def __new__(cls):
        """Ensures that only one instance of Spinner is created (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(Spinner, cls).__new__(cls)  
        return cls._instance
    
    def __init__(self):
        """Initializes the spinner with a line length and an iterator for spinner characters."""
        self._line_length = 0
        self.spinner_iterator = self._create_spinner_iterator()
        
    def _create_spinner_iterator(self):
        """Creates an iterator that cycles through spinner characters indefinitely."""
        spinners = ['-', '/', '|', '\\']
        for spinner in itertools.cycle(spinners):
            yield spinner

    def _clear_line(self):
        """Clears the current line in the console output."""
        sys.stdout.write('\x08' * self._line_length)

    def _write(self, text):
        """Writes text to the console and keeps track of the line length."""
        sys.stdout.write(text)
        sys.stdout.flush()
        self._line_length = len(text)

    def start(self, text=''):
        """Starts the spinner with an optional initial text."""
        self._write(text + next(self.spinner_iterator))

    def spin(self):
        """Updates the spinner with the next character to indicate progress."""
        self._clear_line()  
        spinner = next(self.spinner_iterator) 
        self._write(spinner)

    def stop(self):
        """Stops the spinner and moves the cursor to the next line."""
        self._clear_line()
        sys.stdout.write('\n')

    def wait_for(self, thread: Thread):
        """Keeps the spinner spinning while a given thread is alive."""
        while thread.is_alive():
            self.spin()  
            time.sleep(0.1)

    def example_function_Spinner(self):
        spinner = Spinner()
        spinner.start()
        for i in range(20):
            spinner.spin()
            time.sleep(0.1)
        spinner.stop()
import os
import ast
from pathlib import Path
from typing import Any, Dict 
from DocStringGenerator.Spinner import Spinner
import json
import re
from dataclasses import dataclass

@dataclass
class APIResponse:
    content: Any
    is_valid: bool
    error_message: str = ""

class Utility:
    """
    Utility class providing static methods for common helper tasks like
    reading configurations, loading prompts from files, parsing
    JSON strings, etc.
    """

    @staticmethod
    def extract_json(input_string) -> APIResponse:
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
        found_json_string = ""
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
        return APIResponse(found_json_string, is_valid, error_message)

    @staticmethod
    def parse_json(text) -> APIResponse:
        """
        Tries to parse a JSON string from given text input. Handles
        errors and returns tuple with parsed object or None, 
        validity boolean and error message if any.
        """
        json_object = None
        is_valid = True
        error_message = None
        json_string = ""
        try:
            
            response = Utility.extract_json(text)
            json_string = response.content
            if response.is_valid:
                json_object = json.loads(json_string)
                return APIResponse(json_object, True)
            else:
                return APIResponse(None, False, response.error_message)
        except json.JSONDecodeError as e:
            error_message = str(e)
            return APIResponse(None, False, error_message)
        

    @staticmethod
    def read_config(config_path: Path) -> dict:
        """
        Reads given config file path as JSON and returns
        parsed config dict.
        """
        return json.loads(config_path.read_text())

    @staticmethod
    def load_prompt(file, base_path='.') -> str:
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
    def is_valid_python(code, config=None) -> bool:
        """Checks if given Python code text is valid syntactically."""
        try:
            compile(code, '<string>', 'exec')
            return True
        except SyntaxError as e:
            if config and config.get('verbose', ""):
                print(f'Invalid Python code: {e}')
            return False

    def example_function_Utility(self):
        prompt = Utility.load_prompt('prompt_file')
        print(Utility.convert_newlines(prompt))

    def print_long_string(self, long_string):
        n = 1000  # number of characters to display at a time

        for i in range(0, len(long_string), n):
            print(long_string[i:i+n], "")         

