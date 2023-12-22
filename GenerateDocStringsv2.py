import argparse
import ast
import os
import sys
import requests
from anthropic import Anthropic
from openai import OpenAI
import openai
import threading
import itertools
import time
import threading
import itertools
import time
import json
import re
from json.decoder import JSONDecodeError
DEFAULT_CONFIG = {'path': 'path/to/directory/or/file', 'wipe_docstrings': True, 'verbose': True, 'bot': 'GPT3.5', 'openai_api_key': 'my_key', 'claude_api_key': 'my_key', 'include_subfolders': False}

CONFIG_FILE = 'config.json'
PROMPT_FILE = 'chatbot_prompt.txt'

def load_or_create_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    else:
        with open(CONFIG_FILE, 'w') as file:
            json.dump(DEFAULT_CONFIG, file, indent=4)
        print(f"Created config file '{CONFIG_FILE}'. Please fill in the required fields and run the script again.")
        sys.exit(0)

class ResultThread(threading.Thread):

    def __init__(self, *args, **kwargs):
        super(ResultThread, self).__init__(*args, **kwargs)
        self.result = None

    def run(self):
        if self._target is not None:
            self.result = self._target(*self._args, **self._kwargs)

def spinning_cursor():
    for cursor in itertools.cycle(['-', '/', '|', '\\']):
        yield cursor

def spinner(task):
    spin = spinning_cursor()
    while task.is_alive():
        sys.stdout.write(next(spin))
        sys.stdout.flush()
        time.sleep(0.1)
        sys.stdout.write('\x08')
import ast

def find_split_point(source_code, max_length=2048):
    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        return len(source_code) // 2
    split_point = 0
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            start_line = node.lineno - 1
            if start_line > max_length / 2:
                break
            split_point = start_line
    return split_point

def split_source_code(source_code, max_length=2048):
    split_point = find_split_point(source_code, max_length)
    return (source_code[:split_point], source_code[split_point:])

def insert_docstrings(file_path, docstrings_response, config):
    docstrings, success = docstrings_response
    if not success:
        if config["verbose"]:
            print(f'No valid docstrings to insert for {file_path}.')
        return
    if config["verbose"]:
        print(f'Inserting docstrings into {file_path}.')
    try:
        with open(file_path, 'r') as file:
            content = file.readlines()
        tree = ast.parse(''.join(content))
        lines_to_insert = {}
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                start_line = node.lineno
                indent_level = len(content[start_line - 1]) - len(content[start_line - 1].lstrip())
                docstring = docstrings.get(node.name)
                if docstring:
                    formatted_docstring = format_docstring(docstring, indent_level)
                    lines_to_insert[start_line] = formatted_docstring
        for line_num, docstring in sorted(lines_to_insert.items(), reverse=True):
            content.insert(line_num, docstring)
        with open(file_path, 'w') as file:
            file.writelines(content)
        if config["verbose"]:
            print(f'Successfully inserted docstrings into {file_path}.')
    except Exception as e:
        if config["verbose"]:
            print(f'Failed to insert docstrings into {file_path}: {e}')

def format_docstring(docstring, indent_level):
    indent = ' ' * indent_level + '    '
    formatted_docstring = indent + '"""\n' + indent + docstring.replace('\n', '\n' + indent) + '\n' + indent + '"""\n'
    return formatted_docstring

def list_files(directory, extension):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith(extension)]

def load_prompt(file):
    with open(f"{file}.txt", 'r') as file:
        return file.read()

def ask_claude(prompt_template, replacements, config):    
    prompt_template = prompt_template.replace("{verbosity_level}", str(config.get("verbosity_level", 2)))
    prompt = prompt_template
    for key, val in replacements.items():
        prompt = prompt.replace(f"{{{key}}}", val)
        
    claude_prompt = 'Human: ' + prompt + '\n\nAssistant:'
    
    url = 'https://api.anthropic.com/v1/complete'
    headers = {'anthropic-version': '2023-06-01', 
               'content-type': 'application/json',
               'x-api-key': config['claude_api_key']}
               
    data = {'model': config["model"], 
            'prompt': claude_prompt, 
            'max_tokens_to_sample': 4000,
            'stream': True}
            
    try:
        response = requests.post(url, 
                                headers=headers, 
                                data=json.dumps(data), 
                                stream=True,)
                                
        full_completion = ''
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data:'):
                    event_data = json.loads(decoded_line[6:])
                    completion = event_data.get('completion', '')
                    if config["verbose"]:
                        print(completion, end='')
                    full_completion += completion
                    if event_data.get('stop_reason') is not None:
                        break
                        
        return full_completion
    except Exception as e:
        return f'Error during Claude API call: {str(e)}'

