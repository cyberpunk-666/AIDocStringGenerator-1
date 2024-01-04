import json
import unittest
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from unittest import mock


from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from pathlib import Path
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.DependencyContainer import DependencyContainer
dependencies = DependencyContainer()

class TestValidateResponse(unittest.TestCase):
    def setUp(self):
        self.code_processor: CodeProcessor = dependencies.resolve(CodeProcessor)
        self.validator: DocstringProcessor = dependencies.resolve(DocstringProcessor) 
        self.config = ConfigManager().config

    def test_valid_json_object(self):
        json_object = {
            "docstrings": {
                "global_functions": {},
                "example_class": {
                    "docstring": "Example docstring",
                    "methods": {
                        "example_method": "Example method docstring"
                    }
                }
            }
        }
        response = self.validator.validate_response(json_object)
        self.assertTrue(response.is_valid)
        self.assertEqual(response.error_message, "Response validated successfully.")

    def test_verbose_config(self):
        json_object = {"docstrings": {"global_functions": {}}}
        self.validator.config = {'verbose': True}
        with mock.patch('builtins.print') as mock_print:
            self.validator.validate_response(json_object)
            print(mock_print.mock_calls)
            mock_print.assert_any_call("Validating docstrings...")

    def test_invalid_docstrings_format(self):
        json_object = {"docstrings": []}  # Invalid format
        response = self.validator.validate_response(json_object)
        self.assertFalse(response.is_valid)
        self.assertIn("Invalid format: 'docstrings' should be a dictionary.", response.error_message)

    def test_invalid_global_functions_format(self):
        json_object = {
            "docstrings": {
                "global_functions": []  # Invalid format
            }
        }
        response = self.validator.validate_response(json_object)
        self.assertFalse(response.is_valid)
        self.assertIn("Invalid format: Global functions under", response.error_message)

    def test_invalid_class_format(self):
        json_object = {
            "docstrings": {
                "example_class": {
                    "methods": []  # Invalid format
                }
            }
        }
        response = self.validator.validate_response(json_object)
        self.assertFalse(response.is_valid)
        self.assertIn("Invalid format: Class", response.error_message)

    def test_docstring_exceeds_max_length(self):
        long_docstring = "a" * 51  # Exceeds max_length
        json_object = {
            "docstrings": {
                "example_class": {
                    "docstring": long_docstring
                }
            }
        }
        response = self.validator.validate_response(json_object, max_length=50)
        self.assertFalse(response.is_valid)
        self.assertIn("exceeds maximum length", response.error_message)


    def test_docstring_not_exceeds_max_length(self):
        long_docstring = "a" * 49  # Exceeds max_length
        json_object = {
            "docstrings": {
                "example_class": {
                    "docstring": long_docstring
                }
            }
        }
        response = self.validator.validate_response(json_object, max_length=50)
        self.assertTrue(response.is_valid)
        self.assertNotIn("exceeds maximum length", response.error_message)

    def test_example_only_mode(self):
        json_object = {
            "docstrings": {
                "example_class": {
                    "example": "print('Hello, world!')"
                }
            }
        }
        response = self.validator.validate_response(json_object, example_only=True)
        self.assertTrue(response.is_valid)


    def test_invalid_examples_format(self):
        json_object = {"examples": []}  # Invalid format
        response = self.validator.validate_response(json_object)
        self.assertFalse(response.is_valid)
        self.assertIn("Invalid format: 'examples' should be a dictionary.", response.error_message)


    def test_ask_missing_mode(self):
        json_object = {"docstrings": {"example_class": {"docstring": ""}}}
        response = self.validator.validate_response(json_object, ask_missing=True)
        self.assertTrue(response.is_valid)


    def test_method_docstring_is_string(self):
        json_object = {
            "docstrings": {
                "example_class": {
                    "docstring": "Class docstring",
                    "methods": {
                        "example_method": "Method docstring"
                    }
                }
            }
        }
        response = self.validator.validate_response(json_object)
        self.assertTrue(response.is_valid)
        self.assertEqual(response.error_message, "Response validated successfully.")

    def test_method_docstring_is_not_string(self):
        json_object = {
            "docstrings": {
                "example_class": {
                    "docstring": "Class docstring",
                    "methods": {
                        "example_method": {"not": "a string"}
                    }
                }
            }
        }
        response = self.validator.validate_response(json_object)
        self.assertFalse(response.is_valid)
        self.assertIn("Method 'example_method' docstring should be a string", response.error_message)

    def test_global_method_docstring_is_string(self):
        json_object = {
            "docstrings": {
                "global_functions":{
                    "example_method": "Method docstring"
                }
            }
        }
        response = self.validator.validate_response(json_object)
        self.assertTrue(response.is_valid)
        self.assertEqual(response.error_message, "Response validated successfully.")

    def test_global_method_docstring_is_not_string(self):
        json_object = {
            "docstrings": {
                "global_functions":{
                   "example_method": {"not": "a string"}
                }
            }
        }
        
        response = self.validator.validate_response(json_object)
        self.assertFalse(response.is_valid)
        self.assertIn("Method 'example_method' docstring should be a string", response.error_message)


if __name__ == '__main__':
    unittest.main()
