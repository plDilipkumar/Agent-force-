import { FormEvent, useEffect, useState } from "react";
import { Layers3, ShieldCheck, Sparkles, LoaderCircle, ArrowRight, TriangleAlert, CheckCircle2, Code2, Workflow, Activity, MessageCircle } from "lucide-react";
import App from "./App";

const API = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export default function AuthGate() {
  const [token, setToken] = useState(localStorage.getItem("agentforge_token") || "");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [showAuth, setShowAuth] = useState(false);
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

  if (!showAuth) return <main className="public-home">
    <header className="public-nav">
      <a className="public-brand" href="#" onClick={event=>{event.preventDefault();setShowAuth(false);}}><span className="public-brand-mark"><Layers3 size={21}/></span><span><b>AgentForge</b><small>BUILD WITH INTENT</small></span></a>
      <nav className="public-nav-links" aria-label="Main navigation"><a href="#features">Features</a><a href="#how-it-works">How it works</a></nav>
      <div className="public-nav-actions"><button className="public-login" onClick={()=>{setMode("login");setShowAuth(true);}}>Log in</button><button className="public-signup" onClick={()=>{setMode("register");setShowAuth(true);}}>Get started <ArrowRight size={15}/></button></div>
    </header>
    <section className="public-hero">
      <div className="public-hero-copy"><span className="public-kicker"><span/> A calmer way to build software</span><h1>Good ideas deserve<br/><em>a clear way forward.</em></h1><p>Plan a project, talk through a tricky problem, and shape code drafts in one thoughtful workspace built for real engineering work.</p>
        <div className="public-hero-actions"><button className="public-signup hero-cta" onClick={()=>{setMode("register");setShowAuth(true);}}>Create your free account <ArrowRight size={17}/></button><button className="public-ghost" onClick={()=>{setMode("login");setShowAuth(true);}}>I already have an account</button></div>
        <div className="public-trust-row"><span><ShieldCheck size={15}/> Private account access</span><span><CheckCircle2 size={15}/> Reviewable work</span></div>
      </div>
      <div className="public-hero-art" aria-label="Project illustration"><div className="art-orbit art-orbit-a"/><div className="art-orbit art-orbit-b"/><div className="art-spark art-spark-a"><Sparkles size={18}/></div><div className="art-spark art-spark-b"><Code2 size={18}/></div><div className="art-center"><Layers3 size={36}/><span>YOUR NEXT BUILD</span></div><div className="art-float art-plan"><Workflow size={17}/><span><b>Project plan</b><small>Clear steps</small></span></div><div className="art-float art-chat"><Activity size={17}/><span><b>Conversation</b><small>Explore ideas</small></span></div><div className="art-float art-code"><Code2 size={17}/><span><b>Code drafts</b><small>Ready to review</small></span></div></div>
    </section>
    <section className="public-features" id="features"><div className="public-section-heading"><span>ONE WORKSPACE, THREE WAYS TO MOVE</span><h2>From first thought to first draft.</h2><p>Choose a tool to see what AgentForge can help you do. Sign in or create an account to open any feature.</p></div>
      <div className="public-feature-grid">
        <button className="public-feature-card" onClick={()=>{setMode("login");setShowAuth(true);}}><span className="public-feature-icon"><Workflow size={20}/></span><span className="public-feature-number">01 / PLAN</span><h3>Plan generator</h3><p>Break a project brief into tasks, decisions, risks, and a practical verification checklist.</p><span className="public-feature-link">Access plan generator <ArrowRight size={15}/></span></button>
        <button className="public-feature-card" onClick={()=>{setMode("login");setShowAuth(true);}}><span className="public-feature-icon"><MessageCircle size={20}/></span><span className="public-feature-number">02 / THINK</span><h3>AI chat</h3><p>Ask questions, brainstorm solutions, and work through technical ideas in conversation.</p><span className="public-feature-link">Access AI chat <ArrowRight size={15}/></span></button>
        <button className="public-feature-card" onClick={()=>{setMode("login");setShowAuth(true);}}><span className="public-feature-icon"><Code2 size={20}/></span><span className="public-feature-number">03 / BUILD</span><h3>AI code studio</h3><p>Prepare source and test drafts that you can inspect and adapt to your project.</p><span className="public-feature-link">Access code studio <ArrowRight size={15}/></span></button>
      </div>
    </section>
    <section className="public-how" id="how-it-works"><div><span className="public-section-label">MADE FOR YOUR WORKFLOW</span><h2>Keep the thinking clear.<br/><em>Keep the decisions yours.</em></h2></div><div className="public-how-steps"><div><span>01</span><section><b>Describe the work</b><p>Start with a question, a project brief, or a feature idea.</p></section></div><div><span>02</span><section><b>Explore and shape it</b><p>Use planning, chat, and code tools to move from idea to draft.</p></section></div><div><span>03</span><section><b>Review before using</b><p>Inspect generated suggestions and verify them in your own workflow.</p></section></div></div></section>
    <footer className="public-footer"><a className="public-brand" href="#" onClick={event=>{event.preventDefault();window.scrollTo({top:0,behavior:"smooth"});}}><span className="public-brand-mark"><Layers3 size={18}/></span><span><b>AgentForge</b><small>ENGINEERING WORKSPACE</small></span></a><span>Build with intent. Verify with evidence.</span><button onClick={()=>{setMode("register");setShowAuth(true);}}>Create an account <ArrowRight size={14}/></button></footer>
  </main>;

  return <main className="auth-shell">
    <button className="auth-back-home" onClick={()=>setShowAuth(false)}><ArrowRight size={14}/> Back to home</button>

}
