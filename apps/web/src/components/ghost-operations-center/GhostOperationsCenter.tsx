import React, { useMemo, useState } from "react";
import { SupabaseAuthPanel } from "./SupabaseAuthPanel";
import { SavedProfilesPanel } from "./SavedProfilesPanel";
import { ChannelPagesConnectionCenter } from "./ChannelPagesConnectionCenter";
import "./GhostOperationsCenter.css";
type Screen = "Overview" | "Live jobs" | "Workers" | "Community" | "Channels & profiles" | "Integrations" | "Database" | "Telegram" | "Settings";
type Channel = {
  id: string;
  name: string;
  platform: string;
  niche: string;
  format: string;
  tone: string;
  status: string;
  cadence: string;
  language: string;
  prompt: string;
  handle: string;
  approval: string;
  timezone: string;
  audience: string;
};
const NAV: {
  label: Screen;
  icon: string;
  group: string;
  mpid?: string;
}[] = [{
  label: "Overview",
  icon: "▦",
  group: "WORKSPACE"
}, {
  label: "Live jobs",
  icon: "◷",
  group: "WORKSPACE"
}, {
  label: "Workers",
  icon: "⠿",
  group: "WORKSPACE"
}, {
  label: "Community",
  icon: "♡",
  group: "GROWTH"
}, {
  label: "Channels & profiles",
  icon: "▤",
  group: "GROWTH"
}, {
  label: "Integrations",
  icon: "⌘",
  group: "SYSTEM"
}, {
  label: "Database",
  icon: "▥",
  group: "SYSTEM"
}, {
  label: "Telegram",
  icon: "➤",
  group: "SYSTEM"
}, {
  label: "Settings",
  icon: "⚙",
  group: "SYSTEM"
}];
const WORKERS = [{
  name: "Orchestrator",
  role: "Plans, decomposes and assigns tasks",
  icon: "✳",
  color: "violet",
  status: "Active",
  load: 38,
  jobs: 4
}, {
  name: "Research Scout",
  role: "Web research, evidence and sources",
  icon: "⌕",
  color: "blue",
  status: "Active",
  load: 68,
  jobs: 3
}, {
  name: "Script Writer",
  role: "Scripts, captions and prompts",
  icon: "✎",
  color: "orange",
  status: "Active",
  load: 44,
  jobs: 2
}, {
  name: "Video Producer",
  role: "Scenes, voice, captions and rendering",
  icon: "▷",
  color: "pink",
  status: "Busy",
  load: 84,
  jobs: 4
}, {
  name: "Community Manager",
  role: "Natural replies, moderation and triage",
  icon: "♡",
  color: "green",
  status: "Active",
  load: 29,
  jobs: 2
}, {
  name: "Quality & Safety",
  role: "Fact-check, rights and policy gates",
  icon: "✓",
  color: "cyan",
  status: "Active",
  load: 21,
  jobs: 1
}, {
  name: "Voice & Transcript",
  role: "TTS, transcription and timing checks",
  icon: "♫",
  color: "blue",
  status: "Idle",
  load: 8,
  jobs: 0
}, {
  name: "Operations",
  role: "Alerts, retries and recovery",
  icon: "⌘",
  color: "orange",
  status: "Active",
  load: 17,
  jobs: 1
}];
const seedChannels: Channel[] = [{
  id: "sport",
  name: "SportSaga Hindi",
  platform: "YouTube",
  niche: "Sports stories",
  format: "Shorts · 60 sec",
  tone: "Energetic and punchy",
  status: "Not connected",
  cadence: "Every 2 days",
  language: "Hindi",
  prompt: "Write energetic Hindi sports stories. Establish context fast, build tension, verify facts, and close with a memorable takeaway.",
  handle: "",
  approval: "Review before publish",
  timezone: "Asia/Kolkata",
  audience: "Hindi-speaking sports fans"
}, {
  id: "world",
  name: "WorldScope Hindi",
  platform: "YouTube",
  niche: "Geography & amazing world",
  format: "Shorts · 60 sec",
  tone: "Curious and visual",
  status: "Not connected",
  cadence: "Every 2 days",
  language: "Hindi",
  prompt: "Explain remarkable places with curiosity and visual clarity. Verify geography and avoid unsupported sensational claims.",
  handle: "",
  approval: "Review before publish",
  timezone: "Asia/Kolkata",
  audience: "Curious Hindi viewers"
}, {
  id: "auto",
  name: "AutoTorque Hindi",
  platform: "YouTube",
  niche: "Cars & machines",
  format: "Shorts · 60 sec",
  tone: "Technical, accessible",
  status: "Not connected",
  cadence: "Every 2 days",
  language: "Hindi",
  prompt: "Explain vehicle technology clearly. Verify specifications, model years and pricing from reliable sources.",
  handle: "",
  approval: "Review before publish",
  timezone: "Asia/Kolkata",
  audience: "Auto enthusiasts"
}, {
  id: "itihaas",
  name: "Itihaas Raaz",
  platform: "YouTube",
  niche: "History & mystery",
  format: "Long video · 10 min",
  tone: "Suspenseful, well-sourced",
  status: "Not connected",
  cadence: "Sunday",
  language: "Hindi",
  prompt: "Tell history and mystery stories with suspense, distinguish verified facts from theories and cite reliable sources.",
  handle: "",
  approval: "Review before publish",
  timezone: "Asia/Kolkata",
  audience: "Hindi history fans"
}, {
  id: "history",
  name: "HistoryVault Hindi",
  platform: "YouTube",
  niche: "Historical documentary",
  format: "Long video · 10 min",
  tone: "Documentary, grounded",
  status: "Not connected",
  cadence: "Sunday",
  language: "Hindi",
  prompt: "Create historically grounded documentaries, flag disputed claims and maintain chronological clarity.",
  handle: "",
  approval: "Review before publish",
  timezone: "Asia/Kolkata",
  audience: "Hindi documentary viewers"
}, {
  id: "fact",
  name: "FactShock Hindi",
  platform: "YouTube",
  niche: "Science & strange facts",
  format: "Shorts · 60 sec",
  tone: "Fast, curious",
  status: "Not connected",
  cadence: "Every 2 days",
  language: "Hindi",
  prompt: "Make surprising science explainers with accurate sourced claims and a clear takeaway.",
  handle: "",
  approval: "Review before publish",
  timezone: "Asia/Kolkata",
  audience: "Science-curious viewers"
}, {
  id: "biz",
  name: "BizVault Hindi",
  platform: "YouTube",
  niche: "Business stories",
  format: "Long video · 10 min",
  tone: "Cinematic, analytical",
  status: "Not connected",
  cadence: "Sunday",
  language: "Hindi",
  prompt: "Tell business stories through timelines, verified numbers, strategy and measurable context.",
  handle: "",
  approval: "Review before publish",
  timezone: "Asia/Kolkata",
  audience: "Hindi business viewers"
}];
type Job = {
  id: string;
  title: string;
  channel: string;
  type: string;
  status: string;
  progress: number;
  worker: string;
  elapsed: string;
};
const seedJobs: Job[] = [{
  id: "JOB-2048",
  title: "Create 3 Shorts for SportSaga",
  channel: "SportSaga Hindi",
  type: "Video pipeline",
  status: "Running",
  progress: 72,
  worker: "Video Producer",
  elapsed: "02:14"
}, {
  id: "JOB-2047",
  title: "Research electric hypercars",
  channel: "AutoTorque Hindi",
  type: "Research",
  status: "Running",
  progress: 48,
  worker: "Research Scout",
  elapsed: "01:32"
}, {
  id: "JOB-2046",
  title: "Reply to 18 new comments",
  channel: "WorldScope Hindi",
  type: "Community",
  status: "Needs review",
  progress: 100,
  worker: "Community Manager",
  elapsed: "00:41"
}, {
  id: "JOB-2045",
  title: "Draft a history mystery story",
  channel: "Itihaas Raaz",
  type: "Writing",
  status: "Queued",
  progress: 0,
  worker: "Script Writer",
  elapsed: "Queued"
}];
type Comment = {
  id: number;
  user: string;
  initials: string;
  platform: string;
  channel: string;
  age: string;
  text: string;
  intent: string;
  state: string;
  reply: string;
};
const seedComments: Comment[] = [{
  id: 1,
  user: "Amit Kumar",
  initials: "AK",
  platform: "YouTube",
  channel: "SportSaga Hindi",
  age: "4 min ago",
  text: "Bhai, Dhoni ki captaincy pe ek full video banao 🔥",
  intent: "Positive",
  state: "Suggested",
  reply: "Bilkul bhai! 🙌 Dhoni ki captaincy ke game-changing decisions par ek detailed video plan karte hain. Aapka favourite match kaunsa hai?"
}, {
  id: 2,
  user: "Sana Reviews",
  initials: "SR",
  platform: "Instagram",
  channel: "WorldScope Hindi",
  age: "12 min ago",
  text: "Is place ka exact location kya hai? Looks unreal!",
  intent: "Question",
  state: "Suggested",
  reply: "Ye jagah sach mein incredible lagti hai! 🌍 Main location details verify karke share karungi, taaki aap ise map par easily find kar sakein."
}, {
  id: 3,
  user: "Ravi Verma",
  initials: "RV",
  platform: "YouTube",
  channel: "AutoTorque Hindi",
  age: "21 min ago",
  text: "Price galat hai. Current model is more expensive.",
  intent: "Correction",
  state: "Needs review",
  reply: "Thanks for pointing that out, Ravi. 🙏 We’ll re-check the current model price from an official source and correct the information if needed."
}, {
  id: 4,
  user: "Neha Patel",
  initials: "NP",
  platform: "Facebook",
  channel: "Itihaas Raaz",
  age: "38 min ago",
  text: "Amazing research! Part 2 kab aayega?",
  intent: "Positive",
  state: "Suggested",
  reply: "Thank you, Neha! ❤️ Part 2 ka idea note kar liya hai. Release date confirm hote hi update share karenge."
}, {
  id: 5,
  user: "MK Official",
  initials: "MK",
  platform: "YouTube",
  channel: "FactShock Hindi",
  age: "1 hr ago",
  text: "This is fake news, report kar raha hoon.",
  intent: "Dispute",
  state: "Escalated",
  reply: "Aapki concern ke liye thanks. Hum is claim ko dobara verify karenge. Agar correction ki zarurat hui, to description ya video update karenge."
}];
const seedProviders = [{
  name: "OpenAI",
  cap: "LLM",
  model: "Text & reasoning models",
  status: "Connected",
  route: "Primary"
}, {
  name: "Anthropic",
  cap: "LLM",
  model: "Claude · long context",
  status: "Not tested",
  route: "Fallback"
}, {
  name: "Gemini",
  cap: "LLM",
  model: "Multimodal & research",
  status: "Connected",
  route: "Fallback"
}, {
  name: "Tavily",
  cap: "Web search",
  model: "Research & sources",
  status: "Connected",
  route: "Primary"
}, {
  name: "Image provider",
  cap: "Image",
  model: "Image generation API",
  status: "Needs setup",
  route: "Unassigned"
}, {
  name: "Video provider",
  cap: "Video",
  model: "Video generation API",
  status: "Needs setup",
  route: "Unassigned"
}, {
  name: "Voice provider",
  cap: "Voice",
  model: "TTS / STT API",
  status: "Degraded",
  route: "Fallback"
}, {
  name: "Telegram Bot",
  cap: "Notifications",
  model: "Operations alerts",
  status: "Needs setup",
  route: "Notifications"
}];
const titles: Record<Screen, string> = {
  "Overview": "Your workspace, in motion",
  "Live jobs": "One queue. Every moving part.",
  "Workers": "A team of specialists, working in parallel.",
  "Community": "Every comment deserves a real answer.",
  "Channels & profiles": "One profile per channel, page and identity.",
  "Integrations": "Connect the tools behind the work.",
  "Database": "Where Ghost keeps its memory.",
  "Telegram": "The right alert, at the right time.",
  "Settings": "Make Ghost work your way."
};
const subs: Record<Screen, string> = {
  "Overview": "See operations, community workload and worker capacity without the noise.",
  "Live jobs": "Inspect job state, progress, assignment, retries and review gates.",
  "Workers": "Assign concurrent tasks, inspect capacity and configure specialist roles.",
  "Community": "Context-aware replies, calm moderation and human control.",
  "Channels & profiles": "Add accounts, connect them securely, and customize each identity independently.",
  "Integrations": "Manage multiple providers per capability with explicit health and fallback rules.",
  "Database": "Choose hosted Supabase or your own PostgreSQL deployment.",
  "Telegram": "Manage bot setup, notification events, and alert preferences.",
  "Settings": "Workspace defaults, safety, concurrency, budgets and access."
};
function Badge({
  children,
  tone = "neutral"
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={"g-badge " + tone}><i />{children}</span>;
}
function Btn({
  children,
  onClick,
  variant = "secondary",
  small = false
}: {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost";
  small?: boolean;
}) {
  return <button className={"g-button " + variant + (small ? " small" : "")} onClick={onClick}>{children}</button>;
}
function Toggle({
  label,
  detail,
  initial = false
}: {
  label: string;
  detail?: string;
  initial?: boolean;
}) {
  const [on, setOn] = useState(initial);
  return <div className="g-toggle-row"><div><strong>{label}</strong>{detail && <small>{detail}</small>}</div><button type="button" role="switch" aria-checked={on} className={"g-toggle " + (on ? "on" : "")} onClick={() => setOn(!on)}><i /></button></div>;
}
function Field({
  label,
  value,
  placeholder,
  type = "text",
  onChange,
  required = false
}: {
  label: string;
  value?: string;
  placeholder?: string;
  type?: string;
  onChange?: (v: string) => void;
  required?: boolean;
}) {
  return <label className="g-field"><span>{label}{required && <b className="required"> *</b>}</span><input type={type} required={required} value={value} placeholder={placeholder} onChange={e => onChange?.(e.target.value)} /></label>;
}
function Progress({
  value
}: {
  value: number;
}) {
  return <div className="g-progress"><i style={{
      width: value + "%"
    }} /></div>;
}
export const GhostOperationsCenter = () => {
  const [screen, setScreen] = useState<Screen>("Overview"),
    [mobile, setMobile] = useState(false),
    [jobs, setJobs] = useState(seedJobs),
    [channels, setChannels] = useState(seedChannels),
    [workers] = useState(WORKERS),
    [selectedId, setSelectedId] = useState("sport");
  const selected = channels.find(c => c.id === selectedId) || channels[0];
  const [query, setQuery] = useState(""),
    [filter, setFilter] = useState("All"),
    [profileTab, setProfileTab] = useState("Identity & voice"),
    [editPrompt, setEditPrompt] = useState(selected.prompt);
  const [comments, setComments] = useState(seedComments),
    [activeComment, setActiveComment] = useState(1),
    [commentQuery, setCommentQuery] = useState(""),
    [replyDrafts, setReplyDrafts] = useState<Record<number, string>>({});
  const chosenComment = comments.find(c => c.id === activeComment) || comments[0];
  const [replyTone, setReplyTone] = useState("Natural & friendly"),
    [sendMode, setSendMode] = useState("Review before sending"),
    [providers] = useState(seedProviders),
    [providerFilter, setProviderFilter] = useState("All"),
    [dbMode, setDbMode] = useState("Supabase cloud"),
    [dbHealth, setDbHealth] = useState<{ status: string; checks?: Record<string, string>; message?: string } | null>(null),
    [dbHealthLoading, setDbHealthLoading] = useState(false),
    [telegramOn, setTelegramOn] = useState(false),
    [telegramEvents, setTelegramEvents] = useState(["Job failed", "Needs human review", "Worker offline", "Provider degraded", "Budget threshold"]),
    [settingsTab, setSettingsTab] = useState("General"),
    [autoAssign, setAutoAssign] = useState(true),
    [toast, setToast] = useState("");
  const [wizard, setWizard] = useState(false),
    [step, setStep] = useState(1),
    [platform, setPlatform] = useState("YouTube"),
    [accountType, setAccountType] = useState("Channel"),
    [wName, setWName] = useState(""),
    [wHandle, setWHandle] = useState(""),
    [wNiche, setWNiche] = useState(""),
    [wAudience, setWAudience] = useState(""),
    [wLanguage, setWLanguage] = useState("Hindi"),
    [wFormat, setWFormat] = useState("Shorts · 60 sec"),
    [wTone, setWTone] = useState("Natural and energetic"),
    [wCadence, setWCadence] = useState("Every 2 days"),
    [wTimezone, setWTimezone] = useState("Asia/Kolkata"),
    [wPrompt, setWPrompt] = useState("Create original, accurate, channel-specific content. Verify factual claims and follow platform, rights, safety and approval rules."),
    [wApproval, setWApproval] = useState("Review before publish"),
    [oauthAttempt, setOauthAttempt] = useState(false);
  const checkDatabaseHealth = async () => {
    setDbHealthLoading(true);
    try {
      const apiBase = (import.meta.env.VITE_GHOST_API_URL || "http://localhost:8000").replace(/\/$/, "");
      const response = await fetch(`${apiBase}/health/ready`, { headers: { Accept: "application/json" } });
      const payload = await response.json();
      setDbHealth(payload);
      notify(response.ok ? "Backend readiness check completed." : "Backend reports a dependency issue.");
    } catch {
      setDbHealth({ status: "unreachable", message: "Could not reach the Ghost API. Check VITE_GHOST_API_URL, API availability, and CORS settings." });
      notify("Ghost API could not be reached.");
    } finally {
      setDbHealthLoading(false);
    }
  };
  const notify = (s: string) => {
    setToast(s);
    window.setTimeout(() => setToast(""), 3000);
  };
  const go = (s: Screen) => {
    setScreen(s);
    setMobile(false);
    setQuery("");
  };
  const connected = channels.filter(c => c.status === "Connected").length;
  const filteredJobs = useMemo(() => jobs.filter(j => (filter === "All" || j.status === filter) && (j.title + j.channel + j.worker + j.id).toLowerCase().includes(query.toLowerCase())), [jobs, filter, query]);
  const filteredComments = comments.filter(c => (c.text + c.user + c.channel).toLowerCase().includes(commentQuery.toLowerCase()));
  const filteredProviders = providers.filter(p => (providerFilter === "All" || p.cap === providerFilter) && (p.name + p.model).toLowerCase().includes(query.toLowerCase()));
  const openWizard = () => {
    setStep(1);
    setPlatform("YouTube");
    setAccountType("Channel");
    setWName("");
    setWHandle("");
    setWNiche("");
    setWAudience("");
    setWLanguage("Hindi");
    setWFormat("Shorts · 60 sec");
    setWTone("Natural and energetic");
    setWCadence("Every 2 days");
    setWTimezone("Asia/Kolkata");
    setWPrompt("Create original, accurate, channel-specific content. Verify factual claims and follow platform, rights, safety and approval rules.");
    setWApproval("Review before publish");
    setOauthAttempt(false);
    setWizard(true);
  };
  const createDraft = () => {
    if (!wName.trim() || !wNiche.trim()) {
      notify("Profile name aur niche required hain.");
      setStep(3);
      return;
    }
    const c: Channel = {
      id: "draft-" + Date.now(),
      name: wName.trim(),
      platform,
      niche: wNiche.trim(),
      format: wFormat,
      tone: wTone,
      status: "Not connected",
      cadence: wCadence,
      language: wLanguage,
      prompt: wPrompt,
      handle: wHandle.trim(),
      approval: wApproval,
      timezone: wTimezone,
      audience: wAudience
    };
    setChannels(p => [c, ...p]);
    setSelectedId(c.id);
    setEditPrompt(c.prompt);
    setWizard(false);
    go("Channels & profiles");
    notify("Profile draft saved. OAuth verification is required before connection.");
  };
  const newJob = () => {
    const id = "JOB-" + (2049 + jobs.length - 4);
    setJobs(p => [{
      id,
      title: "New workspace task",
      channel: selected.name,
      type: "Custom task",
      status: "Queued",
      progress: 0,
      worker: "Orchestrator",
      elapsed: "Queued"
    }, ...p]);
    notify("Demo job added locally; no worker process launched.");
    go("Live jobs");
  };
  return <div className="ghost-ops"><aside className={"g-sidebar " + (mobile ? "mobile" : "")}><div className="g-brand"><div className="g-brand-icon">g<i /></div><div><strong>ghost<span>.</span></strong><small>OPERATIONS CENTER</small></div><button className="g-mobile-x" onClick={() => setMobile(false)}>×</button></div><button className="g-workspace" onClick={() => notify("Workspace switch requires account integration.")}><span className="g-workspace-avatar">G</span><span><strong>Ghost Studio</strong><small>Personal workspace</small></span><b>⌄</b></button>{["WORKSPACE", "GROWTH", "SYSTEM"].map(group => <div className="g-nav-group" key={group}><div className="g-nav-label">{group}</div>{NAV.filter(n => n.group === group).map(n => <button key={n.label} className={"g-nav-item " + (screen === n.label ? "active" : "")} onClick={() => go(n.label)}><span className="g-nav-icon">{n.icon}</span><span>{n.label}</span>{n.label === "Community" && <i className="g-nav-count">18</i>}{n.label === "Live jobs" && <i className="g-nav-live" />}</button>)}</div>)}<div className="g-sidebar-bottom"><div className="g-health-card"><div className="g-health-title"><i /> PREVIEW ENVIRONMENT <span>DEMO</span></div><strong>Ready for integration</strong><p>Connect APIs and the worker runtime to see real states here.</p><button onClick={() => go("Integrations")}>Configure services <b>→</b></button></div><button className="g-user" onClick={() => go("Settings")}><span className="g-user-avatar">L</span><span><strong>Workspace owner</strong><small>Administrator</small></span><i>···</i></button></div></aside>
{mobile && <button className="g-scrim" onClick={() => setMobile(false)} aria-label="Close navigation" />}<main className="g-main"><header className="g-topbar"><div className="g-top-crumb"><button className="g-menu" onClick={() => setMobile(true)}>☰</button><span>Ghost</span><b>/</b><strong>{screen}</strong></div><div className="g-top-right"><span className="g-demo-status"><i /> Demo data <b>·</b> not connected</span><button className="g-bell" onClick={() => go("Telegram")}>♧<i /></button><span className="g-top-avatar">L</span></div></header><SupabaseAuthPanel /><div className="g-page"><div className="g-page-head"><div><div className="g-eyebrow"><i /> GHOST WORKSPACE <b>/</b> {screen.toUpperCase()}</div><h1>{titles[screen]}</h1><p>{subs[screen]}</p></div><div className="g-head-actions">{screen === "Overview" && <><Btn onClick={() => go("Live jobs")}>View activity ↗</Btn><Btn variant="primary" onClick={newJob}>＋ New job</Btn></>}{screen === "Live jobs" && <Btn variant="primary" onClick={newJob}>＋ Create job</Btn>}{screen === "Workers" && <Btn variant="primary" onClick={() => notify("A worker requires a capability contract and backend adapter.")}>＋ Register worker</Btn>}{screen === "Channels & profiles" && <Btn variant="primary" onClick={openWizard}>＋ Add channel / page</Btn>}</div></div>
{screen === "Overview" && <div className="g-screen"><div className="g-welcome"><span className="g-welcome-spark">✳</span><div><strong>Your studio is ready to be connected.</strong><p>Job, worker and event counts are illustrative. Profile counts reflect entries in this preview.</p></div><button onClick={() => go("Channels & profiles")}>Set up accounts →</button></div><div className="g-stat-grid"><div className="g-stat"><div className="g-stat-label">Jobs in motion <span className="g-stat-icon violet">◷</span></div><div className="g-stat-value">06 <small>sample</small></div><div className="g-stat-foot">3 running · 1 review</div></div><div className="g-stat"><div className="g-stat-label">Worker roles <span className="g-stat-icon green">⠿</span></div><div className="g-stat-value">08 <small>specialists</small></div><div className="g-stat-foot"><span className="g-dot green" /> Load values are demo</div></div><div className="g-stat"><div className="g-stat-label">Connected profiles <span className="g-stat-icon orange">▤</span></div><div className="g-stat-value">{connected}<small> / {channels.length}</small></div><div className="g-stat-foot"><span className="g-dot orange" />{channels.length - connected} need authorization</div></div><div className="g-stat"><div className="g-stat-label">Integrations <span className="g-stat-icon blue">⌘</span></div><div className="g-stat-value">{providers.length}<small> demo entries</small></div><div className="g-stat-foot"><span className="g-dot green" /> Provider state not live</div></div></div><div className="g-overview-grid"><section className="g-panel"><div className="g-panel-heading"><div><h2>Live operations</h2><p>Latest jobs moving through the pipeline</p></div><button className="g-link" onClick={() => go("Live jobs")}>All jobs →</button></div><div className="g-table-scroll"><table className="g-table"><thead><tr><th>JOB</th><th>STATUS</th><th>PROGRESS</th><th>WORKER</th></tr></thead><tbody>{jobs.slice(0, 4).map(j => <tr key={j.id}><td><strong>{j.title}</strong><small>{j.id} · {j.channel}</small></td><td><Badge tone={j.status === "Running" ? "green" : j.status === "Needs review" ? "orange" : "neutral"}>{j.status}</Badge></td><td><Progress value={j.progress} /><small>{j.progress}%</small></td><td>{j.worker}</td></tr>)}</tbody></table></div><div className="g-panel-foot"><span><i className="g-dot violet" /> Example jobs · not a live feed</span><button onClick={() => notify("Live refresh requires runtime events.")}>↻ Refresh</button></div></section><section className="g-panel"><div className="g-panel-heading"><div><h2>Worker fleet</h2><p>Specialist capacity overview</p></div><button className="g-link" onClick={() => go("Workers")}>Manage →</button></div><div className="g-worker-mini-list">{workers.slice(0, 5).map(w => <div className="g-worker-mini-row" key={w.name}><span className={"g-worker-avatar " + w.color}>{w.icon}</span><div className="g-worker-mini-main"><strong>{w.name}</strong><small>{w.jobs} assigned tasks</small><Progress value={w.load} /></div><b>{w.load}%</b></div>)}</div></section></div><div className="g-overview-grid lower"><section className="g-panel"><div className="g-panel-heading"><div><h2>Needs attention</h2><p>Suggested next steps</p></div></div>{[{
                t: "Connect channel accounts",
                d: "Profile templates ready; OAuth not configured.",
                s: "Channels & profiles" as Screen
              }, {
                t: "Review community replies",
                d: "Sensitive and uncertain replies stay with a human.",
                s: "Community" as Screen
              }, {
                t: "Configure provider secrets",
                d: "Connect and validate APIs before real jobs.",
                s: "Integrations" as Screen
              }].map(a => <div className="g-attention" key={a.t}><span className="g-att-icon violet">✳</span><div><strong>{a.t}</strong><p>{a.d}</p></div><button onClick={() => go(a.s)}>Open →</button></div>)}</section><section className="g-panel"><div className="g-panel-heading"><div><h2>System activity</h2><p>Example operations events</p></div></div>{[{
                t: "Database check example",
                d: "Status is illustrative.",
                time: "2 min ago"
              }, {
                t: "Voice provider rate limit",
                d: "Sample fallback route.",
                time: "5 min ago"
              }, {
                t: "Community queue example",
                d: "Replies remain unsent.",
                time: "11 min ago"
              }].map((e, i) => <div className="g-event" key={i}><span className="g-event-icon violet">{i === 0 ? "✓" : i === 1 ? "!" : "♡"}</span><div><strong>{e.t}</strong><p>{e.d}</p><small>{e.time}</small></div></div>)}</section></div></div>}
{screen === "Live jobs" && <div className="g-screen"><div className="g-small-stats">{[{
              a: "Running",
              b: "06",
              c: "Sample executing"
            }, {
              a: "Queued",
              b: "08",
              c: "Waiting for capacity"
            }, {
              a: "Needs review",
              b: "12",
              c: "Approval required"
            }, {
              a: "Failed today",
              b: "02",
              c: "Illustrative only"
            }].map(s => <div className="g-small-stat" key={s.a}><span>{s.a}</span><strong>{s.b}</strong><small>{s.c}</small></div>)}</div><section className="g-panel"><div className="g-toolbar"><div className="g-search"><span>⌕</span><input placeholder="Search jobs, channels or workers..." value={query} onChange={e => setQuery(e.target.value)} /></div><select value={filter} onChange={e => setFilter(e.target.value)}><option>All</option><option>Running</option><option>Queued</option><option>Needs review</option></select><Btn onClick={() => {
                setFilter("All");
                setQuery("");
              }}>Reset</Btn></div><div className="g-table-scroll"><table className="g-table wide"><thead><tr><th>JOB / CHANNEL</th><th>TYPE</th><th>STATUS</th><th>PROGRESS</th><th>WORKER</th><th>ELAPSED</th></tr></thead><tbody>{filteredJobs.map(j => <tr key={j.id}><td><strong>{j.title}</strong><small>{j.id} · {j.channel}</small></td><td>{j.type}</td><td><Badge tone={j.status === "Running" ? "green" : j.status === "Needs review" ? "orange" : "neutral"}>{j.status}</Badge></td><td><Progress value={j.progress} /><small>{j.progress}%</small></td><td>{j.worker}</td><td>{j.elapsed}</td></tr>)}</tbody></table>{filteredJobs.length === 0 && <div className="g-empty">No matching jobs.</div>}</div><div className="g-panel-foot"><span>Sample records</span><span>Live workers require backend services</span></div></section><div className="g-two-grid"><section className="g-panel g-panel-pad"><h2>Queue controls</h2><p className="g-panel-desc">Limit throughput, retries and cost exposure.</p><Toggle label="Automatic transient retries" initial /><Toggle label="Pause on budget threshold" initial /><Toggle label="Approval before publish" initial /><div className="g-form-grid"><Field label="Maximum concurrent jobs" value="6" /><Field label="Retry attempts" value="2" /></div></section><section className="g-panel g-panel-pad"><h2>Pipeline stages</h2><p className="g-panel-desc">Every output passes required gates.</p>{["Intake & permissions", "Research & generation", "Quality & rights checks", "Human review", "Export / approved publish"].map((x, i) => <div className="g-pipeline-row" key={x}><span>{i + 1}</span><strong>{x}</strong><small>{i === 3 ? "Approval" : i === 4 ? "Separate action" : "Required"}</small></div>)}</section></div></div>}
{screen === "Workers" && <div className="g-screen"><div className="g-worker-overview"><div><i className="g-dot green" /> <strong>Worker role registry</strong><span> · illustrative load, not live telemetry</span></div><label>Auto-assign tasks <button role="switch" aria-checked={autoAssign} className={"g-toggle " + (autoAssign ? "on" : "")} onClick={() => setAutoAssign(!autoAssign)}><i /></button></label></div><div className="g-worker-grid">{workers.map(w => <article className="g-worker-card" key={w.name}><div className="g-worker-card-top"><span className={"g-worker-avatar large " + w.color}>{w.icon}</span><Badge tone={w.load > 80 ? "orange" : "green"}>{w.status}</Badge></div><h3>{w.name}</h3><p>{w.role}</p><div className="g-worker-numbers"><span><small>Assigned</small><strong>{w.jobs}</strong></span><span><small>Load estimate</small><strong>{w.load}%</strong></span></div><Progress value={w.load} /><div className="g-worker-card-foot"><span><i className="g-dot green" />{w.load > 80 ? "Near capacity" : "Ready"}</span><button onClick={() => {
                  setQuery(w.name);
                  go("Live jobs");
                }}>View queue →</button></div></article>)}</div><section className="g-panel"><div className="g-panel-heading"><div><h2>Parallel orchestration model</h2><p>Dependent steps wait; independent work runs concurrently.</p></div><Badge tone="violet">Architecture preview</Badge></div><div className="g-flow">{[{
                t: "Job intake",
                d: "Validate identity"
              }, {
                t: "Orchestrator",
                d: "Build task graph"
              }, {
                t: "Specialist pool",
                d: "Bounded parallel work"
              }, {
                t: "Quality gate",
                d: "Validate / escalate"
              }, {
                t: "Deliver",
                d: "Draft / approval"
              }].map((s, i) => <React.Fragment key={s.t}><div className={"g-flow-step " + (i === 2 ? "highlight" : "")}><span>0{i + 1}</span><strong>{s.t}</strong><small>{s.d}</small></div>{i < 4 && <span className="g-flow-arrow">→</span>}</React.Fragment>)}</div><div className="g-info-banner"><b>✳</b><p>Use per-workspace/account/provider limits, durable checkpoints, bounded retries, idempotency, dead-letter queue and explicit permissions.</p></div></section></div>}
{screen === "Community" && <div className="g-screen"><div className="g-small-stats">{[{
              a: "New comments",
              b: "18",
              c: "Sample across platforms"
            }, {
              a: "Suggested replies",
              b: "12",
              c: "Awaiting review"
            }, {
              a: "Escalated",
              b: "03",
              c: "Human attention"
            }, {
              a: "Avg. response",
              b: "14m",
              c: "Illustrative value"
            }].map(s => <div className="g-small-stat" key={s.a}><span>{s.a}</span><strong>{s.b}</strong><small>{s.c}</small></div>)}</div><div className="g-community-layout"><section className="g-panel g-inbox"><div className="g-inbox-tools"><div className="g-search"><span>⌕</span><input placeholder="Search comments..." value={commentQuery} onChange={e => setCommentQuery(e.target.value)} /></div><span className="g-preview-pill">Preview inbox</span></div><div className="g-comment-list">{filteredComments.map(c => <button className={"g-comment " + (activeComment === c.id ? "selected" : "")} key={c.id} onClick={() => setActiveComment(c.id)}><span className="g-comment-avatar">{c.initials}</span><div className="g-comment-body"><div className="g-comment-meta"><strong>{c.user}</strong><span>{c.age}</span></div><div className="g-comment-channel">{c.platform} · {c.channel}</div><p>{c.text}</p><div className="g-comment-badges"><Badge tone={c.intent === "Positive" ? "green" : c.intent === "Question" ? "blue" : "orange"}>{c.intent}</Badge><Badge tone={c.state === "Escalated" ? "orange" : c.state === "Approved" ? "green" : "neutral"}>{c.state}</Badge></div></div></button>)}</div><div className="g-panel-foot"><span>Account binding is required before reply</span><button onClick={() => notify("Inbox sync needs official platform APIs.")}>↻ Sync</button></div></section><section className="g-panel g-reply"><div className="g-reply-head"><div><div className="g-eyebrow">REPLY WORKSPACE</div><h2>Reply to {chosenComment.user}</h2></div><Badge tone={chosenComment.state === "Escalated" ? "orange" : "violet"}>{chosenComment.state}</Badge></div><div className="g-original"><div><span>ORIGINAL COMMENT</span><span>{chosenComment.platform}</span></div><p>{chosenComment.text}</p><small>{chosenComment.channel} · {chosenComment.age}</small></div><div className="g-tone-select"><label>Reply voice</label><select value={replyTone} onChange={e => setReplyTone(e.target.value)}><option>Natural & friendly</option><option>Energetic & playful</option><option>Helpful & informative</option><option>Calm & professional</option><option>Short & casual</option></select></div><div className="g-reply-edit-head"><label>Suggested reply</label><button className="g-link" onClick={() => setReplyDrafts(v => ({
                  ...v,
                  [chosenComment.id]: chosenComment.reply
                }))}>↻ Reset draft</button></div><textarea className="g-reply-draft" value={replyDrafts[chosenComment.id] ?? chosenComment.reply} onChange={e => setReplyDrafts(v => ({
                ...v,
                [chosenComment.id]: e.target.value
              }))} /><div className="g-reply-tip"><b>✳</b><p><strong>Natural, not robotic.</strong> Address the actual point, match language, avoid repetitive phrasing, verify corrections and escalate sensitive topics.</p></div><div className="g-send-policy"><div><strong>Sending policy</strong><small>High-risk replies always require human review.</small></div><select value={sendMode} onChange={e => setSendMode(e.target.value)}><option>Review before sending</option><option>Draft only</option><option>Low-risk auto-send (future)</option></select></div><div className="g-reply-actions"><Btn onClick={() => {
                  setComments(v => v.map(c => c.id === chosenComment.id ? {
                    ...c,
                    state: "Saved draft"
                  } : c));
                  notify("Reply draft saved locally.");
                }}>Save draft</Btn><Btn variant="primary" onClick={() => {
                  setComments(v => v.map(c => c.id === chosenComment.id ? {
                    ...c,
                    state: "Needs review"
                  } : c));
                  notify(sendMode === "Draft only" ? "Draft saved; nothing sent." : "Added to local review queue; nothing sent.");
                }}>Approve for queue →</Btn></div><div className="g-notsent">Preview only · no response sent to an account</div></section></div><section className="g-panel g-guardrails"><div className="g-panel-heading"><div><h2>Community guardrails</h2><p>Natural replies, moderation and accountability.</p></div></div><div className="g-guard-grid"><div><strong>♡ Personal & relevant</strong><p>Use thread context; never invent personal experiences or promises.</p></div><div><strong>⚑ Escalate uncertainty</strong><p>Disputes, private information, threats and high-stakes issues need human review.</p></div><div><strong>✓ Safe sending</strong><p>Auto-send disabled by default; allow-lists, rate limits and audit logs required.</p></div></div></section></div>}
{screen === "Channels & profiles" && <div className="g-screen"><SavedProfilesPanel /><div className="g-channel-toolbar"><div className="g-search"><span>⌕</span><input placeholder="Search channel or profile..." value={query} onChange={e => setQuery(e.target.value)} /></div><div className="g-account-summary"><span><i className="g-dot green" />{connected} connected</span><span><i className="g-dot orange" />{channels.length - connected} need setup</span></div><Btn variant="primary" onClick={openWizard}>＋ Add channel / page</Btn></div><div className="g-profile-layout"><section className="g-panel g-channel-list"><div className="g-panel-heading"><div><h2>Accounts & profiles</h2><p>Independent settings per profile</p></div><Badge>{channels.length} profiles</Badge></div>{channels.filter(c => (c.name + c.platform + c.niche).toLowerCase().includes(query.toLowerCase())).map(c => <button key={c.id} className={"g-channel-item " + (selectedId === c.id ? "selected" : "")} onClick={() => {
                setSelectedId(c.id);
                setEditPrompt(c.prompt);
              }}><span className={"g-channel-letter " + c.platform.toLowerCase()}>{c.platform === "YouTube" ? "YT" : c.platform === "Instagram" ? "IG" : "f"}</span><span className="g-channel-list-name"><strong>{c.name}</strong><small>{c.platform} · {c.niche}</small><small>{c.format}</small><Badge tone={c.status === "Connected" ? "green" : "orange"}>{c.status}</Badge></span><b className="g-chevron">›</b></button>)}<button className="g-add-channel-row" onClick={openWizard}>＋ Add another account or page</button></section><section className="g-panel g-profile-editor"><div className="g-panel-heading"><div><div className="g-eyebrow">PROFILE CONFIGURATION</div><h2>{selected.name}</h2><p>Customize this profile independently.</p></div><Badge tone={selected.status === "Connected" ? "green" : "orange"}>{selected.status}</Badge></div><div className="g-profile-metadata"><div><small>Platform</small><strong>{selected.platform}</strong></div><div><small>Format</small><strong>{selected.format}</strong></div><div><small>Authorization</small><strong>{selected.status === "Connected" ? "Authorized" : "Required"}</strong></div></div><div className="g-tabs">{["Identity & voice", "Content types", "Provider routing", "Schedule", "Connection"].map(t => <button key={t} className={profileTab === t ? "active" : ""} onClick={() => setProfileTab(t)}>{t}</button>)}</div>
{profileTab === "Identity & voice" && <div className="g-profile-form"><div className="g-form-grid"><Field label="Profile name" value={selected.name} required onChange={v => setChannels(p => p.map(c => c.id === selected.id ? {
                    ...c,
                    name: v
                  } : c))} /><Field label="Public handle / page URL" value={selected.handle} placeholder="Optional" onChange={v => setChannels(p => p.map(c => c.id === selected.id ? {
                    ...c,
                    handle: v
                  } : c))} /><Field label="Content niche" value={selected.niche} required onChange={v => setChannels(p => p.map(c => c.id === selected.id ? {
                    ...c,
                    niche: v
                  } : c))} /><label className="g-field"><span>Language</span><select value={selected.language} onChange={e => setChannels(p => p.map(c => c.id === selected.id ? {
                      ...c,
                      language: e.target.value
                    } : c))}><option>Hindi</option><option>English</option><option>Hindi + English</option><option>Gujarati</option><option>Other</option></select></label><label className="g-field"><span>Brand tone</span><select value={selected.tone} onChange={e => setChannels(p => p.map(c => c.id === selected.id ? {
                      ...c,
                      tone: e.target.value
                    } : c))}>{["Energetic and punchy", "Curious and visual", "Technical, accessible", "Suspenseful, well-sourced", "Documentary, grounded", "Natural and energetic", "Custom brand voice"].map(x => <option key={x}>{x}</option>)}</select></label><label className="g-field"><span>Default format</span><select value={selected.format} onChange={e => setChannels(p => p.map(c => c.id === selected.id ? {
                      ...c,
                      format: e.target.value
                    } : c))}>{["Shorts · 60 sec", "Long video · 10 min", "Reel · 30 sec", "Reel · 60 sec", "Image post", "Carousel", "Text post", "Custom format"].map(x => <option key={x}>{x}</option>)}</select></label><label className="g-field full"><span>Custom system prompt</span><textarea rows={6} value={editPrompt} onChange={e => setEditPrompt(e.target.value)} /><small>System safety, permissions, platform rules, rights and budgets cannot be overridden.</small></label></div><div className="g-profile-actions"><Btn onClick={() => setEditPrompt(selected.prompt)}>Reset prompt</Btn><Btn onClick={() => notify("Prompt preview generated locally.")}>Preview prompt</Btn><Btn variant="primary" onClick={() => {
                    setChannels(p => p.map(c => c.id === selected.id ? {
                      ...c,
                      prompt: editPrompt
                    } : c));
                    notify("Profile updated in local preview state.");
                  }}>Save profile</Btn></div></div>}
{profileTab === "Content types" && <div className="g-profile-form"><label className="g-field"><span>Primary content type</span><select defaultValue="Story-first Short"><option>Story-first Short</option><option>Explainer Documentary</option><option>Top 5 Facts</option><option>Tutorial</option><option>Carousel / image post</option><option>Community response</option><option>Custom content type</option></select></label><div className="g-content-type-grid">{["Hook", "Context", "Core story", "Payoff", "CTA"].map((t, i) => <div key={t}><span>0{i + 1}</span><strong>{t}</strong><small>{["0–3s", "3–10s", "10–42s", "42–55s", "55–60s"][i]}</small></div>)}</div><Toggle label="Validate duration and section order" initial /><Toggle label="Require sources for factual claims" initial /><Toggle label="Isolate templates to this profile" initial /><Btn variant="primary" onClick={() => notify("Content type saved locally.")}>Save content type</Btn></div>}
{profileTab === "Provider routing" && <div className="g-profile-form"><p className="g-panel-desc">Provider overrides scoped to this profile.</p>{["Script / LLM", "Web research", "Image generation", "Video generation", "Voiceover"].map((t, i) => <div className="g-route-row" key={t}><div><strong>{t}</strong><small>Preferred provider</small></div><select defaultValue={["OpenAI", "Tavily", "Image provider", "Video provider", "Voice provider"][i]}>{providers.map(p => <option key={p.name}>{p.name}</option>)}</select></div>)}<Btn variant="primary" onClick={() => notify("Routing saved locally.")}>Save routing</Btn></div>}
{profileTab === "Schedule" && <div className="g-profile-form"><div className="g-form-grid"><label className="g-field"><span>Publishing cadence</span><select value={selected.cadence} onChange={e => setChannels(p => p.map(c => c.id === selected.id ? {
                      ...c,
                      cadence: e.target.value
                    } : c))}>{["Manual", "Every day", "Every 2 days", "Three times a week", "Sunday", "Custom schedule"].map(x => <option key={x}>{x}</option>)}</select></label><Field label="Timezone" value={selected.timezone} onChange={v => setChannels(p => p.map(c => c.id === selected.id ? {
                    ...c,
                    timezone: v
                  } : c))} /><label className="g-field"><span>Approval mode</span><select value={selected.approval} onChange={e => setChannels(p => p.map(c => c.id === selected.id ? {
                      ...c,
                      approval: e.target.value
                    } : c))}><option>Review before publish</option><option>Draft only</option><option>Approved low-risk only</option></select></label></div><Toggle label="Enforce minimum interval between Shorts" initial /><Toggle label="Pause jobs when account expires" initial /><Btn variant="primary" onClick={() => notify("Schedule saved locally.")}>Save schedule</Btn></div>}
{profileTab === "Connection" && <div className="g-profile-form"><div className="g-connection-callout"><span className="g-connection-mark">{selected.platform === "YouTube" ? "YT" : selected.platform === "Instagram" ? "IG" : "f"}</span><div><h3>{selected.platform} authorization</h3><p>Connection status changes only after OAuth callback and permission validation.</p><Badge tone="orange">{selected.status}</Badge></div></div><div className="g-info-banner"><b>ⓘ</b><p>Production must use the official OAuth consent flow and load authorized accounts from its response. A typed handle or ID is not proof of ownership. This canvas has no live OAuth connector.</p></div><Btn variant="primary" onClick={() => notify("OAuth client ID, redirect URI and token exchange are not configured.")}>Start secure authorization ↗</Btn></div>}</section></div></div>}
{screen === "Integrations" && <div className="g-screen"><ChannelPagesConnectionCenter /><div className="g-provider-summary"><div><strong>{providers.length} provider entries</strong><p>Multiple providers per capability with health and fallback settings.</p></div><Btn onClick={() => notify("Provider setup requires secure server-side secret storage.")}>＋ Add provider</Btn></div><section className="g-panel"><div className="g-toolbar"><div className="g-search"><span>⌕</span><input placeholder="Search providers..." value={query} onChange={e => setQuery(e.target.value)} /></div><div className="g-filter-pills">{["All", "LLM", "Web search", "Image", "Video", "Voice", "Notifications"].map(x => <button key={x} className={providerFilter === x ? "active" : ""} onClick={() => setProviderFilter(x)}>{x}</button>)}</div></div><div className="g-provider-grid">{filteredProviders.map(p => <article className="g-provider-card" key={p.name}><div className="g-provider-card-top"><span className="g-provider-logo">{p.name.slice(0, 1)}</span><Badge tone={p.status === "Connected" ? "green" : p.status === "Degraded" || p.status === "Needs setup" ? "orange" : "neutral"}>{p.status}</Badge></div><h3>{p.name}</h3><p>{p.model}</p><div className="g-provider-meta"><span><small>Capability</small><strong>{p.cap}</strong></span><span><small>Route</small><strong>{p.route}</strong></span></div><div className="g-provider-actions"><Btn small onClick={() => notify("Provider test requires a live adapter.")}>Test connection</Btn><button className="g-link" onClick={() => notify("Configuration requires backend secret storage.")}>Configure ↗</button></div></article>)}</div></section><section className="g-panel g-routing"><div className="g-panel-heading"><div><h2>Routing & fallback rules</h2><p>No silent paid calls or unverified fallback.</p></div><Badge tone="violet">Policy preview</Badge></div><div className="g-route-row"><div><strong>LLM / text</strong><small>Retry transient errors, then approved fallback</small></div><select defaultValue="Task-aware routing"><option>Task-aware routing</option><option>Lowest cost</option><option>Highest quality</option><option>Manual only</option></select><Badge tone="green">Budget guard</Badge></div><div className="g-route-row"><div><strong>Media generation</strong><small>Validate format, duration, cost and endpoint health</small></div><select defaultValue="Validated providers only"><option>Validated providers only</option><option>Manual selection</option></select><Badge tone="orange">No silent spend</Badge></div></section></div>}
{screen === "Database" && <div className="g-screen">
  <div className="g-db-choice-grid">{[{
    name: "Local SQLite",
    sub: "Simple local-first database for a PC install",
    icon: "▣",
    tone: "green",
    lines: ["No separate database server required", "Stored in the local ghost.db file", "Best starting mode for local development"]
  }, {
    name: "Local PostgreSQL",
    sub: "Your own PostgreSQL server",
    icon: "▥",
    tone: "blue",
    lines: ["Install and start PostgreSQL", "Create a dedicated Ghost database/user", "Keep credentials in backend environment"]
  }, {
    name: "Supabase cloud",
    sub: "Managed PostgreSQL, hosted by Supabase",
    icon: "☁",
    tone: "green",
    lines: ["Create a Supabase project", "Use its PostgreSQL connection string", "Keep credentials server-side only"]
  }].map(d => <button key={d.name} className={"g-db-card " + (dbMode === d.name ? "selected" : "")} onClick={() => setDbMode(d.name)}><div className="g-db-icon-row"><span className={d.tone}>{d.icon}</span>{dbMode === d.name && <b>✓ Selected</b>}</div><h2>{d.name}</h2><p>{d.sub}</p>{d.lines.map(x => <small key={x}>✓ {x}</small>)}</button>)}</div>
  <section className="g-panel g-db-config">
    <div className="g-panel-heading"><div><h2>Database connection status</h2><p>{dbMode} · mode selection is a guide; the backend's DATABASE_URL determines the actual connection.</p></div><Badge tone={dbHealth?.status === "ok" ? "green" : dbHealth ? "orange" : "neutral"}>{dbHealth?.status || "Not checked"}</Badge></div>
    <div className="g-info-banner"><b>ⓘ</b><p>This page never stores or sends database passwords. Local SQLite is the default when <code>DATABASE_URL</code> is unset. PostgreSQL and Supabase connections are configured in the backend environment as <code>DATABASE_URL</code>. For Supabase, use its PostgreSQL connection string, not the public anon key or service-role key.</p></div>
    <div className="g-profile-actions"><Btn onClick={checkDatabaseHealth}>{dbHealthLoading ? "Checking…" : "Check live backend status"}</Btn><Btn variant="primary" onClick={() => notify("See docs/DATABASE-SETUP.md for the exact setup steps.")}>Setup instructions</Btn></div>
    {dbHealth && <div className="g-route-row" style={{ marginTop: 16 }}><div><strong>API readiness: {dbHealth.status}</strong><small>{dbHealth.message || "Live response from /health/ready"}</small>{dbHealth.checks && <div className="g-provider-meta">{Object.entries(dbHealth.checks).map(([name, status]) => <span key={name}><small>{name.replaceAll("_", " ")}</small><strong>{status}</strong></span>)}</div>}</div></div>}
    <div className="g-panel-heading" style={{ marginTop: 24 }}><div><h2>Setup steps</h2><p>{dbMode === "Local SQLite" ? "Start Ghost locally without provisioning a database server." : "Configure the PostgreSQL connection on the API server."}</p></div></div>
    <ol className="g-setup-steps">
      {dbMode === "Local SQLite" ? <>
        <li>Run the Ghost API from <code>apps/api</code>. With no <code>DATABASE_URL</code>, the engine defaults to <code>sqlite+pysqlite:///./ghost.db</code>.</li>
        <li>Keep the working directory and <code>ghost.db</code> file in a location you back up. The relative path is resolved from the API process working directory.</li>
        <li>Apply schema migrations using Alembic before relying on the database for saved data.</li>
      </> : <>
        {dbMode === "Supabase cloud" && <li><strong>Supabase:</strong> Project → Connect → copy a PostgreSQL URI. Use the connection mode recommended for your runtime.</li>}
        {dbMode === "Local PostgreSQL" && <li><strong>PostgreSQL:</strong> install/start the server and create a dedicated database and least-privilege user.</li>}
        <li>Use a connection URI such as <code>postgresql+psycopg://USER:PASSWORD@HOST:5432/DATABASE</code>.</li>
        <li>Add it to the backend host's secret/environment settings as <code>DATABASE_URL</code>. Do not put it in <code>VITE_*</code> variables, browser storage, GitHub, or chat.</li>
        <li>Set <code>VITE_GHOST_API_URL</code> for the web app to the deployed API base URL. Locally, the default is <code>http://localhost:8000</code>.</li>
        <li>Restart the API, run Alembic migrations, then press <strong>Check live backend status</strong>.</li>
      </>}
    </ol>
    <div className="g-info-banner"><b>!</b><p>Changing an existing database does not copy data automatically. Back up and explicitly migrate data before switching connection targets. The selected card does not change backend settings.</p></div>
  </section>
</div>}
{screen === "Telegram" && <div className="g-screen"><div className="g-two-grid"><section className="g-panel g-panel-pad"><div className="g-panel-heading"><div><h2>Bot connection</h2><p>Secure token, destination and delivery settings.</p></div><button role="switch" aria-checked={telegramOn} className={"g-toggle " + (telegramOn ? "on" : "")} onClick={() => setTelegramOn(!telegramOn)}><i /></button></div><div className="g-form-grid"><Field label="Bot token" placeholder="Server-side secret entry" type="password" /><Field label="Destination chat ID" placeholder="Verify bot access" /><Field label="Message format" value="Concise safe summary" /><Field label="Timezone" value="Asia/Kolkata (IST)" /></div><div className="g-info-banner"><b>ⓘ</b><p>Preview only. Keep bot tokens out of source control and message bodies.</p></div><div className="g-profile-actions"><Btn onClick={() => notify("Bot verification requires a live connector.")}>Test bot</Btn><Btn variant="primary" onClick={() => notify("No test notification sent; Telegram is not connected.")}>Send test</Btn></div></section><section className="g-panel g-panel-pad"><div className="g-panel-heading"><div><h2>Message preview</h2><p>Example only, not delivered</p></div></div><div className="g-chat"><div className="g-chat-head"><b>G</b><span><strong>Ghost Alerts</strong><small>bot · preview</small></span></div><div className="g-chat-bubble"><small>✳ GHOST OPERATIONS</small><strong>Job needs your review</strong><p><b>Task:</b> Reply to 18 new comments</p><p><b>Channel:</b> WorldScope Hindi</p><p><b>Status:</b> Approval required</p><button onClick={() => go("Community")}>Open review queue ↗</button></div></div></section></div><section className="g-panel g-alert-panel"><div className="g-panel-heading"><div><h2>Notification event settings</h2><p>Choose which events deserve an alert.</p></div><button className="g-link" onClick={() => setTelegramEvents(["Job completed", "Job failed", "Needs human review", "Worker offline", "Provider degraded", "Budget threshold", "Credential expiry", "Backup failure"])}>Select all</button></div><div className="g-alert-grid">{["Job completed", "Job failed", "Needs human review", "Worker offline", "Provider degraded", "Budget threshold", "Credential expiry", "Backup failure"].map((x, i) => <label key={x} className="g-alert-option"><span className="g-alert-icon">{["✓", "!", "♡", "⠿", "⌘", "₹", "↻", "▥"][i]}</span><span><strong>{x}</strong><small>{["Successful completion", "Failure after retry limit", "Approval waiting", "Worker heartbeat missing", "Integration unhealthy", "Spend or quota threshold", "Authorization expired", "Recovery failure"][i]}</small></span><input type="checkbox" checked={telegramEvents.includes(x)} onChange={() => setTelegramEvents(p => p.includes(x) ? p.filter(y => y !== x) : [...p, x])} /></label>)}</div><div className="g-profile-actions"><Btn variant="primary" onClick={() => notify("Preferences saved in preview only.")}>Save preferences</Btn></div></section></div>}
{screen === "Settings" && <div className="g-screen g-settings-layout"><section className="g-panel g-settings-nav">{["General", "AI & models", "Worker behavior", "Community voice", "Safety & approvals", "Budgets & limits", "Access & security", "Appearance", "Data retention"].map(x => <button key={x} className={settingsTab === x ? "active" : ""} onClick={() => setSettingsTab(x)}>{x}<span>›</span></button>)}</section><section className="g-panel g-settings-body"><div className="g-panel-heading"><div><h2>{settingsTab}</h2><p>Workspace defaults. Safety and platform controls always take precedence.</p></div><Badge>Preview mode</Badge></div>{settingsTab === "General" && <><Field label="Workspace name" value="Ghost Studio" /><label className="g-field"><span>Default language</span><select defaultValue="Hindi + English"><option>Hindi + English</option><option>Hindi</option><option>English</option></select></label><Toggle label="Compact information density" initial /><Toggle label="Show event stream" initial /></>}{settingsTab === "AI & models" && <><label className="g-field"><span>Provider strategy</span><select defaultValue="Task-aware routing"><option>Task-aware routing</option><option>Lowest cost within quality threshold</option><option>Highest quality</option><option>Manual</option></select></label><Toggle label="Validated providers only" initial /><Toggle label="Approve paid fallback" initial /></>}{settingsTab === "Worker behavior" && <><label className="g-field"><span>Concurrency cap</span><select defaultValue="6 parallel jobs"><option>2 parallel jobs</option><option>4 parallel jobs</option><option>6 parallel jobs</option><option>10 parallel jobs</option></select></label><label className="g-field"><span>Retry policy</span><select defaultValue="2 retries with backoff"><option>No retries</option><option>1 retry</option><option>2 retries with backoff</option><option>3 retries with backoff</option></select></label><Toggle label="Auto-assign independent tasks" initial /><Toggle label="Prioritize interactive jobs" initial /><Toggle label="Pause at budget cap" initial /></>}{settingsTab === "Community voice" && <><label className="g-field"><span>Default reply voice</span><select defaultValue="Natural & friendly"><option>Natural & friendly</option><option>Energetic & playful</option><option>Helpful & informative</option><option>Calm & professional</option></select></label><label className="g-field"><span>Default reply mode</span><select defaultValue="Review before sending"><option>Draft only</option><option>Review before sending</option><option>Low-risk auto-send (future)</option></select></label><Toggle label="Match comment language" initial /><Toggle label="Check reply repetition" initial /><Toggle label="Verify factual corrections first" initial /></>}{settingsTab === "Safety & approvals" && <><Toggle label="Human approval before publishing" initial /><Toggle label="Sensitive comments always escalate" initial /><Toggle label="Remote read-back after uncertain send" initial /><Toggle label="Disable automatic deletion by default" initial /><div className="g-info-banner"><b>⚑</b><p>Prompts cannot override account permissions, rights, safety or budget limits.</p></div></>}{settingsTab === "Budgets & limits" && <><Field label="Daily spend cap" value="$3.00" /><Field label="Monthly spend cap" value="$30.00" /><Field label="Maximum cost per job" value="$0.50" /><Toggle label="Stop paid calls at cap" initial /><Toggle label="Approve paid provider switch" initial /></>}{settingsTab === "Access & security" && <><Toggle label="Server-side encrypted secret storage" initial /><Toggle label="Audit high-impact actions" initial /><Toggle label="Verify permissions for each action" initial /><Toggle label="Redact personal data from logs" initial /></>}{settingsTab === "Appearance" && <><label className="g-field"><span>Theme</span><select defaultValue="Dark graphite"><option>Dark graphite</option><option>Light</option><option>System</option></select></label><label className="g-field"><span>Density</span><select defaultValue="Comfortable"><option>Comfortable</option><option>Compact</option></select></label><Toggle label="Reduce motion" /></>}{settingsTab === "Data retention" && <><label className="g-field"><span>Job event retention</span><select defaultValue="90 days"><option>30 days</option><option>90 days</option><option>180 days</option></select></label><label className="g-field"><span>Comment draft retention</span><select defaultValue="30 days"><option>7 days</option><option>30 days</option><option>90 days</option></select></label><Toggle label="Immutable audit history" initial /><Toggle label="Redact personal data in alerts" initial /></>}<div className="g-settings-save"><span>Preview only · backend persistence is not connected</span><Btn variant="primary" onClick={() => notify("Settings do not persist until backend is connected.")}>Save settings</Btn></div></section></div>}
</div></main>
{wizard && <div className="g-modal-backdrop" onClick={() => setWizard(false)}><section className="g-wizard" role="dialog" aria-modal="true" aria-labelledby="wizard-title" onClick={e => e.stopPropagation()}><header className="g-wizard-head"><div><div className="g-eyebrow">ACCOUNT SETUP WIZARD</div><h2 id="wizard-title">Add a channel or page</h2><p>Authorize the platform, then tailor a profile to that account.</p></div><button className="g-icon-link" onClick={() => setWizard(false)} aria-label="Close wizard">×</button></header><div className="g-wizard-steps">{["Platform", "Authorization", "Profile setup", "Review"].map((x, i) => <div key={x} className={(step === i + 1 ? "active " : "") + (step > i + 1 ? "done" : "")}><span>{step > i + 1 ? "✓" : "0" + (i + 1)}</span><small>{x}</small></div>)}</div><div className="g-wizard-body">
{step === 1 && <><h3>Choose a platform</h3><p className="g-wizard-desc">You can add many channels and pages, including multiple accounts on a single platform.</p><div className="g-platform-choices">{[{
                n: "YouTube",
                sub: "Channel",
                icon: "YT",
                c: "youtube"
              }, {
                n: "Facebook",
                sub: "Page",
                icon: "f",
                c: "facebook"
              }, {
                n: "Instagram",
                sub: "Professional account",
                icon: "IG",
                c: "instagram"
              }].map(p => <button type="button" key={p.n} className={"g-platform-choice " + (platform === p.n ? "selected" : "")} onClick={() => {
                setPlatform(p.n);
                setAccountType(p.sub);
              }}><span className={"g-platform-icon " + p.c}>{p.icon}</span><strong>{p.n}</strong><small>{p.sub}</small><i>{platform === p.n ? "●" : "○"}</i></button>)}</div><label className="g-field"><span>Account type</span><select value={accountType} onChange={e => setAccountType(e.target.value)}>{(platform === "YouTube" ? ["Channel"] : platform === "Facebook" ? ["Page"] : ["Professional account", "Creator account"]).map(x => <option key={x}>{x}</option>)}</select></label><div className="g-wizard-note"><b>ⓘ</b><p>Never enter your social-platform password here. Use the official consent and authorization flow.</p></div></>}
{step === 2 && <><h3>Authorize your {platform} account</h3><p className="g-wizard-desc">The live flow will redirect to the official platform, request only necessary scopes, then load authorized accounts/pages.</p><div className="g-auth-card"><span className={"g-platform-icon " + platform.toLowerCase()}>{platform === "YouTube" ? "YT" : platform === "Facebook" ? "f" : "IG"}</span><div><strong>Official {platform} authorization</strong><small>OAuth consent · permissions · secure callback</small><small>Platform client ID and token exchange must be configured on the backend.</small></div><Badge tone="orange">Not connected</Badge></div><Btn variant="primary" onClick={() => {
              setOauthAttempt(true);
              notify("OAuth cannot launch until platform credentials and callback URL are configured.");
            }}>Continue to secure authorization ↗</Btn>{oauthAttempt && <div className="g-wizard-note warn"><b>!</b><p>OAuth is unavailable in this prototype. You can still create the profile draft; it stays Not connected until the actual callback is verified.</p></div>}<div className="g-form-grid wizard-form"><Field label="Profile display name" value={wName} placeholder="e.g. SportSaga Hindi" onChange={setWName} required /><Field label="Public handle / page URL (optional)" value={wHandle} placeholder="@channel or page URL" onChange={setWHandle} /></div><div className="g-wizard-note"><b>ⓘ</b><p>A handle or ID only helps identify the profile. It does not prove ownership or authorize account access.</p></div></>}
{step === 3 && <><h3>Customize this profile</h3><p className="g-wizard-desc">These settings belong only to this account profile.</p><div className="g-form-grid wizard-form"><Field label="Profile display name" value={wName} placeholder="Name in Ghost" onChange={setWName} required /><Field label="Content niche" value={wNiche} placeholder="e.g. Hindi sports stories" onChange={setWNiche} required /><Field label="Target audience (optional)" value={wAudience} placeholder="e.g. Hindi-speaking cricket fans" onChange={setWAudience} /><label className="g-field"><span>Language</span><select value={wLanguage} onChange={e => setWLanguage(e.target.value)}><option>Hindi</option><option>English</option><option>Hindi + English</option><option>Gujarati</option><option>Other</option></select></label><label className="g-field"><span>Content format</span><select value={wFormat} onChange={e => setWFormat(e.target.value)}>{["Shorts · 60 sec", "Long video · 10 min", "Reel · 30 sec", "Reel · 60 sec", "Image post", "Carousel", "Text post", "Custom"].map(x => <option key={x}>{x}</option>)}</select></label><label className="g-field"><span>Brand voice</span><select value={wTone} onChange={e => setWTone(e.target.value)}>{["Natural and energetic", "Cinematic and documentary", "Calm and informative", "Funny and relatable", "Technical and accessible", "Custom"].map(x => <option key={x}>{x}</option>)}</select></label><label className="g-field"><span>Publishing cadence</span><select value={wCadence} onChange={e => setWCadence(e.target.value)}>{["Manual", "Every day", "Every 2 days", "Three times a week", "Sunday", "Custom schedule"].map(x => <option key={x}>{x}</option>)}</select></label><Field label="Timezone" value={wTimezone} onChange={setWTimezone} required /><label className="g-field full"><span>Custom prompt / brand rules</span><textarea rows={5} value={wPrompt} onChange={e => setWPrompt(e.target.value)} /></label><label className="g-field full"><span>Publishing approval mode</span><select value={wApproval} onChange={e => setWApproval(e.target.value)}><option>Review before publish</option><option>Draft only</option><option>Approved low-risk only</option></select></label></div></>}
{step === 4 && <><h3>Review setup</h3><p className="g-wizard-desc">Save a profile draft. The platform connection stays pending until the authorization flow succeeds.</p><div className="g-review-grid">{[["Platform", platform + " · " + accountType], ["Profile name", wName || "Required"], ["Handle / URL", wHandle || "Not provided"], ["Niche", wNiche || "Required"], ["Audience", wAudience || "Not specified"], ["Language", wLanguage], ["Format", wFormat], ["Brand voice", wTone], ["Schedule", wCadence], ["Timezone", wTimezone], ["Approval", wApproval], ["Authorization", "Not connected · OAuth required"]].map(([a, b]) => <div key={a}><small>{a}</small><strong>{b}</strong></div>)}</div><div className="g-wizard-note warn"><b>!</b><p><strong>Connection remains Not connected.</strong> This canvas has no live OAuth callback. Save the draft now and authorize after platform credentials and backend connector are configured.</p></div></>}
</div><footer className="g-wizard-footer"><div><span className="g-required-note"><b>*</b> Required fields</span><span className="g-step-count">Step {step} of 4</span></div><div>{step > 1 && <Btn onClick={() => setStep(s => s - 1)}>← Back</Btn>}{step < 4 ? <Btn variant="primary" onClick={() => {
              if (step === 2 && !wName.trim()) {
                notify("Profile display name required hai.");
                return;
              }
              if (step === 3 && (!wName.trim() || !wNiche.trim())) {
                notify("Profile name aur niche required hain.");
                return;
              }
              setStep(s => s + 1);
            }}>Continue →</Btn> : <Btn variant="primary" onClick={createDraft}>Save profile draft</Btn>}</div></footer></section></div>}
{toast && <div className="g-toast"><span>✓</span>{toast}</div>}</div>;
};