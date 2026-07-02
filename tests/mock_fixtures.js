/**
 * tests/mock_fixtures.js
 * Shared mock API payloads used by both axe_scan.js and any future
 * JS-based Playwright tests. Mirrors the Python fixtures in test_frontend.py.
 *
 * The Python tests duplicate this data unavoidably (different language), but
 * within the JS test surface these are the single source of truth.
 */

const ok = (data) => ({ success: true, data, meta: {} });

const MOCK_TOKEN = [
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
  Buffer.from(JSON.stringify({ sub: 'ci-user', app_metadata: { role: 'patient' }, exp: 9999999999 })).toString('base64'),
  'mock-sig',
].join('.');

const MOCK_ROUTES = {
  '**/v1/config': ok({ SUPABASE_URL: 'https://mock.supabase.co', SUPABASE_ANON_KEY: 'mock-anon', VAPID_PUBLIC_KEY: 'mock-vapid' }),
  '**/v1/doses/upcoming': ok([{ id: 'd1', scheduled_utc: '2026-06-20T10:00:00Z', reminders: { dose_label: 'Morning', medicines: { name: 'Aspirin', dosage_amount: 100, dosage_unit: 'mg' } }, snooze_count: 0 }]),
  '**/v1/analytics/dashboard': ok({ weekly_adherence: 85, monthly_adherence: 90, weekly_warning: false }),
  '**/v1/analytics/adherence': ok({ overall_percentage: 85, total_taken: 10, total_missed: 2, streak: 5 }),
  '**/v1/analytics/trend': ok([]),
  '**/v1/feedback/': ok([{ id: 'f1', created_at: '2026-01-01T00:00:00Z', severity: 2, description: 'Mild nausea' }]),
  '**/v1/feedback/**': ok([]),
  '**/v1/medicines': ok([{ id: 'm1', name: 'Aspirin', dosage_amount: 100, dosage_unit: 'mg', route: 'oral', frequency_type: 'daily' }]),
  '**/v1/medicines/**': ok([]),
  '**/v1/provider/**': ok(null),
  '**/v1/auth/**': ok({}),
};

/** Register all route mocks on a Playwright page. Must be called before page.goto(). */
async function mockApiRoutes(page) {
  for (const [pattern, payload] of Object.entries(MOCK_ROUTES)) {
    const body = JSON.stringify(payload);
    await page.route(pattern, (r) => r.fulfill({ contentType: 'application/json', body }));
  }
}

/** Inject mock JWT into sessionStorage before any page scripts execute. */
function injectToken(page, token = MOCK_TOKEN) {
  return page.addInitScript((t) => {
    sessionStorage.setItem('adhera_token', t);
    sessionStorage.setItem('adhera_refresh_token', 'mock-refresh');
  }, token);
}

module.exports = { MOCK_TOKEN, MOCK_ROUTES, mockApiRoutes, injectToken };
