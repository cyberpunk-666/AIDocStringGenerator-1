import unittest
from unittest.mock import patch, mock_open, Mock
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.FileProcessor import FileProcessor
from DocStringGenerator.APICommunicator import *
from DocStringGenerator.ConfigManager import ConfigManager

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
        self.config = ConfigManager(initial_config= {"bot":"file","model":"classTest"}).config
        # Prepare mock responses for different retry attempts
        file_content_map = {
            "classTest.response.json": 'Invalid Response',
            "classTest.response2.json": '{"docstrings": {"classTest":{"docstring":"This is a class"}}}',  # Simulate a valid JSON response
            ".ENV":""
            # Add more mock responses as needed
        }
        self.file_mock = FileMock(file_content_map)        


    def test_valid_response_on_retry(self):
        with patch('builtins.open', self.file_mock) as mock_file:
            mock_file: FileMock 
            file_processor = FileProcessor()
            response = file_processor.process_code("class classTest:\n    def test_method(self):\n        pass")
            # Assert that the correct file was read on the second attempt
            if mock_file:
                self.assertEqual(mock_file.filename,"classTest.response2.json")
            self.assertTrue(response.is_valid)
            self.assertIn ('This is a class', response.content)


if __name__ == '__main__':
    unittest.main()
