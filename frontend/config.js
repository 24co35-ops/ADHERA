const CONFIG = {
  API_BASE: window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000/v1"
    : `${window.location.origin}/v1`,
  SUPABASE_URL: "https://olsgvrmxqsftymsbeqve.supabase.co",
  SUPABASE_ANON_KEY: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9sc2d2cm14cXNmdHltc2JlcXZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk2OTA0MjksImV4cCI6MjA5NTI2NjQyOX0.aZLBUgVPtRaCKbjHu8ljvsKOYWU6TDXO1gAE79jq9cM",
  VAPID_PUBLIC_KEY: "BP7gOA_zw733v9HapbDhHW7WHXnXTmCs9rRHWegiWnf8nxsVIU9bytYpAGPCP2XyRYZt_5-OcPKBHyhqKrwQrSU"
};

/**
 * Global API fetch wrapper.
 * - Injects Authorization header automatically.
 * - On 401, attempts a single token refresh then retries.
 * - On persistent 401, shows a toast and redirects to login.
 * @param {string} url - Full URL or path relative to API_BASE
 * @param {RequestInit} opts - Standard fetch options
 * @returns {Response}
 */
async function adheraFetch(url, opts = {}) {
  const fullUrl = url.startsWith("http") ? url : `${CONFIG.API_BASE}${url}`;
  const token = sessionStorage.getItem("adhera_token");

  opts.headers = Object.assign({
    "Content-Type": "application/json",
    ...(token ? { "Authorization": `Bearer ${token}` } : {})
  }, opts.headers || {});

  let res = await fetch(fullUrl, opts);

  if (res.status === 401) {
    // Attempt one transparent refresh
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
            // Retry original request with new token
            opts.headers["Authorization"] = `Bearer ${data.data.access_token}`;
            res = await fetch(fullUrl, opts);
          }
        }
      } catch (e) {
        // Refresh failed — fall through to session expired
      }
    }

    // Still 401 after refresh attempt
    if (res.status === 401) {
      _adheraSessionExpired();
    }
  }

  return res;
}

function _adheraSessionExpired() {
  sessionStorage.removeItem("adhera_token");
  sessionStorage.removeItem("adhera_refresh_token");
  // Show toast if possible
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
