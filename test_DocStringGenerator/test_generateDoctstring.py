import unittest
import tempfile
from unittest.mock import MagicMock, patch
import sys
sys.path.append('./DocStringGenerator')
from pathlib import Path

from DocStringGenerator.APICommunicator import APICommunicator
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.FileProcessor import FileProcessor
from DocStringGenerator.ConfigManager import ConfigManager
from DocStringGenerator.ResultThread import ResultThread
from DocStringGenerator.Utility import *

class TestDocStringGenerator(unittest.TestCase):
    def setUp(self):
        self.config = {
            "path": "./test_DocStringGenerator/classTest.py",
            "wipe_docstrings": False,
            "verbose": False,
            "bot": "file",
            "include_subfolders": False
        }
        self.communicator = APICommunicator(self.config)

    def test_result_thread(self):
        def target_function():
            return "Hello, world!"

        task = ResultThread(target=target_function)
        task.start()
        task.join()
        assert task.result == "Hello, world!"

    def test_find_split_point(self):
        source_code = "def function(self):\n    print('Hello, world!')\n\nprint('Goodbye, world!')"
        split_point = FileProcessor(self.config).find_split_point(source_code, 3)
        assert split_point == 2

    def test_split_source_code(self):
        source_code = "def function(self):\n    print('Hello, world!')\n\nprint('Goodbye, world!')"
        part1, part2 = FileProcessor(self.config).split_source_code(source_code, 2)
        assert part1 == "def function(self):\n    print('Hello, world!')\n"
        assert part2 == "\nprint('Goodbye, world!')"

    def test_insert_docstrings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir, "test_file.py")
            file_path.write_text("def function(self):\n    pass\n\nclass MyClass:\n    pass\n")
            docstrings = {
                "function": "This is a function",
                "MyClass": "This is a class"
            }

            # Assuming DocstringProcessor is defined elsewhere
            DocstringProcessor(self.config).insert_docstrings(file_path, docstrings)
            with open(file_path, "r") as file:
                content = file.read()

            self.assertEqual(content, 'def function(self):\n    """This is a function"""\n    pass\n\nclass MyClass:\n    """This is a class"""\n    pass')


    @patch('DocStringGenerator.APICommunicator.APICommunicator.ask_claude')
    def test_ask_claude(self, mock_ask_claude):
        # Define a mock response
        mock_response = "I do not have a definitive answer to the meaning of life. As an AI assistant created by Anthropic to be helpful, harmless, and honest, I do not make philosophical claims or judgments. The meaning of life is a profound question that has been contemplated and debated by humans for millennia."

        # Set the mock to return this response
        mock_ask_claude.return_value = mock_response

        # Set up your test conditions
        prompt_template = "What is the answer to {question}?"
        replacements = {"question": "the meaning of life"}
        config = {
            "verbose": False, 
            "claude_api_key": "your_api_key",
            "bot": "claude", 
            "model": "claude-2.1"
        }

        # Call the method under test
        response = APICommunicator(config).ask_claude(prompt_template, replacements, config)

        # Assertions
        self.assertIsInstance(response, str)
        self.assertTrue(response.startswith("I do not have a definitive answer"))


    def test_ask_claude_for_docstrings(self):
        source_code = "def function(self):\n    pass\n\nclass MyClass:\n    pass\n"
        config = {"verbose":False, "claude_api_key": "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","bot":"claude", "model": "claude-2.1"}
        response = APICommunicator(self.config).ask_claude_for_docstrings(source_code, config)
        valid = DocstringProcessor(config).validate_response(response)
        self.assertTrue(valid)        
        
    def test_ask_openai_for_docstrings(self):
        source_code = "def function(self):\n    pass\n\nclass MyClass:\n    pass\n"
        config = {"verbose":False, "openai_api_key": "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","bot":"gpt3.5"}
        response = APICommunicator(self.config).ask_openai_for_docstrings(source_code, config)
        valid = DocstringProcessor(config).validate_response(response)
        self.assertTrue(valid)          

    def test_send_code_in_parts(self):
        source_code = "def function(self):\n    pass\n\nclass MyClass:\n    pass\n"
        config = {"verbose":False, 
                  "bot": "claude", 
                  "claude_api_key":"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"
                }
        response = APICommunicator(self.config).send_code_in_parts(source_code, config)
        docstrings, example, is_valid = DocstringProcessor(self.config).extract_docstrings(response, config)
        self.assertTrue(is_valid)

    def test_extract_docstrings(self):
        response = """Some text\n{\n"docstrings": {\n"test": "This is a test function"\n},\n"example": "result = test()\\nprint(result)"\n}\nMore text"""
        config = {"verbose": False}
        docstrings, example, is_valid = DocstringProcessor(self.config).extract_docstrings(response, config)
        self.assertTrue(is_valid)
        assert isinstance(docstrings, dict)
        assert docstrings == {"test": "This is a test function"}
        assert example == 'result = test()\nprint(result)'
        assert is_valid

    def test_is_file_processed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file_path = Path(tmpdir, "test_log.txt")
            log_file_path.write_text("file1.py\nfile2.py")
            assert FileProcessor(self.config).is_file_processed("file1.py", str(log_file_path))
            assert FileProcessor(self.config).is_file_processed("file2.py", str(log_file_path))
            assert not FileProcessor(self.config).is_file_processed("file3.py", str(log_file_path))

    def test_process_file(self):
            file_path = Path("./test_DocStringGenerator", "classTest.py")
            config = {"verbose": False, "bot": "file"}
            # Read the original contents of the file and store it
            with open(str(file_path), "r") as file:
                original_content = file.read()

            # Process the file
            success = FileProcessor(self.config).process_file(file_path, config)
            
            # Perform assertions
            assert success

            # Read the contents of the proccessed file
            with open(str(file_path), "r") as file:
                content = file.read()

            # Restore the original content
            with open(str(file_path), "w") as file:
                file.write(original_content)

            result_file_path = Path("./test_DocStringGenerator", "classTest-result.py")
            # Read the contents of the result file
            result_path = result_file_path.absolute()
            with open(result_path, "r") as file:
                result = file.read() 
            
            # Perform assertions               
            assert content == result


    def test_wipe_docstrings(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir, "classTest.py")
            file_path.write_text("def function(self):\n    \"\"\"\n    This is a function\n    \"\"\"\n    pass\n\nclass MyClass:\n    \"\"\"\n    This is a class\n    \"\"\"    \n    pass")
            FileProcessor(self.config).wipe_docstrings(Path(file_path))
            with open(str(file_path), "r") as file:
                content = file.read()
            assert content == "def function(self):\n    pass\n\nclass MyClass:\n    pass"



    def test_process_file(self):            
        new_test_script_content = """class Calculator:
    def add(self, x, y):
        return x + y

    def subtract(self, x, y):
        return x - y

    def multiply(self, x, y):
        return x * y

    def divide(self, x, y):
        if y == 0:
            raise ValueError("Cannot divide by zero.")
        return x / y"""

        # New content for the JSON file (docstrings_response.json)
        new_docstrings_response_content = """{
    "docstrings": {
        "Calculator": "Class to perform basic arithmetic operations.",
        "add": "Adds two numbers.",
        "subtract": "Subtracts the second number from the first.",
        "multiply": "Multiplies two numbers.",
        "divide": "Divides the first number by the second."
    },
    "example": "calc = Calculator()\\nresult = calc.add(5, 3)\\nprint(result)"
}
        """

        final_script_with_comments = """class Calculator:
    \"\"\"Class to perform basic arithmetic operations.\"\"\"
    def add(self, x, y):
        \"\"\"Adds two numbers.\"\"\"
        return x + y

    def subtract(self, x, y):
        \"\"\"Subtracts the second number from the first.\"\"\"
        return x - y

    def multiply(self, x, y):
        \"\"\"Multiplies two numbers.\"\"\"
        return x * y

    def divide(self, x, y):
        \"\"\"Divides the first number by the second.\"\"\"
        if y == 0:
            raise ValueError("Cannot divide by zero.")
        return x / y"""
        
        # New file paths
        with tempfile.TemporaryDirectory() as tmpdir:  
            new_test_script_file_path = Path(tmpdir, "new_test_script.py")  
            new_docstrings_response_file_path = Path(tmpdir, "new_docstrings_response.json")  

            # Writing the new contents to the files
            with open(new_test_script_file_path, 'w') as file:
                file.write(new_test_script_content.strip())

            with open(new_docstrings_response_file_path, 'w') as file:
                file.write(new_docstrings_response_content.strip())
            self.config.bot_response_path = str(new_docstrings_response_file_path.absolute())

            success = FileProcessor(self.config).process_file(new_test_script_file_path, self.config)
            self.assertTrue(success)

            with open(new_test_script_file_path, 'r') as file:
                result = file.read()

            self.assertEqual(result, final_script_with_comments)  
            FileProcessor(self.config).removed_from_processed_log(new_test_script_file_path)


    def test_list_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create files in the temporary directory
            file1 = Path(tmpdir, "file1.py")
            file1.write_text("print('File 1')")
            file2 = Path(tmpdir, "file2.py")
            file2.write_text("print('File 2')")

            # Call the method under test
            files = FileProcessor(self.config).list_files(Path(tmpdir), ".py")

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
            assert FileProcessor(self.config).is_file_processed("file1.py", log_file_path)
            assert FileProcessor(self.config).is_file_processed("file2.py", log_file_path)
            assert not FileProcessor(self.config).is_file_processed("file3.py", log_file_path)

if __name__ == '__main__':
    unittest.main()
