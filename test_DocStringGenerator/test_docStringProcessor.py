import unittest
import json
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(f"{parent}")
from DocStringGenerator.DocstringProcessor import DocstringProcessor

SAMPLE_JSON_1 = json.dumps({
    "docstrings": {
        "APICommunicator": {
            "docstring": "Handles communication with API services.",
            "ask_claude": "Sends prompt to Claude API."
        }
    },
    "examples": {
        "example_APICommunicator": "api_com = APICommunicator(config)"
    }
})

SAMPLE_JSON_2 = json.dumps({
    "docstrings": {
        "DocstringProcessor": {
            "docstring": "Processes docstrings from raw API response.",
            "insert_docstrings": "Inserts docstrings into source code."
        }
    },
    "examples": {
        "example_DocstringProcessor": "processor = DocstringProcessor(config)"
    }
})


class TestDocstringProcessor(unittest.TestCase):

    def setUp(self):
        self.processor = DocstringProcessor(config={"verbose": False})

    def test_validate_response(self):
        responses = [SAMPLE_JSON_1, SAMPLE_JSON_2]
        self.assertTrue(self.processor.validate_response(responses))

    def test_merge_json_objects(self):
        json_objects = [json.loads(SAMPLE_JSON_1), json.loads(SAMPLE_JSON_2)]
        merged = self.processor.merge_json_objects(json_objects)
        self.assertIn("APICommunicator", merged["docstrings"])
        self.assertIn("DocstringProcessor", merged["docstrings"])

    def test_extract_docstrings(self):
        responses = [SAMPLE_JSON_1, SAMPLE_JSON_2]
        docstrings, examples, is_valid = self.processor.extract_docstrings(responses, {"verbose": False})
        self.assertTrue(is_valid)
        self.assertIn("APICommunicator", docstrings)
        self.assertIn("example_APICommunicator", examples)


# Add more tests as needed

if __name__ == '__main__':
    unittest.main()
