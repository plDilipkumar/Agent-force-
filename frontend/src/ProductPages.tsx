import { Activity, ArrowRight, Box, CheckCircle2, CircleHelp, Clock3, Code2, FolderKanban, KeyRound, Layers3, Plus, ShieldCheck, Sparkles, Workflow } from "lucide-react";

type HistoryItem = { id: string; summary: string; created_at: string; provider?: string; mode?: string; tasks?: { title: string; priority: string }[] };
type ArtifactInfo = { artifact_id: string; filename: string; created_at: string; provider: string; verification_status: string; safety_notice: string } | null;
type Props = { page: string; history: HistoryItem[]; artifact: ArtifactInfo; apiBase: string; onNavigate: (page: string) => void };

const pageCopy: Record<string, { eyebrow: string; title: string; description: string }> = {
  Projects: { eyebrow: "WORKSPACE / PROJECTS", title: "Your engineering projects", description: "Keep briefs, plans, decisions and generated deliverables organised by project." },
  "Run history": { eyebrow: "WORKSPACE / ACTIVITY", title: "Run history", description: "Review planning runs from this browser session. Persistent account history will require connected authentication and storage." },
  Artifacts: { eyebrow: "WORKSPACE / DELIVERABLES", title: "Artifact library", description: "Review generated files and their verification state before using them." },
  Settings: { eyebrow: "ADMINISTRATION / SETTINGS", title: "Workspace settings", description: "Inspect this preview's configuration and the safety boundaries applied to your workspace." },
  Help: { eyebrow: "SUPPORT / DOCUMENTATION", title: "How can we help?", description: "Understand AgentForge's workflow, artifacts, and verification guarantees." },
  "Sign in": { eyebrow: "AGENTFORGE ACCOUNT", title: "Your workspace, securely connected.", description: "Account sign-in UI is reserved here. Production authentication is not connected yet, so this preview never asks for or stores your password." }
};

