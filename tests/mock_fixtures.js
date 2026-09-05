/**
 * tests/mock_fixtures.js
 * Shared mock API payloads used by axe_scan.js and Playwright tests.
 */

const ok = (data) => ({ success: true, data, meta: { version: '2.0', timestamp: new Date().toISOString() } });

const MOCK_TOKEN = [
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
  Buffer.from(JSON.stringify({
    sub: 'ci-user-123',
    email: 'ci@adhera.app',
    role: 'patient',
    user_metadata: { role: 'patient', full_name: 'CI Patient User' },
    exp: 9999999999
  })).toString('base64'),
  'mock-sig',
].join('.');

const MOCK_PROVIDER_TOKEN = [
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
  Buffer.from(JSON.stringify({
    sub: 'ci-prov-123',
    email: 'doctor@adhera.app',
    role: 'provider',
    user_metadata: { role: 'provider', full_name: 'Dr. CI Provider' },
    exp: 9999999999
  })).toString('base64'),
  'mock-sig',
].join('.');

const MOCK_ADMIN_TOKEN = [
  'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9',
  Buffer.from(JSON.stringify({
    sub: 'ci-admin-123',
    email: 'admin@adhera.app',
    role: 'admin',
    user_metadata: { role: 'admin', full_name: 'CI Administrator' },
    exp: 9999999999
  })).toString('base64'),
  'mock-sig',
].join('.');

const MOCK_ROUTES = {
  '**/v1/config': ok({
    SUPABASE_URL: 'https://mock.supabase.co',
    SUPABASE_ANON_KEY: 'mock-anon-key',
    VAPID_PUBLIC_KEY: 'mock-vapid-public-key',
  }),
  '**/v1/profile/': ok({
    id: 'ci-user-123',
    role: 'patient',
    full_name: 'CI Patient User',
    email: 'ci@adhera.app',
    date_of_birth: '1990-01-01',
    blood_group: 'O+',
    allergies: ['Penicillin'],
    medical_conditions: ['Hypertension'],
    emergency_contacts: [
      { name: 'Jane Doe', phone: '+1234567890', relationship: 'Spouse' }
    ],
    timezone: 'UTC',
    is_active: true,
  }),
  '**/v1/assignments/my-provider': ok({
    assigned: false,
    data: null,
  }),
  '**/v1/doses/upcoming': ok([
    {
      id: 'd1',
      scheduled_utc: '2026-06-20T10:00:00Z',
      status: 'pending',
      reminders: {
        id: 'r1',
        medicine_id: 'm1',
        user_id: 'ci-user-123',
        dose_label: 'Morning',
        dose_time_utc: '10:00:00',
        recurrence_type: 'daily',
        advance_notification_minutes: 15,
        is_active: true,
        medicines: {
          id: 'm1',
          name: 'Aspirin',
          dosage: '100mg',
          route: 'oral',
          frequency: 'Daily',
          start_date: '2026-01-01',
          is_active: true,
        },
      },
    },
  ]),
  '**/v1/analytics/dashboard': ok({
    weekly_adherence: 85,
    monthly_adherence: 90,
    weekly_warning: false,
    weekly_percentage: 85,
    streak: 5,
    missed_this_month: 2,
    today_taken: 1,
    today_total: 2,
  }),
  '**/v1/analytics/adherence': ok({
    overall_percentage: 85,
    total_taken: 10,
    total_missed: 2,
    streak: 5,
  }),
  '**/v1/analytics/trend': ok([]),
  '**/v1/medicines': ok([
    {
      id: 'm1',
      user_id: 'ci-user-123',
      name: 'Aspirin',
      dosage: '100mg',
      route: 'oral',
      frequency: 'Daily',
      start_date: '2026-01-01',
      is_active: true,
      instructions: 'Take after meals',
      reminders: [
        {
          id: 'r1',
          medicine_id: 'm1',
          user_id: 'ci-user-123',
          dose_label: 'Morning',
          dose_time_utc: '10:00:00',
          recurrence_type: 'daily',
          advance_notification_minutes: 15,
          is_active: true,
        },
      ],
    },
  ]),
  '**/v1/medicines/**': ok([]),
  '**/v1/feedback/': ok([
    {
      id: 'f1',
      user_id: 'ci-user-123',
      medicine_id: 'm1',
      severity: 2,
      description: 'Mild nausea after taking dose',
      created_at: '2026-01-01T00:00:00Z',
      medicines: { name: 'Aspirin' },
    },
  ]),
  '**/v1/feedback/**': ok([]),
  '**/v1/provider/patients': ok([
    {
      patient_id: 'p1',
      profiles: { full_name: 'Patient One', email: 'p1@demo.com', timezone: 'UTC' },
      overall_adherence: 85,
    },
  ]),
  '**/v1/provider/**': ok(null),
  '**/v1/admin/stats': ok({
    total_users: 10,
    active_patients: 6,
    active_providers: 3,
    pending_approvals: 1,
  }),
  '**/v1/admin/users': ok([
    {
      id: 'u1',
      full_name: 'Dr. Smith',
      email: 'dr.smith@demo.com',
      role: 'provider',
      is_active: false,
      created_at: '2026-01-01T00:00:00Z',
    },
  ]),
  '**/v1/admin/pending-providers': ok([]),
  '**/v1/admin/assignments': ok([]),
  '**/v1/admin/**': ok({}),
  '**/v1/auth/**': ok({}),
};

/** Register all route mocks on a Playwright page. Must be called before page.goto(). */
async function mockApiRoutes(page) {
  for (const [pattern, payload] of Object.entries(MOCK_ROUTES)) {
    const body = JSON.stringify(payload);
    await page.route(pattern, (r) => r.fulfill({ contentType: 'application/json', body }));
  }
}

/** Inject mock JWT into sessionStorage & localStorage before any page scripts execute. */
function injectToken(page, token = MOCK_TOKEN) {
  return page.addInitScript((t) => {
    sessionStorage.setItem('adhera_token', t);
    sessionStorage.setItem('adhera_refresh_token', 'mock-refresh-token');
    localStorage.setItem('adhera_token', t);
    localStorage.setItem('adhera_refresh_token', 'mock-refresh-token');
  }, token);
}

module.exports = { MOCK_TOKEN, MOCK_PROVIDER_TOKEN, MOCK_ADMIN_TOKEN, MOCK_ROUTES, mockApiRoutes, injectToken };
