import pytest
from playwright.sync_api import Page, expect
import os
import threading
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

# Get absolute path to the frontend directory
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'screenshots')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

PORT = 8089

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)
    def log_message(self, format, *args):
        pass

@pytest.fixture(scope="session", autouse=True)
def local_server():
    with TCPServer(("", PORT), QuietHandler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        yield
        httpd.shutdown()

def file_url(filename):
    return f"http://localhost:{PORT}/{filename}"

def mock_api(page: Page):
    # Route for login
    page.route("**/v1/auth/login", lambda route: route.fulfill(
        json={"success": True, "data": {"access_token": "mock.eyJzdWIiOiAidXNlcjEyMyIsICJ1c2VyX21ldGFkYXRhIjogeyJyb2xlIjogInBhdGllbnQifX0=.token"}, "meta": {"version": "1.0", "timestamp": "now"}}
    ))
    # Route for dashboard data
    page.route("**/v1/doses/upcoming", lambda route: route.fulfill(
        json={"success": True, "data": [{"id": "d1", "scheduled_utc": "2026-06-20T10:00:00Z", "reminders": {"dose_label": "Morning", "medicines": {"name": "Aspirin", "dosage_amount": 100, "dosage_unit": "mg"}}, "snooze_count": 0}], "meta": {}}
    ))
    page.route("**/v1/analytics/dashboard", lambda route: route.fulfill(
        json={"success": True, "data": {"weekly_adherence": 65, "monthly_adherence": 80, "weekly_warning": True}, "meta": {}}
    ))
    page.route("**/v1/feedback/", lambda route, request: route.fulfill(
        json={"success": True, "data": [{"id": "f1", "created_at": "2025-01-01T00:00:00Z", "severity": 4, "description": "Pain"}], "meta": {}}
    ) if request.method == "GET" else route.fulfill(
        json={"success": True, "data": {"id": "f2"}, "meta": {}}
    ))
    import re
    page.route(re.compile(r".*/v1/medicines.*"), lambda route, request: route.fulfill(
        json={"success": True, "data": [{"id": "m1", "name": "Aspirin", "dosage_amount": 100, "dosage_unit": "mg", "route": "oral", "frequency_type": "daily"}], "meta": {}}
    ) if request.method in ["GET", "OPTIONS"] else (route.fulfill(json={"success": True, "data": {"message": "Deleted."}, "meta": {}}) if request.method == "DELETE" else route.fulfill(
        json={"success": True, "data": {"id": "m2"}, "meta": {}}
    )))
    
    page.route("**/v1/provider/patients", lambda route: route.fulfill(
        json={"success": True, "data": [{"patient_id": "p1", "profiles": {"full_name": "patient1", "contact_number": "1234567890"}}], "meta": {}}
    ))
    page.route(re.compile(r".*/v1/admin/users.*"), lambda route: route.fulfill(
        json={"success": True, "data": [{"id": "prov1", "full_name": "Dr. Smith", "email": "dr@demo.com", "role": "provider", "is_active": False}], "meta": {}}
    ))
    page.route("**/v1/admin/assignments", lambda route: route.fulfill(
        json={"success": True, "data": [], "meta": {}}
    ))

def set_mock_session(page: Page, role="patient"):
    import base64, json
    # Mock JWT logic needs payload base64 string
    payload = base64.b64encode(json.dumps({"sub": "user123", "user_metadata": {"role": role}}).encode()).decode()
    token = f"header.{payload}.sig"
    page.add_init_script(f"sessionStorage.setItem('jwt', '{token}'); sessionStorage.setItem('adhera_token', '{token}');")

def test_login(page: Page):
    mock_api(page)
    page.goto(file_url("index.html"))
    page.fill("input[type='email']", "patient1@demo.adhera.app")
    page.fill("input[type='password']", "Demo@1234")
    # Setup route listener to check redirect manually since file:// redirects don't always trigger wait_for_url
    page.click("button[type='submit']")
    page.wait_for_timeout(500) # wait for js
    expect(page.locator("text=Today's Schedule")).to_be_visible(timeout=5000)
    page.screenshot(path=f"{SCREENSHOT_DIR}/index_login.png")

def test_dashboard(page: Page):
    mock_api(page)
    set_mock_session(page)
    page.goto(file_url("dashboard.html"))
    expect(page.locator("text=Aspirin")).to_be_visible()
    # Charts render check (canvas exists)
    expect(page.locator("canvas#weeklyChart")).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/dashboard.png")

def test_register_disclaimer(page: Page):
    mock_api(page)
    page.goto(file_url("register.html"))
    page.fill("input[type='email']", "test@demo.com")
    page.fill("input[type='password']", "Pass123")
    # Disclaimer unchecked by default. Submit should be blocked by browser validation (required).
    # Playwright's click will trigger native validation if we try to click submit, or we can check property.
    is_required = page.locator("input#disclaimer").evaluate("el => el.required")
    assert is_required == True
    page.check("input#disclaimer")
    page.screenshot(path=f"{SCREENSHOT_DIR}/register.png")

def test_medicines(page: Page):
    mock_api(page)
    set_mock_session(page)
    page.goto(file_url("medicines.html"))
    expect(page.locator("text=Aspirin")).to_be_visible()
    # Add medicine
    page.fill("input[x-model='form.name']", "TestMed")
    page.click("form button[type='submit']")
    # Delete medicine
    page.on("dialog", lambda dialog: dialog.accept()) # Auto-accept confirm
    page.click("button:has-text('Delete')")
    page.screenshot(path=f"{SCREENSHOT_DIR}/medicines.png")

def test_feedback_emergency(page: Page):
    mock_api(page)
    set_mock_session(page)
    page.goto(file_url("feedback.html"))
    page.fill("textarea[x-model='form.description']", "Severe pain")
    page.select_option("select[x-model='form.severity']", "4")
    expect(page.locator("text=Warning:")).to_be_visible()
    page.click("button:has-text('Submit')")
    expect(page.locator("h3:has-text('EMERGENCY')")).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/feedback.png")

def test_provider_dashboard(page: Page):
    mock_api(page)
    set_mock_session(page, "provider")
    page.goto(file_url("provider-dashboard.html"))
    expect(page.locator("text=patient1").first).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/provider_dashboard.png")

def test_admin_dashboard(page: Page):
    mock_api(page)
    set_mock_session(page, "admin")
    page.goto(file_url("admin-dashboard.html"))
    expect(page.locator("text=Dr. Smith").first).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/admin_dashboard.png")
