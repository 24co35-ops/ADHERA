import os
import re

app_dir = "app"

for root, dirs, files in os.walk(app_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Replace import statements
            new_content = re.sub(
                r"from app\.db\.supabase import supabase_admin( as supabase)?",
                "from app.db.supabase import supabase",
                content
            )
            
            # Also replace any other import combinations
            new_content = re.sub(
                r"from app\.db\.supabase import supabase, supabase_admin",
                "from app.db.supabase import supabase",
                new_content
            )
            new_content = re.sub(
                r"from app\.db\.supabase import supabase_admin, supabase",
                "from app.db.supabase import supabase",
                new_content
            )

            # Replace supabase_admin with supabase
            new_content = new_content.replace("supabase_admin", "supabase")
            
            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Refactored {path}")

print("Refactor complete.")
