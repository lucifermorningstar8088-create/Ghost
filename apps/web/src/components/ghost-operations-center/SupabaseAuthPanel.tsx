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
    void getCurrentSession().then((value) => { if (active) setSession(value); }).catch((error: unknown) => {
      if (active) setMessage(error instanceof Error ? error.message : "Could not read session.");
    });
    const unsubscribe = onSupabaseSessionChange((value) => { if (active) setSession(value); });
    return () => { active = false; unsubscribe(); };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setMessage("");
    try { await requestMagicLink(email); setMessage("Sign-in link sent if this email is allowed. Check your inbox."); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Could not send sign-in link."); }
    finally { setBusy(false); }
  }

  async function signOut() {
    setBusy(true); setMessage("");
    try { await signOutSupabase(); setSession(null); setMessage("Signed out."); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Could not sign out."); }
    finally { setBusy(false); }
  }

  const button: React.CSSProperties = { padding: "9px 13px", borderRadius: 8, border: "1px solid #6662e8", background: "#5148dc", color: "#fff", cursor: "pointer" };
  return <section aria-label="Supabase account" style={{ margin: "12px 24px 0", padding: 14, border: "1px solid #30333b", borderRadius: 12, background: "#17191f", display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
    <div style={{ minWidth: 220, flex: "1 1 260px" }}>
      <small style={{ opacity: .7, letterSpacing: 1 }}>ACCOUNT AUTHENTICATION</small>
      <div><strong>{session ? "Signed in" : configured ? "Sign in with a secure email link" : "Supabase setup required"}</strong></div>
      <small>{session ? session.user.email ?? session.user.id : configured ? "Passwordless sign-in. Configure the redirect URL in Supabase Auth." : "Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in apps/web/.env.local."}</small>
      {message && <div role="status" style={{ marginTop: 6, fontSize: 13 }}>{message}</div>}
    </div>
    {session ? <button type="button" disabled={busy} onClick={() => void signOut()} style={button}>{busy ? "Working…" : "Sign out"}</button> :
      <form onSubmit={(event) => void submit(event)} style={{ display: "flex", gap: 8, flex: "1 1 330px", flexWrap: "wrap" }}>
        <input type="email" autoComplete="email" required aria-label="Email address" placeholder="you@example.com" value={email} onChange={(event) => setEmail(event.target.value)} disabled={!configured || busy} style={{ minWidth: 180, flex: "1 1 200px", padding: 10, borderRadius: 8, border: "1px solid #414550", background: "#101116", color: "inherit" }} />
        <button type="submit" disabled={!configured || busy} style={{ ...button, opacity: !configured || busy ? .55 : 1 }}>{busy ? "Sending…" : "Send sign-in link"}</button>
      </form>}
  </section>;
}
