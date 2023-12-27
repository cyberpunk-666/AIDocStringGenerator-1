
import unittest
import json
import os
import unittest
from DocStringGenerator.DocstringProcessor import DocstringProcessor
from DocStringGenerator.APICommunicatorv2 import *
from dotenv import load_dotenv

class TestFindSplitPoint(unittest.TestCase):
    
    def setUp(self):

        self.config = {"verbose": False}
        self.test_instance = None

    def test_normal_code(self):
        source_code = "def func1():\n    pass\n\ndef func2():\n    pass\n"
        split_point = self.test_instance.find_split_point(source_code, 3)
        self.assertEqual(split_point, 3)


class BaseDocStringGeneratorTest(unittest.TestCase):

    bot_communicator = None

    @classmethod
    def setUpClass(cls):
        load_dotenv()
        cls.config = {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
            "CLAUDE_API_KEY": os.getenv("CLAUDE_API_KEY"),
            "BARD_API_KEY": os.getenv("BARD_API_KEY"),
            # Add other common configurations here...
        }

    def setUp(self):
        if self.__class__ == BaseDocStringGeneratorTest:
            self.skipTest("Skipping tests in base class")

        # self.api_communicator initialization if necessary
        self.api_communicator = CommunicatorManager(self.config)


if __name__ == '__main__':
    unittest.main()
