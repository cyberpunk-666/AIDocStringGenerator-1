
   

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

from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
dependencies = DependencyContainer()
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.ConfigManager import ConfigManager
from dotenv import load_dotenv

class TestAPICommunicator(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        
        ConfigManager().update_config({"dry_run": True,"keep_responses": False, "bot": "file", 'verbose': False, "model": "classTest"})
        self.communicator_manager: CommunicatorManager = dependencies.resolve("CommunicatorManager")
        self.communicator_manager.initialize_bot_communicator()
        if self.communicator_manager.bot_communicator:
            self.bot_communicator: BaseBotCommunicator = self.communicator_manager.bot_communicator

    @patch('requests.post')
    def test_send_request(self, mock_post):
        # Mocking the post request to return a predefined response
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = iter([{"docstrings": {"TestCode": {"exemple": "example code", "docstring": "Class docstring"}}}])
        mock_post.return_value = mock_response

        response = self.bot_communicator.ask_for_docstrings('class TestCode:')
        self.assertEqual(response.error_message, "")
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



if __name__ == '__main__':
    unittest.main()
