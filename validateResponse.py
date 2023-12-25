import json
import re
from json.decoder import JSONDecodeError

# def extract_json(input_string):
#     # Pattern to match JSON object - starting with '{' and ending with '}'
#     pattern = r'^\{((?:[^{}]+|{(?:[^{}]+)*})*)\}'

#     # Searching for the pattern in the input string
#     match = re.search(pattern, input_string, re.DOTALL)

#     # If a match is found, return it
#     if match:
#         return match.group()
#     else:
#         return "{}"
    
def extract_json(input_string):
    json_strings = []
    brace_count = 0
    in_string = False
    escape = False
    start_index = None

    for i, char in enumerate(input_string):
        if char == '"' and not escape:
            in_string = not in_string
        elif char == '\\' and in_string:
            escape = not escape
            continue
        elif char == '{' and not in_string:
            brace_count += 1
            if brace_count == 1:
                start_index = i
        elif char == '}' and not in_string:
            brace_count -= 1
            if brace_count == 0 and start_index is not None:
                json_strings.append(input_string[start_index:i+1])
                start_index = None
        if char != '\\':
            escape = False

    return json_strings


def parse_json(json_strings):
    json_objects = []
    is_valid = True

    for json_str in json_strings:
        try:
            json_obj = json.loads(json_str)
            json_objects.append(json_obj)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {json_str}\nError: {e}")
            is_valid = False

    return json_objects, is_valid
    
def validate_response(response):
    try:
        json_str = extract_json(response)
        data = parse_json(json_str)

        if not isinstance(data["docstrings"], dict):
            return False
            
        keys = set(data.keys())
        if len(keys) != 2: 
            return False
    except (JSONDecodeError, KeyError):
        return False
    return True


response = """Some text
{
    "docstrings": {
        "test": "This is a test function"
    },
    "example": "result = test()\\nprint(result)"
}
More text
"""

print(validate_response(response))