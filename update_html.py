import os

html_dir = 'frontend'

for filename in os.listdir(html_dir):
    if filename.endswith('.html'):
        filepath = os.path.join(html_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        changed = False

        if '<script src="/config.js"></script>' not in content and '<script src="config.js"></script>' not in content:
            content = content.replace('<head>', '<head>\n    <script src="config.js"></script>', 1)
            changed = True
        
        if '"http://localhost:8000/v1"' in content:
            content = content.replace('"http://localhost:8000/v1"', 'CONFIG.API_BASE')
            changed = True
        if "'http://localhost:8000/v1'" in content:
            content = content.replace("'http://localhost:8000/v1'", 'CONFIG.API_BASE')
            changed = True
        
        if '"http://localhost:8000"' in content:
            content = content.replace('"http://localhost:8000"', 'CONFIG.API_BASE.replace("/v1", "")')
            changed = True
        
        if "'http://localhost:8000'" in content:
            content = content.replace("'http://localhost:8000'", 'CONFIG.API_BASE.replace("/v1", "")')
            changed = True

        if changed:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {filename}")
