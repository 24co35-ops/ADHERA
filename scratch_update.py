import os
import re

ROUTERS_DIR = "app/routers"

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Skip auth.py, doses.py, feedback.py since they are already done
    if any(x in filepath for x in ['auth.py', 'doses.py', 'feedback.py', '__init__.py', '__pycache__']):
        return
    
    if "SuccessResponse" in content:
        return

    print(f"Processing {filepath}...")
    
    # 1. Add import SuccessResponse
    import_match = re.search(r'^from fastapi .*', content, re.MULTILINE)
    if import_match:
        content = content[:import_match.end()] + "\nfrom app.core.responses import SuccessResponse" + content[import_match.end():]
    else:
        content = "from app.core.responses import SuccessResponse\n" + content

    # 2. Update decorators
    # @router.get(...) -> @router.get(..., response_model=SuccessResponse[list/dict])
    # This is tricky without knowing the return type. We can use `Any` if we don't know, or try to infer.
    # Actually, we can just omit `response_model` or set it to `SuccessResponse[Any]`. Let's use `SuccessResponse[Any]`.
    content = content.replace("from typing import List", "from typing import List, Any")
    
    # If it doesn't have Any imported
    if "from typing import Any" not in content and "from typing import" in content:
        content = content.replace("from typing import", "from typing import Any,")
    elif "from typing import" not in content:
        content = "from typing import Any\n" + content
    
    # Replace return statements
    # `return response.data` -> `return SuccessResponse(data=response.data)`
    # `return {"message": ...}` -> `return SuccessResponse(data={"message": ...})`
    # We will use regex to find `return <expr>`
    content = re.sub(r'^[ \t]*return\s+(.+)$', r'    return SuccessResponse(data=\1)', content, flags=re.MULTILINE)
    
    with open(filepath, 'w') as f:
        f.write(content)

for root, _, files in os.walk(ROUTERS_DIR):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))
