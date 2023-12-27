import json
import os
import unittest
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.APICommunicatorv2 import *
from dotenv import load_dotenv

# Import other necessary modules...

class DocStringGeneratorTest(unittest.TestCase):
    bot_communicator = None

    @classmethod
    def setUpClass(cls):
        load_dotenv()
        cls.config = {
            "verbose": True,
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
            "BARD_API_KEY": os.getenv("BARD_API_KEY"),
            # Add other common configurations here...
        }

    def setUp(self):
        if self.__class__ == DocStringGeneratorTest:
            self.skipTest("Skipping tests in base class")

        # self.api_communicator initialization if necessary
        self.api_communicator = CommunicatorManager(self.config) 

    def test_docstring_generation(self):
        # Test generating docstrings for a sample Python code
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.api_communicator.get_response(sample_code)
        # Assert response is not None or empty
        self.assertIsNotNone(response)
        self.assertTrue(response.is_valid)

        # Further assertions to check the response format, content, etc.

    def test_response_parsing(self):
        # Test parsing the response into the desired JSON format
        sample_response = '{"docstrings": {"MyClass": {"docstring": "Description"}}}'
        docstring_processor = DocstringProcessor(self.config)
        parsed_response = docstring_processor.extract_docstrings(sample_response)
        # Assertions to check if the parsing is correct
        self.assertIn("MyClass", parsed_response)

        # Further assertions to check the detailed structure of parsed_response

    def test_length_limit_enforcement(self):
        # Configuring a short max_line_length for testing
        self.config['max_line_length'] = 50  # Example length
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.api_communicator.get_response(sample_code)

        self.assertIsNotNone(response)
        self.assertNotEqual(response, "")

        # Assuming response is a JSON string; parse it
        response_data = json.loads(response)
        docstrings = response_data.get('docstrings', {})

        for class_name, class_info in docstrings.items():
            self.assertTrue(all(len(line) <= 50 for line in class_info['docstring'].split('\n')))
            self.assertTrue(all(len(line) <= 50 for line in class_info['example'].split('\n')))
            for method, method_doc in class_info['methods'].items():
                self.assertTrue(all(len(line) <= 50 for line in method_doc.split('\n')))

    def test_verbosity_levels(self):
        # Set distinct verbosity levels for testing
        self.config['class_docstrings_verbosity_level'] = 4
        self.config['function_docstrings_verbosity_level'] = 4
        self.config['example_verbosity_level'] = 4

        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.api_communicator.get_response(sample_code, self.config)

        self.assertIsNotNone(response)
        self.assertNotEqual(response, "")

        # Parse response and check verbosity
        response_data = json.loads(response)
        docstrings = response_data.get('docstrings', {})

        for class_name, class_info in docstrings.items():
            # Assert class docstring verbosity level
            class_docstring = class_info['docstring']
            self.assertTrue(self.check_verbosity(class_docstring, 4))  # Check if class docstring meets verbosity level 4

            # Assert method docstring verbosity level
            for method, method_doc in class_info['methods'].items():
                self.assertTrue(self.check_verbosity(method_doc, 4))  # Check if method docstring meets verbosity level 4

            # Assert example verbosity level
            example = class_info['example']
            self.assertTrue(self.check_verbosity(example, 4))  # Check if example meets verbosity level 4

    def check_verbosity(self, text, expected_verbosity):
        # Implement heuristic checks here
        if expected_verbosity == 0:
            return text == ""
        elif expected_verbosity == 1:
            return len(text.splitlines()) == 1
        elif expected_verbosity == 2:
            return len(text) < 100  # Example condition
        elif expected_verbosity == 3:
            return "parameters" in text.lower() or "return" in text.lower()
        elif expected_verbosity == 4:
            return len(text) > 100  # Example condition
        elif expected_verbosity == 5:
            return "example" in text.lower() and "edge case" in text.lower()
        return False


    def test_empty_code_input(self):
        # Test behavior with empty Python code input
        response = self.api_communicator.get_response("", self.config)
        # Expecting an empty or specific response for empty input
        self.assertEqual(response, "")

    def test_invalid_code_input(self):
        # Test behavior with invalid Python code
        invalid_code = "def incomplete_function("
        response = self.api_communicator.get_response(invalid_code, self.config)
        # Depending on how your system handles errors, adjust the assertion
        self.assertIsNone(response)  # or some error message

    def test_json_format_compliance(self):
        # Test if the response complies with the specified JSON format
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.api_communicator.get_response(sample_code, self.config)
        try:
            json_response = json.loads(response)
            self.assertIsInstance(json_response, dict)
            self.assertIn("docstrings", json_response)
        except json.JSONDecodeError:
            self.fail("Response is not valid JSON")

    def test_method_docstrings_inclusion(self):
        # Test if methods within classes have their docstrings generated
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.api_communicator.get_response(sample_code, self.config)
        json_response = json.loads(response)
        self.assertIn("my_method", json_response["docstrings"]["MyClass"]["methods"])

    def test_global_function_docstring_generation(self):
        # Test if global functions have their docstrings generated
        sample_code = "def my_function():\n    pass"
        response = self.api_communicator.get_response(sample_code, self.config)
        json_response = json.loads(response)
        self.assertIn("my_function", json_response["docstrings"]["global_functions"])

    def test_character_limit_enforcement(self):
        # Test if the character limit is enforced in the response
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.api_communicator.get_response(sample_code, self.config)
        json_response = json.loads(response)
        for line in json.dumps(json_response, indent=4).split("\n"):
            self.assertLessEqual(len(line), self.config["max_line_length"])

    def test_class_with_multiple_methods(self):
        # Test generating docstrings for a class with multiple methods
        sample_code = """
class MyClass:
    def method1(self):
        pass

    def method2(self, param):
        pass
"""
        response = self.api_communicator.get_response(sample_code, self.config)
        json_response = json.loads(response)
        self.assertIn("method1", json_response["docstrings"]["MyClass"]["methods"])
        self.assertIn("method2", json_response["docstrings"]["MyClass"]["methods"])

    def test_inheritance_handling(self):
        # Test generating docstrings for classes with inheritance
        sample_code = """
class ParentClass:
    def parent_method(self):
        pass

class ChildClass(ParentClass):
    def child_method(self):
        pass
"""
        response = self.api_communicator.get_response(sample_code, self.config)
        json_response = json.loads(response)
        self.assertIn("ParentClass", json_response["docstrings"])
        self.assertIn("ChildClass", json_response["docstrings"])

    def test_docstring_for_complex_functions(self):
        # Test generating docstrings for functions with complex signatures
        sample_code = """
def complex_function(param1, param2='default', *args, **kwargs):
    pass
        """
        response = self.api_communicator.get_response(sample_code, self.config)
        json_response = json.loads(response)
        self.assertIn("complex_function", json_response["docstrings"]["global_functions"])

    def test_handling_of_decorators(self):
        # Test generating docstrings for decorated functions and methods
        sample_code = """
def my_decorator(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@my_decorator
def decorated_function(param):
    pass
"""
        response = self.api_communicator.get_response(sample_code, self.config)
        json_response = json.loads(response)
        self.assertIn("decorated_function", json_response["docstrings"]["global_functions"])

    def test_docstring_format_consistency(self):
        # Test if the docstring format is consistent across various elements
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.api_communicator.get_response(sample_code, self.config)
        json_response = json.loads(response)
        # Check for consistent formatting in class and method docstrings, examples, etc.
        class_docstring = json_response["docstrings"]["MyClass"]["docstring"]
        method_docstring = json_response["docstrings"]["MyClass"]["methods"]["my_method"]
        self.assertTrue(self.is_consistent_format(class_docstring, method_docstring))

    def is_consistent_format(self, *args):
        # Helper method to check formatting consistency
        # Implement specific checks based on your docstring format requirements
        pass



