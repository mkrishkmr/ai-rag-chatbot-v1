"use client";

import { useState, useRef, useEffect } from "react";
import { Send, FileText, CheckCircle2, ShieldAlert } from "lucide-react";

export default function Home() {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: "assistant", content: "I am the official Groww Mutual Fund fact assistant. I provide verified data directly from SIDs and live NAV metrics. How can I help you?" }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleChat = async (overrideInput?: string) => {
    const textToSend = overrideInput || input;
    if (!textToSend.trim()) return;

    const userMsg = { role: "user", content: textToSend };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    // Placeholder for stream
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: textToSend,
          history: messages.slice(1) // exclude intro
        }),
      });

      if (res.status === 403 || res.status === 400) {
        const errorData = await res.json();
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { role: "assistant", content: `🚨 Security Block: ${errorData.detail}` }
        ]);
        setIsTyping(false);
        return;
      }

      if (!res.body) throw new Error("No response body");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        const chunkValue = decoder.decode(value);
        if (chunkValue) {
          setMessages((prev) => {
            const last = prev[prev.length - 1];
            return [
              ...prev.slice(0, -1),
              { role: "assistant", content: last.content + chunkValue }
            ];
          });
        }
      }
    } catch (err) {
      console.error(err);
      setMessages((prev) => [
        ...prev.slice(0, -1),
        { role: "assistant", content: "Error connecting to the Groww Facts API. Make sure the backend is running." }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const quickQuestions = [
    "What is the lock-in period for ELSS Tax Saver?",
    "What is the exit load for Value Fund?",
    "Which fund is better for me?", // Tests refusal
    "My PAN is ABCDE1234F, tell me my NAV." // Tests PII block
  ];

  return (
    <main className="min-h-screen relative overflow-hidden flex flex-col items-center py-10 px-4">
      {/* Background Decorators */}
      <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-blue-600/30 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] bg-emerald-500/20 rounded-full blur-[150px] pointer-events-none" />

      {/* Main Container */}
      <div className="w-full max-w-4xl glass rounded-3xl flex flex-col h-[85vh] z-10 overflow-hidden text-slate-100">

        {/* Header */}
        <div className="px-6 py-4 border-b border-white/10 flex items-center justify-between bg-white/5">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
              <ShieldAlert className="text-white w-6 h-6" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">Groww Fact Assistant</h1>
              <div className="flex items-center space-x-2 text-xs text-emerald-400">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span>Live Connection: Official Sources</span>
              </div>
            </div>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/20">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className={`max-w-[85%] rounded-2xl px-5 py-4 ${msg.role === "user"
                ? "bg-blue-600/80 backdrop-blur-sm text-white rounded-br-none shadow-lg shadow-blue-900/50"
                : "glass-card text-slate-200 rounded-bl-none"
                }`}>
                {msg.role === "assistant" && i > 0 && msg.content.includes("Source:") && (
                  <div className="mb-3 p-3 bg-black/30 rounded-lg flex items-start space-x-3 border border-white/5">
                    <CheckCircle2 className="w-5 h-5 text-emerald-400 mt-0.5 shrink-0" />
                    <div className="text-sm">
                      <p className="font-semibold text-emerald-400">Verified Source Citation</p>
                      <p className="text-slate-400 italic mt-1 line-clamp-2">{msg.content.split("Source:")[1]?.split("\\n")[0] || "Groww Official Document"}</p>
                    </div>
                  </div>
                )}

                <p className="whitespace-pre-wrap leading-relaxed tracking-wide text-[15px]">
                  {msg.content.replace(/Source:.*\\n/g, '')}
                </p>
              </div>
            </div>
          ))}
          {/* Skeleton Loader while typing (cold start buffer) */}
          {isTyping && messages[messages.length - 1]?.content === "" && (
            <div className="flex justify-start">
              <div className="max-w-[85%] rounded-2xl px-5 py-4 glass-card rounded-bl-none animate-pulse flex space-x-2">
                <div className="w-2 h-2 bg-white/40 rounded-full"></div>
                <div className="w-2 h-2 bg-white/40 rounded-full animation-delay-200"></div>
                <div className="w-2 h-2 bg-white/40 rounded-full animation-delay-400"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-black/20 border-t border-white/10">
          {/* Quick Chips */}
          <div className="flex space-x-2 mb-4 overflow-x-auto pb-2 scrollbar-none">
            {quickQuestions.map((q, idx) => (
              <button
                key={idx}
                onClick={() => handleChat(q)}
                disabled={isTyping}
                className="whitespace-nowrap px-4 py-2 text-xs font-medium bg-white/5 border border-white/10 rounded-full hover:bg-white/10 transition-colors text-emerald-100 hover:text-white"
              >
                {q}
              </button>
            ))}
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleChat()}
              placeholder="Ask about Lock-ins, Exit Loads, or NAV..."
              className="flex-1 px-5 py-3 rounded-xl bg-white/5 border border-white/10 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-transparent transition-all"
              disabled={isTyping}
            />
            <button
              onClick={() => handleChat()}
              disabled={!input.trim() || isTyping}
              className="px-5 py-3 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl shadow-lg shadow-emerald-900/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center shrink-0"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
          <div className="mt-3 text-center text-xs text-slate-500">
            Strictly factual responses. No investment advice is provided by this system.
          </div>
        </div>
      </div>
    </main>
  );
}
