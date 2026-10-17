import { useCallback, useEffect, useState, type FormEvent } from "react";
import type { Session } from "@supabase/supabase-js";
import { getCurrentSession, onSupabaseSessionChange } from "../../lib/supabaseAuth";
import {
  createGhostProfile,
  deleteGhostProfile,
  listGhostProfiles,
  type GhostPlatform,
  type GhostProfile,
} from "../../lib/profileApi";

const panelStyle: React.CSSProperties = {
  marginBottom: 20, padding: 18, border: "1px solid #30333b",
  borderRadius: 12, background: "#17191f", color: "#ececf2",
};
const fieldStyle: React.CSSProperties = {
  minWidth: 160, padding: "10px 11px", borderRadius: 8,
  border: "1px solid #414550", background: "#101116", color: "inherit",
};
const actionStyle: React.CSSProperties = {
  padding: "9px 12px", borderRadius: 8, border: "1px solid #6662e8",
  background: "#5148dc", color: "#fff", cursor: "pointer",
};

export function SavedProfilesPanel() {
  const [session, setSession] = useState<Session | null>(null);
  const [profiles, setProfiles] = useState<GhostProfile[]>([]);
  const [platform, setPlatform] = useState<GhostPlatform>("youtube");
  const [name, setName] = useState("");
  const [handle, setHandle] = useState("");
  const [niche, setNiche] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refresh = useCallback(async (accessToken: string) => {
    setLoading(true);
    setError("");
    try {
      setProfiles(await listGhostProfiles(accessToken));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load saved profiles.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    const applySession = (next: Session | null) => {
      if (!active) return;
      setSession(next);
      setProfiles([]);
      setError("");
      setNotice("");
      if (next?.access_token) void refresh(next.access_token);
    };
    void getCurrentSession().then(applySession).catch((err: unknown) => {
      if (active) setError(err instanceof Error ? err.message : "Could not read sign-in session.");
    });
    const unsubscribe = onSupabaseSessionChange(applySession);
    return () => { active = false; unsubscribe(); };
  }, [refresh]);

  async function createProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!session?.access_token) {
      setError("Sign in with Supabase before saving profiles.");
      return;
    }
    const cleanName = name.trim();
    if (!cleanName) return;
    setSaving(true);
    setError("");
    setNotice("");
    const id = crypto.randomUUID();
    try {
      const created = await createGhostProfile(session.access_token, {
        profile_id: `profile-${id}`,
        connected_account_id: `pending-${id}`,
        platform,
        display_name: cleanName,
        profile_version: 1,
        profile_data: {
          handle: handle.trim(),
          niche: niche.trim(),
          connection_status: "not_connected",
          source: "ghost_profile_manager",
        },
      });
      setProfiles((current) => [created, ...current.filter((item) => item.profile_id !== created.profile_id)]);
      setName("");
      setHandle("");
      setNiche("");
      setNotice("Profile saved to the authenticated Ghost API. Social account authorization is still required.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save profile.");
    } finally {
      setSaving(false);
    }
  }

  async function removeProfile(profile: GhostProfile) {
    if (!session?.access_token) return;
    if (!window.confirm(`Delete saved profile "${profile.display_name}" from this workspace?`)) return;
    setError("");
    setNotice("");
    try {
      await deleteGhostProfile(session.access_token, profile.profile_id);
      setProfiles((current) => current.filter((item) => item.profile_id !== profile.profile_id));
      setNotice("Saved profile deleted.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not delete profile.");
    }
  }

  return <section aria-label="Persisted workspace profiles" style={panelStyle}>
    <div style={{ display: "flex", alignItems: "start", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
      <div>
        <small style={{ opacity: .7, letterSpacing: 1 }}>BACKEND-SAVED RECORDS</small>
        <h2 style={{ margin: "5px 0", fontSize: 18 }}>Saved profiles</h2>
        <p style={{ margin: 0, opacity: .75, fontSize: 13 }}>Separate from demo cards below. Records load from the authenticated, tenant-scoped API.</p>
      </div>
      <button type="button" onClick={() => session?.access_token && void refresh(session.access_token)} disabled={!session || loading} style={{ ...actionStyle, background: "transparent", borderColor: "#414550" }}>
        {loading ? "Loading…" : "↻ Refresh"}
      </button>
    </div>

    {!session && <p role="status" style={{ margin: "14px 0 0", fontSize: 13 }}>Sign in above to load or save workspace profiles. Preview profiles below are not stored in the database.</p>}

    {session && <form onSubmit={(event) => void createProfile(event)} style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 15 }}>
      <select aria-label="Platform" value={platform} onChange={(event) => setPlatform(event.target.value as GhostPlatform)} style={fieldStyle}>
        <option value="youtube">YouTube</option><option value="facebook">Facebook</option><option value="instagram">Instagram</option>
      </select>
      <input aria-label="Profile display name" required maxLength={120} placeholder="Profile / channel name" value={name} onChange={(event) => setName(event.target.value)} style={{ ...fieldStyle, flex: "1 1 180px" }} />
      <input aria-label="Profile handle" maxLength={120} placeholder="Handle (optional)" value={handle} onChange={(event) => setHandle(event.target.value)} style={{ ...fieldStyle, flex: "1 1 140px" }} />
      <input aria-label="Content niche" maxLength={160} placeholder="Niche (optional)" value={niche} onChange={(event) => setNiche(event.target.value)} style={{ ...fieldStyle, flex: "1 1 160px" }} />
      <button type="submit" disabled={saving} style={{ ...actionStyle, opacity: saving ? .6 : 1 }}>{saving ? "Saving…" : "＋ Save profile"}</button>
    </form>}

    {error && <p role="alert" style={{ color: "#ff9a9a", fontSize: 13, marginBottom: 0 }}>{error}</p>}
    {notice && <p role="status" style={{ color: "#9ee5bb", fontSize: 13, marginBottom: 0 }}>{notice}</p>}

    {session && <div style={{ display: "grid", gap: 8, marginTop: 14 }}>
      {!loading && profiles.length === 0 && !error && <p style={{ opacity: .7, fontSize: 13 }}>No saved profiles in this workspace yet.</p>}
      {profiles.map((profile) => {
        const data = profile.profile_data;
        const handleValue = typeof data.handle === "string" ? data.handle : "";
        const nicheValue = typeof data.niche === "string" ? data.niche : "";
        const connected = data.connection_status === "connected";
        return <article key={profile.profile_id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, padding: 12, border: "1px solid #30333b", borderRadius: 9, flexWrap: "wrap" }}>
          <div style={{ minWidth: 0, flex: "1 1 220px" }}>
            <strong>{profile.display_name}</strong>
            <div style={{ opacity: .72, fontSize: 12, marginTop: 4 }}>{profile.platform.toUpperCase()}{handleValue ? ` · ${handleValue}` : ""}{nicheValue ? ` · ${nicheValue}` : ""}</div>
            <div style={{ fontSize: 12, marginTop: 5, color: connected ? "#9ee5bb" : "#f1c27d" }}>{connected ? "Account connected" : "Saved only · OAuth not connected"}</div>
          </div>
          <button type="button" onClick={() => void removeProfile(profile)} style={{ ...actionStyle, background: "transparent", borderColor: "#6d4141", color: "#ffb4b4" }}>Delete</button>
        </article>;
      })}
    </div>}
  </section>;
}
