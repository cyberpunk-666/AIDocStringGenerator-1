import unittest
import os
import sys
import tempfile
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from DocStringGenerator.FileProcessor import FileProcessor
from dotenv import load_dotenv

class test_addExampleFunctionsToClasses(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.config = {"verbose": False}
        # Create a temporary file to use for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w+')
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
        success, _ = FileProcessor(self.config).add_example_functions_to_classes(self.file_path, examples, config)
        self.assertTrue(success)

        with open(self.file_path, 'r') as file:
            content = file.read()
        lines = content.splitlines()
        self.assertIn("def example_function_TestClass(self):", lines[5])
        self.assertIn("print('Hello, World!')", lines[6])

    def test_append_function_nonexistent_class(self):
        examples = {"NonExistentClass": "print('This should not work')"}
        config = {"verbose": False}
        success, failed_class_names = FileProcessor(self.config).add_example_functions_to_classes(self.file_path, examples, config)
        self.assertFalse(success)
        self.assertIn("NonExistentClass", failed_class_names)    

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
        success, _ = FileProcessor(self.config).add_example_functions_to_classes(self.file_path, examples, config)
        self.assertTrue(success)

        with open(self.file_path, 'r') as file:
            content = file.read()
        lines = content.splitlines()
        self.assertIn("def example_function_TestClass(self):", content)
        self.assertIn("def example_function_AnotherTestClass(self):", content)

    def test_append_complex_code_snippet(self):
        examples = {"TestClass": "for i in range(5):\n    print(i)"}
        config = {"verbose": False}
        success, _ = FileProcessor(self.config).add_example_functions_to_classes(self.file_path, examples, config)
        self.assertTrue(success)

        with open(self.file_path, 'r') as file:
            content = file.read()
        self.assertIn("for i in range(5):", content)
        self.assertIn("print(i)", content)


    def test_invalid_python_code(self):
        examples = {"TestClass": "if True print('Missing colon')"}
        config = {"verbose": False}
        success, _ = FileProcessor(self.config).add_example_functions_to_classes(self.file_path, examples, config)
        self.assertFalse(success)

        with open(self.file_path, 'r') as file:
            content = file.read()
        self.assertNotIn("if True print('Missing colon')", content)

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
        success, _ = FileProcessor(self.config).add_example_functions_to_classes(self.file_path, examples, config)
        self.assertTrue(success)

        with open(self.file_path, 'r') as file:
            content = file.read()
        self.assertIn("def example_function_InnerClass(self):", content)
        self.assertIn("print('Hello from InnerClass')", content)

    def test_empty_file(self):
        # Overwrite the file with an empty content
        with open(self.file_path, 'w') as file:
            file.write("")

        examples = {"TestClass": "print('Hello from TestClass')"}
        config = {"verbose": False}
        success, failed_class_names = FileProcessor(self.config).add_example_functions_to_classes(self.file_path, examples, config)
        self.assertFalse(success)
        self.assertIn("TestClass", failed_class_names)

    def test_append_multiline_function(self):
        # Define a multi-line function example
        multiline_example = """
if True:
    for i in range(3):
        print(f"Line {i}")
    print("End of multi-line example")
"""
        examples = {"TestClass": multiline_example}
        config = {"verbose": False}

        # Append the multi-line function to TestClass
        success, _ = FileProcessor(self.config).add_example_functions_to_classes(self.file_path, examples, config)
        self.assertTrue(success)

        # Read and check the modified file content
        with open(self.file_path, 'r') as file:
            content = file.read()

        # Check for specific lines in the multi-line function
        self.assertIn("def example_function_TestClass(self):", content)
        self.assertIn("for i in range(3):", content)
        self.assertIn("print(f\"Line {i}\")", content)
        self.assertIn("print(\"End of multi-line example\")", content)        