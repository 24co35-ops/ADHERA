import subprocess, sys
result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/test_e2e_real.py", "-v", "--tb=short", "-x"],
    capture_output=True, text=True, cwd=".",
    env={**__import__('os').environ, "PYTHONIOENCODING": "utf-8"}
)
print(result.stdout)
if result.stderr:
    print(result.stderr)
sys.exit(result.returncode)
