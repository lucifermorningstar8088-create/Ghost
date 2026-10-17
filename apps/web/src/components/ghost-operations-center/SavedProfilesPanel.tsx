import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import type { Session } from "@supabase/supabase-js";
import { getCurrentSession, onSupabaseSessionChange } from "../../lib/supabaseAuth";
import {
  createGhostProfile,
  deleteGhostProfile,
  listGhostProfiles,
  updateGhostProfile,
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
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editPlatform, setEditPlatform] = useState<GhostPlatform>("youtube");
  const [editHandle, setEditHandle] = useState("");
  const [editNiche, setEditNiche] = useState("");
  const [updating, setUpdating] = useState(false);
  const requestSequence = useRef(0);
  const sessionGeneration = useRef(0);

  const refresh = useCallback(async (accessToken: string) => {
    const sequence = ++requestSequence.current;
    setLoading(true);
    setError("");
    try {
      const result = await listGhostProfiles(accessToken);
      if (sequence === requestSequence.current) setProfiles(result);
    } catch (err) {
      if (sequence === requestSequence.current) {
        setError(err instanceof Error ? err.message : "Could not load saved profiles.");
      }
    } finally {
      if (sequence === requestSequence.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    const applySession = (next: Session | null) => {
      if (!active) return;
      requestSequence.current += 1;
      sessionGeneration.current += 1;
      setSession(next);
      setProfiles([]);
      setEditingId(null);
      setSaving(false);
      setUpdating(false);
      setError("");
      setNotice("");
      setLoading(Boolean(next?.access_token));
      if (next?.access_token) void refresh(next.access_token);
      else setLoading(false);
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
    const generation = sessionGeneration.current;
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
      if (generation !== sessionGeneration.current) return;
      setProfiles((current) => [created, ...current.filter((item) => item.profile_id !== created.profile_id)]);
      setName("");
      setHandle("");
      setNiche("");
      setNotice("Profile saved to the authenticated Ghost API. Social account authorization is still required.");
    } catch (err) {
      if (generation === sessionGeneration.current) {
        setError(err instanceof Error ? err.message : "Could not save profile.");
      }
    } finally {
      if (generation === sessionGeneration.current) setSaving(false);
    }
  }

  function beginEdit(profile: GhostProfile) {
    const data = profile.profile_data;
    setEditingId(profile.profile_id);
    setEditName(profile.display_name);
    setEditPlatform(profile.platform);
    setEditHandle(typeof data.handle === "string" ? data.handle : "");
    setEditNiche(typeof data.niche === "string" ? data.niche : "");
    setError("");
    setNotice("");
  }

  async function saveEdit(event: FormEvent<HTMLFormElement>, profile: GhostProfile) {
    event.preventDefault();
    if (!session?.access_token || !editingId) return;
    const cleanName = editName.trim();
    if (!cleanName) {
      setError("Profile name is required.");
      return;
    }
    const generation = sessionGeneration.current;
    setUpdating(true);
    setError("");
    setNotice("");
    try {
      const updated = await updateGhostProfile(session.access_token, profile.profile_id, {
        display_name: cleanName,
        platform: editPlatform,
        expected_profile_version: profile.profile_version,
        profile_data: {
          ...profile.profile_data,
          handle: editHandle.trim(),
          niche: editNiche.trim(),
        },
      });
      if (generation !== sessionGeneration.current) return;
      setProfiles((current) => current.map((item) => item.profile_id === updated.profile_id ? updated : item));
      setEditingId(null);
      setNotice("Profile changes saved to the Ghost API.");
    } catch (err) {
      if (generation === sessionGeneration.current) {
        setError(err instanceof Error ? err.message : "Could not update profile.");
      }
    } finally {
      if (generation === sessionGeneration.current) setUpdating(false);
    }
  }

  async function removeProfile(profile: GhostProfile) {
    if (!session?.access_token) return;
    if (!window.confirm(`Delete saved profile "${profile.display_name}" from this workspace?`)) return;
    const generation = sessionGeneration.current;
    setError("");
    setNotice("");
    try {
      await deleteGhostProfile(session.access_token, profile.profile_id);
      if (generation !== sessionGeneration.current) return;
      setProfiles((current) => current.filter((item) => item.profile_id !== profile.profile_id));
      setNotice("Saved profile deleted.");
    } catch (err) {
      if (generation === sessionGeneration.current) {
        setError(err instanceof Error ? err.message : "Could not delete profile.");
      }
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
        return <article key={profile.profile_id} style={{ display: "grid", gap: 10, padding: 12, border: "1px solid #30333b", borderRadius: 9 }}>
          {editingId === profile.profile_id ? <form onSubmit={(event) => void saveEdit(event, profile)} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            <input aria-label="Edit profile name" required maxLength={120} value={editName} onChange={(event) => setEditName(event.target.value)} style={{ ...fieldStyle, flex: "1 1 180px" }} />
            <select aria-label="Edit platform" value={editPlatform} onChange={(event) => setEditPlatform(event.target.value as GhostPlatform)} style={fieldStyle}>
              <option value="youtube">YouTube</option><option value="facebook">Facebook</option><option value="instagram">Instagram</option>
            </select>
            <input aria-label="Edit handle" maxLength={120} placeholder="Handle" value={editHandle} onChange={(event) => setEditHandle(event.target.value)} style={{ ...fieldStyle, flex: "1 1 140px" }} />
            <input aria-label="Edit niche" maxLength={160} placeholder="Niche" value={editNiche} onChange={(event) => setEditNiche(event.target.value)} style={{ ...fieldStyle, flex: "1 1 160px" }} />
            <button type="submit" disabled={updating} style={{ ...actionStyle, opacity: updating ? .6 : 1 }}>{updating ? "Saving…" : "Save changes"}</button>
            <button type="button" disabled={updating} onClick={() => setEditingId(null)} style={{ ...actionStyle, background: "transparent", borderColor: "#414550" }}>Cancel</button>
          </form> : <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <div style={{ minWidth: 0, flex: "1 1 220px" }}>
              <strong>{profile.display_name}</strong>
              <div style={{ opacity: .72, fontSize: 12, marginTop: 4 }}>{profile.platform.toUpperCase()}{handleValue ? ` · ${handleValue}` : ""}{nicheValue ? ` · ${nicheValue}` : ""}</div>
              <div style={{ fontSize: 12, marginTop: 5, color: connected ? "#9ee5bb" : "#f1c27d" }}>{connected ? "Account connected" : "Saved only · OAuth not connected"}</div>
            </div>
            <div style={{ display: "flex", gap: 8 }}>
              <button type="button" onClick={() => beginEdit(profile)} style={{ ...actionStyle, background: "transparent", borderColor: "#414550" }}>Edit</button>
              <button type="button" onClick={() => void removeProfile(profile)} style={{ ...actionStyle, background: "transparent", borderColor: "#6d4141", color: "#ffb4b4" }}>Delete</button>
            </div>
          </div>}
        </article>;
      })}
    </div>}
  </section>;
}
