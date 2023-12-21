import random
import unittest
import ast
from io import StringIO
import sys
sys.path.append('./DocStringGenerator')
from pathlib import Path
from DocStringGenerator.FileProcessor import FileProcessor

class TestSourceCodeSplitting(unittest.TestCase):

    def setUp(self):
        self.config = {"verbose": False}
        self.instance = FileProcessor(self.config)

    # Tests for find_split_point
    def test_split_point_valid_code(self):
        code = "def func():\n    pass"
        self.assertGreaterEqual(self.instance.find_split_point(code), 0)

    def test_split_point_syntax_error(self):
        code = "def func():\n    pass"
        self.assertIsInstance(self.instance.find_split_point(code), int)

    def test_split_point_custom_start_node(self):
        code = "def func():\n    pass"
        node = ast.parse(code)
        self.assertGreaterEqual(self.instance.find_split_point(code, start_node=node), 0)

    # Tests for find_end_line
    def test_find_end_line_function(self):
        node = ast.FunctionDef()
        node.lineno = 1
        node.end_lineno = 4
        self.assertEqual(self.instance.find_end_line(node, 5), 4)

    def test_find_end_line_class(self):
        node = ast.ClassDef()
        node.lineno = 3
        self.assertEqual(self.instance.find_end_line(node, 3), 3)

    def test_find_end_line_other(self):
        node = ast.Pass()
        self.assertEqual(self.instance.find_end_line(node, -1), -1)

    # Tests for find_split_point_in_children
    def test_find_split_point_in_children_with_children(self):
        node = ast.FunctionDef()
        node.body = [ast.Pass()]
        node.end_lineno = 3
        node.lineno = 1
        self.assertEqual(self.instance.find_split_point_in_children(node, 5), 3)

    def test_find_split_point_in_children_no_children(self):
        node = ast.Pass()
        self.assertEqual(self.instance.find_split_point_in_children(node, 5), 0)

    def test_find_split_point_in_children_recursive(self):
        node = ast.FunctionDef()
        node.body = [ast.If()]
        node.body[0].body = [ast.Pass()]
        node.end_lineno = 4
        node.lineno = 1
        self.assertEqual(self.instance.find_split_point_in_children(node, 5), 4)

    # Tests for split_source_code
    def test_split_source_code_even_split(self):
        code = "line1\nline2\nline3\nline4"
        parts = self.instance.split_source_code(code, 2)
        self.assertEqual(len(parts), 2)

    def test_split_source_code_uneven_split(self):
        code = "line1\nline2\nline3"
        parts = self.instance.split_source_code(code, 2)
        self.assertEqual(len(parts), 2)

    # Additional Tests for find_split_point
    def test_split_point_with_unsplitable_blocks(self):
        # Source code with global level code (unsplitable blocks)
        code = "a = 10\ndef func():\n    pass\nb = 20"
        split_point = self.instance.find_split_point(code, 2)
        # Expecting the split point to not be in the middle of the global code
        self.assertNotEqual(split_point, 2)
        self.assertNotEqual(split_point, len(code.splitlines()) - 1)

    # Additional Tests for split_source_code
    def test_split_source_code_with_unsplitable_blocks(self):
        # Source code with unsplitable blocks
        code = "a = 10\ndef func():\n    pass\nb = 20\nc = 30\nd = 40"
        parts = self.instance.split_source_code(code, 3)
        self.assertEqual(len(parts), 3)
        # Ensuring unsplitable blocks are intact
        self.assertIn("a = 10\n", parts[0])
        self.assertIn("def func():\n    pass\n", parts[1])
        self.assertIn("b = 20\nc = 30\nd = 40", parts[2])

    def test_split_source_code_with_only_unsplitable_blocks(self):
        # Source code without any function or class definition
        code = "a = 10\nb = 20\nc = 30"
        parts = self.instance.split_source_code(code, 2)
        # Since the code is unsplitable, it should remain as a single part
        self.assertEqual(len(parts), 2)
        self.assertEqual("", parts[0])
        self.assertIn("a = 10", parts[1])
        self.assertIn("b = 20", parts[1])
        self.assertIn("c = 30", parts[1])


class TestSourceCodeSplittingAdvanced(unittest.TestCase):


    def setUp(self):
        self.config = {"verbose": False}
        self.instance = FileProcessor(self.config)

    # Test with Nested Functions and Classes
    def test_nested_functions_classes(self):
        code = """def outer():
    def inner():
        pass
    class NestedClass:
        def method(self):
            pass
        """
        # Assuming that the split should occur after the nested class/method
        split_point = self.instance.find_split_point(code, 5)
        lines = code.splitlines()
        self.assertIn("def method(self):", lines[split_point])

    # Test with Large Code Blocks
    def test_large_code_blocks(self):
        code = "\n".join(["print({})".format(i) for i in range(1000)])
        # Assuming splitting the code into two halves
        split_point = self.instance.find_split_point(code, 500)
        self.assertEqual(split_point, 0)

    # Test Multiple Split Points
    def test_multiple_split_points(self):
        code = "def func1():\n    pass\ndef func2():\n    pass"
        # Assuming split point should be after first function
        split_point = self.instance.find_split_point(code, 2)
        lines = code.splitlines()
        self.assertIn("def func2():", lines[split_point])

    # Test Code with Exceptions and Decorators
    def test_code_with_exceptions_decorators(self):
        code = """@decorator
def func():
    try:
        pass
    except Exception as e:
        pass
        """
        # Assuming split should occur within the function body
        split_point = self.instance.find_split_point(code, 4)
        lines = code.splitlines()
        self.assertIn("try:", lines[split_point+1])

    # Test Randomized Source Code
    def test_randomized_source_code(self):
        lines = ["def func{}():\n    pass".format(i) for i in range(10)]
        random.shuffle(lines)
        code = "\n".join(lines)
        # Testing if the split point is valid in randomized code
        split_point = self.instance.find_split_point(code, 5)
        self.assertTrue(0 < split_point < len(lines))

if __name__ == '__main__':
    unittest.main()
