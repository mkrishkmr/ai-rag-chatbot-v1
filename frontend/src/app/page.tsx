"use client";

import { useState, useRef, useEffect } from "react";
import { Send, TrendingUp, ShieldCheck, Activity, BrainCircuit } from "lucide-react";

type Message = {
  role: "user" | "assistant";
  content: string;
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
  const endOfMessagesRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new message
  useEffect(() => {
    endOfMessagesRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: text,
          history: messages.slice(-5), // Keep last 5 messages for context
        }),
      });

      if (!response.ok) {
        throw new Error(await response.text());
      }

      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (reader && !done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunkValue = decoder.decode(value);
        if (chunkValue) {
          setMessages((prev) => {
            const newMsgs = [...prev];
            const lastMsg = newMsgs[newMsgs.length - 1];
            newMsgs[newMsgs.length - 1] = {
              ...lastMsg,
              content: lastMsg.content + chunkValue
            };
            return newMsgs;
          });
        }
      }
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
    "Compare NAV of Value Fund vs Aggressive Hybrid.",
  ];

  const formatContent = (text: string) => {
    // Split text by URLs
    const parts = text.split(/(https?:\/\/[^\s]+)/g);
    return parts.map((part, i) => {
      // If the part is a URL, render it nicely
      if (part.match(/^https?:\/\//)) {
        // Strip trailing punctuation from URL if caught
        const cleanUrl = part.replace(/[.)\]}]+$/, '');
        return (
          <a
            key={i}
            href={cleanUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-emerald-400 hover:text-emerald-300 font-medium underline underline-offset-4 transition-colors"
          >
            [View Source]
          </a>
        );
      }
      return <span key={i}>{part}</span>;
    });
  };

  return (
    <div className="min-h-screen relative overflow-hidden bg-[#0B0E14] text-[#F8F9FA] flex flex-col items-center">
      {/* Background Decorative Blobs */}
      <div className="absolute top-[-10%] left-[-10%] w-[40vw] h-[40vw] bg-sky-600/20 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40vw] h-[40vw] bg-blue-900/40 rounded-full blur-[120px] pointer-events-none" />

      {/* Header */}
      <header className="w-full max-w-4xl pt-8 pb-4 px-6 flex items-center justify-between z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-sky-500/10 rounded-xl border border-sky-400/20 glass-glow">
            <TrendingUp className="text-sky-400 w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-wide">Groww AI Fact Engine</h1>
            <p className="text-xs text-slate-400">Strictly Factual. No Advisory.</p>
          </div>
        </div>

        {/* Trust Indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-medium text-emerald-400 tracking-wide uppercase">Live Connection</span>
        </div>
      </header>

      {/* Chat Container */}
      <main className="flex-1 w-full max-w-4xl px-4 md:px-6 py-4 flex flex-col z-10 h-0">
        <div className="glass-panel flex-1 rounded-3xl p-4 md:p-6 overflow-y-auto flex flex-col gap-6 relative">

          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} animate-in slide-in-from-bottom-2 duration-300`}>
              <div
                className={`max-w-[85%] md:max-w-[75%] rounded-2xl p-4 ${msg.role === "user"
                  ? "bg-sky-500/20 border border-sky-400/30 text-white rounded-br-sm"
                  : "bg-white/5 border border-white/10 text-slate-200 rounded-bl-sm"
                  }`}
              >
                {msg.role === "assistant" && (
                  <div className="flex items-center gap-2 mb-2 pb-2 border-b border-white/5">
                    <BrainCircuit className="w-4 h-4 text-sky-400" />
                    <span className="text-xs font-semibold text-sky-400 uppercase tracking-widest">Growth AI</span>
                  </div>
                )}

                <div className="leading-relaxed whitespace-pre-wrap text-[15px]">
                  {formatContent(msg.content)}
                </div>

                {/* Source/Citation Highlighting */}
                {msg.role === "assistant" && msg.content.includes("Source:") && (
                  <div className="mt-3 pt-3 border-t border-white/10 flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs text-emerald-400">Fact-checked against verified SID/Web data</span>
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="glass-panel max-w-[75%] rounded-2xl rounded-bl-sm p-4 border border-white/5 flex flex-col gap-3">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-sky-400 animate-pulse" />
                  <span className="text-xs font-semibold text-slate-300 tracking-wider">RETRIEVING CONTEXT</span>
                </div>
                <div className="flex gap-1.5 mt-1">
                  <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 rounded-full bg-slate-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={endOfMessagesRef} />
        </div>

        {/* Input Area */}
        <div className="mt-6 flex flex-col gap-3">
          {messages.length === 1 && (
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-xs text-slate-400 font-medium uppercase tracking-wider mr-2">Quick asks:</span>
              {QUICK_PROMPTS.map((prompt, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(prompt)}
                  className="text-xs px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-slate-300 hover:bg-sky-500/20 hover:text-sky-300 hover:border-sky-400/30 transition-all duration-300"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}

          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-sky-500/20 to-blue-500/20 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition duration-500" />
            <div className="relative glass-panel rounded-2xl flex items-end p-2 border border-white/10 group-focus-within:border-sky-500/50 transition duration-300 bg-[#12161E]/80">
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
                placeholder="Ask about NAV, Expense Ratios, or Exit Loads..."
                className="w-full bg-transparent resize-none outline-none py-3 px-4 text-white placeholder-slate-500 max-h-32 min-h-[56px]"
                rows={1}
              />
              <button
                onClick={() => handleSend(input)}
                disabled={!input.trim() || loading}
                className="p-3 bg-sky-500 hover:bg-sky-400 disabled:bg-white/5 disabled:text-slate-500 text-white rounded-xl shadow-[0_0_15px_rgba(56,189,248,0.3)] transition-all duration-300 m-1 flex-shrink-0"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
