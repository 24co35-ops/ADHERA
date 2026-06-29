/**
 * Adhera Frontend Configuration
 * Keys are fetched dynamically from the backend /v1/config endpoint
 * — no secrets hardcoded here. This file is safe to commit.
 */

const _API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://localhost:8000/v1"
  : `${window.location.origin}/v1`;

// Shared mutable config object — populated by initConfig()
const CONFIG = {
  API_BASE: _API_BASE,
  SUPABASE_URL: null,
  SUPABASE_ANON_KEY: null,
  VAPID_PUBLIC_KEY: null,
  _ready: false,
  _listeners: [],
  onReady(cb) {
    if (this._ready) { cb(); return; }
    this._listeners.push(cb);
  }
};

/**
 * Initialise CONFIG by fetching /v1/config from the backend.
 * Must be awaited (or onReady() used) before Supabase calls.
 */
async function initConfig() {
  if (CONFIG._ready) return CONFIG;
  try {
    const res = await fetch(`${_API_BASE}/config`, { cache: "no-store" });
    if (!res.ok) throw new Error(`/v1/config returned ${res.status}`);
    const body = await res.json();
    const d = body.data;
    CONFIG.SUPABASE_URL      = d.SUPABASE_URL;
    CONFIG.SUPABASE_ANON_KEY = d.SUPABASE_ANON_KEY;
    CONFIG.VAPID_PUBLIC_KEY  = d.VAPID_PUBLIC_KEY;
  } catch (err) {
    console.error("[Adhera] Failed to load config from /v1/config:", err);
    // Fall back to window-injected values if present (set in Vercel env at build time)
    CONFIG.SUPABASE_URL      = window.__ADHERA_SUPABASE_URL      || "";
    CONFIG.SUPABASE_ANON_KEY = window.__ADHERA_SUPABASE_ANON_KEY || "";
    CONFIG.VAPID_PUBLIC_KEY  = window.__ADHERA_VAPID_KEY         || "";
  }
  CONFIG._ready = true;
  CONFIG._listeners.forEach(cb => cb());
  CONFIG._listeners = [];
  return CONFIG;
}

// Automatically start fetching config on script load!
initConfig();

/**
 * Global API fetch wrapper.
 * - Injects Authorization header automatically.
 * - On 401, attempts a single token refresh then retries.
 * - On persistent 401, shows a toast and redirects to login.
 * @param {string} url  - Full URL or path relative to API_BASE
 * @param {RequestInit} opts - Standard fetch options
 * @returns {Response}
 */
async function adheraFetch(url, opts = {}) {
  // Ensure config is loaded before any fetch
  if (!CONFIG._ready) {
    await new Promise(resolve => CONFIG.onReady(resolve));
  }

  const fullUrl = url.startsWith("http") ? url : `${CONFIG.API_BASE}${url}`;
  const token = sessionStorage.getItem("adhera_token");

  opts.headers = Object.assign(
    { "Content-Type": "application/json", ...(token ? { "Authorization": `Bearer ${token}` } : {}) },
    opts.headers || {}
  );

  let res = await fetch(fullUrl, opts);

  if (res.status === 401) {
    const refreshToken = sessionStorage.getItem("adhera_refresh_token");
    if (refreshToken) {
      try {
        const refreshRes = await fetch(`${CONFIG.API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (refreshRes.ok) {
          const data = await refreshRes.json();
          if (data.success && data.data) {
            sessionStorage.setItem("adhera_token", data.data.access_token);
            sessionStorage.setItem("adhera_refresh_token", data.data.refresh_token);
            opts.headers["Authorization"] = `Bearer ${data.data.access_token}`;
            res = await fetch(fullUrl, opts);
          }
        }
      } catch (_) { /* fall through */ }
    }
    if (res.status === 401) _adheraSessionExpired();
  }

  return res;
}

function _adheraSessionExpired() {
  sessionStorage.removeItem("adhera_token");
  sessionStorage.removeItem("adhera_refresh_token");
  const toast = document.createElement("div");
  toast.textContent = "Session expired. Please log in again.";
  toast.style.cssText = [
    "position:fixed", "bottom:24px", "left:50%", "transform:translateX(-50%)",
    "background:#1e2330", "color:#e2e2e8", "border:1px solid rgba(255,255,255,0.12)",
    "border-radius:12px", "padding:12px 24px", "font-family:Inter,sans-serif",
    "font-size:14px", "z-index:9999", "box-shadow:0 4px 30px rgba(0,0,0,0.3)"
  ].join(";");
  document.body?.appendChild(toast);
  setTimeout(() => { window.location.href = "/index.html"; }, 1800);
}
