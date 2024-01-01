import unittest
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from dotenv import load_dotenv
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
dependencies = DependencyContainer()
from pathlib import Path



class TestCodeSplitter(unittest.TestCase):
    
    def setUp(self):
        load_dotenv()
        self.config = {"verbose": False}
        self.code_splitter = dependencies.resolve("CodeProcessor")

    def test_split_simple_code(self):
        code = "line1\nline2\nline3\nline4"
        parts = self.code_splitter.split_source_code(code, 2)
        self.assertEqual(len(parts), 2)
        self.assertIn("", parts[0])
        self.assertIn("line1\nline2\nline3\nline4", parts[1])

    def test_split_source_code_with_functions(self):
        code = "def func1():\n    pass\n\ndef func2():\n    pass\n"
        parts = self.code_splitter.split_source_code(code, 2)
        self.assertEqual(len(parts), 2)
        self.assertIn("def func1():\n    pass\n", parts[0])
        self.assertIn("def func2():\n    pass\n", parts[1])

    def test_split_source_code_single_part(self):
        code = "line1\nline2"
        parts = self.code_splitter.split_source_code(code, 1)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0], code)

    def test_split_empty_code(self):
        code = ""
        parts = self.code_splitter.split_source_code(code, 2)
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "")
        self.assertEqual(parts[1], "")

    def test_split_more_parts_than_code(self):
        code = "line1\nline2"
        parts = self.code_splitter.split_source_code(code, 3)
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], "")
        self.assertEqual(parts[1], "")
        self.assertEqual(parts[2], "line1\nline2")

    def test_split_source_code_complex_structure(self):
        code = (
            "class MyClass:\n"
            "    def method1(self):\n"
            "        pass\n"
            "    def method2(self):\n"
            "        pass\n"
            "def func1():\n"
            "    pass\n"
                                               
        )
        parts = self.code_splitter.split_source_code(code, 3)
        self.assertEqual(len(parts), 3)
        self.assertIn("class MyClass:", parts[0])
        self.assertIn("def method1", parts[1])
        self.assertIn("def func1():", parts[2])

    def test_split_source_code_with_line_limit(self):
        code = "line1\nline2\nline3\nline4\nline5\nline6"
        parts = self.code_splitter.split_source_code(code, 2)
        self.assertEqual(len(parts), 2)
        self.assertTrue(len(parts[0]) == 0)
        self.assertTrue(len(parts[1]) == 35)

    def test_split_source_code_with_only_newlines(self):
        code = "\n\n\n\n"
        parts = self.code_splitter.split_source_code(code, 2)
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0], "")
        self.assertEqual(parts[1], "\n\n\n\n")

    def test_split_source_code_with_unicode_characters(self):
        code = "def func1():\n    print('🙂')\n\ndef func2():\n    print('😀')\n"
        parts = self.code_splitter.split_source_code(code, 2)
        self.assertEqual(len(parts), 2)
        self.assertIn("print('🙂')", parts[0])
        self.assertIn("print('😀')", parts[1])


    def test_split_source_code(self):
        source_code = "def foo():\n    print('Hello, world!')\n\nprint('Goodbye, world!')"
        num_parts = 2
        expected_output = ["def foo():\n    print('Hello, world!')\n", "\nprint('Goodbye, world!')"]
        self.assertEqual(self.code_splitter.split_source_code(source_code, num_parts), expected_output)

        source_code = "def bar():\n    x = 10\n    return x"
        num_parts = 1
        expected_output = ["def bar():\n    x = 10\n    return x"]
        self.assertEqual(self.code_splitter.split_source_code(source_code, num_parts), expected_output)

        source_code = ""
        num_parts = 3
        expected_output = ["","",""]
        self.assertEqual(self.code_splitter.split_source_code(source_code, num_parts), expected_output)

        source_code = "def baz():\n    pass"
        num_parts = 5
        expected_output = ["","def baz():\n    pass","","",""]
        self.assertEqual(self.code_splitter.split_source_code(source_code, num_parts), expected_output)

        source_code = "def qux():\n    print('Qux')"
        num_parts = 0
        expected_output = []
        self.assertEqual(self.code_splitter.split_source_code(source_code, num_parts), expected_output)

        source_code = "def fizz():\n    print('Fizz')\n\nprint('Buzz')"
        num_parts = 4
        expected_output = ["", "def fizz():\n    print('Fizz')\n", "", "\nprint('Buzz')"]
        self.assertEqual(self.code_splitter.split_source_code(source_code, num_parts), expected_output)

        source_code = "def buzz():\n    x = 5\n\ny = 10"
        num_parts = 2
        expected_output = ["def buzz():\n    x = 5\n", "\ny = 10"]
        self.assertEqual(self.code_splitter.split_source_code(source_code, num_parts), expected_output)

if __name__ == '__main__':
    unittest.main()        

if __name__ == '__main__':
    unittest.main()
