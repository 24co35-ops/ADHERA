import { fetchConfig, config } from './config';
import { ApiResponse } from '../types';

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function onRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

export function getToken(): string | null {
  return sessionStorage.getItem('adhera_token') || localStorage.getItem('adhera_token');
}

export function getRefreshToken(): string | null {
  return sessionStorage.getItem('adhera_refresh_token') || localStorage.getItem('adhera_refresh_token');
}

export function setTokens(accessToken: string, refreshToken: string, remember: boolean = true) {
  if (remember) {
    localStorage.setItem('adhera_token', accessToken);
    localStorage.setItem('adhera_refresh_token', refreshToken);
  }
  sessionStorage.setItem('adhera_token', accessToken);
  sessionStorage.setItem('adhera_refresh_token', refreshToken);
}

export function clearTokens() {
  localStorage.removeItem('adhera_token');
  localStorage.removeItem('adhera_refresh_token');
  localStorage.removeItem('adhera_user');
  sessionStorage.removeItem('adhera_token');
  sessionStorage.removeItem('adhera_refresh_token');
  sessionStorage.removeItem('adhera_user');
}

export async function adheraFetch(url: string, options: RequestInit = {}): Promise<Response> {
  await fetchConfig();

  const fullUrl = url.startsWith('http') ? url : `${config.API_BASE}${url.startsWith('/') ? '' : '/'}${url}`;
  const token = getToken();

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  let response = await fetch(fullUrl, {
    ...options,
    headers,
  });

  if (response.status === 401) {
    const refreshToken = getRefreshToken();
    if (refreshToken) {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          const refreshRes = await fetch(`${config.API_BASE}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken }),
          });

          if (refreshRes.ok) {
            const data = await refreshRes.json();
            if (data.success && data.data) {
              setTokens(data.data.access_token, data.data.refresh_token);
              onRefreshed(data.data.access_token);
              isRefreshing = false;
              headers.set('Authorization', `Bearer ${data.data.access_token}`);
              return fetch(fullUrl, { ...options, headers });
            }
          }
        } catch (e) {
          console.error('[Adhera] Token refresh failed:', e);
        } finally {
          isRefreshing = false;
        }
      } else {
        // Wait for token refresh to complete
        const retryToken = await new Promise<string>((resolve) => {
          refreshSubscribers.push(resolve);
        });
        headers.set('Authorization', `Bearer ${retryToken}`);
        return fetch(fullUrl, { ...options, headers });
      }
    }

    // Persistent 401 -> Session Expired
    clearTokens();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/register')) {
      window.location.href = '/login';
    }
  }

  return response;
}

export const api = {
  async get<T>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, { ...options, method: 'GET' });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json?.error?.message || json?.detail || `HTTP ${res.status}`);
    }
    return json;
  },

  async post<T>(url: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json?.error?.message || json?.detail || `HTTP ${res.status}`);
    }
    return json;
  },

  async put<T>(url: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json?.error?.message || json?.detail || `HTTP ${res.status}`);
    }
    return json;
  },

  async patch<T>(url: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json?.error?.message || json?.detail || `HTTP ${res.status}`);
    }
    return json;
  },

  async delete<T>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, { ...options, method: 'DELETE' });
    const json = await res.json();
    if (!res.ok) {
      throw new Error(json?.error?.message || json?.detail || `HTTP ${res.status}`);
    }
    return json;
  },
};
