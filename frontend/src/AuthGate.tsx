import { FormEvent, useEffect, useState } from "react";
import { Layers3, ShieldCheck, Sparkles, LoaderCircle, ArrowRight, TriangleAlert } from "lucide-react";
import App from "./App";

const API = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export default function AuthGate() {
  const [token, setToken] = useState(localStorage.getItem("agentforge_token") || "");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(Boolean(localStorage.getItem("agentforge_token")));
  const [error, setError] = useState("");

  useEffect(() => {
    const onUnauthorized = () => { setToken(""); setChecking(false); };
    window.addEventListener("agentforge:unauthorized", onUnauthorized);
    const existing = localStorage.getItem("agentforge_token");
    if (existing) {
      fetch(API + "/api/auth/me", { headers: { Authorization: `Bearer ${existing}` } })
        .then(response => { if (!response.ok) throw new Error("session"); setToken(existing); })
        .catch(() => { localStorage.removeItem("agentforge_token"); setToken(""); })
        .finally(() => setChecking(false));
    }
    return () => window.removeEventListener("agentforge:unauthorized", onUnauthorized);
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await fetch(API + (mode === "login" ? "/api/auth/login" : "/api/auth/register"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "Could not authenticate. Please try again.");
      localStorage.setItem("agentforge_token", body.access_token);
      setToken(body.access_token);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not reach AgentForge. Check your connection.");
    } finally {
      setLoading(false);
    }
  }

  if (checking) return <div className="auth-loading"><LoaderCircle className="spin" size={24}/> Checking your session…</div>;
  if (token) return <App />;

  return <main className="auth-shell">
    <section className="auth-hero">
      <div className="auth-brand"><span><Layers3 size={22}/></span><div><b>AgentForge</b><small>ENGINEERING WORKSPACE</small></div></div>
      <div className="auth-hero-content">
        <span className="auth-eyebrow"><Sparkles size={14}/> YOUR ENGINEERING WORKSPACE</span>
        <h1>Turn your ideas into <em>clear next steps.</em></h1>
        <p>Plan projects, chat through ideas, and generate code drafts in one focused workspace.</p>
        <div className="auth-benefit"><ShieldCheck size={17}/> Your account protects access to every AI feature.</div>
        <div className="auth-benefit"><ShieldCheck size={17}/> A connected workspace for planning, chat, and code generation.</div>
      </div>
      <small className="auth-footnote">Built for clarity, control, and reviewable results.</small>
    </section>
    <section className="auth-form-side">
      <form className="auth-card" onSubmit={submit}>
        <div className="auth-card-icon"><Layers3 size={21}/></div>
        <span className="auth-card-eyebrow">{mode === "login" ? "WELCOME BACK" : "GET STARTED"}</span>
        <h2>{mode === "login" ? "Sign in to AgentForge" : "Create your account"}</h2>
        <p>{mode === "login" ? "Sign in to continue to your workspace." : "Create an account to start using your workspace."}</p>
        <label htmlFor="auth-email">EMAIL ADDRESS</label>
        <input id="auth-email" type="email" autoComplete="email" required maxLength={254} value={email} onChange={event => setEmail(event.target.value)} placeholder="you@example.com"/>
        <label htmlFor="auth-password">PASSWORD <span>At least 10 characters</span></label>
        <input id="auth-password" type="password" autoComplete={mode === "login" ? "current-password" : "new-password"} required minLength={10} maxLength={128} value={password} onChange={event => setPassword(event.target.value)} placeholder="Enter your password"/>
        {error && <div className="auth-error"><TriangleAlert size={16}/>{error}</div>}
        <button className="auth-submit" type="submit" disabled={loading}>{loading ? <LoaderCircle size={17} className="spin"/> : null}{mode === "login" ? "Sign in securely" : "Create account"}<ArrowRight size={16}/></button>
        <div className="auth-switch">{mode === "login" ? "New to AgentForge?" : "Already have an account?"}<button type="button" onClick={() => {setMode(mode === "login" ? "register" : "login");setError("");}}> {mode === "login" ? "Create an account" : "Sign in"}</button></div>
        <div className="auth-security"><ShieldCheck size={14}/> Passwords are hashed on the server. AI endpoints require a valid session.</div>
      </form>
    </section>
  </main>;
}
