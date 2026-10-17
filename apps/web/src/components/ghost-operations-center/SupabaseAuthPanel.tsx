import { useEffect, useState, type FormEvent } from "react";
import type { Session } from "@supabase/supabase-js";
import { getCurrentSession, getSupabaseBrowserClient, onSupabaseSessionChange, requestMagicLink, signOutSupabase } from "../../lib/supabaseAuth";

export function SupabaseAuthPanel() {
  const [session, setSession] = useState<Session | null>(null);
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const configured = Boolean(getSupabaseBrowserClient());

  useEffect(() => {
    let active = true;
    void getCurrentSession().then((value) => {
      if (active) setSession(value);
    }).catch((error: unknown) => {
      if (active) setMessage(error instanceof Error ? error.message : "Could not read session.");
    });
    const unsubscribe = onSupabaseSessionChange((value) => {
      if (active) setSession(value);
    });
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("");
    try {
      await requestMagicLink(email);
      setMessage("Sign-in link sent if this email is allowed. Check your inbox.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not send sign-in link.");
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    setBusy(true);
    setMessage("");
    try {
      await signOutSupabase();
      setSession(null);
      setMessage("Signed out.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not sign out.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="g-auth-panel" aria-label="Supabase account">
      <div className="g-auth-copy">
        <small className="g-auth-label">ACCOUNT AUTHENTICATION</small>
        <strong>{session ? "Signed in" : configured ? "Sign in with a secure email link" : "Supabase setup required"}</strong>
        <small>
          {session
            ? session.user.email ?? session.user.id
            : configured
              ? "Passwordless sign-in. Configure the redirect URL in Supabase Auth."
              : "Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in apps/web/.env.local."}
        </small>
        {message && <div className="g-auth-message" role="status" aria-live="polite">{message}</div>}
      </div>
      {session ? (
        <button className="g-auth-action" type="button" disabled={busy} onClick={() => void signOut()}>
          {busy ? "Working…" : "Sign out"}
        </button>
      ) : (
        <form className="g-auth-form" onSubmit={(event) => void submit(event)}>
          <input
            type="email"
            autoComplete="email"
            required
            aria-label="Email address"
            placeholder="you@example.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            disabled={!configured || busy}
          />
          <button type="submit" disabled={!configured || busy}>
            {busy ? "Sending…" : "Send sign-in link"}
          </button>
        </form>
      )}
    </section>
  );
}
