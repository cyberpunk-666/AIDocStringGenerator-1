import json
import os
import unittest
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.FileProcessor import FileProcessor
from DocStringGenerator.APICommunicator import *
from DocStringGenerator.ConfigManager import ConfigManager
from dotenv import load_dotenv


# Import other necessary modules...

class DocStringGeneratorTest(unittest.TestCase):
    bot_communicator = None

    @classmethod
    def setUpClass(cls):
        load_dotenv()


    def setUp(self):
        if self.__class__ == DocStringGeneratorTest:
            self.skipTest("Skipping tests in base class")
        self.file_processor: FileProcessor = dependencies.resolve("FileProcessor")
        self.communicator_manager: CommunicatorManager = dependencies.resolve("CommunicatorManager") 
        self.config = ConfigManager().config


    def test_docstring_generation(self):
        # Test generating docstrings for a sample Python code
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.file_processor.try_generate_docstrings(sample_code)
        json_response = response.content
        # Assert response is not None or empty
        self.assertIsNotNone(json_response)
        self.assertTrue(response.is_valid)

        # Further assertions to check the response format, content, etc.

    def test_response_parsing(self):
        # Test parsing the response into the desired JSON format
        sample_response = '{"docstrings": {"MyClass": {"docstring": "Description"}}}'
        response = self.file_processor.try_generate_docstrings(sample_response)
        self.assertTrue(response.is_valid)
        self.assertIn("MyClass", str(response.content))

        # Further assertions to check the detailed structure of parsed_response

    def test_length_limit_enforcement(self):
        # Configuring a short max_line_length for testing
        ConfigManager().set_config('max_line_length', 50)
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.communicator_manager.send_code_in_parts(sample_code)

        self.assertTrue(response.is_valid)
        self.assertNotEqual(response.content, "")

        # Assuming response is a JSON string; parse it

        #response_data = json.loads(response.content)
        #docstrings = response_data.get('docstrings', {})
        docstrings, is_valid = dependencies.resolve("DocstringProcessor").extract_docstrings([response.content])

        self.assertTrue(is_valid)

        for class_name, class_info in docstrings.items():
            if class_name != 'global_functions':
                self.assertTrue(all(len(line) <= 50 for line in class_info['docstring'].split('\n')))
                self.assertTrue(all(len(line) <= 50 for line in class_info['example'].split('\n')))

            if 'methods' in class_info:
                for method, method_doc in class_info['methods'].items():
                    self.assertTrue(all(len(line) <= 50 for line in method_doc.split('\n')))


    def test_empty_code_input(self):
        # Test behavior with empty Python code input
        response = self.communicator_manager.send_code_in_parts("")
        # Expecting an empty or specific response for empty input
        self.assertNotEqual(response, "")

    def test_json_format_compliance(self):
        # Test if the response complies with the specified JSON format
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.file_processor.try_generate_docstrings(sample_code)
        self.assertTrue(response.is_valid)

    def test_method_docstrings_inclusion(self):
        # Test if methods within classes have their docstrings generated
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.file_processor.try_generate_docstrings(sample_code)
        
        self.assertTrue(response.is_valid)
        self.assertIn("my_method", response.content["docstrings"]["MyClass"]["methods"])

    def test_global_function_docstring_generation(self):
        # Test if global functions have their docstrings generated
        sample_code = "def my_function():\n    pass"
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.file_processor.try_generate_docstrings(sample_code)
        json_response = response.content
        self.assertIn("my_function", json_response["docstrings"]["global_functions"])

    def test_character_limit_enforcement(self):
        # Test if the character limit is enforced in the response
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.file_processor.try_generate_docstrings(sample_code)
        json_response = response.content
        for line in json.dumps(json_response, indent=4).split("\n"):            
            self.assertLessEqual(len(line), self.config.get("max_line_length", 79))

    def test_class_with_multiple_methods(self):
        # Test generating docstrings for a class with multiple methods
        sample_code = """
class MyClass:
    def method1(self):
        pass

    def method2(self, param):
        pass
"""
        response = self.file_processor.try_generate_docstrings(sample_code)
        json_response = response.content
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
        response = self.file_processor.try_generate_docstrings(sample_code)
        json_response = response.content
        self.assertIn("ParentClass", json_response["docstrings"])
        self.assertIn("ChildClass", json_response["docstrings"])

    def test_docstring_for_complex_functions(self):
        # Test generating docstrings for functions with complex signatures
        sample_code = """
def complex_function(param1, param2='default', *args, **kwargs):
    pass
        """
        response = self.file_processor.try_generate_docstrings(sample_code)
        json_response = response.content
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
        response = self.file_processor.try_generate_docstrings(sample_code)
        json_response = response.content
        self.assertIn("decorated_function", json_response["docstrings"]["global_functions"])

    def test_docstring_format_consistency(self):
        # Test if the docstring format is consistent across various elements
        sample_code = "class MyClass:\n    def my_method(self):\n        pass"
        response = self.file_processor.try_generate_docstrings(sample_code)
        json_response = response.content
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
        ConfigManager().set_config("bot", "claude")
        ConfigManager().set_config("model", "claude-2.1")
        cls.bot_communicator = ClaudeCommunicator()

class OpenAIDocStringGeneratorTest(DocStringGeneratorTest):
    @classmethod
    def setUpClass(cls):
        super(OpenAIDocStringGeneratorTest, cls).setUpClass()
        ConfigManager().set_config("bot", "openai")
        ConfigManager().set_config("model", "gpt-4-1106-preview")
        cls.bot_communicator = OpenAICommunicator()

class BardDocStringGeneratorTest(DocStringGeneratorTest):
    @classmethod
    def setUpClass(cls):
        super(BardDocStringGeneratorTest, cls).setUpClass()
        ConfigManager().set_config("bot", "bard")
        ConfigManager().set_config("model", "")        
        cls.bot_communicator = BardCommunicator()

class FileDocStringGeneratorTest(DocStringGeneratorTest):
    @classmethod
    def setUpClass(cls):
        super(FileDocStringGeneratorTest, cls).setUpClass()
        ConfigManager().set_config("bot", "file")
        ConfigManager().set_config("model", "")
        cls.bot_communicator = FileCommunicator()

if __name__ == '__main__':
    unittest.main()
