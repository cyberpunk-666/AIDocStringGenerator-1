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

    
class FileProcessor:
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
        if not start_node:        
            start_node = ast.parse(source_code)

        split_point = self.find_split_point_in_children(start_node, max_lines)
        return split_point

    def find_end_line(self, node, max_lines):
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




    def is_file_processed(self, file_path, log_file_path):
        try:
            with open(log_file_path, 'r') as log_file:
                processed_files = log_file.read().splitlines()
            return file_path in processed_files
        except FileNotFoundError:
            return False

    def process_folder_or_file(self, path: Path, config):
        if path.is_dir():
            self._process_dir(path, config)
        elif path.is_file():
            self.process_file(path, config)
        else:
            print("Invalid path")

    def _process_dir(self, dir_path: Path, config):
        for filepath in dir_path.glob("**/*.py"):
            self.process_file(filepath, config)

    def process_file(self,file_path, config):
        from DocStringGenerator.APICommunicator import APICommunicator
        from DocStringGenerator.DocstringProcessor import DocstringProcessor
        
        if config["verbose"]:
            print(f'Processing file: {str(file_path)}')
        with open(str(file_path.absolute()), 'r') as file:
            source_code = file.read()
        file_path_str = str(file_path)
        task = ResultThread(target=APICommunicator(config).ask_for_docstrings, args=(source_code,config))
        task.start()
        if not config["verbose"]:
            spinner = Spinner()
            spinner.wait_for(task)
            spinner.stop()
        task.join()
        if task.result:
            response, is_valid = task.result
            if is_valid:
                docstrings_tuple = DocstringProcessor(config).extract_docstrings(response, config)
                docstrings, example, success = docstrings_tuple
                if not success:                
                    if config["verbose"]:
                        print(f'Failed to generate docstrings for {file_path_str}')
                    return False
                DocstringProcessor(config).insert_docstrings(file_path,docstrings)
                if config["verbose"]:
                    print(f'Inserted docstrings in {file_path_str}')
            else:
                if config["verbose"]:
                    print(f'Failed to generate docstrings for {file_path_str}')
                return False
        else:
            if config["verbose"]:
                print(f'No response received for file: {file_path_str}')
            return False
        return True   

    def _insert_docstrings(self, filepath: Path):
        try:
            source_code = filepath.read_text()
            docstrings = self._get_docstrings(source_code)
            self._docstring_inserter.insert(filepath, docstrings)
        except Exception as e:
            print(f"Failed to process {filepath}: {e}")

    def _get_docstrings(self, source_code: str) -> Dict[str, str]:
        response = self._api_communicator.ask_for_docstrings(source_code, self.config)
        return DocstringProcessor(self.config).extract_docstrings(response)

    def wipe_docstrings(self, file_path: Path):
        source = file_path.read_text()

        try:
            tree = ast.parse(source)
        except SyntaxError:
            print(f"Failed parsing {file_path}")
            return

        class DocstringRemover(ast.NodeTransformer):
            def visit_FunctionDef(self, node):
                node.body = [n for n in node.body if not isinstance(n, ast.Expr)] 
                return node

            def visit_ClassDef(self, node):
                node.body = [n for n in node.body if not isinstance(n, ast.Expr)]
                return node

        tree = DocstringRemover().visit(tree)
        new_source = ast.unparse(tree)

        file_path.write_text(new_source)

    def list_files(self, directory: Path, extension: str) -> List[Path]:
        return [f for f in directory.iterdir() if f.suffix == extension]  