import unittest
import ast
from DocStringGenerator.FileProcessor import FileProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
dependencies = DependencyContainer()

# Assuming APIResponse and DocstringRemover are defined elsewhere in your code
# from your_module import APIResponse, DocstringRemover, wipe_docstrings

class TestWipeDocstrings(unittest.TestCase):
    def setUp(self) -> None:
        self.file_processor: FileProcessor = dependencies.resolve("FileProcessor")

    def test_remove_docstrings(self):
        source = '''
class MyClass:
    """Class docstring"""
    def my_method(self):
        """Method docstring"""
        pass
'''
        expected = '''
class MyClass:
    def my_method(self):
        pass
'''
        response = self.file_processor.wipe_docstrings(source)
        self.assertTrue(response.is_valid)
        self.assertEqual(response.content, ast.unparse(ast.parse(expected)))

    def test_no_docstrings(self):
        source = '''
class MyClass:
    def my_method(self):
        pass
'''
        response = self.file_processor.wipe_docstrings(source)
        self.assertTrue(response.is_valid)
        self.assertEqual(response.content, ast.unparse(ast.parse(source)))

    def test_invalid_python_code(self):
        source = '''
class MyClass
    def my_method(self):
        pass
'''
        response = self.file_processor.wipe_docstrings(source)
        self.assertFalse(response.is_valid)
        self.assertIn("Invalid Python code:", response.error_message)

if __name__ == '__main__':
    unittest.main()
