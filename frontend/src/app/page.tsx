"use client";

import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import { Send, ShieldCheck, Activity, BrainCircuit, X, Database, ChevronRight, Info, Clock, ExternalLink } from "lucide-react";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  follow_ups?: string[];
  gate_blocked?: string | null;
  response_type?: string;
  fund_slug?: string;
};

const FUND_METADATA: Record<string, { name: string; theme: string }> = {
  "nifty50_index": { name: "Nifty 50 Index Fund", theme: "theme-nifty50_index" },
  "value_fund": { name: "Value Fund", theme: "theme-value_fund" },
  "aggressive_hybrid": { name: "Aggressive Hybrid Fund", theme: "theme-aggressive_hybrid" },
  "elss_tax_saver": { name: "ELSS Tax Saver Fund", theme: "theme-elss_tax_saver" },
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Welcome to the Groww AI Fact Engine. I provide verified, factual data on Groww Mutual Funds directly from official documents. How can I help you today?",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);
  const [kbTree, setKbTree] = useState<Record<string, string[]>>({});
  const [drawerSource, setDrawerSource] = useState<any | null>(null);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchKb = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
        const res = await fetch(`${apiUrl}/api/kb`);
        const data = await res.json();
        setKbTree(data);
      } catch (err) {
        console.error("Failed to fetch KB schema:", err);
      }
    };
    fetchKb();
  }, []);

  const activeSources = useMemo(() => {
    if (streamingMessage?.sources) return streamingMessage.sources;
    const lastMsg = messages[messages.length - 1];
    return lastMsg?.role === "assistant" && lastMsg.sources ? lastMsg.sources : [];
  }, [streamingMessage, messages]);

  const isSourceActive = useCallback((fundName: string, docType: string) => {
    return activeSources.some((s: any) => {
      if (!s.fund_name || !s.doc_type) return false;
      const normalizedS = s.fund_name.toLowerCase().replace(/groww|direct|growth/g, '').trim();
      const normalizedTarget = fundName.toLowerCase().replace(/groww|direct|growth/g, '').trim();
      
      const isFundMatch = normalizedS.includes(normalizedTarget) || normalizedTarget.includes(normalizedS);
      const isDocMatch = (docType === "Live Data" && s.doc_type.toLowerCase() === "web") || s.doc_type === docType;
      
      return isFundMatch && isDocMatch;
    });
  }, [activeSources]);

  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  const detectFundSlug = (text: string): string | undefined => {
    const t = text.toLowerCase();
    if (t.includes("nifty") || t.includes("index")) return "nifty50_index";
    if (t.includes("value")) return "value_fund";
    if (t.includes("hybrid")) return "aggressive_hybrid";
    if (t.includes("elss") || t.includes("tax saver")) return "elss_tax_saver";
    return undefined;
  };

  const renderAnswer = (text: string) => {
    // 1. Clean tags and system text
    let cleaned = text
      .replace(/\[Source:[^\]]*\]/g, '')
      .replace(/\[View Source\]/g, '')
      .replace(/\[\/?ANSWER\]/g, '')
      .replace(/\[\/?SOURCE_SUMMARIES\]/g, '')
      .replace(/\[\/?NEXT_STEPS\]/g, '')
      .trim();
    
    const lines = cleaned.split('\n').map(l => l.trim()).filter(Boolean);
    if (lines.length === 0) return null;
    
    return (
      <div className="flex flex-col gap-3">
        {lines.map((line, i) => {
          // 2. Simple regex for **bold** text support
          const parts = line.split(/(\*\*.*?\*\*)/g);
          return (
            <p key={i} className="text-[15px] leading-relaxed text-white/90">
              {parts.map((part, pi) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                  return <strong key={pi} className="text-white font-bold">{part.slice(2, -2)}</strong>;
                }
                return part.replace(/^[\u2022\-\*]\s*/, '');
              })}
            </p>
          );
        })}
      </div>
    );
  };

  const handleSend = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: text,
          history: messages.map(m => ({ role: m.role === "assistant" ? "ai" : m.role, content: m.content })), 
        }),
      });

      if (!response.ok) throw new Error(await response.text());

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let accumulatedAnswer = "";
      let accumulatedSources: any[] = [];
      let accumulatedFollowUps: string[] = [];
      let accumulatedResponseType: string | undefined;
      let accumulatedGateBlocked: string | null = null;

      while (reader && !done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\n').filter(line => line.trim());
          
          for (const line of lines) {
            const cleanLine = line.startsWith('data: ') ? line.slice(6) : line;
            if (!cleanLine || cleanLine === '[DONE]') continue;
            
            try {
              const data = JSON.parse(cleanLine);
              if (data.answer) accumulatedAnswer += data.answer;
              if (data.sources) accumulatedSources = data.sources;
              if (data.follow_ups) accumulatedFollowUps = data.follow_ups;
              if (data.response_type) accumulatedResponseType = data.response_type;
              if (data.gate_blocked) accumulatedGateBlocked = data.gate_blocked;

              setStreamingMessage({
                role: "assistant",
                content: accumulatedAnswer,
                sources: accumulatedSources,
                follow_ups: accumulatedFollowUps,
                gate_blocked: accumulatedGateBlocked,
                fund_slug: detectFundSlug(text) || detectFundSlug(accumulatedAnswer),
                ...(accumulatedResponseType ? { response_type: accumulatedResponseType } : {})
              });
            } catch (e) { continue; }
          }
        }
      }

      if (accumulatedAnswer || accumulatedGateBlocked) {
        setMessages(prev => [...prev, {
          role: "assistant",
          content: accumulatedAnswer,
          sources: accumulatedSources,
          follow_ups: accumulatedFollowUps,
          gate_blocked: accumulatedGateBlocked,
          fund_slug: detectFundSlug(text) || detectFundSlug(accumulatedAnswer),
          ...(accumulatedResponseType ? { response_type: accumulatedResponseType } : {})
        }]);
      }
      setStreamingMessage(null);
    } catch (err: any) {
      setMessages(prev => [...prev, { role: "assistant", content: `❌ Error: ${err.message}` }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="layout-container">
      <aside className="sidebar-container glass-panel">
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-white/5">
            <Database size={18} className="text-[#C9A84C]" />
          </div>
          <h2 className="font-serif text-lg text-white/90 m-0">Knowledge Base</h2>
        </div>
        <p className="text-[11px] text-white/40 leading-relaxed mb-6">
          High-fidelity vector store populated from official documents and live metrics.
        </p>
        
        <div className="flex flex-col gap-6">
          {Object.entries(kbTree).map(([fund, docs], idx) => (
            <div key={idx} className="fade-in">
              <h3 className="text-[10px] font-bold text-white/30 uppercase tracking-[0.15em] mb-3">{fund}</h3>
              <div className="flex flex-wrap gap-1.5">
                {docs.map((doc, dIdx) => (
                  <span key={dIdx} className={`doc-tag ${isSourceActive(fund, doc) ? 'active' : ''}`}>
                    {doc}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-auto pt-8 border-t border-white/5">
          <div className="flex items-center gap-2 text-[9px] text-white/20 uppercase tracking-[0.2em] font-bold">
            <ShieldCheck size={12} />
            <span>Verified Environment</span>
          </div>
        </div>
      </aside>

      <div className="chat-area-wrapper">
        <div className="chat-container">
          <header className="header-section fade-in">
            <div className="status-pill mb-4">
              <div className="status-dot" />
              <span>System Live • Verified Apr 5</span>
            </div>
            <h1 className="header-title">Groww Fact Engine</h1>
            <p className="header-subtitle">
              Strictly factual responses from verified AMC and SEBI sources.
            </p>
          </header>

          <main className="flex flex-col">
            {messages.map((msg, i) => (
              <div key={i} className={msg.role === "user" ? "message-user" : `message-ai ${msg.fund_slug ? FUND_METADATA[msg.fund_slug]?.theme : ''}`}>
                {msg.role === "user" ? (
                  <div className="message-user-bubble">
                    {msg.content}
                  </div>
                ) : (
                  <div className="fade-in">
                    <div className="message-ai-label">
                      {msg.fund_slug ? FUND_METADATA[msg.fund_slug]?.name : "Fact Engine"}
                    </div>
                    
                    {msg.gate_blocked && msg.gate_blocked !== 'advice_query' ? (
                       <div className="gate-message">
                         {msg.gate_blocked === 'out_of_scope' && "I only have information about the 4 Groww Direct Growth funds in scope."}
                         {msg.gate_blocked === 'pii' && "Security: Sensitive identifiers detected. Request blocked."}
                         {msg.gate_blocked === 'zero_retrieval' && "I don't have that specific data in my current knowledge base."}
                       </div>
                    ) : (
                      <>
                        <div className="message-content">
                          {renderAnswer(msg.content)}
                        </div>

                        {msg.sources && msg.sources.length > 0 && msg.response_type !== 'refusal' && (
                          <div className="mt-5 pt-4 border-t border-white/5">
                            <div className="flex items-center gap-2 mb-3">
                              <Info size={12} className="text-white/20" />
                              <span className="text-[10px] uppercase tracking-widest text-white/20 font-bold">Citations</span>
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {msg.sources.slice(0, 3).map((s: any, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => setDrawerSource(s)}
                                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 hover:bg-white/10 transition-all text-[11px] text-white/60"
                                >
                                  <span className="text-[#00D4C8] font-bold">[{idx + 1}]</span>
                                  <span>{s.doc_type || 'Web'}</span>
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {msg.follow_ups && msg.follow_ups.length > 0 && (
                          <div className="chip-container mt-5">
                            {msg.follow_ups.map((q, qIdx) => (
                              <button key={qIdx} onClick={() => handleSend(q)} className="pulse-chip">
                                <ChevronRight size={14} className="opacity-30" />
                                {q}
                              </button>
                            ))}
                          </div>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}

            {streamingMessage && (
              <div className={`message-ai ${streamingMessage.fund_slug ? FUND_METADATA[streamingMessage.fund_slug]?.theme : ''}`}>
                <div className="message-ai-label">
                  {streamingMessage.fund_slug ? FUND_METADATA[streamingMessage.fund_slug]?.name : "Fact Engine"}
                </div>
                {renderAnswer(streamingMessage.content)}
              </div>
            )}

            {loading && !streamingMessage && (
              <div className="message-ai">
                <div className="message-ai-label flex items-center gap-2">
                  <Activity size={12} className="animate-pulse" />
                  <span>Synthesizing...</span>
                </div>
              </div>
            )}
            <div ref={endOfMessagesRef} className="h-10" />
          </main>
        </div>

        <div className="input-bar-container">
          <div className="input-bar-content">
            {messages.length === 1 && !loading && (
              <div className="flex flex-wrap gap-2 mb-6 justify-center">
                {["Nifty 50 NAV?", "ELSS Lock-in?", "Value Fund manager?"].map((q, i) => (
                  <button key={i} onClick={() => handleSend(q)} className="pulse-chip bg-white/5 border-white/10">
                    {q}
                  </button>
                ))}
              </div>
            )}
            <div className="input-glass">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), handleSend(input))}
                placeholder="Query verified Groww data..."
                className="input-field"
                disabled={loading}
              />
              <button 
                onClick={() => handleSend(input)} 
                disabled={!input.trim() || loading}
                className="p-2.5 rounded-xl bg-white/10 hover:bg-white/20 transition-all text-white/80 disabled:opacity-20"
              >
                <Send size={20} />
              </button>
            </div>
            <div className="flex justify-center items-center gap-4 mt-4 opacity-30">
              <div className="flex items-center gap-1.5 text-[9px] uppercase tracking-[0.15em] text-white font-bold">
                <ShieldCheck size={10} />
                <span>Zero Advisory</span>
              </div>
              <div className="w-1 h-1 rounded-full bg-white/20" />
              <div className="flex items-center gap-1.5 text-[9px] uppercase tracking-[0.15em] text-white font-bold">
                <Clock size={10} />
                <span>Factual Integrity</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className={`insight-drawer glass-panel ${drawerSource ? 'open' : ''}`}>
        <div className="flex items-center justify-between mb-8">
          <h3 className="font-serif text-xl text-white/90 m-0 flex items-center gap-2">
            <BrainCircuit size={20} className="text-[#00D4C8]" />
            <span>Context</span>
          </h3>
          <button className="p-2 hover:bg-white/5 rounded-full transition-colors" onClick={() => setDrawerSource(null)}>
            <X size={20} className="text-white/40" />
          </button>
        </div>
        
        {drawerSource && (
          <div className="flex flex-col h-full gap-8">
            <div className="space-y-1.5">
              <label className="text-[10px] uppercase tracking-[0.2em] text-white/30 font-black">Verified Origin</label>
              <p className="text-sm text-[#00D4C8] font-semibold">{drawerSource.fund_name}</p>
            </div>
            
            <div className="flex flex-col gap-3 flex-1">
              <label className="text-[10px] uppercase tracking-[0.2em] text-white/30 font-black">Extracted Fragment</label>
              <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-xs text-white/60 leading-relaxed italic border-l-2 border-[#00D4C8]/40">
                "{drawerSource.snippet?.substring(0, 400)}..."
              </div>
            </div>
            
            <div className="mt-auto pb-8">
              <a 
                href={drawerSource.source_url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 w-full py-4 rounded-xl bg-white/5 border border-white/10 text-xs text-white hover:bg-white/10 transition-all font-bold"
               >
                <span>Open Official Document</span>
                <ExternalLink size={14} />
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
