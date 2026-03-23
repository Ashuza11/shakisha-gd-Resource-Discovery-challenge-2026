"use client";

import { useEffect, useRef, useState } from "react";
import { api, ChatMessage, Study } from "../lib/api";

interface Props {
  study: Study;
  onClose: () => void;
}

const SUGGESTED_QUESTIONS = [
  "What are the key findings of this study?",
  "What data is available for women and girls?",
  "Which districts or provinces are covered?",
  "What years does this data cover?",
  "How can this data be used for advocacy?",
];

export default function SourceChatModal({ study, onClose }: Props) {
  const [messages, setMessages]               = useState<ChatMessage[]>([]);
  const [input, setInput]                     = useState("");
  const [loading, setLoading]                 = useState(false);
  const [extractedContent, setExtractedContent] = useState<string | undefined>(undefined);
  const [sourceUsed, setSourceUsed]           = useState<"tavily" | "abstract" | null>(null);
  const [error, setError]                     = useState("");
  const bottomRef                             = useRef<HTMLDivElement>(null);
  const inputRef                              = useRef<HTMLInputElement>(null);

  // Close on Escape
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Focus input on open
  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 100);
  }, []);

  async function send(question: string) {
    if (!question.trim() || loading) return;
    setError("");
    const userMsg: ChatMessage = { role: "user", content: question };
    const nextHistory = [...messages, userMsg];
    setMessages(nextHistory);
    setInput("");
    setLoading(true);

    try {
      const r = await api.ask(
        study.study_id,
        question,
        messages,              // history BEFORE this message (backend adds current question)
        extractedContent,      // undefined on first call → Tavily extracts; cached thereafter
      );
      setMessages([...nextHistory, { role: "assistant", content: r.answer }]);
      // Cache extracted content so follow-up messages skip Tavily
      if (!extractedContent) {
        setExtractedContent(r.extracted_content);
        setSourceUsed(r.source_used);
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Something went wrong. Please try again.");
      // Remove the optimistic user message on error
      setMessages(messages);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed", inset: 0,
          background: "rgba(26,20,16,0.55)",
          zIndex: 1200,
          backdropFilter: "blur(2px)",
        }}
      />

      {/* Modal panel */}
      <div
        className="chat-modal"
        style={{
          position: "fixed",
          top: "50%", left: "50%",
          transform: "translate(-50%, -50%)",
          background: "var(--warm-white)",
          borderRadius: 16,
          boxShadow: "0 24px 80px rgba(0,0,0,0.28)",
          zIndex: 1300,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* ── Header ── */}
        <div style={{
          padding: "16px 18px 12px",
          borderBottom: "1px solid var(--border)",
          flexShrink: 0,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: "var(--coral)", textTransform: "uppercase", letterSpacing: "0.07em", marginBottom: 4 }}>
                Ask about this source
              </div>
              <div style={{ fontWeight: 700, fontSize: 14, color: "var(--charcoal)", lineHeight: 1.4, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                {study.title}
              </div>
              <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
                {[study.organization, study.year, study.geographic_coverage].filter(Boolean).join(" · ")}
              </div>
            </div>
            <button
              onClick={onClose}
              style={{ background: "none", border: "none", cursor: "pointer", fontSize: 20, color: "var(--muted)", lineHeight: 1, padding: "2px 6px", flexShrink: 0 }}
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          {/* Source badge — shown once extraction is done */}
          {sourceUsed && (
            <div style={{ marginTop: 8 }}>
              <span style={{
                fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 999,
                background: sourceUsed === "tavily" ? "var(--rw-green-light)" : "var(--rw-yellow-light)",
                color: sourceUsed === "tavily" ? "var(--rw-green)" : "#92620A",
              }}>
                {sourceUsed === "tavily" ? "Content extracted from source" : "Answering from catalog summary"}
              </span>
            </div>
          )}
        </div>

        {/* ── Messages ── */}
        <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px", display: "flex", flexDirection: "column", gap: 12 }}>

          {/* Empty state — suggested questions */}
          {messages.length === 0 && !loading && (
            <div>
              <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 14, lineHeight: 1.6 }}>
                Ask any question about this study. Shakisha will read the source and answer based on what it finds.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                {SUGGESTED_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => send(q)}
                    style={{
                      textAlign: "left", padding: "8px 14px",
                      background: "var(--cream)", border: "1px solid var(--border)",
                      borderRadius: 8, fontSize: 13, color: "var(--charcoal)",
                      cursor: "pointer", transition: "background 0.15s",
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.background = "rgba(192,79,79,0.06)")}
                    onMouseLeave={(e) => (e.currentTarget.style.background = "var(--cream)")}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Message bubbles */}
          {messages.map((msg, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: msg.role === "user" ? "flex-end" : "flex-start",
              }}
            >
              <div
                style={{
                  maxWidth: "82%",
                  padding: "10px 14px",
                  borderRadius: msg.role === "user" ? "12px 12px 4px 12px" : "12px 12px 12px 4px",
                  background: msg.role === "user" ? "var(--coral)" : "var(--cream)",
                  color: msg.role === "user" ? "white" : "var(--charcoal)",
                  fontSize: 13,
                  lineHeight: 1.65,
                  border: msg.role === "assistant" ? "1px solid var(--border)" : "none",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {msg.content}
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {loading && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div style={{
                padding: "10px 16px", borderRadius: "12px 12px 12px 4px",
                background: "var(--cream)", border: "1px solid var(--border)",
                display: "flex", gap: 4, alignItems: "center",
              }}>
                {[0, 1, 2].map((i) => (
                  <span key={i} style={{
                    width: 6, height: 6, borderRadius: "50%",
                    background: "var(--muted)",
                    animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
                    display: "inline-block",
                  }} />
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          {error && (
            <div style={{
              padding: "10px 14px", borderRadius: 8,
              background: "#FCE8E8", border: "1px solid #E8A0A0",
              fontSize: 13, color: "var(--coral-dark)",
            }}>
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* ── Input bar ── */}
        <div style={{
          padding: "12px 16px",
          borderTop: "1px solid var(--border)",
          flexShrink: 0,
          display: "flex", gap: 10,
          background: "var(--warm-white)",
        }}>
          <input
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }}
            placeholder="Ask a question about this study…"
            disabled={loading}
            style={{
              flex: 1, padding: "10px 14px",
              border: "1.5px solid var(--border)", borderRadius: 10,
              background: "var(--cream)", fontSize: 13,
              color: "var(--charcoal)", outline: "none",
            }}
          />
          <button
            onClick={() => send(input)}
            disabled={!input.trim() || loading}
            style={{
              padding: "10px 18px", borderRadius: 10,
              background: !input.trim() || loading ? "var(--cream-dark)" : "var(--coral)",
              color: !input.trim() || loading ? "var(--muted)" : "white",
              border: "none", cursor: !input.trim() || loading ? "default" : "pointer",
              fontWeight: 600, fontSize: 13, flexShrink: 0,
              transition: "background 0.15s",
            }}
          >
            Send
          </button>
        </div>
      </div>

      <style>{`
        @keyframes pulse {
          0%, 80%, 100% { opacity: 0.3; transform: scale(0.85); }
          40% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </>
  );
}
