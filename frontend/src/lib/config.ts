export interface AdheraConfig {
  API_BASE: string;
  SUPABASE_URL: string;
  SUPABASE_ANON_KEY: string;
  VAPID_PUBLIC_KEY: string;
}

const getApiBase = () => {
  if (typeof window === 'undefined') return 'http://localhost:8000/v1';
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  return isLocal ? 'http://localhost:8000/v1' : `${window.location.origin}/v1`;
};

export const config: AdheraConfig = {
  API_BASE: getApiBase(),
  SUPABASE_URL: '',
  SUPABASE_ANON_KEY: '',
  VAPID_PUBLIC_KEY: '',
};

let configLoaded = false;
let configPromise: Promise<AdheraConfig> | null = null;

export async function fetchConfig(): Promise<AdheraConfig> {
  if (configLoaded) return config;
  if (configPromise) return configPromise;

  configPromise = (async () => {
    try {
      const token = typeof window !== 'undefined'
        ? sessionStorage.getItem('adhera_token') || localStorage.getItem('adhera_token')
        : null;
      const headers: Record<string, string> = {};
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const res = await fetch(`${config.API_BASE}/config`, {
        cache: 'no-store',
        headers,
      });
      if (res.ok) {
        const json = await res.json();
        if (json.success && json.data) {
          config.SUPABASE_URL = json.data.SUPABASE_URL || '';
          config.SUPABASE_ANON_KEY = json.data.SUPABASE_ANON_KEY || '';
          config.VAPID_PUBLIC_KEY = json.data.VAPID_PUBLIC_KEY || '';
        }
      }
    } catch (err) {
      console.warn('[Adhera] /v1/config fetch failed, using environment fallbacks:', err);
      // @ts-ignore
      config.SUPABASE_URL = window.__ADHERA_SUPABASE_URL || '';
      // @ts-ignore
      config.SUPABASE_ANON_KEY = window.__ADHERA_SUPABASE_ANON_KEY || '';
      // @ts-ignore
      config.VAPID_PUBLIC_KEY = window.__ADHERA_VAPID_KEY || '';
    }
    configLoaded = true;
    return config;
  })();

  return configPromise;
}
