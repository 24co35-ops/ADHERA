import os
import re

TESTS_DIR = "tests"

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # We need to change `data = response.json()`
    # and then usages like `data["id"]` to `data["data"]["id"]`
    # Or simpler: replace `response.json()` with `response.json().get("data", response.json())`
    # That works if they just assign it to a variable! But they might do `response.json()["id"]`.
    
    # A safer hack for tests:
    content = content.replace("response.json()", "response.json().get('data', response.json())")
    
    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk(TESTS_DIR):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))
