import unittest
import tempfile
from pathlib import Path
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from dotenv import load_dotenv

class TestInsertDocstrings(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w')
        self.file_path = Path(self.temp_file.name)
        self.config = {"verbose": True}

    def test_insert_docstrings(self):
        self.temp_file.write("""
class MyClass:
    def method_one(self):
        pass
    def method_two(self):
        pass
""")
        self.temp_file.close()
        docstrings = {
            "MyClass": {
                "docstring": "This is a class",
                "methods": {
                    "method_one": "This is a function"
                }
            }
        }
        modified_content = DocstringProcessor(self.config).insert_docstrings(self.file_path, docstrings)

        expected_content = """
class MyClass:
    \"\"\"This is a class\"\"\"
    def method_one(self):
        \"\"\"This is a function\"\"\"
        pass
    def method_two(self):
        pass
"""
        self.assertEqual(modified_content.strip(), expected_content.strip())

    def test_multiple_methods_in_class(self):
        self.temp_file.write("""
class MyClass:
    def method_one(self):
        pass
    def method_two(self):
        pass
""")
        self.temp_file.close()

        docstrings = {
            "MyClass": {
                "docstring": "This is a class",
                "methods": {
                    "method_one": "Comment for method_one",
                    "method_two": "Comment for method_two"
                }
            }
        }
        modified_content = DocstringProcessor(self.config).insert_docstrings(self.file_path, docstrings)
        
        self.assertIn("\"\"\"Comment for method_one\"\"\"", modified_content)
        self.assertIn("\"\"\"Comment for method_two\"\"\"", modified_content)

    def test_no_matches(self):
        self.temp_file.write("""
class MyClass:
    def my_method(self):
        pass
""")
        self.temp_file.close()

        docstrings = {"NonExistentMethod": {"docstring": "Comment for NonExistentMethod"}}
        DocstringProcessor(self.config).insert_docstrings(self.file_path, docstrings)

        with open(self.file_path, 'r') as file:
            modified_content = file.read()

        self.assertNotIn("Comment for NonExistentMethod", modified_content)

    def test_different_indentation_styles(self):
        self.temp_file.write("""
class MyClass:
\tdef my_method(self):
\t\tpass
""")
        self.temp_file.close()

        docstrings = {
            "MyClass": {
                "docstring": "Comment for MyClass"
            }
        }  
        DocstringProcessor(self.config).insert_docstrings(self.file_path, docstrings)

        with open(self.file_path, 'r') as file:
            content = file.read()

        self.assertIn("\"\"\"Comment for MyClass\"\"\"", content)

    def test_insert_docstrings3(self):
        mock_content = """
class TestClass:
    def method_one(self):
        pass

def test_function():
    pass
"""

        docstrings = {
            "TestClass": {
                "docstring": "Comment for TestClass"
            },
            "global_functions": {
                "test_function": "Comment for test_function"
            }
        }
        self.temp_file.write(mock_content)
        self.temp_file.close()

        modified_content = DocstringProcessor(self.config).insert_docstrings(self.file_path, docstrings)

        expected_modified_content = """
class TestClass:
    \"\"\"Comment for TestClass\"\"\"
    def method_one(self):
        pass

def test_function():
    \"\"\"Comment for test_function\"\"\"
    pass
"""

        self.assertEqual(modified_content.strip(), expected_modified_content.strip())


    def test_nested_classes(self):
        self.temp_file.write("""
class OuterClass:
    class InnerClass:
        def inner_method(self):
            pass
    """)
        self.temp_file.close()

        docstrings = {
            "OuterClass": {
                "docstring": "Comment for OuterClass"
            },
            "InnerClass": {
                "docstring": "Comment for InnerClass",
                "methods": {
                    "inner_method": "Comment for inner_method"
                }   
            }
        }
        modified_content = DocstringProcessor(self.config).insert_docstrings(self.file_path, docstrings)

        expected_modified_content = """
class OuterClass:
    \"\"\"Comment for OuterClass\"\"\"
    class InnerClass:
        \"\"\"Comment for InnerClass\"\"\"
        def inner_method(self):
            \"\"\"Comment for inner_method\"\"\"
            pass
    """

        self.assertEqual(modified_content.strip(), expected_modified_content.strip())


if __name__ == '__main__':
    unittest.main()
