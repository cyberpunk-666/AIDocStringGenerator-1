
   

import unittest
from unittest.mock import MagicMock, patch, ANY, mock_open
import sys
import os
import tempfile
import shutil
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from pathlib import Path

from DocStringGenerator.APICommunicator import APICommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.FileProcessor import FileProcessor
from dotenv import load_dotenv

class TestAPICommunicator(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.config = {"model":"claude2.1", "bot": "claude",'openai_api_key': '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', 'claude_api_key': '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', 'verbose': False}
        self.communicator = APICommunicator(self.config)

    @patch('requests.post')
    def test_send_request(self, mock_post):
        # Mocking the post request to return a predefined response
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = iter([
            b'header or metadata', 
            b'data: {"completion": "mocked completion"}'
        ])
        mock_post.return_value = mock_response

        response = self.communicator.ask_claude_for_docstrings('test code', self.config)
        self.assertIn('mocked completion', response) 

    @patch('requests.post')
    def test_error_handling(self, mock_post):
        # Simulate an exception during the request
        mock_post.side_effect = Exception("Connection error")

        response = self.communicator.ask_claude_for_docstrings('test code', self.config)
        self.assertIn('Error during Claude API call', response)

    @patch('requests.post')
    def test_response_parsing(self, mock_post):
        # Testing parsing of a valid response
        valid_response = iter([
            b'header or metadata', 
            b'data: {"completion": "test docstring"}'
        ])
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = valid_response
        mock_post.return_value = mock_response

        response = self.communicator.ask_claude_for_docstrings('test code', self.config)
        self.assertIn('test docstring', response)


class TestDocstringProcessor(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.config = {"model":"claude2.1", "bot": "claude",'openai_api_key': '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', 'claude_api_key': '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', 'verbose': True}

        self.processor = DocstringProcessor(self.config)
        self.mock_file_path = MagicMock()
        self.mock_file_path.read_text.return_value = "def test_function():\n    pass"


    def test_validate_response(self):
        # Test validation of a JSON response
        valid_response = '{"docstrings": {"MyClass": {"exemple": "example code", "docstring": "Class docstring", "methods": {"my_method": "Method docstring"}}}}'        
        self.assertTrue(self.processor.validate_response(valid_response, self.config))
#

    def test_extract_docstrings(self):
        mock_response = ['{"docstrings": {"example": "example", "test_function": "Test function docstring"}}']
        docstrings, success = self.processor.extract_docstrings(mock_response, self.config)
        self.assertTrue(success)
        self.assertEqual(docstrings, {'example': 'example', 'test_function': 'Test function docstring'})



class TestFileProcessor(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.config = {"keep_responses": False, "model":"file", "bot": "file",'openai_api_key': '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', 'claude_api_key': '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', 'verbose': False}
        self.file_processor = FileProcessor(self.config)

    def test_process_file(self):
        self.config = {"keep_responses": False, "verbose": True, "bot": "file", "bot_response_file": ["classTest.response","classTest.response2"]}

        classTest_file_path = Path('./tests/classTest.py')
        temp_dir = tempfile.mkdtemp()  # Create a temporary directory
        temp_file_path = Path(temp_dir, 'classTest_temp.py')

        # Copy the original file to the temporary file
        shutil.copy2(str(classTest_file_path), str(temp_file_path))

        # Create a FileProcessor instance and call process_file on the temp file
        file_processor = FileProcessor(self.config)
        success = file_processor.process_file(temp_file_path, self.config)

        # Assert that the process was successful
        self.assertTrue(success)

        # Read the contents of the temporary file after processing
        with open(str(temp_file_path), 'r') as file:
            processed_content = file.read()

        # Read the expected contents from the result file
        result_file_path = Path('./tests/classTest-result.py')
        with open(str(result_file_path), 'r') as file:
            expected_docstrings = file.read()

        # Assert that the processed content matches the expected content
        self.assertEqual(expected_docstrings, processed_content)

        # Clean up: remove the temporary file and directory
        os.remove(str(temp_file_path))
        os.rmdir(temp_dir)


    @patch('DocStringGenerator.FileProcessor.FileProcessor.process_file')
    def test_process_directory(self, mock_process_file):
        # Mocking the process_file method to simulate file processing
        mock_process_file.return_value = True

        file_processor = FileProcessor(self.config)

        file_processor.process_file("tests/classTest.py", self.config)

        # Assuming the directory contains two Python files
        self.assertEqual(mock_process_file.call_count, 1)


    def test_process_file2(self):            
        new_test_script_content = """class Calculator:
    def add(self, x, y):
        return x + y

    def subtract(self, x, y):
        return x - y

    def multiply(self, x, y):
        return x * y

    def divide(self, x, y):
        if y == 0:
            raise ValueError("Cannot divide by zero.")
        return x / y"""

        # New content for the JSON file (docstrings_response.json)
        new_docstrings_response_content = """{
    "docstrings": {
        "Calculator":{
            "docstring": "Class to perform basic arithmetic operations.",
            "example": "calc = Calculator()\\nresult = calc.add(5, 3)\\nprint(result)",
            "methods": {
                "add": "Adds two numbers.",
                "subtract": "Subtracts the second number from the first.",
                "multiply": "Multiplies two numbers.",
                "divide": "Divides the first number by the second."
            }
        }
    }  
}
"""

        final_script_with_comments = """class Calculator:
    \"\"\"Class to perform basic arithmetic operations.\"\"\"
    def add(self, x, y):
        \"\"\"Adds two numbers.\"\"\"
        return x + y

    def subtract(self, x, y):
        \"\"\"Subtracts the second number from the first.\"\"\"
        return x - y

    def multiply(self, x, y):
        \"\"\"Multiplies two numbers.\"\"\"
        return x * y

    def divide(self, x, y):
        \"\"\"Divides the first number by the second.\"\"\"
        if y == 0:
            raise ValueError("Cannot divide by zero.")
        return x / y

    def example_function_Calculator(self):
        calc = Calculator()
        result = calc.add(5, 3)
        print(result)"""
        
        # New file paths
        with tempfile.TemporaryDirectory() as tmpdir:  
            new_test_script_file_path = Path(tmpdir, "new_test_script.py")  
            new_docstrings_response_file_path = Path(tmpdir, "new_docstrings_response.json")  

            # Writing the new contents to the files
            with open(new_test_script_file_path, 'w') as file:
                file.write(new_test_script_content.strip())

            with open(new_docstrings_response_file_path, 'w') as file:
                file.write(new_docstrings_response_content.strip())
            self.config["bot_response_file"] = str(new_docstrings_response_file_path.absolute())

            success = FileProcessor(self.config).process_file(new_test_script_file_path, self.config)
            self.assertTrue(success)

            with open(new_test_script_file_path, 'r') as file:
                result = file.read()

            self.assertEqual(result, final_script_with_comments)  
            FileProcessor(self.config).removed_from_processed_log(new_test_script_file_path)


if __name__ == '__main__':
    unittest.main()
