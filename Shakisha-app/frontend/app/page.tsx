"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api, CatalogStats, DomainConfig, Study } from "./lib/api";

// ── Constants ─────────────────────────────────────────────────────────────────

const ACTIVE_DOMAINS = ["labour", "agriculture", "health", "household", "finance", "population"];

const CYCLE = [
  { word: "Search",   color: "var(--coral)" },
  { word: "Discover", color: "var(--rw-green)" },
  { word: "Validate", color: "#92620A" },
  { word: "Act",      color: "var(--earth)" },
  { word: "Grow",     color: "#1565C0" },
];

const QUALITY_STRIPE: Record<string, string> = {
  good:     "card-stripe-good",
  warning:  "card-stripe-warning",
  critical: "card-stripe-critical",
};
const QUALITY_PILL: Record<string, { cls: string; label: string }> = {
  good:     { cls: "badge-good",     label: "Good" },
  warning:  { cls: "badge-warning",  label: "Warning" },
  critical: { cls: "badge-critical", label: "Critical" },
};

// ── Shakisha logo SVG ─────────────────────────────────────────────────────────

function ShakishaLogo({ size = 60 }: { size?: number }) {
  const w = Math.round(size * 0.68);
  const h = size;
  return (
    <svg width={w} height={h} viewBox="0 0 32 50" fill="none" aria-hidden="true">
      {/* Lens circle */}
      <circle cx="16" cy="13" r="11" stroke="var(--coral)" strokeWidth="2.2" fill="none" />
      {/* 4 data dots — 2×2 grid inside lens */}
      <circle cx="11" cy="8"  r="2" fill="var(--coral)" />
      <circle cx="21" cy="8"  r="2" fill="var(--coral)" />
      <circle cx="11" cy="18" r="2" fill="var(--coral)" />
      <circle cx="21" cy="18" r="2" fill="var(--coral)" />
      {/* Handle + ♀ stem */}
      <line x1="16" y1="24" x2="16" y2="42" stroke="var(--coral)" strokeWidth="2.2" strokeLinecap="round" />
      {/* ♀ crossbar */}
      <line x1="9"  y1="34" x2="23" y2="34" stroke="var(--coral)" strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}

// ── Imigongo divider between sections ────────────────────────────────────────

function ImigongoDivider() {
  return (
    <div aria-hidden="true" style={{ overflow: "hidden", height: 24, lineHeight: 0 }}>
      <svg width="100%" height="24" viewBox="0 0 800 24" preserveAspectRatio="xMidYMid slice">
        <defs>
          <pattern id="imi-sec" x="0" y="0" width="48" height="24" patternUnits="userSpaceOnUse">
            <polygon points="0,0 24,12 48,0 48,3 24,15 0,3"   fill="#C04F4F" opacity="0.13" />
            <polygon points="0,21 24,9 48,21 48,24 24,12 0,24" fill="#8B5E3C" opacity="0.09" />
          </pattern>
        </defs>
        <rect width="100%" height="24" fill="url(#imi-sec)" />
      </svg>
    </div>
  );
}

// ── Home study card ───────────────────────────────────────────────────────────

function HomeStudyCard({
  study,
  domainKey,
  domains,
}: {
  study: Study;
  domainKey: string;
  domains: Record<string, DomainConfig>;
}) {
  const q      = QUALITY_PILL[study.quality_level] ?? QUALITY_PILL.warning;
  const stripe = QUALITY_STRIPE[study.quality_level] ?? "card-stripe-default";
  const dom    = domains[domainKey];
  const org    = study.organization
    ? study.organization.split(" ").slice(0, 5).join(" ") + (study.organization.split(" ").length > 5 ? "…" : "")
    : "";

  return (
    <div
      className={`study-card ${stripe}`}
      style={{ padding: "18px 20px", display: "flex", flexDirection: "column", height: "100%" }}
    >
      {/* Domain + quality row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
        <span style={{ fontSize: 12, color: "var(--muted)", display: "flex", alignItems: "center", gap: 5 }}>
          <span>{dom?.emoji}</span>
          <span>{dom?.name}</span>
        </span>
        <span className={`pill ${q.cls}`}>{q.label}</span>
      </div>

      {/* Title */}
      <div
        style={{
          fontWeight: 700,
          fontSize: 14,
          color: "var(--charcoal)",
          lineHeight: 1.45,
          marginBottom: 8,
          flex: 1,
          display: "-webkit-box",
          WebkitLineClamp: 3,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {study.title}
      </div>

      {/* Metadata */}
      <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 14 }}>
        {[org, study.year].filter(Boolean).join(" · ")}
        {study.resource_count > 0 && ` · ${study.resource_count} resource${study.resource_count !== 1 ? "s" : ""}`}
      </div>

      {/* Actions */}
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <Link
          href={`/discovery?domain=${domainKey}`}
          className="btn-ghost"
          style={{ fontSize: 11, padding: "4px 10px" }}
        >
          Explore →
        </Link>
        <Link
          href={`/brief?study=${study.study_id}`}
          className="btn-primary"
          style={{ fontSize: 11, padding: "4px 12px", marginLeft: "auto" }}
        >
          Generate brief
        </Link>
      </div>
    </div>
  );
}

// ── How-it-works step ────────────────────────────────────────────────────────

function Step({
  n, icon, title, body,
}: {
  n: string; icon: string; title: string; body: string;
}) {
  return (
    <div style={{ textAlign: "center", padding: "0 8px" }}>
      <div
        style={{
          width: 52,
          height: 52,
          background: "var(--coral)",
          color: "white",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 22,
          margin: "0 auto 14px",
          boxShadow: "0 4px 16px rgba(192,79,79,0.28)",
        }}
      >
        {icon}
      </div>
      <div style={{ fontSize: 11, fontWeight: 700, color: "var(--coral)", letterSpacing: "0.08em", textTransform: "uppercase", marginBottom: 6 }}>
        Step {n}
      </div>
      <div style={{ fontWeight: 700, fontSize: 15, color: "var(--charcoal)", marginBottom: 8 }}>{title}</div>
      <div style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.65 }}>{body}</div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

type FeaturedStudy = { study: Study; domainKey: string };

export default function Home() {
  const router = useRouter();

  const [stats,    setStats]    = useState<CatalogStats | null>(null);
  const [domains,  setDomains]  = useState<Record<string, DomainConfig>>({});
  const [featured, setFeatured] = useState<FeaturedStudy[]>([]);
  const [loadingStudies, setLoadingStudies] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  // Cycling word animation
  const [cycleIdx,     setCycleIdx]     = useState(0);
  const [cycleVisible, setCycleVisible] = useState(true);

  useEffect(() => {
    api.stats().then(setStats).catch(() => {});
    api.domains().then(setDomains).catch(() => {});

    // Fetch 2 studies per domain in parallel (NISR base = all studies)
    Promise.all(
      ACTIVE_DOMAINS.map((domain) =>
        api
          .search({ domain, query: "", sort_order: "Newest first", use_ai: false })
          .then((r) => r.results.slice(0, 2).map((study) => ({ study, domainKey: domain })))
          .catch(() => [] as FeaturedStudy[])
      )
    )
      .then((groups) => setFeatured(groups.flat()))
      .finally(() => setLoadingStudies(false));
  }, []);

  // Cycle animation: fade out → swap word → fade in
  useEffect(() => {
    const t = setInterval(() => {
      setCycleVisible(false);
      setTimeout(() => {
        setCycleIdx((i) => (i + 1) % CYCLE.length);
        setCycleVisible(true);
      }, 320);
    }, 2200);
    return () => clearInterval(t);
  }, []);

  const handleSearch = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      const q = searchQuery.trim();
      router.push(q ? `/discovery?q=${encodeURIComponent(q)}` : "/discovery");
    },
    [router, searchQuery]
  );

  const activeDomains = Object.entries(domains).filter(([, d]) => d.status === "active");

  return (
    <div style={{ background: "var(--cream)", minHeight: "100vh" }}>

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section style={{ textAlign: "center", padding: "64px 24px 52px", maxWidth: 760, margin: "0 auto" }}>

        {/* Logo + wordmark */}
        <div className="animate-fade-up" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14, marginBottom: 28 }}>
          <ShakishaLogo size={80} />
          <div>
            <div
              style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontWeight: 700,
                fontSize: "clamp(28px, 5vw, 44px)",
                letterSpacing: "0.12em",
                color: "var(--charcoal)",
                lineHeight: 1,
              }}
            >
              SHAKISHA
            </div>
            <div
              style={{
                fontSize: 13,
                fontWeight: 400,
                color: "var(--muted)",
                letterSpacing: "0.1em",
                textTransform: "uppercase",
                marginTop: 6,
              }}
            >
              Gender Data Discovery
            </div>
          </div>
        </div>

        {/* Animated cycling tagline */}
        <div
          className="animate-fade-up"
          style={{ display: "flex", alignItems: "baseline", justifyContent: "center", gap: 8, marginBottom: 36, minHeight: 40 }}
        >
          <span style={{ fontSize: 16, color: "var(--muted)" }}>One platform to</span>
          <span
            key={cycleIdx}
            className="word-cycle-enter"
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: 24,
              fontWeight: 700,
              color: CYCLE[cycleIdx].color,
              opacity: cycleVisible ? 1 : 0,
              transition: "opacity 0.28s ease",
              display: "inline-block",
              minWidth: 110,
              textAlign: "left",
            }}
          >
            {CYCLE[cycleIdx].word}
          </span>
        </div>

        {/* Search bar */}
        <form onSubmit={handleSearch} style={{ position: "relative", maxWidth: 640, margin: "0 auto 14px" }} className="animate-fade-up">
          <input
            className="search-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="e.g. women's land ownership after 2018…"
            style={{ paddingRight: 130, fontSize: 15 }}
          />
          <button
            type="submit"
            className="btn-primary"
            style={{ position: "absolute", right: 6, top: "50%", transform: "translateY(-50%)", padding: "9px 22px", fontSize: 14 }}
          >
            Search →
          </button>
        </form>

        <p style={{ fontSize: 12, color: "var(--muted-light)" }}>
          {stats
            ? `${stats.study_count.toLocaleString()} studies · ${stats.resource_count.toLocaleString()} resources · ${stats.active_domains} domains`
            : "Loading catalog…"}
        </p>
      </section>

      {/* ── Catalog stats row ──────────────────────────────────────────────── */}
      <section style={{ maxWidth: 960, margin: "0 auto", padding: "0 24px 56px" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: 16 }}>
          {[
            { label: "Studies in catalog",  value: stats?.study_count.toLocaleString()    ?? "—" },
            { label: "Total resources",      value: stats?.resource_count.toLocaleString() ?? "—" },
            { label: "Active domains",       value: stats?.active_domains                  ?? "—" },
            { label: "AI-powered search",    value: stats ? (stats.ai_available ? "Active ✓" : "Off") : "—" },
          ].map(({ label, value }) => (
            <div
              key={label}
              style={{
                background: "var(--warm-white)",
                border: "1px solid var(--border)",
                borderRadius: 12,
                padding: "20px 24px",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontFamily: "'Playfair Display', Georgia, serif",
                  fontSize: 32,
                  fontWeight: 700,
                  color: "var(--coral)",
                  lineHeight: 1,
                }}
              >
                {value}
              </div>
              <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 6 }}>{label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── NISR preview cards ────────────────────────────────────────────── */}
      <section style={{ maxWidth: 1200, margin: "0 auto", padding: "0 24px 64px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24, flexWrap: "wrap", gap: 12 }}>
          <div>
            <h2
              style={{
                fontFamily: "'Playfair Display', Georgia, serif",
                fontSize: 26,
                fontWeight: 700,
                color: "var(--charcoal)",
                marginBottom: 4,
              }}
            >
              Latest from the NISR catalog
            </h2>
            <p style={{ color: "var(--muted)", fontSize: 13 }}>
              Most recent studies across all active domains — authentic NISR microdata.
            </p>
          </div>
          <Link href="/discovery" className="btn-ghost" style={{ fontSize: 13, whiteSpace: "nowrap" }}>
            Browse all studies →
          </Link>
        </div>

        {loadingStudies ? (
          <div className="grid-3col">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="skeleton" style={{ height: 200, borderRadius: 12 }} />
            ))}
          </div>
        ) : (
          <div className="grid-3col">
            {featured.map(({ study, domainKey }) => (
              <HomeStudyCard
                key={`${domainKey}-${study.study_id}`}
                study={study}
                domainKey={domainKey}
                domains={domains}
              />
            ))}
          </div>
        )}
      </section>

      {/* ── Imigongo divider ─────────────────────────────────────────────── */}
      <ImigongoDivider />

      {/* ── Domain coverage ───────────────────────────────────────────────── */}
      <section style={{ maxWidth: 1200, margin: "0 auto", padding: "56px 24px" }}>
        <h2
          style={{
            fontFamily: "'Playfair Display', Georgia, serif",
            fontSize: 26,
            fontWeight: 700,
            color: "var(--charcoal)",
            marginBottom: 6,
          }}
        >
          Domain coverage
        </h2>
        <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 28 }}>
          Six validated gender data domains — each linked directly to the NISR microdata catalog.
        </p>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))",
            gap: 16,
          }}
        >
          {activeDomains.map(([key, d]) => (
            <Link key={key} href={`/discovery?domain=${key}`} style={{ textDecoration: "none" }}>
              <div
                className="study-card"
                style={{ padding: "22px 20px", cursor: "pointer", height: "100%" }}
              >
                <div style={{ fontSize: 30, marginBottom: 10 }}>{d.emoji}</div>
                <div style={{ fontWeight: 700, fontSize: 15, color: "var(--charcoal)", marginBottom: 4 }}>
                  {d.name}
                </div>
                <div style={{ color: "var(--muted)", fontSize: 12, marginBottom: 14 }}>
                  {d.study_count.toLocaleString()} studies
                </div>
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--muted)",
                    lineHeight: 1.5,
                    borderTop: "1px solid var(--border)",
                    paddingTop: 10,
                  }}
                >
                  {d.description.slice(0, 80)}{d.description.length > 80 ? "…" : ""}
                </div>
                <div
                  style={{
                    marginTop: 14,
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 5,
                    background: "var(--rw-green-light)",
                    color: "var(--rw-green)",
                    padding: "3px 10px",
                    borderRadius: 999,
                    fontSize: 11,
                    fontWeight: 600,
                  }}
                >
                  ● Active
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ── Imigongo divider ─────────────────────────────────────────────── */}
      <ImigongoDivider />

      {/* ── How it works ──────────────────────────────────────────────────── */}
      <section
        style={{
          background: "var(--warm-white)",
          borderTop: "1px solid var(--border)",
          borderBottom: "1px solid var(--border)",
          padding: "60px 24px",
        }}
      >
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <h2
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: 26,
              fontWeight: 700,
              color: "var(--charcoal)",
              textAlign: "center",
              marginBottom: 8,
            }}
          >
            How it works
          </h2>
          <p style={{ textAlign: "center", color: "var(--muted)", fontSize: 13, marginBottom: 48 }}>
            From question to advocacy-ready brief in under five minutes.
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 40 }}>
            <Step
              n="1" icon="🔍"
              title="Search"
              body="Type a plain-language question. AI interprets your intent and filters 2,740 NISR studies."
            />
            <Step
              n="2" icon="✦"
              title="Discover"
              body="Results ranked by relevance. Each shows a quality badge, abstract preview, and source link."
            />
            <Step
              n="3" icon="✅"
              title="Validate"
              body="Quality signals flag missing fields. The link checker verifies all source URLs are live."
            />
            <Step
              n="4" icon="📄"
              title="Act"
              body="Generate an AI-written advocacy brief with citations and recommendations — download as .txt."
            />
          </div>
        </div>
      </section>

      {/* ── Demo scenario ─────────────────────────────────────────────────── */}
      <section style={{ maxWidth: 960, margin: "0 auto", padding: "56px 24px 80px" }}>
        <div
          style={{
            background: "var(--warm-white)",
            border: "1px solid var(--border)",
            borderLeft: "4px solid var(--coral)",
            borderRadius: 12,
            padding: "36px 40px",
          }}
        >
          <p
            style={{
              fontSize: 11,
              fontWeight: 700,
              letterSpacing: "0.12em",
              color: "var(--coral)",
              textTransform: "uppercase",
              marginBottom: 10,
            }}
          >
            Try this demo scenario
          </p>
          <h3
            style={{
              fontFamily: "'Playfair Display', Georgia, serif",
              fontSize: 22,
              fontWeight: 700,
              color: "var(--charcoal)",
              marginBottom: 18,
              lineHeight: 1.3,
            }}
          >
            A CSO officer needs data on women&rsquo;s workforce participation — in 5 minutes
          </h3>
          <ol style={{ color: "var(--muted)", fontSize: 14, lineHeight: 2.1, paddingLeft: 20 }}>
            <li>Open <strong style={{ color: "var(--charcoal)" }}>Discovery</strong> → domain pre-set to Labour &amp; Employment</li>
            <li>Search: <em>&ldquo;women workforce participation Rwanda after 2019&rdquo;</em></li>
            <li>Review the Rwanda Labour Force Survey results — check quality badge and abstract</li>
            <li>Click <strong style={{ color: "var(--charcoal)" }}>Generate Brief</strong> → receive a structured advocacy brief in ~10 seconds</li>
            <li>Download as <code style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 13 }}>.txt</code> → paste directly into your funding proposal</li>
          </ol>
          <div style={{ marginTop: 28, display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Link
              href="/discovery?domain=labour&q=women+workforce+participation+Rwanda+after+2019"
              className="btn-primary"
              style={{ fontSize: 14, padding: "11px 26px" }}
            >
              Try it now →
            </Link>
            <Link href="/analytics" className="btn-ghost" style={{ fontSize: 14, padding: "11px 20px" }}>
              View analytics
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