def ask_claude_for_docstrings(source_code, config):
    prompt_template = load_prompt("prompts/prompt_docStrings")
    replacements = {
        "source_code": source_code
    }
    
    return ask_claude(prompt_template, replacements, config)


def ask_openai(prompt_template, replacements, config, system_prompt="You are a helpful assistant.", verbose=False):
    prompt_template = prompt_template.replace("{verbosity_level}", str(config.get("verbosity_level", 2)))    
    prompt = prompt_template
    for key, val in replacements.items():
        prompt = prompt.replace(f"{{{key}}}", val)
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    client = OpenAI(api_key=config['openai_api_key'])
    try:
        stream = client.chat.completions.create(
            model=config["model"], 
            messages=messages, 
            temperature=0,
            stream=True
        )
        
        response = ''
        for chunk in stream:
            if config["verbose"]:
                print(convert_newlines(chunk.choices[0].delta.content or ''), end='')
            response += chunk.choices[0].delta.content or ''
            
        return response
    
    except Exception as e:
        return f'Error during OpenAI API call: {e}'

def ask_openai_for_docstrings(source_code, config):
    prompt_template = load_prompt("prompts/prompt_docStrings")
    replacements = {
        "source_code": source_code
    }
    return ask_openai(prompt_template, replacements, config)

def send_code_in_parts(source_code, config):

    def make_request(code):
        if config["bot"] == 'claude':
            return ask_claude_for_docstrings(code, config)
        else:
            return ask_openai_for_docstrings(code, config)

    def split_source_code(code, num_parts):
        part_length = len(code) // num_parts
        return [code[i:i + part_length] for i in range(0, len(code), part_length)]

    def attempt_send(code, iteration=0):
        print(f'Sending code in {2 ** iteration} parts.')
        num_parts = 2 ** iteration
        parts = split_source_code(code, num_parts)
        responses = []
        for part in parts:
            print(f'Sending part {parts.index(part) + 1} of {len(parts)}')
            print(part)
            response = make_request(part)
            if 'context_length_exceeded' in response:
                print('Context length exceeded. Trying again with more parts.')
                return attempt_send(code, iteration + 1)
            responses.append(response)
        return '\n'.join(responses)
    
    return attempt_send(source_code)

def log_processed_file(file_path, log_file_path):
    with open(log_file_path, 'a') as log_file:
        log_file.write(file_path + '\n')

def is_file_processed(file_path, log_file_path):
    try:
        with open(log_file_path, 'r') as log_file:
            processed_files = log_file.read().splitlines()
        return file_path in processed_files
    except FileNotFoundError:
        return False



EXPECTED_KEYS = {'docstrings'}

def get_response_validity(response, config):
    context_exceeded = 'context_length_exceeded' in response
    has_docstrings = 'docstrings = {' in response
    is_valid = validate_response(response)
    
    if not is_valid and not context_exceeded and not has_docstrings and config["verbose"]:
        print('Retrying with the full code as the response format was incorrect.')
        
    return (context_exceeded, has_docstrings, is_valid)




def extract_json(input_string):
    pattern = r'\{((?:[^{}]+|{(?:[^{}]+)*})*)\}'
    match = re.search(pattern, input_string, re.DOTALL)
    if match:
        json_string = match.group()
        # Replace "\\n" with "\\n" to preserve escape sequences
        json_string = re.sub(r'\\\\n', r'\\\\n', json_string)
        # Replace "\\n" with "\n" to convert escaped newlines
        json_string = re.sub(r'\\\\n', r'\n', json_string)
        return json_string
    else:
        return "{}"
    
def validate_response(response):
    try:
        json_str = extract_json(response)
        data = json.loads(json_str)

        if not isinstance(data["docstrings"], dict):
            return False
            
        keys = set(data.keys())
        if len(keys) != 2: 
            return False
    except (JSONDecodeError, KeyError):
        return False
    return True


BOTS = {
    'gpt3.5': "gpt-3.5-turbo-1106",
    'gpt4': 'gpt-4',
    'gpt4-120k': "gpt-4-1106-preview", 
    'claude': 'claude-2.1',
    'file': "mock_bot"
}

