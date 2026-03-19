"use client";

import { useState, useRef, useEffect } from "react";
import { Send, TrendingUp, ShieldCheck, Activity, BrainCircuit } from "lucide-react";

type Message = {
  role: "user" | "assistant";
  content: string;
  sources?: any[];
  gate_blocked?: string | null;
  response_type?: string;
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hi there! I am your factual AI guide for Groww Mutual Funds. Ask me about NAVs, expense ratios, exit loads, or benchmark data based on directly verified sources.",
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState<Message | null>(null);
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new message
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  const cleanAnswer = (text: string) =>
    text
      .replace(/\[Source:[^\]]*\]/g, '')
      .replace(/\[View Source\]/g, '')
      .trim();

  const renderAnswer = (text: string) => {
    const cleaned = cleanAnswer(text);
    const lines = cleaned
      .split('\n')
      .map(l => l.trim())
      .filter(Boolean);
      
    if (lines.length === 0) return null;
    
    return (
      <ul className="answer-list">
        {lines.map((line, i) => (
          <li key={i} className="answer-item">
            {line.replace(/^[\u2022\-\*]\s*/, '')}
          </li>
        ))}
      </ul>
    );
  };

  const getSourceLabel = (source: any) => {
    if (source.fund_name) {
      return source.fund_name
        .replace('Direct Growth', '')
        .replace('Groww', '')
        .trim();
    }
    // fallback: parse from URL
    const url = source.source_url || '';
    const slug = url.split('/').pop() || url;
    return slug
      .replace('groww-', '')
      .replace(/-/g, ' ')
      .replace('direct growth', '')
      .trim()
      .split(' ')
      .map((w: string) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  };

  const getSourceTypeLabel = (source: any) => {
    if (source.doc_type === 'SID') return 'Scheme Info Doc';
    if (source.doc_type === 'KIM') return 'Key Info Memo';
    return 'Live Data';
  };

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = { role: "user", content: text };
    const currentMessages = [...messages, userMsg];
    setMessages(currentMessages);
    setInput("");
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: text,
          history: messages
            .filter(m => m.role !== "assistant" || (m.content && !m.content.startsWith("❌ Error")))
            .map(m => ({ 
              role: m.role === "assistant" ? "ai" : m.role, 
              content: m.content 
            })), 
        }),
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      // Placeholder removed to prevent double bubbles. streamingMessage handles the active bubble.

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let accumulatedAnswer = "";
      let accumulatedSources: any[] = [];
      let accumulatedResponseType: string | undefined;
      let accumulatedGateBlocked: string | null = null;

      while (reader && !done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n').filter(line => line.trim());
        
        for (const line of lines) {
          const cleanLine = line.startsWith('data: ') ? line.slice(6) : line;
          if (!cleanLine || cleanLine === '[DONE]') continue;
          
          try {
            const data = JSON.parse(cleanLine);
            if (data.answer) accumulatedAnswer += data.answer;
            if (data.sources) accumulatedSources = data.sources;
            if (data.response_type) accumulatedResponseType = data.response_type;
            if (data.gate_blocked) accumulatedGateBlocked = data.gate_blocked;

            setStreamingMessage({
              role: "assistant",
              content: accumulatedAnswer,
              sources: accumulatedSources,
              gate_blocked: accumulatedGateBlocked,
              ...(accumulatedResponseType ? { response_type: accumulatedResponseType } : {})
            } as any);
          } catch (e) {
            continue;
          }
        }
      }

      // After stream completes, push the final message to history
      if (accumulatedAnswer || accumulatedGateBlocked) {
        setMessages(prev => [...prev, {
          role: "assistant",
          content: accumulatedAnswer,
          sources: accumulatedSources,
          gate_blocked: accumulatedGateBlocked,
          ...(accumulatedResponseType ? { response_type: accumulatedResponseType } : {})
        } as any]);
      }
      setStreamingMessage(null);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `❌ Error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const QUICK_PROMPTS = [
    "What is the Expense Ratio of the Nifty 50 Index Fund?",
    "Show me the Exit Load for ELSS Tax Saver.",
    "Show me the fund manager for Groww Value Fund.",
  ];

  return (
    <div className="chat-container">
      <header className="chat-header">
        <div className="header-badge">BETA</div>
        <h1 className="header-title">Groww Fact Engine</h1>
        <p className="header-subtitle">
          Verified data from official AMC documents & live sources
        </p>
      </header>

      <main className="flex flex-col gap-6">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "message-user" : "flex flex-col"}>
            {msg.role === "user" ? (
              <div className="message-user-bubble">
                {msg.content}
              </div>
            ) : (
              <div className="message-ai">
                <div className="message-ai-label">Growth AI</div>
                
                {msg.gate_blocked ? (
                   <div className={`gate-message ${msg.gate_blocked === 'advice_query' ? 'advice' : msg.gate_blocked}`}>
                     {msg.gate_blocked === 'out_of_scope' && "I only have information about Groww Nifty 50 Index Fund, Groww Value Fund, Groww Aggressive Hybrid Fund, and Groww ELSS Tax Saver Fund."}
                     {msg.gate_blocked === 'pii' && "Your query was blocked because it contains sensitive personal information."}
                     {msg.gate_blocked === 'zero_retrieval' && "I don't have that information in my knowledge base."}
                     {msg.gate_blocked === 'empty_query' && "Please enter a valid question."}
                     {msg.gate_blocked === 'advice_query' && (
                       renderAnswer(msg.content)
                     )}
                   </div>
                ) : (
                  <>
                    <div className="mb-4">
                      {renderAnswer(msg.content)}
                    </div>

                    {msg.sources && msg.sources.length > 0 && msg.response_type !== 'refusal' && (
                      <div className="sources-panel">
                        {(() => {
                          const validSources = msg.sources
                            .filter(s => s?.source_url && s.source_url.startsWith('https://'))
                            .filter((s, i, arr) =>
                              arr.findIndex(x =>
                                  x.fund_name === s.fund_name &&
                                  x.source_url === s.source_url
                              ) === i
                            )
                            .slice(0, 3);

                          if (validSources.length === 0) return null;

                          return (
                            <>
                              <div className="sources-header">
                                <span className="sources-icon">⟨/⟩</span>
                                <span className="sources-label">Verified Sources</span>
                              </div>
                              <div className="sources-list">
                                {validSources.map((s: any, idx) => (
                                  <a
                                    key={idx}
                                    href={s.source_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="source-link"
                                  >
                                    <span className="source-index">{idx + 1}</span>
                                    <span className="source-type">
                                      {getSourceTypeLabel(s)}
                                    </span>
                                    <span className="source-fund">
                                      {getSourceLabel(s)}
                                    </span>
                                    <span className="source-arrow">↗</span>
                                  </a>
                                ))}
                              </div>
                            </>
                          );
                        })()}
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </div>
        ))}

        {streamingMessage && (
          <div className="flex flex-col">
            <div className="message-ai">
              <div className="message-ai-label">Growth AI</div>
              {streamingMessage.gate_blocked ? (
                 <div className={`gate-message ${streamingMessage.gate_blocked === 'advice_query' ? 'advice' : streamingMessage.gate_blocked}`}>
                   {streamingMessage.gate_blocked === 'out_of_scope' && "I only have information about Groww Nifty 50 Index Fund, Groww Value Fund, Groww Aggressive Hybrid Fund, and Groww ELSS Tax Saver Fund."}
                   {streamingMessage.gate_blocked === 'pii' && "Your query was blocked because it contains sensitive personal information."}
                   {streamingMessage.gate_blocked === 'zero_retrieval' && "I don't have that information in my knowledge base."}
                   {streamingMessage.gate_blocked === 'empty_query' && "Please enter a valid question."}
                   {streamingMessage.gate_blocked === 'advice_query' && (
                     renderAnswer(streamingMessage.content)
                   )}
                 </div>
              ) : (
                <>
                  <div className="mb-4">
                    {renderAnswer(streamingMessage.content)}
                  </div>
                  {streamingMessage.sources && streamingMessage.sources.length > 0 && streamingMessage.response_type !== 'refusal' && (
                    <div className="sources-panel">
                       <div className="sources-header">
                        <span className="sources-icon">⟨/⟩</span>
                        <span className="sources-label">Verified Sources</span>
                      </div>
                      <div className="sources-list animate-pulse opacity-50">
                        {streamingMessage.sources.filter((s: any, i: number, arr: any[]) =>
                            arr.findIndex((x: any) =>
                                x.fund_name === s.fund_name &&
                                x.source_url === s.source_url
                            ) === i
                          )
.slice(0,3).map((s: any, idx: number) => (
                           <div key={idx} className="source-link cursor-default">
                            <span className="source-index">{idx + 1}</span>
                            <span className="source-fund">{getSourceLabel(s)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        )}

        {loading && !streamingMessage && (
          <div className="message-ai">
            <div className="message-ai-label">Retrieving Context</div>
            <div className="loading-dots">
              <div className="loading-dot" />
              <div className="loading-dot" />
              <div className="loading-dot" />
            </div>
          </div>
        )}

        <div ref={endOfMessagesRef} />
      </main>

      <div className="input-bar">
        <div className="max-w-[760px] mx-auto mb-4">
          {messages.length === 1 && (
            <div className="flex flex-wrap gap-2 mb-4 justify-center">
              {QUICK_PROMPTS.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(prompt)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-slate-400 hover:bg-gold/10 hover:text-gold hover:border-gold/30 transition-all duration-300"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="input-wrapper">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend(input);
              }
            }}
            disabled={loading}
            placeholder="Ask about Groww Mutual Funds..."
            className="input-field resize-none h-6 pt-0"
            rows={1}
          />
          <button
            onClick={() => handleSend(input)}
            disabled={!input.trim() || loading}
            className="send-button"
          >
            <Send size={18} />
          </button>
        </div>
        
        <p className="text-[10px] text-center mt-3 text-slate-500 uppercase tracking-widest opacity-50">
          Strictly Factual. No Advisory. Powered by Groww RAG Engine.
        </p>
      </div>
    </div>
  );
}
