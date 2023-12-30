import unittest
from unittest.mock import Mock, patch

def my_function(filename):
    with open(filename, 'r') as f:
        response_text = f.read()
    return response_text

class FileMock:
    def __init__(self, file_content_map):
        self.file_content_map = file_content_map

    def __call__(self, filename, mode='r'):
        file_content = self.file_content_map.get(filename, '')
        mock_file = Mock()
        mock_file.read.return_value = file_content

        # Correctly handle the context manager protocol
        mock_file.__enter__ = lambda _: mock_file
        mock_file.__exit__ = lambda _1, _2, _3, _4: None
        return mock_file

class MyTestCase(unittest.TestCase):
    def test_my_function(self):
        file_content_map = {
            'path/to/file1.txt': 'content1',
            'path/to/file2.txt': 'content2'
        }

        file_mock = FileMock(file_content_map)
        with patch('builtins.open', file_mock):
            result1 = my_function('path/to/file1.txt')
            self.assertEqual(result1, 'content1')

            result2 = my_function('path/to/file2.txt')
            self.assertEqual(result2, 'content2')

if __name__ == '__main__':
    unittest.main()

