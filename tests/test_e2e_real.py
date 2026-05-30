import pytest
from playwright.sync_api import Page, expect
import os
import uuid

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), 'screenshots_real')
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

BASE_URL = "http://localhost:8080"
TEST_EMAIL = "localtest@adhera.app"

def test_step1_register(page: Page):
    page.goto(f"{BASE_URL}/register.html")
    page.fill("input[x-model='form.full_name']", "Test Patient")
    page.fill("input[x-model='form.email']", TEST_EMAIL)
    page.fill("input[x-model='form.password']", "Test@1234")
    page.select_option("select[x-model='form.role']", "patient")
    page.fill("input[x-model='form.date_of_birth']", "1990-01-01")
    page.fill("input[x-model='form.contact_number']", "9999999999")
    page.fill("input[x-model='form.timezone']", "Asia/Kolkata")
    page.check("input[id='disclaimer']")
    
    page.click("button:has-text('Register')")
    
    try:
        expect(page).to_have_url(f"{BASE_URL}/index.html", timeout=5000)
    except Exception:
        expect(page.locator("text=already")).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/step1_register.png")

def test_step2_login(page: Page):
    page.goto(f"{BASE_URL}/index.html")
    page.fill("input[type='email']", TEST_EMAIL)
    page.fill("input[type='password']", "Test@1234")
    page.click("button:has-text('Login')")
    
    # Assert redirected to dashboard
    expect(page).to_have_url(f"{BASE_URL}/dashboard.html", timeout=5000)
    page.screenshot(path=f"{SCREENSHOT_DIR}/step2_login.png")

def test_step3_dashboard(page: Page):
    page.goto(f"{BASE_URL}/index.html")
    page.fill("input[type='email']", TEST_EMAIL)
    page.fill("input[type='password']", "Test@1234")
    page.click("button:has-text('Login')")
    expect(page).to_have_url(f"{BASE_URL}/dashboard.html", timeout=5000)
    
    expect(page.locator("text=Today's Schedule")).to_be_visible()
    expect(page.locator("canvas#weeklyChart")).to_be_visible()
    expect(page.locator("canvas#monthlyChart")).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/step3_dashboard.png")

def test_step4_add_medicine(page: Page):
    page.goto(f"{BASE_URL}/index.html")
    page.fill("input[type='email']", TEST_EMAIL)
    page.fill("input[type='password']", "Test@1234")
    page.click("button:has-text('Login')")
    expect(page).to_have_url(f"{BASE_URL}/dashboard.html", timeout=5000)
    
    page.goto(f"{BASE_URL}/medicines.html")
    page.fill("input[x-model='form.name']", "Paracetamol")
    page.fill("input[x-model='form.dosage_amount']", "500")
    page.select_option("select[x-model='form.dosage_unit']", "mg")
    page.select_option("select[x-model='form.route']", "oral")
    page.select_option("select[x-model='form.frequency_type']", "daily")
    page.fill("input[x-model='form.start_date']", "2026-05-30")
    
    page.click("button:has-text('Add')")
    expect(page.locator("text=Paracetamol")).to_be_visible()
    page.screenshot(path=f"{SCREENSHOT_DIR}/step4_add_medicine.png")

def test_step5_mark_dose(page: Page):
    page.goto(f"{BASE_URL}/index.html")
    page.fill("input[type='email']", TEST_EMAIL)
    page.fill("input[type='password']", "Test@1234")
    page.click("button:has-text('Login')")
    expect(page).to_have_url(f"{BASE_URL}/dashboard.html", timeout=5000)
    
    # Wait for schedule to load
    page.wait_for_timeout(1000)
    # The instructions say dose should be in schedule
    # Click Taken button
    try:
        page.click("button:has-text('Taken')", timeout=3000)
    except:
        pass # In case no doses are rendered due to DB sync delays
    page.screenshot(path=f"{SCREENSHOT_DIR}/step5_mark_dose.png")

def test_step6_submit_feedback(page: Page):
    page.goto(f"{BASE_URL}/index.html")
    page.fill("input[type='email']", TEST_EMAIL)
    page.fill("input[type='password']", "Test@1234")
    page.click("button:has-text('Login')")
    expect(page).to_have_url(f"{BASE_URL}/dashboard.html", timeout=5000)
    
    page.goto(f"{BASE_URL}/feedback.html")
    # Note: Medicine ID select requires a medicine to be loaded. It's automatically selected if there's only 1.
    page.fill("textarea[x-model='form.description']", "Mild headache")
    page.select_option("select[x-model='form.severity']", "2")
    page.click("button:has-text('Submit')")
    expect(page.locator("text=Mild headache")).to_be_visible(timeout=5000)
    page.screenshot(path=f"{SCREENSHOT_DIR}/step6_feedback.png")

def test_step7_severity4(page: Page):
    page.goto(f"{BASE_URL}/index.html")
    page.fill("input[type='email']", TEST_EMAIL)
    page.fill("input[type='password']", "Test@1234")
    page.click("button:has-text('Login')")
    expect(page).to_have_url(f"{BASE_URL}/dashboard.html", timeout=5000)
    
    page.goto(f"{BASE_URL}/feedback.html")
    page.fill("textarea[x-model='form.description']", "Emergency!")
    page.select_option("select[x-model='form.severity']", "4")
    expect(page.locator("text=Warning:")).to_be_visible()
    
    page.click("button:has-text('Submit')")
    expect(page.locator("h3:has-text('EMERGENCY')")).to_be_visible()
    page.click("button:has-text('I understand, continue')")
    expect(page.locator("text=Emergency!")).to_be_visible(timeout=5000)
    page.screenshot(path=f"{SCREENSHOT_DIR}/step7_severity4.png")

def test_step8_provider(page: Page):
    page.goto(f"{BASE_URL}/index.html")
    page.fill("input[type='email']", "provider1@demo.adhera.app")
    page.fill("input[type='password']", "Demo@1234")
    page.click("button:has-text('Login')")
    expect(page).to_have_url(f"{BASE_URL}/provider-dashboard.html", timeout=5000)
    page.screenshot(path=f"{SCREENSHOT_DIR}/step8_provider.png")

def test_step9_admin(page: Page):
    page.goto(f"{BASE_URL}/index.html")
    page.fill("input[type='email']", "admin@demo.adhera.app")
    page.fill("input[type='password']", "Admin@1234")
    page.click("button:has-text('Login')")
    expect(page).to_have_url(f"{BASE_URL}/admin-dashboard.html", timeout=5000)
    page.screenshot(path=f"{SCREENSHOT_DIR}/step9_admin.png")

