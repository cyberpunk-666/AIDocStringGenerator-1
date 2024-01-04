import unittest
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")

from unittest.mock import patch, mock_open, Mock
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
dependencies = DependencyContainer()
from DocStringGenerator.ConfigManager import ConfigManager
from pathlib import Path

class FileMock:
    def __init__(self, file_content_map):
        self.file_content_map = file_content_map
        self.filename = None

    def __call__(self, file_path, mode='r', **kwargs):
        file_name = Path(file_path).name
        self.filename = file_name
        file_content = self.file_content_map.get(file_name, '')
        mock_file = Mock()
        mock_file.read.return_value = file_content

        # Correctly handle the context manager protocol
        mock_file.__enter__ = lambda _: mock_file
        mock_file.__exit__ = lambda _1, _2, _3, _4: None
        return mock_file

class TestAIDocStringGenerator(unittest.TestCase):
    def setUp(self):
        ConfigManager().update_config({"bot":"file","model":"classTest"})
        self.config = ConfigManager().config
        self.communicator_manager: CommunicatorManager = dependencies.resolve(CommunicatorManager)
        self.communicator_manager.initialize_bot_communicator()        
        # Prepare mock responses for different retry attempts
        file_content_map = {
            "classTest.response.json": 'Invalid Response',
            "classTest.response2.json": '{"docstrings": {"classTest":{"methods":{"test_method":"Description 1"},"example":"Bad Code","docstring":"This is a class"}}}', 
            "classTest.example.json": '{"docstrings": {"classTest":{"example":"print(\'Hello, world!\')"}}}', 
            "classTest.missing.json": '{"docstrings": {"classTest":{"methods":{"test_method2":"Description 2"}}}}', 
            ".ENV":""
            # Add more mock responses as needed
        }
        self.file_mock = FileMock(file_content_map)        


    def test_valid_response_on_retry(self):
        with patch('builtins.open', self.file_mock) as mock_file:
            mock_file: FileMock 
            code_processor = CodeProcessor()
            response = code_processor.process_code("class classTest:\n    def test_method(self):\n        pass\n    def test_method2(self):\n        pass")
            # Assert that the correct file was read on the second attempt
            self.assertEqual(response.error_message, "")
            self.assertTrue(response.is_valid)
            self.assertIn ('This is a class', response.content)
            self.assertIn ('Hello, world!', response.content)
            self.assertIn ('Description 2', response.content)


if __name__ == '__main__':
    unittest.main()
