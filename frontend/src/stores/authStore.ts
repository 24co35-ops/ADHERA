import { create } from 'zustand';
import { User, UserRole, Profile } from '../types';
import { getToken, getRefreshToken, setTokens, clearTokens, api } from '../lib/api';
import { fetchConfig, config } from '../lib/config';

interface AuthState {
  user: User | null;
  profile: Profile | null;
  role: UserRole;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (accessToken: string, refreshToken: string, user: User, remember?: boolean) => void;
  setProfile: (profile: Profile) => void;
  logout: () => void;
  initialize: () => Promise<void>;
}

export function parseJwt(token: string): any {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      window
        .atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch (e) {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  profile: null,
  role: 'patient',
  isAuthenticated: false,
  isLoading: true,

  login: (accessToken, refreshToken, user, remember = true) => {
    setTokens(accessToken, refreshToken, remember);
    
    let resolvedUser = user;
    if (!resolvedUser) {
      const payload = parseJwt(accessToken);
      const role: UserRole = payload?.user_metadata?.role || payload?.role || 'patient';
      resolvedUser = {
        id: payload?.sub || '',
        email: payload?.email || '',
        role: role,
        full_name: payload?.user_metadata?.full_name || '',
      };
    }

    set({
      user: resolvedUser,
      role: resolvedUser.role,
      isAuthenticated: true,
      isLoading: false,
    });
  },

  setProfile: (profile) => {
    set({ profile });
  },

  logout: () => {
    clearTokens();
    set({
      user: null,
      profile: null,
      role: 'patient',
      isAuthenticated: false,
      isLoading: false,
    });
  },

  initialize: async () => {
    const token = getToken();
    if (!token) {
      set({ isLoading: false, isAuthenticated: false, user: null });
      return;
    }

    try {
      let currentToken = token;
      let payload = parseJwt(currentToken);
      if (!payload) throw new Error('Invalid token payload');

      // Check if token is expired before setting isAuthenticated
      if (payload.exp && payload.exp * 1000 <= Date.now()) {
        const refreshToken = getRefreshToken();
        if (refreshToken) {
          try {
            await fetchConfig();
            const refreshRes = await fetch(`${config.API_BASE}/auth/refresh`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh_token: refreshToken }),
            });
            if (refreshRes.ok) {
              const data = await refreshRes.json();
              if (data.success && data.data) {
                setTokens(data.data.access_token, data.data.refresh_token);
                currentToken = data.data.access_token;
                payload = parseJwt(currentToken);
              }
            }
          } catch (e) {
            console.warn('Silent refresh failed during init:', e);
          }
        }
        // If still expired after refresh attempt, clear tokens cleanly
        if (!payload || (payload.exp && payload.exp * 1000 <= Date.now())) {
          clearTokens();
          set({ user: null, isAuthenticated: false, isLoading: false });
          return;
        }
      }

      const role: UserRole = payload?.user_metadata?.role || payload?.role || 'patient';
      const user: User = {
        id: payload.sub,
        email: payload.email || '',
        role: role,
        full_name: payload.user_metadata?.full_name || '',
      };

      set({
        user,
        role,
        isAuthenticated: true,
      });

      // Fetch profile to get full details
      try {
        const res = await api.get<Profile>('/profile/');
        if (res.success && res.data) {
          set({
            profile: res.data,
            user: {
              ...user,
              full_name: res.data.full_name || user.full_name,
              role: res.data.role || role,
              timezone: res.data.timezone,
            },
            role: res.data.role || role,
          });
        }
      } catch (err) {
        console.warn('Profile fetch failed during auth init:', err);
      }
    } catch (e) {
      console.error('Auth initialization error:', e);
      clearTokens();
      set({ user: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },
}));
