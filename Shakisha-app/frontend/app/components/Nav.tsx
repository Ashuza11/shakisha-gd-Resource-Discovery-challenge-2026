"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";

const LINKS = [
  { href: "/", label: "Home", emoji: "🏠" },
  { href: "/discovery", label: "Discovery", emoji: "🔍" },
  { href: "/analytics", label: "Analytics", emoji: "📊" },
  { href: "/quality", label: "Data Quality", emoji: "✅" },
  { href: "/brief", label: "Brief", emoji: "📄" },
  { href: "/pipeline", label: "Pipeline", emoji: "⚙️" },
];

export default function Nav() {
  const path = usePathname();
  const [menuOpen, setMenuOpen] = useState(false);

  // Close on route change, unlock scroll
  useEffect(() => { setMenuOpen(false); }, [path]);
  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuOpen]);

  const close = () => setMenuOpen(false);

  return (
    <>
      {/* ── Top bar ─────────────────────────────────────────── */}
      <header style={{ background: "var(--warm-white)", borderBottom: "1px solid var(--border)", position: "sticky", top: 0, zIndex: 1100 }}>
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "0 16px", height: 56, display: "flex", alignItems: "center", gap: 12 }}>

          {/* Logo */}
          <Link href="/" style={{ textDecoration: "none", display: "flex", alignItems: "center", gap: 9, flexShrink: 0 }}>
            {/* Shakisha logo: magnifying glass lens + 4 data dots + ♀ symbol */}
            <svg width="22" height="34" viewBox="0 0 32 50" fill="none" aria-hidden="true">
              <circle cx="16" cy="13" r="11" stroke="var(--coral)" strokeWidth="2.2" fill="none" />
              <circle cx="11" cy="8"  r="1.9" fill="var(--coral)" />
              <circle cx="21" cy="8"  r="1.9" fill="var(--coral)" />
              <circle cx="11" cy="18" r="1.9" fill="var(--coral)" />
              <circle cx="21" cy="18" r="1.9" fill="var(--coral)" />
              <line x1="16" y1="24" x2="16" y2="42" stroke="var(--coral)" strokeWidth="2.2" strokeLinecap="round" />
              <line x1="9"  y1="34" x2="23" y2="34" stroke="var(--coral)" strokeWidth="2.2" strokeLinecap="round" />
            </svg>
            <span style={{ fontFamily: "'Playfair Display', Georgia, serif", fontWeight: 700, fontSize: 18, color: "var(--charcoal)", letterSpacing: "0.04em" }}>
              Shakisha
            </span>
          </Link>

          {/* Desktop links — hidden below 768px via CSS */}
          <nav style={{ display: "flex", alignItems: "center", gap: 2, flex: 1, overflowX: "auto", scrollbarWidth: "none" }} className="nav-desktop">
            {LINKS.map(({ href, label }) => {
              const active = path === href || (href !== "/" && path.startsWith(href));
              return (
                <Link key={href} href={href} style={{ padding: "5px 10px", borderRadius: 8, fontSize: 13, fontWeight: active ? 600 : 400, color: active ? "var(--coral)" : "var(--muted)", background: active ? "rgba(192,79,79,0.08)" : "transparent", textDecoration: "none", whiteSpace: "nowrap", flexShrink: 0 }}>
                  {label}
                </Link>
              );
            })}
          </nav>

          {/* Badge — desktop only */}
          <span className="nav-badge">GDRD Hackathon 2026</span>

          {/* Hamburger — mobile only, hidden on desktop via CSS */}
          <button
            className="nav-hamburger"
            onClick={() => setMenuOpen((v) => !v)}
            aria-label="Open navigation"
          >
            <span style={{ display: "block", width: 22, height: 2, background: menuOpen ? "var(--coral)" : "var(--charcoal)", borderRadius: 2, transition: "transform .25s, opacity .25s", transform: menuOpen ? "translateY(7px) rotate(45deg)" : "none" }} />
            <span style={{ display: "block", width: 22, height: 2, background: menuOpen ? "var(--coral)" : "var(--charcoal)", borderRadius: 2, transition: "opacity .25s", opacity: menuOpen ? 0 : 1 }} />
            <span style={{ display: "block", width: 22, height: 2, background: menuOpen ? "var(--coral)" : "var(--charcoal)", borderRadius: 2, transition: "transform .25s, opacity .25s", transform: menuOpen ? "translateY(-7px) rotate(-45deg)" : "none" }} />
          </button>
        </div>
      </header>

      {/* ── Overlay (mobile only, conditional render) ────────── */}
      {menuOpen && (
        <div
          onClick={close}
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 201, cursor: "pointer" }}
        />
      )}

      {/* ── Side drawer (always mounted, slides via transform) ── */}
      <div
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          height: "100dvh",
          width: "min(270px, 88vw)",
          background: "var(--warm-white)",
          zIndex: 202,
          boxShadow: "-4px 0 32px rgba(0,0,0,0.15)",
          transform: menuOpen ? "translateX(0)" : "translateX(100%)",
          transition: "transform 0.28s cubic-bezier(0.4,0,0.2,1)",
          display: "flex",
          flexDirection: "column",
        }}
        className="nav-drawer"
      >
        {/* Drawer top bar */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 20px", height: 56, borderBottom: "1px solid var(--border)", flexShrink: 0 }}>
          <span style={{ fontFamily: "'Playfair Display', Georgia, serif", fontWeight: 700, fontSize: 16, color: "var(--charcoal)" }}>Menu</span>
          <button onClick={close} style={{ background: "none", border: "none", cursor: "pointer", fontSize: 22, color: "var(--muted)", lineHeight: 1, padding: "4px 8px" }}>✕</button>
        </div>

        {/* Links */}
        <nav style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
          {LINKS.map(({ href, label, emoji }) => {
            const active = path === href || (href !== "/" && path.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                onClick={close}
                style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 20px", fontSize: 15, fontWeight: active ? 600 : 400, color: active ? "var(--coral)" : "var(--charcoal)", background: active ? "rgba(192,79,79,0.06)" : "transparent", textDecoration: "none", borderLeft: `3px solid ${active ? "var(--coral)" : "transparent"}` }}
              >
                <span style={{ fontSize: 18, lineHeight: 1 }}>{emoji}</span>
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding: "16px 20px", borderTop: "1px solid var(--border)", flexShrink: 0 }}>
          <span className="nav-badge">GDRD Hackathon 2026</span>
        </div>
      </div>
    </>
  );
}
