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
    pattern = r'\{((?:[^{}]+|{(?:[^{}]+)*})*)\}'
    matches = re.findall(pattern, input_string, re.DOTALL)
    json_objects = []

    for match in matches:
        try:
            # Convert the matched string to a JSON object
            json_obj = json.loads('{' + match + '}')
            json_objects.append(json_obj)
        except json.JSONDecodeError:
            # Handle the case where the string is not a valid JSON
            continue

    return json_objects
    
def validate_response(response):
    try:
        json_str = extract_json(response)
        data = json.loads(json_str)

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