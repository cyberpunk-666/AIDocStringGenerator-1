import unittest
import tempfile
from unittest.mock import MagicMock, patch
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from pathlib import Path

from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.CodeProcessor import CodeProcessor
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.Utility import *
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.CommunicatorManager import CommunicatorManager
from DocStringGenerator.BaseBotCommunicator import BaseBotCommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.DependencyContainer import DependencyContainer
dependencies = DependencyContainer()
from dotenv import load_dotenv

class TestDocStringGenerator(unittest.TestCase):
    def setUp(self):
        load_dotenv()

        self.config = {
            "path": "./tests/classTest_orig.py",
            "wipe_docstrings": False,
            "verbose": False,
            "bot": "file",
            "include_subfolders": False
        }
        ConfigManager(initial_config=self.config)
        self.communicator = dependencies.resolve("CommunicatorManager")

    def test_result_thread(self):
        def target_function():
            return "Hello, world!"

        task = ResultThread(target=target_function)
        task.start()
        task.join()
        assert task.result == "Hello, world!"

    def test_find_split_point(self):
        source_code = "def function(self):\n    print('Hello, world!')\n\nprint('Goodbye, world!')"
        split_point = dependencies.resolve("CodeProcessor").find_split_point(source_code, 3)
        assert split_point == 2

    def test_split_source_code(self):
        source_code = "def function(self):\n    print('Hello, world!')\n\nprint('Goodbye, world!')"
        part1, part2 = dependencies.resolve("CodeProcessor").split_source_code(source_code, 2)
        assert part1 == "def function(self):\n    print('Hello, world!')\n"
        assert part2 == "\nprint('Goodbye, world!')"
         

    def test_wipe_docstrings(self):
        source_code = "def function(self):\n    \"\"\"\n    This is a function\n    \"\"\"\n    pass\n\nclass MyClass:\n    \"\"\"\n    This is a class\n    \"\"\"    \n    pass"
        response = dependencies.resolve("CodeProcessor").wipe_docstrings(source_code)
        assert response.content == "def function(self):\n    pass\n\nclass MyClass:\n    pass"


    def test_list_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files in the temporary directory
            file1 = Path(tmpdir, "file1.py")
            file1.write_text("print('File 1')")
            file2 = Path(tmpdir, "file2.py")
            file2.write_text("print('File 2')")

            # Call the method under test
            files = dependencies.resolve("CodeProcessor").list_files(Path(tmpdir), ".py")

            # Assertions
            self.assertEqual(len(files), 2)
            self.assertIn(Path(tmpdir, "file1.py"), files)
            self.assertIn(Path(tmpdir, "file2.py"), files)

    def test_load_prompt(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            prompt_file = Path(tmpdir, "test_prompt.txt")
            prompt_file.write_text("This is a test prompt")
            prompt = Utility.load_prompt("test_prompt", tmpdir)
            assert prompt == "This is a test prompt"


    def test_is_file_processed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file_path = Path(tmpdir) / "test_log.txt"
            log_file_path.write_text("file1.py\nfile2.py")
            assert dependencies.resolve("CodeProcessor").is_file_processed("file1.py", log_file_path)
            assert dependencies.resolve("CodeProcessor").is_file_processed("file2.py", log_file_path)
            assert not dependencies.resolve("CodeProcessor").is_file_processed("file3.py", log_file_path)

if __name__ == '__main__':
    unittest.main()
