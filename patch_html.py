import os
import re

files = [
    'index.html',
    'register.html',
    'dashboard.html',
    'medicines.html',
    'feedback.html',
    'provider-dashboard.html',
    'provider-patient.html',
    'admin-dashboard.html'
]

with open('frontend/partials/logo.html', 'r') as f:
    logo_svg = f.read().strip()

# Wrap the SVG in a container that scales it down for nav/headers without altering the SVG itself.
auth_logo_html = f'''<div class="flex justify-center w-full mb-4" style="height: 60px;">
    <div style="transform: scale(0.3); transform-origin: center;">
        {logo_svg}
    </div>
</div>'''

nav_logo_html = f'''<a href="dashboard.html" class="flex items-center" style="height: 40px; overflow: visible;">
    <div style="transform: scale(0.25); transform-origin: left center; width: 50px;">
        {logo_svg}
    </div>
    <span style="color: #00dbe7; font-weight: 700; font-size: 1.5rem; letter-spacing: -0.02em;">Adhera</span>
</a>'''

new_style = '''    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        body { background: #111318; color: #e2e2e8; font-family: 'Inter', sans-serif; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(24px); border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 24px; }
        input, select, textarea { background: rgba(255, 255, 255, 0.05) !important; border: 1px solid rgba(255, 255, 255, 0.12) !important; color: #e2e2e8 !important; border-radius: 12px !important; }
        input:focus, select:focus, textarea:focus { outline: none !important; border-color: #00dbe7 !important; }
        button[type="submit"], button.bg-cyan-600 { background: #00dbe7 !important; color: #002022 !important; border-radius: 12px !important; }
        button.bg-slate-700 { background: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.12) !important; border-radius: 12px !important; }
        [x-cloak] { display: none !important; }
    </style>'''

for fname in files:
    path = os.path.join('frontend', fname)
    if not os.path.exists(path): continue
    
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Replace styles
    content = re.sub(r'<style>.*?</style>', new_style, content, flags=re.DOTALL)
    
    # 2. Add font link if missing
    if 'fonts.googleapis.com' not in content:
        # Added inside style above
        pass
    
    # 3. Logo replacements
    if fname in ['index.html', 'register.html']:
        content = re.sub(r'<h1 class="text-3xl font-bold mb-6 text-cyan-400 text-center">Adhera</h1>', auth_logo_html, content)
    else:
        # Replace nav branding
        content = re.sub(r'<a href=".*?" class="text-xl font-bold text-cyan-400">Adhera.*?</a>', nav_logo_html, content)
        content = re.sub(r'<div class="text-xl font-bold text-cyan-400">Adhera.*?</div>', nav_logo_html, content)
        content = re.sub(r'<a href="#" class="text-xl font-bold text-cyan-400">Adhera.*?</a>', nav_logo_html, content)
    
    # 4. Color replacements for generic Tailwind classes
    content = content.replace('bg-slate-800', 'bg-transparent')
    content = content.replace('border-slate-700', 'border-transparent')
    content = content.replace('bg-slate-900', 'bg-transparent')
    content = content.replace('text-cyan-400', '') # Remove conflicting text colors, managed by CSS or inline
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