export default function ProductPages({ page, history, artifact, apiBase, onNavigate }: Props) {
  const copy = pageCopy[page] ?? pageCopy.Projects;
  return <div className="product-page">
    <div className="product-page-heading">
      <div className="eyebrow"><span className="eyebrow-line" /> {copy.eyebrow}</div>
      <h1>{copy.title}</h1>
      <p>{copy.description}</p>
    </div>
    {page === "Projects" && <>
      <div className="product-summary-grid">
        <div className="product-summary"><span><FolderKanban size={16}/> PROJECTS</span><strong>1 workspace</strong><small>Personal engineering space</small></div>
        <div className="product-summary"><span><Activity size={16}/> PLANNING RUNS</span><strong>{history.length}</strong><small>Runs in this session</small></div>
        <div className="product-summary"><span><Code2 size={16}/> ARTIFACTS</span><strong>{artifact ? "1" : "0"}</strong><small>Generated this session</small></div>
      </div>
      <section className="product-card project-card">
        <div className="project-icon"><Layers3 size={22}/></div><div className="project-details"><div className="product-card-top"><h2>My engineering workspace</h2><span className="state-pill"><span/> Active</span></div><p>Drafts, plans and code artifacts created in the current browser session.</p><div className="project-meta"><span><Workflow size={13}/> Planning studio</span><span><Clock3 size={13}/> Session-only storage</span></div></div>
        <button className="product-primary" onClick={()=>onNavigate("Studio")}><Plus size={15}/> New plan</button>
      </section>
      <div className="product-note"><ShieldCheck size={17}/><span><b>Data transparency</b> — project records are not yet backed by user accounts or a database. This page does not imply persistent cloud storage.</span></div>
    </>}
    {page === "Run history" && <section className="product-card-list">
      {history.length === 0 ? <div className="product-empty"><div className="product-empty-icon"><Activity size={23}/></div><h2>No runs in this session yet</h2><p>Create an engineering plan and it will appear here while this page remains open.</p><button className="product-primary" onClick={()=>onNavigate("Studio")}>Start a planning run <ArrowRight size={15}/></button></div> :
        history.map((run, index)=><article className="product-history-item" key={run.id}><div className="history-mark"><CheckCircle2 size={17}/></div><div className="history-main"><div className="product-card-top"><h2>{run.summary || "Engineering plan"}</h2><span className="state-pill neutral">Plan generated</span></div><p>{run.id} · {run.provider || "Provider not specified"}</p><small>{run.created_at ? new Date(run.created_at).toLocaleString() : "Time unavailable"}</small></div><button className="icon-button" aria-label={`Open run ${index + 1}`} onClick={()=>onNavigate("Studio")}><ArrowRight size={15}/></button></article>)
      }
    </section>}
    {page === "Artifacts" && <section className="product-card-list">
      {!artifact ? <div className="product-empty"><div className="product-empty-icon"><Code2 size={23}/></div><h2>Your artifact library is empty</h2><p>Generate code and test files from the planning studio to review them here.</p><button className="product-primary" onClick={()=>onNavigate("Studio")}>Open planning studio <ArrowRight size={15}/></button></div> :
        <article className="product-history-item"><div className="history-mark"><Code2 size={17}/></div><div className="history-main"><div className="product-card-top"><h2>{artifact.filename}</h2><span className="state-pill warning">Not executed</span></div><p>{artifact.provider} · {artifact.artifact_id}</p><small>{artifact.safety_notice}</small><div className="product-note compact"><ShieldCheck size={15}/><span>Generated code is untrusted input. The API has not executed these tests.</span></div></div></article>
      }
    </section>}
    {page === "Settings" && <>
      <section className="product-card settings-card"><div className="settings-icon"><KeyRound size={18}/></div><div><h2>API connection</h2><p>Configured frontend API base URL. A successful connection has not been inferred from this value alone.</p><code>{apiBase}</code></div><span className="state-pill neutral">Configured</span></section>
      <section className="product-card settings-card"><div className="settings-icon"><ShieldCheck size={18}/></div><div><h2>Security boundaries</h2><p>Provider credentials stay server-side. Generated source is displayed for review and is not executed inside the API process.</p></div><span className="state-pill"><span/> Enabled</span></section>
      <section className="product-card settings-card"><div className="settings-icon"><KeyRound size={18}/></div><div><h2>Account & access</h2><p>Authentication, roles, and durable cloud history still need a configured identity provider and persistence layer.</p></div><button className="product-secondary" onClick={()=>onNavigate("Sign in")}>Account setup</button></section>
    </>}
    {page === "Help" && <div className="help-grid">
      <article className="product-card help-card"><div className="settings-icon"><Sparkles size={18}/></div><h2>1. Describe the task</h2><p>Provide the outcome, context, technology stack, and constraints.</p></article>
      <article className="product-card help-card"><div className="settings-icon"><Workflow size={18}/></div><h2>2. Review the plan</h2><p>Inspect the specification, priorities, architecture decisions, and risk register.</p></article>
      <article className="product-card help-card"><div className="settings-icon"><Code2 size={18}/></div><h2>3. Review artifacts</h2><p>Generated code and test files are suggestions; their verification state must remain explicit.</p></article>
      <article className="product-card help-card"><div className="settings-icon"><CircleHelp size={18}/></div><h2>Need more help?</h2><p>Use the planning studio to generate a sample plan. Live support and account management are not configured in this preview.</p><button className="product-secondary" onClick={()=>onNavigate("Studio")}>Open studio</button></article>
    </div>}
    {page === "Sign in" && <section className="signin-layout"><div className="signin-visual"><div className="signin-logo"><Layers3 size={25}/></div><div className="eyebrow">AGENTFORGE WORKSPACE</div><h2>From first brief to a build you can review.</h2><p>A focused engineering workspace for plans, implementation artifacts, and evidence-based verification.</p><div className="signin-feature"><CheckCircle2 size={16}/> Structured task planning</div><div className="signin-feature"><CheckCircle2 size={16}/> Reviewable code artifacts</div><div className="signin-feature"><CheckCircle2 size={16}/> Explicit verification status</div></div><div className="signin-panel"><div className="settings-icon"><KeyRound size={20}/></div><h2>Secure sign-in setup</h2><p>Authentication is not wired to an identity provider yet. To protect your account, this preview intentionally does not collect credentials or pretend a sign-in succeeded.</p><div className="auth-requirement"><ShieldCheck size={17}/><span><b>Next integration step</b><br/>Connect a real auth provider and server-side session validation before enabling sign-in or team workspaces.</span></div><button className="product-primary full-width" onClick={()=>onNavigate("Studio")}>Continue in preview <ArrowRight size={15}/></button><small>Preview mode · no account created</small></div></section>}
    <div className="product-footer"><span>AGENTFORGE <i>/</i> PRODUCT PREVIEW</span><span>Built for clarity, control and evidence.</span></div>
  </div>;
}
