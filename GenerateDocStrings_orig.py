claude_api_key = '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'
from anthropic import Anthropic, HUMAN_PROMPT, AI_PROMPT
import argparse
import ast
import re
import os
import requests
import ast
import sys

def insert_docstrings(file_path, docstrings):
    with open(file_path, 'r') as file:
        content = file.readlines()
    tree = ast.parse(''.join(content))
    lines_to_insert = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            start_line = node.lineno
            indent_level = len(content[start_line - 1]) - len(content[start_line - 1].lstrip())
            is_class_node = isinstance(node, ast.ClassDef)
            docstring = docstrings.get(node.name)
            if docstring:
                formatted_docstring = format_docstring(docstring, indent_level, is_class=is_class_node)
                lines_to_insert[start_line] = formatted_docstring
    for line_num, docstring in sorted(lines_to_insert.items(), reverse=True):
        content.insert(line_num, docstring)
    with open(file_path, 'w') as file:
        file.write(''.join(content))

def format_docstring(docstring, indent_level, is_class=False):
    if is_class:
        additional_indent = ' ' * 4
    else:
        additional_indent = ' ' * 4
    indented_docstring = additional_indent + '"""' + docstring.strip() + '\n'
    indented_docstring += additional_indent + '"""'
    lines = indented_docstring.split('\n')
    indented_lines = [' ' * indent_level + line for line in lines]
    return '\n'.join(indented_lines) + '\n'

def list_files(directory, extention):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f)) and f.endswith(extention)]

def ask_claude_for_docstrings(source_code, api_key):
    HUMAN_PROMPT = '\n\nHuman: Please generate detailed docstrings for the following Python code. For each class and function, provide a docstring that describes its purpose and usage. Include parameters and return types where applicable. Your response should be in the format: \'docstrings = {"ClassName": "Class docstring...", "function_name": "Function docstring..."}\'.\n\nPython Code:\n' + source_code + '\n\nAssistant:'
    anthropic = Anthropic(api_key=api_key)
    completion = anthropic.completions.create(model='claude-2.0', max_tokens_to_sample=4000, temperature=0, prompt=HUMAN_PROMPT)
    return completion.completion

def extract_docstrings(text):
    start_marker = 'docstrings = {'
    end_marker = '}'
    start_idx = text.find(start_marker)
    end_idx = text.find(end_marker, start_idx) + 1
    dict_str = text[start_idx:end_idx]
    try:
        normalized_str = dict_str.replace('\n', '').replace('  ', ' ')
        dict_str = normalized_str.split('docstrings = ')[1]
        dict_str = dict_str.strip()
        docstrings_dict = ast.literal_eval(dict_str)
        return docstrings_dict
    except IndexError:
        print("Error: The input string does not contain 'docstrings = '")
        return None
    except SyntaxError as e:
        print('Syntax error during evaluation:', e)
        return None
        docstrings_dict = ast.literal_eval(normalized_str)
        return docstrings_dict
    except (SyntaxError, ValueError) as e:
        print('Error evaluating the dictionary string:', e)
        return None

def is_file_processed(file_path, log_file_path):
    try:
        with open(log_file_path, 'r') as log_file:
            processed_files = log_file.read().splitlines()
        return file_path in processed_files
    except FileNotFoundError:
        return False

def log_processed_file(file_path, log_file_path):
    with open(log_file_path, 'a') as log_file:
        log_file.write(file_path + '\n')

def process_file(file_path, api_key_claude=claude_api_key):
    with open(file_path, 'r') as file:
        content = file.readlines()
    print(f'processing file: {file_path}')
    print(f'Asking claude for docstrings')
    docstrings_raw = ask_claude_for_docstrings(content)
    print(f'Extracting docstrings')
    docstrings = extract_docstrings(docstrings_raw)
    print(f'Inserting docstrings')
    insert_docstrings(file_path, docstrings)

def main():
    parser = argparse.ArgumentParser(description='Generate Docstrings using AI Models')
    parser.add_argument('directory_path', type=str, help='Directory containing Python files')
    parser.add_argument('-bot', '--bot_type', type=str, choices=['claude', 'gpt4', 'gpt3.5'], default='claude', help='AI bot to use')
    parser.add_argument('--claude_api_key', type=str, required=False, help='API key for Claude model')
    parser.add_argument('--openai_api_key', type=str, required=False, help='API key for OpenAI GPT models')
    args = parser.parse_args()
    if args.bot_type == 'claude' and (not args.claude_api_key):
        raise ValueError('Claude API key is required for Claude model')
    if args.bot_type in ['gpt4', 'gpt3.5'] and (not args.openai_api_key):
        raise ValueError('OpenAI API key is required for GPT models')
    python_files = list_files(args.directory_path, '.py')
    for file in python_files:
        file_path = os.path.join(args.directory_path, file)
        if args.bot_type == 'claude':
            process_file(file_path, args.bot_type, args.claude_api_key)
        else:
            process_file(file_path, args.bot_type, args.openai_api_key)
if __name__ == '__main__':
    main()