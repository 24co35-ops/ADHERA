/**
 * tests/axe_scan.js
 * Playwright + @axe-core/playwright accessibility scan for the React SPA.
 * Spins up the frontend static SPA server, injects mock JWT + page.route() API
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
const { execSync } = require('child_process');
const { mockApiRoutes, injectToken, MOCK_TOKEN, MOCK_PROVIDER_TOKEN, MOCK_ADMIN_TOKEN } = require('./mock_fixtures');

const FRONTEND_DIR = path.resolve(__dirname, '..', 'frontend');
const DIST_DIR = path.resolve(FRONTEND_DIR, 'dist');
const PORT = 8091;

// ── Ensure frontend is built ──────────────────────────────────────────────────
function ensureBuild() {
  console.log('Building React frontend for accessibility scan...');
  execSync('npm run build', { cwd: FRONTEND_DIR, stdio: 'inherit' });
}

// ── Minimal SPA static file server ────────────────────────────────────────────
function startServer() {
  const mimeTypes = {
    '.html': 'text/html',
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.ico': 'image/x-icon',
    '.json': 'application/json',
    '.webmanifest': 'application/manifest+json',
    '.woff2': 'font/woff2',
    '.woff': 'font/woff',
    '.ttf': 'font/ttf',
  };

  const server = http.createServer((req, res) => {
    let urlPath = req.url.split('?')[0];
    let file = path.join(DIST_DIR, urlPath);

    // If file doesn't exist or is a directory, fallback to index.html for SPA routing
    if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
      file = path.join(DIST_DIR, 'index.html');
    }

    const ext = path.extname(file);
    res.writeHead(200, {
      'Content-Type': mimeTypes[ext] || 'text/html',
      'Access-Control-Allow-Origin': '*',
    });
    fs.createReadStream(file).pipe(res);
  });

  return new Promise((resolve) => server.listen(PORT, () => resolve(server)));
}

// ── Scan a single page, return violations ─────────────────────────────────────
async function scanPage(browser, url, label, token = null) {
  const context = await browser.newContext();
  const page = await context.newPage();
  try {
    // Register API mocks BEFORE navigation
    await mockApiRoutes(page);
    if (token) {
      await injectToken(page, token);
    }

    await page.goto(url, { waitUntil: 'networkidle', timeout: 20000 });

    // Wait for React to mount & state to settle
    await page.waitForTimeout(1000);

    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    if (results.violations.length > 0) {
      console.error(`\n❌  ${label} (${url}) — ${results.violations.length} violation(s):`);
      for (const v of results.violations) {
        console.error(`  [${v.impact}] ${v.id}: ${v.description}`);
        for (const n of v.nodes) {
          console.error(`    → ${n.html.slice(0, 500)}`);
          if (n.any) n.any.slice(0, 2).forEach((a) => console.error(`      ✗ ${a.message}`));
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
  ensureBuild();
  const server = await startServer();
  const base = `http://localhost:${PORT}`;
  let browser;
  let totalViolations = 0;

  try {
    browser = await chromium.launch();

    const pages = [
      { path: '/login', label: 'Login Page', token: null },
      { path: '/register', label: 'Register Page', token: null },
      { path: '/dashboard', label: 'Patient Dashboard', token: MOCK_TOKEN },
      { path: '/medicines', label: 'Medicines Page', token: MOCK_TOKEN },
      { path: '/feedback', label: 'Feedback Page', token: MOCK_TOKEN },
      { path: '/profile', label: 'Profile Page', token: MOCK_TOKEN },
      { path: '/provider', label: 'Provider Dashboard', token: MOCK_PROVIDER_TOKEN },
      { path: '/admin', label: 'Admin Dashboard', token: MOCK_ADMIN_TOKEN },
    ];

    for (const { path: routePath, label, token } of pages) {
      const vs = await scanPage(browser, `${base}${routePath}`, label, token);
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
