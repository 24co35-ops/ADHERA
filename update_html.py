import os, re, glob

def process():
    files = glob.glob('frontend/**/*.html', recursive=True)
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        orig_content = content
        
        # 1. Ensure config.js is the first script tag
        if 'src="config.js"' not in content and 'src="/config.js"' not in content and 'src="../config.js"' not in content:
            # Add correct relative path
            depth = f.count(os.sep) - 1 # frontend/ is depth 0
            if '/' in f:
                depth = f.count('/') - 1
            
            prefix = '../' * depth if depth > 0 else ''
            config_tag = f'<script src="{prefix}config.js"></script>'
            
            first_script_idx = content.find('<script')
            if first_script_idx != -1:
                content = content[:first_script_idx] + config_tag + '\n    ' + content[first_script_idx:]
            else:
                # insert in head
                head_end_idx = content.find('</head>')
                if head_end_idx != -1:
                    content = content[:head_end_idx] + f'    {config_tag}\n' + content[head_end_idx:]

        # 2. Replace URLs
        content = content.replace('RENDER_URL_PLACEHOLDER/v1', '${CONFIG.API_BASE}')
        content = content.replace('RENDER_URL_PLACEHOLDER', '${CONFIG.API_BASE}')
        content = content.replace('https://adhera-api-xxxx.onrender.com/v1', '${CONFIG.API_BASE}')
        
        content = content.replace('`${config.SUPABASE_URL}/v1', '`${CONFIG.API_BASE}')
        content = content.replace('http://localhost:8000/v1', '${CONFIG.API_BASE}')
        
        if content != orig_content:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            print(f"Updated {f}")

process()
