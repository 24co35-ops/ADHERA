import glob

for f in glob.glob('frontend/*.html'):
    with open(f, 'r', encoding='utf-8') as file:
        c = file.read()
    
    c = c.replace("'/dashboard.html'", "'dashboard.html'")
    c = c.replace("'/index.html'", "'index.html'")
    c = c.replace("'/provider-dashboard.html'", "'provider-dashboard.html'")
    c = c.replace("'/admin-dashboard.html'", "'admin-dashboard.html'")
    c = c.replace("'/provider-patient.html?id='", "'provider-patient.html?id='")
    
    c = c.replace('href="/dashboard.html"', 'href="dashboard.html"')
    c = c.replace('href="/medicines.html"', 'href="medicines.html"')
    c = c.replace('href="/feedback.html"', 'href="feedback.html"')
    c = c.replace('href="/index.html"', 'href="index.html"')
    c = c.replace('href="/register.html"', 'href="register.html"')
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(c)
