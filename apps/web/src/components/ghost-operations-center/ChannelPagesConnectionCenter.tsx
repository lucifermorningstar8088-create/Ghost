import { useCallback, useEffect, useState } from "react";
import { getCurrentSession } from "../../lib/supabaseAuth";

type Platform = "youtube" | "facebook" | "instagram" | "tiktok" | "x" | "telegram" | "other";
type Connection = {
  connection_id: string; platform: Platform; label: string; method: string; status: string;
  metadata: Record<string, unknown>; permissions: string[]; last_checked_at: string | null;
  created_at: string; updated_at: string; has_credentials: boolean;
};
const platforms: { id: Platform; name: string; hint: string }[] = [
  { id: "youtube", name: "YouTube", hint: "Google OAuth tokens" },
  { id: "facebook", name: "Facebook Pages", hint: "Meta access token" },
  { id: "instagram", name: "Instagram", hint: "Meta professional account token" },
  { id: "tiktok", name: "TikTok", hint: "TikTok developer token" },
  { id: "x", name: "X (Twitter)", hint: "Bearer or user access token" },
  { id: "telegram", name: "Telegram", hint: "BotFather bot token" },
  { id: "other", name: "Other platform", hint: "Custom API credentials" },
];
type SecretField = { key: string; value: string };
const emptySecret = (): SecretField => ({ key: "", value: "" });

