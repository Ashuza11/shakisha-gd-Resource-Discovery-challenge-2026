"use client";

import { useEffect, useState } from "react";
import { api, PipelineStatus, PipelineSource } from "../lib/api";

const BADGE_STYLE: Record<string, { bg: string; color: string; icon: string }> = {
  active:   { bg: "var(--rw-green-light)", color: "var(--rw-green)",  icon: "●" },
  crawler:  { bg: "#E8F4FD",               color: "#1565C0",           icon: "↻" },
  academic: { bg: "var(--rw-yellow-light)", color: "#92620A",          icon: "📖" },
  planned:  { bg: "var(--cream-dark)",      color: "var(--muted)",     icon: "○" },
};

function MetricCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div
      style={{
        background: "var(--warm-white)",
        border: "1px solid var(--border)",
        borderRadius: 12,
        padding: "20px 24px",
      }}
    >
      <div style={{ color: "var(--muted)", fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 32, fontWeight: 700, color: "var(--charcoal)", lineHeight: 1 }}>
        {value}
      </div>
      {sub && <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 4 }}>{sub}</div>}
    </div>
  );
}

function SourceCard({ src }: { src: PipelineSource }) {
  const [showCmd, setShowCmd] = useState(false);
  const badge = BADGE_STYLE[src.badge_type] ?? BADGE_STYLE.planned;

  return (
    <div
      style={{
        background: "var(--warm-white)",
        border: "1px solid var(--border)",
        borderLeft: src.active ? "4px solid var(--rw-green)" : "4px solid var(--border)",
        borderRadius: 12,
        padding: "20px 24px",
      }}
    >
      <div className="source-header-row">
        <div style={{ flex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
            <span style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)" }}>
              {src.name}
            </span>
            <span
              style={{
                background: badge.bg,
                color: badge.color,
                fontSize: 11,
                fontWeight: 600,
                padding: "2px 10px",
                borderRadius: 999,
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              {badge.icon} {src.badge}
            </span>
          </div>
          <p style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.6, margin: 0 }}>
            {src.description}
          </p>
        </div>

        {/* Stats column */}
        <div style={{ textAlign: "right", minWidth: 120, flexShrink: 0 }}>
          {src.active ? (
            <>
              <div style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 26, fontWeight: 700, color: "var(--coral)", lineHeight: 1 }}>
                {src.study_count.toLocaleString()}
              </div>
              <div style={{ color: "var(--muted)", fontSize: 11, marginTop: 2 }}>studies</div>
              {src.resource_count !== null && src.resource_count > 0 && (
                <div style={{ color: "var(--muted)", fontSize: 11, marginTop: 2 }}>
                  {src.resource_count.toLocaleString()} resources
                </div>
              )}
              <div style={{ color: "var(--muted)", fontSize: 11, marginTop: 4 }}>
                Last run: {src.last_ingested}
              </div>
            </>
          ) : (
            <div style={{ color: "var(--muted)", fontSize: 13, fontStyle: "italic" }}>
              Not yet run
            </div>
          )}
        </div>
      </div>

      {/* Run command */}
      {src.run_cmd && (
        <div style={{ marginTop: 10 }}>
          <button
            className="btn-ghost"
            style={{ fontSize: 12, padding: "3px 10px" }}
            onClick={() => setShowCmd(!showCmd)}
          >
            {showCmd ? "▲ Hide command" : "▼ Show run command"}
          </button>
          {showCmd && (
            <pre
              style={{
                marginTop: 8,
                background: "var(--cream-dark)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                padding: "10px 14px",
                fontSize: 13,
                fontFamily: "'JetBrains Mono', monospace",
                color: "var(--charcoal)",
                overflowX: "auto",
              }}
            >
              {src.run_cmd}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}

export default function PipelinePage() {
  const [data, setData]     = useState<PipelineStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]   = useState("");

  useEffect(() => {
    api.pipeline()
      .then(setData)
      .catch(() => setError("Could not load pipeline status. Is the FastAPI server running?"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div style={{ background: "var(--cream)", minHeight: "100vh" }}>
      <div className="page-wrap">
        <h1 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 32, fontWeight: 700, color: "var(--charcoal)", marginBottom: 8 }}>
          Data Pipeline
        </h1>
        <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 28, maxWidth: 680 }}>
          Shakisha ships with the NISR microdata catalog as the authoritative base. The pipeline
          layer ingests OpenAlex, World Bank, and ILO on demand — keeping the catalog current
          without manual data entry.
        </p>

        {error && (
          <div style={{ background: "#FCE8E8", border: "1px solid #E8A0A0", borderRadius: 8, padding: "12px 16px", color: "var(--coral-dark)", fontSize: 13, marginBottom: 24 }}>
            {error}
          </div>
        )}

        {/* Top metrics */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 32 }}>
          <MetricCard label="Total studies" value={loading ? "—" : (data?.total_studies ?? 0).toLocaleString()} />
          <MetricCard label="Total resources" value={loading ? "—" : (data?.total_resources ?? 0).toLocaleString()} />
          <MetricCard label="Active sources" value={loading ? "—" : (data?.active_sources ?? 0)} />
          <MetricCard label="Added today" value={loading ? "—" : (data?.new_today ?? 0)} sub="pipeline-ingested" />
        </div>

        {/* Source cards */}
        <h2 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 22, fontWeight: 700, color: "var(--charcoal)", marginBottom: 16 }}>
          Data sources
        </h2>
        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {[1, 2, 3].map((i) => (
              <div key={i} className="skeleton" style={{ height: 120, borderRadius: 12 }} />
            ))}
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 36 }}>
            {(data?.sources ?? []).map((src) => (
              <SourceCard key={src.key} src={src} />
            ))}
          </div>
        )}

        {/* How to refresh */}
        <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px", marginBottom: 28 }}>
          <h2 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 20, fontWeight: 700, color: "var(--charcoal)", marginBottom: 12 }}>
            How to refresh the catalog
          </h2>
          <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 16, lineHeight: 1.6 }}>
            Run the adapters for whichever sources have new data, then merge into the live catalog.
            The NISR crawler automatically skips studies already in the catalog.
          </p>
          <pre
            style={{
              background: "var(--cream-dark)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "16px 20px",
              fontSize: 13,
              fontFamily: "'JetBrains Mono', monospace",
              color: "var(--charcoal)",
              lineHeight: 1.8,
              overflowX: "auto",
            }}
          >
{`# 1. Crawl new NISR studies (skips existing ones automatically)
python data_pipeline/nisr_crawler.py

# 2. Fetch latest OpenAlex research papers
python data_pipeline/openalex_adapter.py

# 3. Merge all sources into the live catalog
python data_pipeline/build_dataset.py

# Restart the FastAPI server to reflect updated catalog
uvicorn api.main:app --reload --port 8000`}
          </pre>
        </div>

        {/* Recently added */}
        <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px" }}>
          <h2 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 20, fontWeight: 700, color: "var(--charcoal)", marginBottom: 16 }}>
            Recently added studies
          </h2>
          {loading ? (
            <div className="skeleton" style={{ height: 120, borderRadius: 8 }} />
          ) : !data?.recently_added.length ? (
            <p style={{ color: "var(--muted)", fontSize: 13, fontStyle: "italic" }}>
              No pipeline-ingested studies yet — base NISR catalog studies predate the ingested_at column.
              Run an adapter above to populate this section.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {data.recently_added.map((study) => (
                <div
                  key={study.study_id}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    gap: 16,
                    paddingBottom: 12,
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "var(--charcoal)", marginBottom: 3 }}>
                      {study.title}
                    </div>
                    <div style={{ color: "var(--muted)", fontSize: 12 }}>
                      {[study.organization, study.year].filter((v) => v && v !== "—").join(" · ")}
                      {" · "}
                      Source: <code style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 11 }}>{study.source_adapter}</code>
                    </div>
                  </div>
                  <div style={{ color: "var(--muted)", fontSize: 12, whiteSpace: "nowrap", flexShrink: 0 }}>
                    Added {study.ingested_at.slice(0, 10)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
