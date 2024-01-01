import unittest
import os
import sys
import tempfile
from urllib import response
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.Utility import Utility
from DocStringGenerator.DependencyContainer import DependencyContainer
from dotenv import load_dotenv
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from pathlib import Path

dependencies = DependencyContainer()
class test_addExampleFunctionsToClasses(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.config = {"verbose": False}
        # Create a temporary file to use for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w+')
        
        self.communicator_manager: CommunicatorManager = dependencies.resolve("CommunicatorManager")
        self.docstring_processor: DocstringProcessor = dependencies.resolve("DocstringProcessor")
        self.code_processor: CodeProcessor = dependencies.resolve("CodeProcessor")
        self.bot_communicator: BaseBotCommunicator | None = self.communicator_manager.bot_communicator

        self.file_path = self.temp_file.name
        self.temp_file.write("""
class TestClass:
    def existing_method(self):
        pass
""")
        self.temp_file.close()

    def tearDown(self):
        # Clean up the temporary file after tests
        os.remove(self.file_path)

    def test_append_function_success(self):
        examples = {"TestClass": "print('Hello, World!')"}
        config = {"verbose": False}
        # load file from self.file_path
        code_source = Path(self.file_path).read_text()
        response = self.code_processor.add_example_functions_to_classes(code_source, examples)
        self.assertEqual(response.error_message, "")
        self.assertTrue(response.is_valid)

        lines = response.content.splitlines()
        self.assertIn("def example_function_TestClass(self):", lines[5])
        self.assertIn("print('Hello, World!')", lines[6])

    def test_append_function_nonexistent_class(self):
        examples = {"NonExistentClass": "print('This should not work')"}
        config = {"verbose": False}
        response = self.code_processor.add_example_functions_to_classes(self.file_path, examples)
        self.assertFalse(response.is_valid)
        self.assertIn("NonExistentClass", response.content)    

    def test_append_multiple_classes(self):
        # Add content for multiple classes to the temp file
        with open(self.file_path, 'a') as file:
            file.write("""
class AnotherTestClass:
    def another_method(self):
        pass
""")

        examples = {
            "TestClass": "print('Hello from TestClass')",
            "AnotherTestClass": "print('Hello from AnotherTestClass')"
        }
        config = {"verbose": False}   
        code_source = Path(self.file_path).read_text()     
        response = self.code_processor.add_example_functions_to_classes(code_source, examples)
        self.assertEqual(response.error_message, "")
        self.assertTrue(response.is_valid)

        self.assertIn("def example_function_TestClass(self):", response.content)
        self.assertIn("def example_function_AnotherTestClass(self):", response.content)

    def test_append_complex_code_snippet(self):
        examples = {"TestClass": "for i in range(5):\n    print(i)"}
        config = {"verbose": False}
        code_source = Path(self.file_path).read_text() 
        response = self.code_processor.add_example_functions_to_classes(code_source, examples)
        self.assertEqual(response.error_message, "")
        self.assertTrue(response.is_valid)

        content= response.content
        self.assertIn("for i in range(5):", content)
        self.assertIn("print(i)", content)


    def test_invalid_python_code(self):
        examples = {"TestClass": "if True print('Missing colon')"}
        config = {"verbose": False}
        code_source = Path(self.file_path).read_text()
        response = self.code_processor.add_example_functions_to_classes(code_source, examples)
        self.assertFalse(response.is_valid)

        self.assertNotIn("if True print('Missing colon')", response.content)

    def test_different_indentation_levels(self):
        # Adding a nested class to the test file
        with open(self.file_path, 'a') as file:
            file.write("""
class OuterClass:
    class InnerClass:
        def inner_method(self):
            pass
""")

        examples = {"InnerClass": "print('Hello from InnerClass')"}
        config = {"verbose": False}
        code_source = Path(self.file_path).read_text()
        response = self.code_processor.add_example_functions_to_classes(code_source, examples)
        self.assertEqual(response.error_message, "")
        self.assertTrue(response.is_valid)


        self.assertIn("def example_function_InnerClass(self):", response.content)
        self.assertIn("print('Hello from InnerClass')", response.content)

    def test_empty_file(self):
        # Overwrite the file with an empty content
        with open(self.file_path, 'w') as file:
            file.write("")

        examples = {"TestClass": "print('Hello from TestClass')"}
        config = {"verbose": False}
        code_source = Path(self.file_path).read_text()
        response= self.code_processor.add_example_functions_to_classes(code_source, examples)
        self.assertFalse(response.is_valid)
        self.assertIn("TestClass", response.content)

    def test_append_multiline_function(self):
        # Define a multi-line function example
        multiline_example = 'if True:\\n    for i in range(3):\\n        print(f"Line {i}")\\n        print("End of multi-line example")'        
        examples = {"TestClass": multiline_example}
        config = {"verbose": False}

        # Append the multi-line function to TestClass
        code_source = Path(self.file_path).read_text()
        response = self.code_processor.add_example_functions_to_classes(code_source, examples)
        self.assertEqual(response.error_message, "")
        self.assertTrue(response.is_valid)

        # Check for specific lines in the multi-line function
        self.assertIn("def example_function_TestClass(self):", response.content)
        self.assertIn("for i in range(3):", response.content)
        self.assertIn("print(f\"Line {i}\")", response.content)
        self.assertIn("print(\"End of multi-line example\")", response.content)        

