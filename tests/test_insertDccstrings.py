import unittest
import tempfile
from pathlib import Path
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
from dotenv import load_dotenv

dependencies = DependencyContainer()
class TestInsertDocstrings(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        # Create a temporary file for testing
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.py', mode='w')
        self.file_path = Path(self.temp_file.name)
        dependencies.resolve(DocstringProcessor)
        # self.config = {"verbose": True}

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
        # read content of file
        with open(self.file_path, 'r') as file:
            content = file.read()
        modified_response = dependencies.resolve(DocstringProcessor).insert_docstrings(content, docstrings)

        expected_content = """
class MyClass:
    \"\"\"This is a class\"\"\"
    def method_one(self):
        \"\"\"This is a function\"\"\"
        pass
    def method_two(self):
        pass
"""
        self.assertEqual(modified_response.strip(), expected_content.strip())

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
        with open(self.temp_file.name, 'r') as file:
            content = file.read()        
        modified_response = dependencies.resolve(DocstringProcessor).insert_docstrings(content, docstrings)

        
        self.assertIn("\"\"\"Comment for method_one\"\"\"", modified_response)
        self.assertIn("\"\"\"Comment for method_two\"\"\"", modified_response)

    def test_no_matches(self):
        self.temp_file.write("""
class MyClass:
    def my_method(self):
        pass
""")
        self.temp_file.close()

        docstrings = {"NonExistentMethod": {"docstring": "Comment for NonExistentMethod"}}
        with open(self.temp_file.name, 'r') as file:
            content = file.read()         
        dependencies.resolve(DocstringProcessor).insert_docstrings(content, docstrings)

        with open(self.temp_file.name, 'r') as file:
            content = file.read()

        self.assertNotIn("Comment for NonExistentMethod", content)

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
        with open(self.temp_file.name, 'r') as file:
            content = file.read()          
        new_content = dependencies.resolve(DocstringProcessor).insert_docstrings(content, docstrings)

        self.assertIn("\"\"\"Comment for MyClass\"\"\"", new_content)

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
        with open(self.temp_file.name, 'r') as file:
            content = file.read() 
        modified_response = dependencies.resolve(DocstringProcessor).insert_docstrings(content, docstrings)


        expected_response = """
class TestClass:
    \"\"\"Comment for TestClass\"\"\"
    def method_one(self):
        pass

def test_function():
    \"\"\"Comment for test_function\"\"\"
    pass
"""

        self.assertEqual(modified_response.strip(), expected_response.strip())


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
        with open(self.temp_file.name, 'r') as file:
            content = file.read()         
        modified_response = dependencies.resolve(DocstringProcessor).insert_docstrings(content, docstrings)


        expected_response = """
class OuterClass:
    \"\"\"Comment for OuterClass\"\"\"
    class InnerClass:
        \"\"\"Comment for InnerClass\"\"\"
        def inner_method(self):
            \"\"\"Comment for inner_method\"\"\"
            pass
    """

        self.assertEqual(modified_response.strip(), expected_response.strip())

    def test_multi_line_docstrings(self):
        self.temp_file.write("""
class MyClass:
    def my_method(self):
        pass
""")
        self.temp_file.close()

        multi_line_docstring = "This is a multi-line docstring.\\nIt spans multiple lines and describes the class or method."

        docstrings = {
            "MyClass": {
                "docstring": multi_line_docstring
            }
        }
        with open(self.temp_file.name, 'r') as file:
            content = file.read()         
        modified_response = dependencies.resolve(DocstringProcessor).insert_docstrings(content, docstrings)


        expected_content = """
class MyClass:
    \"\"\"
    This is a multi-line docstring.
    It spans multiple lines and describes the class or method.
    \"\"\"
    def my_method(self):
        pass
"""
        self.assertEqual(modified_response.strip(), expected_content.strip())



if __name__ == '__main__':
    unittest.main()
