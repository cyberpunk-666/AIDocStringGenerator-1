import unittest
import json
import sys
import os
from unittest.mock import patch
from urllib import response

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
dependencies = DependencyContainer()
from dotenv import load_dotenv

dependencies = DependencyContainer()

SAMPLE_JSON_1 = json.dumps({
    "docstrings": {
        "APICommunicator": {
            "docstring": "Handles communication with API services.",
            "ask_anthropic": "Sends prompt to Anthropic API."
        }
    },
    "examples": {
        "example_APICommunicator": "api_com = APICommunicator()"
    }
})

SAMPLE_JSON_2 = json.dumps({
    "docstrings": {
        "DocstringProcessor": {
            "docstring": "Processes docstrings from raw API response.",
            "insert_docstrings": "Inserts docstrings into source code."
        }
    },
    "examples": {
        "example_DocstringProcessor": "processor = DocstringProcessor()"
    }
})


class TestDocstringProcessor(unittest.TestCase):
    response = """
I am requesting docstrings for specific Python functions and classes that currently lack documentation and a functional example for each classes in the following Python code, with an adjustable level of detail based on a verbosity scale from 0 to 5.
The meanings of each verbosity level are as follows:

- 0: No comments or docstrings.
- 1: Very brief, one-line comments for major functions and classes only.
- 2: Concise but informative docstrings for classes and functions, covering basic purposes and functionality.
- 3: Detailed docstrings including parameters, return types, and a description of the function or class behavior.
- 4: Very detailed explanations, including usage examples in the docstrings.
- 5: Extremely detailed docstrings, providing in-depth explanations, usage examples, and covering edge cases.

The current verbosity level for this task is set to and should be used to determine the level of detail in your explanations. Additionally, please provide a code example demonstrating the functionality of the main class or a key function in the code.

Please adhere to the following JSON format for the response, ensuring the usage of simple double quotes for strings:

{
    "docstrings": {
        "ClassName": {
            "docstring": "ClassName description",
            "example": "variable = ClassName.function1_name()\\nprint(variable)",
            "methods": {
                "function1_name": "function1_name description",
                "function2_name": "function2_name description"
            }
        },
        "ClassName2": {
            "docstring": "ClassName2 description",
            "example": "variable = ClassName2.function1_name()\\nprint(variable)",
            "methods": {
                "function1_name": "function1_name description",
                "function2_name": "function2_name description"
            }
        },
        "global_functions": {
            "global_function1": "global_function1 description",
            "global_function2": "global_function2 description"
        }
    }
}


Here is the Python code for which I need the docstrings and functional example, adhering to the verbosity level as per the configuration setting:

Note: Only generate docstrings for functions and classes that currently lack them.
Ensure the response follows the specified format and reflects the appropriate level of detail as per the verbosity setting.

        """
    def setUp(self):
        load_dotenv()
        self.communicator_manager: CommunicatorManager = dependencies.resolve(CommunicatorManager)
        self.docstring_processor: DocstringProcessor = dependencies.resolve(DocstringProcessor)
        self.bot_communicator: BaseBotCommunicator | None = self.communicator_manager.bot_communicator        

    def test_extract_docstrings(self):
        
        response = self.docstring_processor.extract_docstrings([{'content':TestDocstringProcessor.response}])
        self.assertEqual(response.error_message, "")
        self.assertTrue(response.is_valid)

    def test_merge_json_objects(self):
        json_objects = [json.loads(SAMPLE_JSON_1), json.loads(SAMPLE_JSON_2)]
        merged = self.docstring_processor.merge_json_objects(json_objects)
        self.assertIn("APICommunicator", merged["docstrings"])
        self.assertIn("DocstringProcessor", merged["docstrings"])


class TestExtractDocstrings(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.docstring_processor = DocstringProcessor()
        self.config = {"verbose": False}

    def test_extract_docstrings(self):
        
        responses = [{'content':"""
```json
{
    "docstrings": {
        "MyClass": {
            "docstring": "A basic placeholder class for demonstration purposes.",
            "example": "my_object = MyClass()\\nmy_object.my_method()",
            "methods": {
                "my_method": "A placeholder method that does nothing."
            }
        }
    }
}
```
"""}]
        config = {"verbose": False}
        response = self.docstring_processor.extract_docstrings(responses)
        self.assertEqual(response.error_message, "")
        self.assertTrue(response.is_valid)
        assert isinstance(response.content, dict)
        assert response.content == {'MyClass': {'docstring': 'A basic placeholder class for demonstration purposes.', 'example': 'my_object = MyClass()\nmy_object.my_method()', 'methods': {'my_method': 'A placeholder method that does nothing.'}}}

    def test_extract_docstrings_valid(self):
        responses = [{'content':'{"docstrings": {"class1":{"docstring":""}}}'}]
        
        response = self.docstring_processor.extract_docstrings(responses)
        self.assertEqual(response.error_message, "")
        self.assertTrue(response.is_valid)
        self.assertEqual(response.content, {'class1': {'docstring': ''}})

    def test_extract_docstrings_invalid(self):
        responses = [{'content':'invalid json response'}]
        
        response = self.docstring_processor.extract_docstrings(responses)
        self.assertFalse(response.is_valid)
# Add more tests as needed

if __name__ == '__main__':
    unittest.main()
