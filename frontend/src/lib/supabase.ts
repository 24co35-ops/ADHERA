import { createClient, SupabaseClient } from '@supabase/supabase-js';
import { fetchConfig, config } from './config';

let client: SupabaseClient | null = null;

export async function getSupabaseClient(): Promise<SupabaseClient | null> {
  if (client) return client;
  await fetchConfig();
  if (config.SUPABASE_URL && config.SUPABASE_ANON_KEY) {
    client = createClient(config.SUPABASE_URL, config.SUPABASE_ANON_KEY, {
      auth: {
        persistSession: false,
        autoRefreshToken: false,
      },
    });
  }
  return client;
}
