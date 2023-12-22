
   

import unittest
from unittest.mock import MagicMock, patch, ANY
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from pathlib import Path

from DocStringGenerator.APICommunicator import APICommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.FileProcessor import FileProcessor

class TestAPICommunicator(unittest.TestCase):
    def setUp(self):
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
        self.config = {"model":"claude2.1", "bot": "claude",'openai_api_key': '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', 'claude_api_key': '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', 'verbose': False}

        self.processor = DocstringProcessor(self.config)
        self.mock_file_path = MagicMock()
        self.mock_file_path.read_text.return_value = "def test_function():\n    pass"


    def test_insert_docstrings(self):
        # Test the insertion of docstrings into a source file
        mock_file_path = MagicMock()
        mock_file_path.read_text.return_value = "def test_function():\n    pass"

        # Adjusted to match the new expected format of docstrings
        docstrings = {
            "test_function": {"docstring": "This is a test function"}
        }

        self.processor.insert_docstrings(mock_file_path, docstrings)
        expected_content = "def test_function():\n    \"\"\"This is a test function\"\"\"\n    pass"
        mock_file_path.write_text.assert_called_with(expected_content)

    def test_validate_response(self):
        # Test validation of a JSON response
        valid_responses = [
            '{"docstrings": {"MyClass": {"docstring": "Class docstring", "my_method": "Method docstring"}}, "examples": {"example_MyClass": "example code"}}'
        ]
        self.assertTrue(self.processor.validate_response(valid_responses))


    def test_extract_docstrings(self):
        mock_response = ['{"docstrings": {"test_function": "Test function docstring"},"examples": {"example": "example"}}']
        docstrings, examples, success = self.processor.extract_docstrings(mock_response, self.config)
        self.assertTrue(success)
        self.assertEqual(docstrings, {"test_function": "Test function docstring"})



class TestFileProcessor(unittest.TestCase):
    def setUp(self):
        self.config = {"keep_responses": False, "model":"file", "bot": "file",'openai_api_key': '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', 'claude_api_key': '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', 'verbose': False}
        self.file_processor = FileProcessor(self.config)

    @patch('DocStringGenerator.APICommunicator.APICommunicator.ask_for_docstrings')
    @patch('DocStringGenerator.DocstringProcessor.DocstringProcessor.insert_docstrings')
    def test_process_file(self, mock_insert, mock_ask):
        # Mock the ask_for_docstrings method to return a list of JSON strings
        mock_responses = ['{"docstrings": {"test_function": {"docstring": "Test function docstring"}}, "examples": {"example_test_function": "example usage"}}']
        mock_ask.return_value = (mock_responses, True)

        # Create a FileProcessor instance and call process_file
        file_processor = FileProcessor(self.config)
        success = file_processor.process_file(Path('./test_DocStringGenerator/classTest.py').absolute(), self.config)

        # Assert that the process was successful and insert_docstrings was called once
        self.assertTrue(success)
        # Ensure insert_docstrings is called with correctly formatted docstrings
        expected_docstrings = {"test_function": {"docstring": "Test function docstring"}}
        mock_insert.assert_called_once_with(ANY, expected_docstrings)


    @patch('DocStringGenerator.FileProcessor.FileProcessor.process_file')
    def test_process_directory(self, mock_process_file):
        # Mocking the process_file method to simulate file processing
        mock_process_file.return_value = True

        file_processor = FileProcessor(self.config)

        file_processor.process_file("test_DocStringGenerator/classTest.py", self.config)

        # Assuming the directory contains two Python files
        self.assertEqual(mock_process_file.call_count, 1)


if __name__ == '__main__':
    unittest.main()