class ClaudeDocStringGeneratorTest(DocStringGeneratorTest):
    @classmethod
    def setUpClass(cls):
        super(ClaudeDocStringGeneratorTest, cls).setUpClass()
        cls.config["bot"] = "claude"
        cls.config["model"] = "claude-2.1"
        cls.bot_communicator = ClaudeCommunicator(cls.config)

class OpenAIDocStringGeneratorTest(DocStringGeneratorTest):
    @classmethod
    def setUpClass(cls):
        super(OpenAIDocStringGeneratorTest, cls).setUpClass()
        cls.config["bot"] = "openai"
        cls.config["model"] = "gpt-4-1106-preview"
        cls.bot_communicator = OpenAICommunicator(cls.config)

class BardDocStringGeneratorTest(DocStringGeneratorTest):
    @classmethod
    def setUpClass(cls):
        super(BardDocStringGeneratorTest, cls).setUpClass()
        cls.config["bot"] = "bard"
        cls.bot_communicator = BardCommunicator(cls.config)

class FileDocStringGeneratorTest(DocStringGeneratorTest):
    @classmethod
    def setUpClass(cls):
        super(FileDocStringGeneratorTest, cls).setUpClass()
        cls.config["bot"] = "file"
        cls.bot_communicator = FileCommunicator(cls.config)

if __name__ == '__main__':
    unittest.main()
