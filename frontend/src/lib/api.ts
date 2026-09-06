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
    if (refreshToken && !isRefreshing) {
      isRefreshing = true;
      try {
        const refreshRes = await fetch(`${config.API_BASE}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (refreshRes.ok) {
          const data = await refreshRes.json();
          if (data.success && data.data?.access_token) {
            setTokens(data.data.access_token, data.data.refresh_token);
            onRefreshed(data.data.access_token);
            headers.set('Authorization', `Bearer ${data.data.access_token}`);
            return fetch(fullUrl, { ...options, headers });
          }
        }
      } catch (e) {
        console.error('[Adhera] Token refresh failed:', e);
      } finally {
        isRefreshing = false;
      }
    } else if (refreshToken && isRefreshing) {
      // Another request is already refreshing — queue and retry
      const retryToken = await new Promise<string>((resolve) => {
        refreshSubscribers.push(resolve);
      });
      headers.set('Authorization', `Bearer ${retryToken}`);
      return fetch(fullUrl, { ...options, headers });
    }

    // Refresh failed or no refresh token.
    // Only clear + redirect if we're on a protected route (not during/just after login).
    // Background calls (profile, analytics, etc.) should NOT force-logout a fresh session.
    const isAuthPage = typeof window !== 'undefined' &&
      (window.location.pathname.startsWith('/login') ||
       window.location.pathname.startsWith('/register'));

    if (!isAuthPage) {
      // Give a short grace period — a token minted seconds ago is valid,
      // so only redirect if the stored token is genuinely absent/expired.
      const storedToken = getToken();
      const isGenuinelyLoggedOut = !storedToken || storedToken.split('.').length !== 3;
      if (isGenuinelyLoggedOut) {
        clearTokens();
        window.location.href = '/login';
      }
      // Otherwise: return the 401 response and let the caller handle it
    }
  }

  return response;
}

export class ApiError extends Error {
  status: number;
  code?: string;
  field?: string;
  details?: { field: string; message: string; type?: string }[];
  data?: any;

  constructor(message: string, status: number, errorData?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = errorData?.code;
    this.field = errorData?.field;
    this.details = errorData?.details;
    this.data = errorData;
  }
}

async function handleResponse<T>(res: Response): Promise<ApiResponse<T>> {
  let json: any = null;
  try {
    json = await res.json();
  } catch (e) {
    // Ignore non-JSON body
  }

  if (!res.ok) {
    const errMsg =
      json?.error?.message ||
      (typeof json?.detail === 'string' ? json.detail : null) ||
      (Array.isArray(json?.detail) && json.detail[0]?.msg ? `${json.detail[0]?.loc?.slice(-1)}: ${json.detail[0]?.msg}` : null) ||
      `HTTP ${res.status}`;
    throw new ApiError(errMsg, res.status, json?.error || json);
  }
  return json;
}

export const api = {
  async get<T>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, { ...options, method: 'GET' });
    return handleResponse<T>(res);
  },

  async post<T>(url: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
    return handleResponse<T>(res);
  },

  async put<T>(url: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
    return handleResponse<T>(res);
  },

  async patch<T>(url: string, body?: any, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body),
    });
    return handleResponse<T>(res);
  },

  async delete<T>(url: string, options?: RequestInit): Promise<ApiResponse<T>> {
    const res = await adheraFetch(url, { ...options, method: 'DELETE' });
    return handleResponse<T>(res);
  },
};