export function ChannelPagesConnectionCenter() {
  const [items, setItems] = useState<Connection[]>([]);
  const [platform, setPlatform] = useState<Platform>("youtube");
  const [label, setLabel] = useState("");
  const [secrets, setSecrets] = useState<SecretField[]>([{ key: "access_token", value: "" }]);
  const [permissions, setPermissions] = useState("read_profile");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const selected = platforms.find(p => p.id === platform)!;
  const base = ((import.meta.env.VITE_GHOST_API_URL as string | undefined) ?? (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "http://localhost:8000").replace(/\/$/, "");

  const request = useCallback(async (path: string, init: RequestInit = {}) => {
    const session = await getCurrentSession();
    if (!session?.access_token) throw new Error("Sign in to Ghost first. The API requires a verified workspace session.");
    const response = await fetch(base + path, {
      ...init,
      headers: { Accept: "application/json", Authorization: `Bearer ${session.access_token}`, ...(init.body ? { "Content-Type": "application/json" } : {}), ...init.headers },
    });
    const body = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) throw new Error(body?.detail || `Request failed (${response.status})`);
    return body;
  }, [base]);

  const refresh = useCallback(async () => {
    try { setItems(await request("/api/v1/connections")); setError(""); }
    catch (e) { setError(e instanceof Error ? e.message : "Could not load connections."); }
  }, [request]);

  useEffect(() => { void refresh(); }, [refresh]);

  const save = async () => {
    setBusy(true); setError(""); setMessage("");
    try {
      const credentials: Record<string, string> = {};
      for (const field of secrets) {
        if (field.key.trim() && field.value.trim()) credentials[field.key.trim()] = field.value.trim();
      }
      if (!label.trim()) throw new Error("Enter a label for this account.");
      if (!Object.keys(credentials).length) throw new Error("Add at least one credential value.");
      await request("/api/v1/connections", { method: "POST", body: JSON.stringify({
        platform, label: label.trim(), method: "manual", credentials,
        metadata: {}, permissions: permissions.split(",").map(x => x.trim()).filter(Boolean),
      }) });
      setLabel(""); setSecrets([{ key: platform === "telegram" ? "bot_token" : platform === "x" ? "bearer_token" : "access_token", value: "" }]);
      setMessage("Credentials encrypted and saved. Run Test connection to verify the provider.");
      await refresh();
    } catch (e) { setError(e instanceof Error ? e.message : "Could not save connection."); }
    finally { setBusy(false); }
  };

  const test = async (id: string) => {
    setBusy(true); setError(""); setMessage("");
    try { const result = await request(`/api/v1/connections/${encodeURIComponent(id)}/test`, { method: "POST" }); setMessage(`Connection status: ${result.status}`); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Connection test failed."); await refresh(); }
    finally { setBusy(false); }
  };
  const disconnect = async (id: string) => {
    if (!window.confirm("Disconnect this account and delete its saved credentials?")) return;
    setBusy(true); setError(""); setMessage("");
    try { await request(`/api/v1/connections/${encodeURIComponent(id)}`, { method: "DELETE" }); setMessage("Connection removed."); await refresh(); }
    catch (e) { setError(e instanceof Error ? e.message : "Disconnect failed."); }
    finally { setBusy(false); }
  };

  return <section className="g-panel g-panel-pad g-connection-center">
    <div className="g-panel-heading"><div><h2>Channel & Pages Connection Center</h2><p>Connect original accounts with official API credentials. Secrets stay on the API server.</p></div><button className="g-link" onClick={() => void refresh()} disabled={busy}>↻ Refresh</button></div>
    <div className="g-info-banner"><b>🔐</b><p>Never enter your account password. Use platform-issued OAuth tokens or API credentials. OAuth authorization and channel/page discovery are not yet available for every provider; unsupported tests stay explicitly unverified.</p></div>
    <div className="g-platform-choices">{platforms.map(p => <button type="button" key={p.id} className={"g-platform-choice " + (platform === p.id ? "selected" : "")} onClick={() => { setPlatform(p.id); setSecrets([{ key: p.id === "telegram" ? "bot_token" : p.id === "x" ? "bearer_token" : "access_token", value: "" }]); }}><strong>{p.name}</strong><small>{p.hint}</small></button>)}</div>
    <div className="g-form-grid">
      <label className="g-field"><span>Account / Page label</span><input value={label} onChange={e => setLabel(e.target.value)} placeholder={`e.g. My ${selected.name} account`} /></label>
      <label className="g-field"><span>Requested permissions (comma-separated)</span><input value={permissions} onChange={e => setPermissions(e.target.value)} placeholder="read_profile, publish_content" /></label>
    </div>
    <div className="g-panel-heading"><div><h3>Manual API credentials</h3><p>{selected.name}: add the exact credential names required by the provider adapter.</p></div></div>
    {secrets.map((field, index) => <div className="g-form-grid" key={index}>
      <label className="g-field"><span>Credential name</span><input autoComplete="off" value={field.key} onChange={e => setSecrets(old => old.map((x,i) => i === index ? { ...x, key: e.target.value } : x))} placeholder="access_token" /></label>
      <label className="g-field"><span>Secret value</span><input type="password" autoComplete="new-password" value={field.value} onChange={e => setSecrets(old => old.map((x,i) => i === index ? { ...x, value: e.target.value } : x))} placeholder="Paste provider-issued token" /></label>
    </div>)}
    <div className="g-profile-actions"><button className="g-button" type="button" onClick={() => setSecrets(old => [...old, emptySecret()])}>＋ Add credential field</button><button className="g-button primary" type="button" disabled={busy} onClick={() => void save()}>{busy ? "Working…" : "Save encrypted credentials"}</button></div>
    {message && <p role="status" className="g-auth-message">{message}</p>}{error && <p role="alert" className="g-error-message">{error}</p>}
    <div className="g-panel-heading"><div><h3>Saved accounts</h3><p>{items.length} stored connection(s). Tokens are never displayed here.</p></div></div>
    {items.length === 0 ? <p className="g-panel-desc">No saved accounts yet. Connect an account above to get started.</p> : <div className="g-provider-grid">{items.map(item => <article className="g-provider-card" key={item.connection_id}><div className="g-provider-card-top"><span className="g-provider-logo">{item.platform.slice(0,1).toUpperCase()}</span><strong>{item.label}</strong></div><p>{platforms.find(p => p.id === item.platform)?.name ?? item.platform}</p><div className="g-provider-meta"><span><small>Status</small><strong>{item.status.replaceAll("_", " ")}</strong></span><span><small>Method</small><strong>{item.method}</strong></span></div><div className="g-provider-actions"><button className="g-button" disabled={busy} onClick={() => void test(item.connection_id)}>Test connection</button><button className="g-link" disabled={busy} onClick={() => void disconnect(item.connection_id)}>Disconnect</button></div></article>)}</div>}
  </section>;
}