def get_model(bot):
    if bot not in BOTS:
        print(f'Invalid bot: {bot}') 
        return

    model = BOTS.get(bot)
    if model is None:
        print(f'No model needed for: {bot}')

    return model

def convert_newlines(content):
    try:
        return ast.literal_eval(f"'{content}'")
    except (ValueError, SyntaxError):
        return content


def ask_for_docstrings(source_code, config):
    
    if config['bot'] == 'file':
        with open(config["bot_response_path"]) as f:
            response = f.read()
        is_valid = True    
    else:
        response = send_code_in_parts(source_code, config)

    context_exceeded, has_docstrings, is_valid = get_response_validity(response, config)    
    if not is_valid and not context_exceeded:
        prompt_retry = load_prompt("prompts/prompt_retry")         
        if config['bot'] == 'claude':
            return ask_claude(prompt_retry, {}, config) 
        else:
            return ask_openai(prompt_retry, {}, config)
            
        
    return (response, is_valid)

def process_file(file_path, config):
    if config["verbose"]:
        print(f'Processing file: {file_path}')
    with open(file_path, 'r') as file:
        source_code = file.read()
    task = ResultThread(target=ask_for_docstrings, args=(source_code,config))
    task.start()
    if not config["verbose"]:
        spinner(task)
    task.join()
    if task.result:
        response, is_valid = task.result
        if is_valid:
            docstrings = extract_docstrings(response, config)
            insert_docstrings(file_path,docstrings, config)
            if config["verbose"]:
                print(f'Inserted docstrings in {file_path}')
        else:
            if config["verbose"]:
                print(f'Failed to generate docstrings for {file_path}')
            return False
    else:
        if config["verbose"]:
            print(f'No response received for file: {file_path}')
        return False
    return True

def extract_docstrings(response, config):
    try:
        start_marker = 'docstrings = {'
        if start_marker not in response:
            if config["verbose"]:
                print("Response does not contain the expected 'docstrings = {' format.")
            return ({}, False)
        end_idx = response.find('}', response.find(start_marker)) + 1
        dict_str = response[response.find(start_marker):end_idx]
        docstrings_dict = ast.literal_eval(dict_str.split('docstrings = ')[1].strip())
        if config["verbose"]:
            print('Successfully extracted docstrings.')
        return (docstrings_dict, True)
    except (IndexError, ValueError, SyntaxError) as e:
        if config["verbose"]:
            print(f'Error extracting docstrings: {e}')
        return ({}, False)

def wipe_docstrings(file_path):
    print(f'Wiping docstrings from {file_path}')
    with open(file_path, 'r') as file:
        content = file.read()
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        print(f'Syntax error in file {file_path}: {e}')
        return

    class DocstringRemover(ast.NodeTransformer):

        def visit_FunctionDef(self, node):
            node.body = [n for n in node.body if not isinstance(n, ast.Expr) or not isinstance(n.value, ast.Str)]
            return node

        def visit_ClassDef(self, node):
            node.body = [n for n in node.body if not isinstance(n, ast.Expr) or not isinstance(n.value, ast.Str)]
            return node
    tree = DocstringRemover().visit(tree)
    new_content = ast.unparse(tree)
    with open(file_path, 'w') as file:
        file.write(new_content)
    print(f'Wiped docstrings from {file_path}')

def process_folder_or_file(config):
    path = config['path']
    config["model"] = get_model(config["bot"])
    include_subfolders = config.get('include_subfolders', False)
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            if not include_subfolders and root != path:
                continue
            for file in files:
                full_file_path = os.path.join(root, file)
                if file.endswith('.py'):
                    if config['wipe_docstrings']:
                        wipe_docstrings(full_file_path)
                    else:
                        success = process_file(full_file_path, config)
                        if not success:
                            print(f'Failed to process {full_file_path}')

    elif os.path.isfile(path) and path.endswith('.py'):
        if config['wipe_docstrings']:
            wipe_docstrings(path)
        else:
            success = process_file(path, config)
            if not success:
                print(f'Failed to process {path}')
    else:
        print('Invalid path or file type. Please provide a Python file or directory.')

def read_config(config_path):
    with open(config_path, 'r') as file:
        return json.load(file)

    def main():
        config = load_or_create_config()
        process_folder_or_file(config)
    if __name__ == '__main__':
        main()