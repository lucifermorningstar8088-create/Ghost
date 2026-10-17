import { createClient, type Session, type SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | null = null;

/**
 * Returns the configured browser client. Only the public anon/publishable key
 * belongs here; service-role keys and provider secrets must stay server-side.
 */
export function getSupabaseBrowserClient(): SupabaseClient | null {
  const url = import.meta.env.VITE_SUPABASE_URL?.trim();
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY?.trim();

  if (!url || !anonKey) return null;
  if (!client) client = createClient(url, anonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    },
  });
  return client;
}

export type AuthConfiguration = "configured" | "missing";

export function getAuthConfiguration(): AuthConfiguration {
  return getSupabaseBrowserClient() ? "configured" : "missing";
}

export async function requestMagicLink(email: string): Promise<void> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) throw new Error("Supabase sign-in is not configured. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY.");
  const normalizedEmail = email.trim();
  if (!normalizedEmail) throw new Error("Enter your email address.");

  const { error } = await supabase.auth.signInWithOtp({
    email: normalizedEmail,
    options: { emailRedirectTo: window.location.origin },
  });
  if (error) throw new Error(error.message);
}

export async function getCurrentSession(): Promise<Session | null> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) return null;
  const { data, error } = await supabase.auth.getSession();
  if (error) throw new Error(error.message);
  return data.session;
}

export async function signOutSupabase(): Promise<void> {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) return;
  const { error } = await supabase.auth.signOut();
  if (error) throw new Error(error.message);
}

export function onSupabaseSessionChange(callback: (session: Session | null) => void): () => void {
  const supabase = getSupabaseBrowserClient();
  if (!supabase) {
    callback(null);
    return () => undefined;
  }
  const { data } = supabase.auth.onAuthStateChange((_event, session) => callback(session));
  return () => data.subscription.unsubscribe();
}
