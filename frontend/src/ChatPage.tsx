import { FormEvent, useState } from "react";
import { apiFetch } from "./api";
import { Bot, Send, Sparkles, UserRound, LoaderCircle, RotateCcw, ShieldCheck, TriangleAlert } from "lucide-react";

type Message = { role: "user" | "assistant"; content: string; provider?: string };
type Props = { apiBase: string };

export default function ChatPage({ apiBase }: Props) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function sendMessage(event?: FormEvent, suggested?: string) {
    event?.preventDefault();
    const text = (suggested ?? draft).trim();
    if (!text || loading) return;
    setMessages(previous => [...previous, { role: "user", content: text }]);
    setDraft("");
    setError("");
    setLoading(true);
    try {
      const response = await apiFetch(apiBase + "/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text })
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail || "We couldn’t get a response just now. Please try again.");
      setMessages(previous => [...previous, { role: "assistant", content: body.reply, provider: body.provider }]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not reach AgentForge. Check the connection and retry.");
    } finally {
      setLoading(false);
    }
  }

  return <div className="chat-page">
    <div className="eyebrow"><span className="eyebrow-line" /> YOUR WORKSPACE / CHAT</div>
    <div className="chat-heading"><div><h1>Ask anything. <em>Build with clarity.</em></h1><p>A place to think through problems, explore ideas, and work through your next build.</p></div><span className="chat-model"><span/> Ready when you are</span></div>
    <section className="chat-workspace">
      <div className="chat-toolbar"><div className="chat-bot-icon"><Bot size={19}/></div><div><strong>AgentForge Assistant</strong><span>Ask questions, explore ideas, and solve problems</span></div><button className="icon-button" title="Clear conversation" onClick={() => {setMessages([]);setError("");}}><RotateCcw size={15}/></button></div>
      <div className="chat-messages">
        {messages.length === 0 && <div className="chat-welcome"><div className="chat-welcome-icon"><Sparkles size={24}/></div><h2>What can I help you with?</h2><p>Ask a question, learn a concept, draft something, or brainstorm your next idea.</p><div className="chat-suggestions">{["Explain APIs in simple terms","Help me debug a Python error","Suggest a project for my portfolio"].map(item=><button key={item} onClick={() => sendMessage(undefined, item)}>{item}<Send size={13}/></button>)}</div></div>}
        {messages.map((message, index) => <div className={"chat-message "+message.role} key={index}><div className="chat-message-avatar">{message.role === "user" ? <UserRound size={16}/> : <Bot size={16}/>}</div><div className="chat-message-content"><span className="chat-message-label">{message.role === "user" ? "YOU" : "AGENTFORGE"}</span><p>{message.content}</p></div></div>)}
        {loading && <div className="chat-message assistant"><div className="chat-message-avatar"><Bot size={16}/></div><div className="chat-message-content"><span className="chat-message-label">AGENTFORGE</span><p className="chat-thinking"><LoaderCircle size={15} className="spin"/> Thinking…</p></div></div>}
        {error && <div className="error-box"><TriangleAlert size={16}/><span>{error}</span><button onClick={() => {const last=[...messages].reverse().find(item=>item.role==="user"); if(last) void sendMessage(undefined,last.content);}} disabled={loading}>Retry</button></div>}
      </div>
      <form className="chat-composer" onSubmit={event => void sendMessage(event)}>
        <textarea value={draft} onChange={event=>setDraft(event.target.value)} maxLength={4000} rows={2} placeholder="Message AgentForge Assistant…" aria-label="Message AgentForge Assistant"/>
        <div className="chat-composer-bottom"><span><ShieldCheck size={13}/> Your conversation is sent securely for a response</span><button className="run-button" type="submit" disabled={loading || !draft.trim()}>{loading?<LoaderCircle size={16} className="spin"/>:<Send size={15}/>} Send</button></div>
      </form>
    </section>
    <div className="chat-footnote">AI responses can be inaccurate. Verify important information before relying on it.</div>
  </div>;
}
