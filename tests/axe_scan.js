/**
 * tests/axe_scan.js
 * Playwright + @axe-core/playwright accessibility scan.
 * Spins up the frontend static server, injects a mock JWT + page.route() API
 * mocks so auth-gated pages render fully, then runs axe against the live DOM.
 *
 * Usage: node tests/axe_scan.js
 * Exit 1 on any WCAG 2 violations.
 */

const { chromium } = require('playwright');
const { AxeBuilder } = require('@axe-core/playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');
const { mockApiRoutes, injectToken } = require('./mock_fixtures');

const FRONTEND_DIR = path.resolve(__dirname, '..', 'frontend');
const PORT = 8091;

// ── Minimal static file server ────────────────────────────────────────────────
function startServer() {
  const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
    '.webmanifest': 'application/manifest+json',
  };
  const server = http.createServer((req, res) => {
    let urlPath = req.url.split('?')[0];
    if (urlPath === '/') urlPath = '/index.html';
    const file = path.join(FRONTEND_DIR, urlPath);
    if (!fs.existsSync(file)) { res.writeHead(404); res.end(); return; }
    const ext = path.extname(file);
    res.writeHead(200, { 'Content-Type': mimeTypes[ext] || 'text/plain' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(resolve => server.listen(PORT, () => resolve(server)));
}

// ── Scan a single page, return violations ─────────────────────────────────────
async function scanPage(browser, url, label) {
  const context = await browser.newContext();
  const page = await context.newPage();
  try {
    // Register API mocks BEFORE navigation — config.js fetches /v1/config
    // synchronously on script load; route intercepts must be in place first.
    await mockApiRoutes(page);
    await injectToken(page);

    await page.goto(url, { waitUntil: 'networkidle', timeout: 15000 });

    // Assert mock config was used: CONFIG.SUPABASE_URL must be the mock value,
    // not empty string (which would indicate the /v1/config fetch fell through
    // to the window.__ADHERA_* fallback and we'd be scanning a broken page).
    if (url.includes('dashboard') || url.includes('medicines')) {
      const supabaseUrl = await page.evaluate(() => {
        return typeof CONFIG !== 'undefined' ? CONFIG.SUPABASE_URL : '__CONFIG_MISSING__';
      });
      if (!supabaseUrl || supabaseUrl === '__CONFIG_MISSING__' || supabaseUrl === '') {
        throw new Error(`[${label}] CONFIG.SUPABASE_URL is empty — /v1/config mock was not intercepted. Axe would scan a broken page.`);
      }
      console.log(`  ✓ CONFIG.SUPABASE_URL = "${supabaseUrl}" (mock confirmed)`);
    }

    // Wait for Alpine.js to initialize
    await page.waitForTimeout(1500);

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    if (results.violations.length > 0) {
      console.error(`\n❌  ${label} — ${results.violations.length} violation(s):`);
      for (const v of results.violations) {
        console.error(`  [${v.impact}] ${v.id}: ${v.description}`);
        for (const n of v.nodes) {
          console.error(`    → ${n.html.slice(0, 120)}`);
        }
      }
    } else {
      console.log(`✅  ${label} — no violations`);
    }
    return results.violations;
  } finally {
    await page.close();
    await context.close();
  }
}

// ── Main ──────────────────────────────────────────────────────────────────────
(async () => {
  const server = await startServer();
  const base = `http://localhost:${PORT}`;
  let browser;
  let totalViolations = 0;

  try {
    browser = await chromium.launch();

    const pages = [
      [base + '/index.html',     'index.html (login)'],
      [base + '/register.html',  'register.html'],
      [base + '/dashboard.html', 'dashboard.html (patient)'],
      [base + '/medicines.html', 'medicines.html'],
    ];

    for (const [url, label] of pages) {
      const vs = await scanPage(browser, url, label);
      totalViolations += vs.length;
    }
  } finally {
    if (browser) await browser.close();
    server.close();
  }

  if (totalViolations > 0) {
    console.error(`\nTotal violations: ${totalViolations}. Failing build.`);
    process.exit(1);
  }
  console.log('\nAll accessibility checks passed.');
})();
