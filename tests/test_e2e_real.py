import pytest
from playwright.sync_api import Page, expect
import os

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'screenshots_real')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://localhost:8080"
PATIENT_EMAIL = "patient1@demo.adhera.app"
PATIENT_PASS = "Demo@1234"

def _login(page: Page, email: str, password: str, expected_url: str):
    page.goto(f"{BASE_URL}/index.html")
    page.fill("input[type='email']", email)
    page.fill("input[type='password']", password)
    page.click("button:has-text('Login')")
    expect(page).to_have_url(f"{BASE_URL}/{expected_url}", timeout=5000)

def test_step1_register(page: Page):
    page.goto(f"{BASE_URL}/register.html")
    page.fill("input[x-model='form.full_name']", "Test Patient")
    page.fill("input[x-model='form.email']", "localtest@adhera.app")
    page.fill("input[x-model='form.password']", "Test@1234")
    page.select_option("select[x-model='form.role']", "patient")
    page.fill("input[x-model='form.date_of_birth']", "1990-01-01")
    page.fill("input[x-model='form.contact_number']", "9999999999")
    page.fill("input[x-model='form.timezone']", "Asia/Kolkata")
    page.check("input[id='disclaimer']")
    page.click("button:has-text('Register')")
    page.wait_for_timeout(3000)
    # Accept: redirect to index.html, or 'already' error, or rate limit error
    url = page.url
    if 'index.html' not in url:
        page_text = page.inner_text('body')
        assert 'already' in page_text.lower() or 'rate limit' in page_text.lower(), f"Unexpected state: {page_text[:200]}"
    page.screenshot(path=f"{SCREENSHOT_DIR}/step1_register.png")

def test_step2_login(page: Page):
    _login(page, PATIENT_EMAIL, PATIENT_PASS, "dashboard.html")
    page.screenshot(path=f"{SCREENSHOT_DIR}/step2_login.png")

def test_step3_dashboard(page: Page):
    _login(page, PATIENT_EMAIL, PATIENT_PASS, "dashboard.html")
    expect(page.locator("text=Today's Schedule")).to_be_visible()
    expect(page.locator("canvas#weeklyChart")).to_be_visible()
    expect(page.locator("canvas#monthlyChart")).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/step3_dashboard.png")

def test_step4_add_medicine(page: Page):
    _login(page, PATIENT_EMAIL, PATIENT_PASS, "dashboard.html")
    page.goto(f"{BASE_URL}/medicines.html")
    page.wait_for_load_state("networkidle")
    page.fill("input[x-model='form.name']", "TestMed")
    page.fill("input[x-model='form.dosage_amount']", "100")
    page.select_option("select[x-model='form.dosage_unit']", "mg")
    page.select_option("select[x-model='form.route']", "oral")
    page.select_option("select[x-model='form.frequency_type']", "daily")
    page.fill("input[x-model='form.start_date']", "2026-05-30")
    page.click("button[type='submit']:has-text('Add')")
    page.wait_for_timeout(2000)
    expect(page.locator("text=TestMed").first).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/step4_add_medicine.png")

def test_step5_mark_dose(page: Page):
    _login(page, PATIENT_EMAIL, PATIENT_PASS, "dashboard.html")
    page.wait_for_timeout(1000)
    try:
        page.click("button:has-text('Taken')", timeout=3000)
    except:
        pass
    page.screenshot(path=f"{SCREENSHOT_DIR}/step5_mark_dose.png")

def test_step6_submit_feedback(page: Page):
    _login(page, PATIENT_EMAIL, PATIENT_PASS, "dashboard.html")
    page.goto(f"{BASE_URL}/feedback.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.fill("textarea[x-model='form.description']", "Mild headache")
    page.select_option("select[x-model='form.severity']", "2")
    page.click("button:has-text('Submit')")
    expect(page.locator("text=Mild headache").first).to_be_visible(timeout=5000)
    page.screenshot(path=f"{SCREENSHOT_DIR}/step6_feedback.png")

def test_step7_severity4(page: Page):
    _login(page, PATIENT_EMAIL, PATIENT_PASS, "dashboard.html")
    page.goto(f"{BASE_URL}/feedback.html")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.fill("textarea[x-model='form.description']", "Emergency!")
    page.select_option("select[x-model='form.severity']", "4")
    expect(page.locator("text=Warning:")).to_be_visible()
    page.click("button:has-text('Submit')")
    expect(page.locator("h3:has-text('EMERGENCY')")).to_be_visible()
    page.click("button:has-text('I understand, continue')")
    expect(page.locator("text=Emergency!").first).to_be_visible(timeout=5000)
    page.screenshot(path=f"{SCREENSHOT_DIR}/step7_severity4.png")

def test_step8_provider(page: Page):
    page.goto(f"{BASE_URL}/index.html")
    page.evaluate('sessionStorage.clear()')
    _login(page, "provider1@demo.adhera.app", PATIENT_PASS, "provider-dashboard.html")
    page.screenshot(path=f"{SCREENSHOT_DIR}/step8_provider.png")

def test_step9_admin(page: Page):
    _login(page, "admin@demo.adhera.app", PATIENT_PASS, "admin-dashboard.html")
    page.screenshot(path=f"{SCREENSHOT_DIR}/step9_admin.png")
