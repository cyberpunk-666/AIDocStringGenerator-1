import unittest
import tempfile
from unittest.mock import MagicMock, patch
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from pathlib import Path
from dotenv import load_dotenv

from DocStringGenerator.APICommunicator import APICommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.FileProcessor import FileProcessor
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.Utility import *


class TestFindSplitPoint(unittest.TestCase):
    
    def setUp(self):
        load_dotenv()
        self.config = {"verbose": False}
        self.test_instance = FileProcessor(self.config)
        

    def test_normal_code(self):
        source_code = "def func1():\n    pass\n\ndef func2():\n    pass\n"
        split_point = self.test_instance.find_split_point(source_code, 3)
        self.assertEqual(split_point, 3)  # Assuming the split point should be at the beginning

    def test_code_with_classes_and_functions(self):
        source_code = "class MyClass:\n    def method(self):\n        pass\n\ndef func():\n    pass\n"
        split_point = self.test_instance.find_split_point(source_code)
        self.assertEqual(split_point, 6) 

    def test_long_code_exceeding_max_length(self):
        source_code = "class test:"
        source_code += "x = 1\n" * 1000
        source_code += "class test2:"
        source_code += "x = 1\n" * 1000
        split_point = self.test_instance.find_split_point(source_code, max_lines=len("x = 1\n")*1200)
        self.assertLessEqual(split_point, 1001)  # Split point should respect the max_length

    def test_code_with_syntax_error(self):
        source_code = "def func1():\n    pass\n\ndef func2():\n    pass\n\nif x = 5: pass\n"
        split_point = self.test_instance.find_split_point(source_code)
        self.assertTrue(split_point > 0)  # Split point should be greater than 0 despite the syntax error

    # You can add more test cases for different scenarios

if __name__ == '__main__':
    unittest.main()
