import os
import glob

def patch_file(filepath, expected_role):
    with open(filepath, 'r') as f:
        content = f.read()

    # check if already patched
    if "JSON.parse(atob(this.token.split('.')[1])).role" in content:
        return

    redirect_logic = f"""
                    const payload = JSON.parse(atob(this.token.split('.')[1]));
                    if (payload.role !== '{expected_role}') {{
                        if (payload.role === 'patient') return window.location.href = 'dashboard.html';
                        if (payload.role === 'provider') return window.location.href = 'provider-dashboard.html';
                        if (payload.role === 'admin') return window.location.href = 'admin-dashboard.html';
                        return window.location.href = 'index.html';
                    }}"""
    
    # Insert after `if (!this.token) return window.location.href = 'index.html';`
    target = "if (!this.token) return window.location.href = 'index.html';"
    
    if target in content:
        new_content = content.replace(target, target + redirect_logic)
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Patched {filepath} for role {expected_role}")

patch_file("frontend/dashboard.html", "patient")
patch_file("frontend/medicines.html", "patient")
patch_file("frontend/feedback.html", "patient")
patch_file("frontend/provider-dashboard.html", "provider")
patch_file("frontend/provider-patient.html", "provider")
patch_file("frontend/admin-dashboard.html", "admin")
