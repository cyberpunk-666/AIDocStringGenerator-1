
   

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

from DocStringGenerator.APICommunicator import *
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.FileProcessor import FileProcessor
from DocStringGenerator.ConfigManager import ConfigManager
from dotenv import load_dotenv

class TestAPICommunicator(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        ConfigManager(initial_config={"dry_run": True,"keep_responses": False, "bot": "file", 'verbose': False, "model": "classTest"})        
        self.communicator_manager: CommunicatorManager = dependencies.resolve("CommunicatorManager")
        if self.communicator_manager.bot_communicator:
            self.bot_communicator: BaseBotCommunicator = self.communicator_manager.bot_communicator

    @patch('requests.post')
    def test_send_request(self, mock_post):
        # Mocking the post request to return a predefined response
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = iter([{"docstrings": {"TestCode": {"exemple": "example code", "docstring": "Class docstring"}}}])
        mock_post.return_value = mock_response

        response = self.bot_communicator.ask_for_docstrings('class TestCode:')
        self.assertTrue(response.is_valid)

class TestDocstringProcessor(unittest.TestCase):
    def setUp(self):
        load_dotenv()

        self.processor = dependencies.resolve("DocstringProcessor")
        self.mock_file_path = MagicMock()
        self.mock_file_path.read_text.return_value = "def test_function():\n    pass"


    def test_extract_docstrings2(self):
        # Test validation of a JSON response
        valid_response = '{"docstrings": {"MyClass": {"exemple": "example code", "docstring": "Class docstring", "methods": {"my_method": "Method docstring"}}}}'        
        self.assertTrue(self.processor.extract_docstrings([valid_response]))


class TestFileProcessor(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        ConfigManager(initial_config={"dry_run": True, "keep_responses": False, "bot": "file", 'verbose': False, "model": "classTest"})
        self.file_processor: FileProcessor = dependencies.resolve("FileProcessor")

    def test_process_file(self):
        classTest_file_path = Path('./tests/classTest.py')

        # Create a FileProcessor instance and call process_file on the temp file
        file_processor: FileProcessor = dependencies.resolve("FileProcessor")
        response = file_processor.process_file(classTest_file_path)

        # Assert that the process was successful
        self.assertTrue(response.is_valid)

        # Read the expected contents from the result file
        result_file_path = Path('./tests/classTest-result.py')
        with open(str(result_file_path), 'r') as file:
            expected_docstrings = file.read()

        # Assert that the processed content matches the expected content
        self.assertEqual(expected_docstrings, response.content)

    @patch('DocStringGenerator.FileProcessor.FileProcessor.process_file')
    def test_process_directory(self, mock_process_file):
        # Mocking the process_file method to simulate file processing
        mock_process_file.return_value = True

        file_processor = dependencies.resolve("FileProcessor")

        file_processor.process_file("tests/classTest_orig.py")

        # Assuming the directory contains two Python files
        self.assertEqual(mock_process_file.call_count, 1)




if __name__ == '__main__':
    unittest.main()
