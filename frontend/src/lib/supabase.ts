import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { fetchConfig, config } from './config';

let client: SupabaseClient | null = null;

export async function getSupabaseClient(): Promise<SupabaseClient | null> {
  if (client) return client;
  await fetchConfig();
  if (config.SUPABASE_URL && config.SUPABASE_ANON_KEY) {
    client = createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY, {
      auth: {
        // Fix: use sessionStorage so JWT tokens are NOT persisted across browser
        // sessions/tabs. localStorage tokens survive indefinitely and are
        // accessible to any XSS payload on the same origin.
        storage: window.sessionStorage,
        persistSession: true,
        autoRefreshToken: true,
      },
    });
  }
  return client;
}
