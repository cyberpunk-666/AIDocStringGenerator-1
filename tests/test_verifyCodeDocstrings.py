import unittest
import ast
import os
import sys
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
dependencies = DependencyContainer()        

# Assuming your APIResponse and DocstringChecker classes are defined above

class TestVerifyCodeDocstrings(unittest.TestCase):

    def setUp(self):
        self.code_processor: CodeProcessor = dependencies.resolve("CodeProcessor")        
        # Setup that runs before each test
        self.function_to_test = self.code_processor.verify_code_docstrings

    def test_valid_code_with_docstrings(self):
        source = '''
def example():
    """This is a docstring."""
    pass
        '''
        response = self.function_to_test(source)
        self.assertTrue(response.is_valid)
        self.assertEqual(response.error_message, "All functions have docstrings.")

    def test_valid_code_without_docstrings(self):
        source = '''
def example():
    pass
        '''
        response = self.function_to_test(source)
        self.assertFalse(response.is_valid)
        self.assertIn("example", response.content)
        self.assertIn("Functions without docstrings", response.error_message)

    def test_invalid_code(self):
        source = '''
def example(
        '''
        response = self.function_to_test(source)
        self.assertFalse(response.is_valid)
        self.assertEqual(response.content, "")
        self.assertIn("Invalid Python code", response.error_message)

# More tests can be added here for different scenarios

if __name__ == '__main__':
    unittest.main()
