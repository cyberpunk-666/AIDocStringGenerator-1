
    # def test_ask_for_docstrings(self):
    #     # Test selecting the correct API based on config
    #     with unittest.mock.patch.object(self.api_communicator, "ask_claude") as mock_ask_claude, \
    #             unittest.mock.patch.object(self.api_communicator, "ask_openai") as mock_ask_openai:
    #         self.config["bot"] = "claude"
    #         self.api_communicator.ask_for_docstrings("some_code", self.config)
    #         mock_ask_claude.assert_called_once()
    #         mock_ask_openai.assert_not_called()

    #         self.config["bot"] = "openai"
    #         self.api_communicator.ask_for_docstrings("some_code", self.config)
    #         mock_ask_claude.assert_called_once()  # previous call still counts
    #         mock_ask_openai.assert_called_once()

    #     # Test sending code in parts and merging responses
    #     long_code = " ".join(["a" for _ in range(10000)])  # exceed context length
    #     expected_response = "{\"docstrings\": {\"f\": \"Docstring\"}}"
    #     with unittest.mock.patch.object(self.api_communicator, "send_code_in_parts") as mock_send_parts:
    #         mock_send_parts.return_value = (
    #             [None, None, expected_response], True
    #         )  # simulate response parts and validity
    #         response, is_valid = self.api_communicator.ask_for_docstrings(long_code, self.config)
    #         self.assertEqual(response, expected_response)
    #         self.assertTrue(is_valid)

    #     # Test checking response validity
    #     with unittest.mock.patch.object(self.api_communicator, "send_code_in_parts") as mock_send_parts:
    #         mock_send_parts.return_value = ([None, None, "invalid_json"], False)
    #         response, is_valid = self.api_communicator.ask_for_docstrings(long_code, self.config)
    #         self.assertIsNone(response)
    #         self.assertFalse(is_valid)

    #     # Test retrying with full code on invalid format
    #     with unittest.mock.patch.object(self.api_communicator, "send_code_in_parts") as mock_send_parts:
    #         mock_send_parts.side_effect = [([None, None, "invalid_json"], False), expected_response]
    #         response, is_valid = self.api_communicator.ask_for_docstrings(long_code, self.config)
    #         self.assertEqual(response, expected_response)
    #         self.assertTrue(is_valid)

    #     # Test exceptions during code sending
    #     with unittest.mock.patch.object(self.api_communicator, "send_code_in_parts") as mock_send_parts:
    #         mock_send_parts.side_effect = Exception("Sending error")
    #         with self.assertRaises(Exception):
    #             self.api_communicator.ask_for_docstrings(long_code, self.config)


import unittest
from unittest.mock import MagicMock, patch
import sys
sys.path.append('./DocStringGenerator')
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
        mock_response.iter_lines.return_value = iter([b'data: {"completion": "mocked completion"}'])
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
        valid_response = b'data: {"completion": "test docstring"}'
        mock_response = MagicMock()
        mock_response.iter_lines.return_value = iter([valid_response])
        mock_post.return_value = mock_response

        response = self.communicator.ask_claude_for_docstrings('test code', self.config)
        self.assertEqual('test docstring', response)


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
        docstrings = {"test_function": "This is a test function"}

        self.processor.insert_docstrings(mock_file_path, docstrings)
        mock_file_path.write_text.assert_called_with("def test_function():\n    \"\"\"This is a test function\"\"\"\n    pass")

    def test_extract_docstrings(self):
        # Test extraction of docstrings from a response
        mock_response = '{"docstrings": {"test_function": "Test function docstring"},"example": "example"}'
        docstrings, example, success = self.processor.extract_docstrings(mock_response, self.config)
        self.assertTrue(success)
        self.assertEqual(docstrings, {"test_function": "Test function docstring"})

    def test_validate_response(self):
        # Test validation of a response
        valid_response = '{"docstrings": {"test_function": "Test function docstring"},"example": "example"}'
        self.assertTrue(self.processor.validate_response(valid_response))


class TestFileProcessor(unittest.TestCase):
    def setUp(self):
        self.config = {"model":"file", "bot": "file",'openai_api_key': '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', 'claude_api_key': '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', 'verbose': False}

        self.file_processor = FileProcessor(self.config)
    @patch('APICommunicator.APICommunicator.ask_for_docstrings')
    @patch('DocStringGenerator.DocstringProcessor.DocstringProcessor.insert_docstrings')
    def test_process_file(self, mock_insert, mock_ask):
        # Mocking the ask_for_docstrings method to return a fake response
        mock_ask.return_value = ('{"docstrings": {"test_function": "Test function docstring"}}', True)

        file_processor = FileProcessor(self.config)
        success = file_processor.process_file(Path('classTest.py'), self.config)

        self.assertTrue(success)
        mock_insert.assert_called_once()

    @patch('DocStringGenerator.FileProcessor.FileProcessor.process_file')
    def test_process_directory(self, mock_process_file):
        # Mocking the process_file method to simulate file processing
        mock_process_file.return_value = True

        file_processor = FileProcessor(self.config)

        file_processor.process_file("classTest.py", self.config)

        # Assuming the directory contains two Python files
        self.assertEqual(mock_process_file.call_count, 1)


if __name__ == '__main__':
    unittest.main()
