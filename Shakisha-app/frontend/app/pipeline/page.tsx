"use client";

import { useEffect, useState } from "react";
import { api, PipelineStatus, CrawlResult, CrawlStudy } from "../lib/api";

// ── Source definitions ─────────────────────────────────────────────────────────

const CRAWL_SOURCES = [
  {
    key: "all",
    label: "All Sources",
    description: "Search across NISR, World Bank, ILO, and OpenAlex simultaneously.",
    icon: "🌐",
  },
  {
    key: "nisr",
    label: "NISR",
    description: "National Institute of Statistics of Rwanda — authoritative national surveys.",
    icon: "🇷🇼",
  },
  {
    key: "openalex",
    label: "OpenAlex",
    description: "Open-access academic research papers on Rwanda gender topics.",
    icon: "📖",
  },
  {
    key: "worldbank",
    label: "World Bank",
    description: "World Bank Open Data — Rwanda gender indicators and reports.",
    icon: "🏦",
  },
  {
    key: "ilo",
    label: "ILO / ILOSTAT",
    description: "International Labour Organization — Rwanda labour & employment by sex.",
    icon: "⚖️",
  },
];

const SOURCE_ADAPTER_LABELS: Record<string, string> = {
  tavily_nisr:      "NISR",
  tavily_worldbank: "World Bank",
  tavily_ilo:       "ILO",
  tavily_openalex:  "OpenAlex",
  tavily:           "Web",
};

const YEAR_OPTIONS = [
  { value: 0,    label: "Any year" },
  { value: 2025, label: "Since 2025" },
  { value: 2024, label: "Since 2024" },
  { value: 2023, label: "Since 2023" },
  { value: 2022, label: "Since 2022" },
  { value: 2020, label: "Since 2020" },
];

// ── Sub-components ─────────────────────────────────────────────────────────────

function MetricCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 24px" }}>
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

function SourceAdapterBadge({ adapter }: { adapter: string }) {
  const label = SOURCE_ADAPTER_LABELS[adapter] ?? adapter;
  const colors: Record<string, { bg: string; color: string }> = {
    "NISR":       { bg: "var(--rw-green-light)", color: "var(--rw-green)" },
    "World Bank": { bg: "#E3F0FF",               color: "#1565C0" },
    "ILO":        { bg: "#FFF3E0",               color: "#E65100" },
    "OpenAlex":   { bg: "var(--rw-yellow-light)", color: "#92620A" },
    "Web":        { bg: "var(--cream-dark)",      color: "var(--muted)" },
  };
  const style = colors[label] ?? colors["Web"];
  return (
    <span style={{
      background: style.bg, color: style.color,
      fontSize: 10, fontWeight: 700, padding: "2px 8px",
      borderRadius: 999, whiteSpace: "nowrap",
    }}>
      {label}
    </span>
  );
}

function CrawlStudyRow({ s }: { s: CrawlStudy }) {
  return (
    <div style={{
      display: "flex", gap: 12, alignItems: "flex-start",
      padding: "12px 0", borderBottom: "1px solid var(--border)",
    }}>
      {/* New / duplicate tag */}
      <div style={{ paddingTop: 2, flexShrink: 0 }}>
        {s.is_new ? (
          <span style={{
            background: "var(--rw-green-light)", color: "var(--rw-green)",
            fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 999,
          }}>NEW</span>
        ) : (
          <span style={{
            background: "var(--cream-dark)", color: "var(--muted)",
            fontSize: 10, fontWeight: 600, padding: "3px 8px", borderRadius: 999,
          }}>KNOWN</span>
        )}
      </div>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 4 }}>
          <span style={{ fontWeight: 600, fontSize: 13, color: "var(--charcoal)" }}>
            {s.title.length > 100 ? s.title.slice(0, 100) + "…" : s.title}
          </span>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <SourceAdapterBadge adapter={s.source_adapter} />
          {s.year && (
            <span style={{ fontSize: 12, color: "var(--muted)" }}>{s.year}</span>
          )}
          {s.url && (
            <a
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ fontSize: 12, color: "var(--coral)", wordBreak: "break-all" }}
            >
              {s.url.replace(/^https?:\/\//, "").slice(0, 60)}{s.url.length > 60 ? "…" : ""}
            </a>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

export default function PipelinePage() {
  const [pipelineData, setPipelineData] = useState<PipelineStatus | null>(null);
  const [pipelineLoading, setPipelineLoading] = useState(true);
  const [pipelineError, setPipelineError]     = useState("");

  // Crawl state
  const [selectedSource, setSelectedSource] = useState("all");
  const [yearFrom, setYearFrom]             = useState(0);
  const [crawling, setCrawling]             = useState(false);
  const [crawlResult, setCrawlResult]       = useState<CrawlResult | null>(null);
  const [crawlError, setCrawlError]         = useState("");

  useEffect(() => {
    api.pipeline()
      .then(setPipelineData)
      .catch(() => setPipelineError("Unable to load pipeline information. Please check your connection and try again."))
      .finally(() => setPipelineLoading(false));
  }, []);

  async function handleCrawl() {
    setCrawling(true);
    setCrawlResult(null);
    setCrawlError("");
    try {
      const result = await api.crawl(selectedSource, yearFrom > 0 ? yearFrom : undefined);
      setCrawlResult(result);
      // Refresh pipeline stats to reflect new count
      api.pipeline().then(setPipelineData).catch(() => {});
    } catch (e: unknown) {
      setCrawlError(e instanceof Error ? e.message : "Something went wrong while searching for new data. Please try again or contact the Shakisha team.");
    } finally {
      setCrawling(false);
    }
  }

  const selectedSourceDef = CRAWL_SOURCES.find((s) => s.key === selectedSource)!;

  return (
    <div style={{ background: "var(--cream)", minHeight: "100vh" }}>
      <div className="page-wrap">

        {/* ── Header ── */}
        <h1 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 32, fontWeight: 700, color: "var(--charcoal)", marginBottom: 8 }}>
          Data Pipeline
        </h1>
        <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 28, maxWidth: 700, lineHeight: 1.7 }}>
          Shakisha ships with the NISR microdata catalog as the authoritative base. The pipeline
          layer ingests OpenAlex, World Bank, and ILO on demand — keeping the catalog current
          without manual data entry. CSOs can grow the dataset themselves by running an on-demand
          crawl whenever they need the latest evidence.
        </p>

        {/* ── Metrics ── */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 36 }}>
          <MetricCard label="Total studies"   value={pipelineLoading ? "—" : (pipelineData?.total_studies   ?? 0).toLocaleString()} />
          <MetricCard label="Total resources" value={pipelineLoading ? "—" : (pipelineData?.total_resources ?? 0).toLocaleString()} />
          <MetricCard label="Active sources"  value={pipelineLoading ? "—" : (pipelineData?.active_sources  ?? 0)} />
          <MetricCard
            label="Added today"
            value={pipelineLoading ? "—" : (crawlResult?.new_count ?? pipelineData?.new_today ?? 0)}
            sub="via on-demand crawl"
          />
        </div>

        {/* ── On-demand crawl panel ── */}
        <div style={{
          background: "var(--warm-white)",
          border: "1px solid var(--border)",
          borderLeft: "4px solid var(--coral)",
          borderRadius: 12,
          padding: "clamp(16px, 3vw, 28px) clamp(16px, 3vw, 32px)",
          marginBottom: 32,
        }}>
          <h2 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 22, fontWeight: 700, color: "var(--charcoal)", marginBottom: 6 }}>
            Discover New Data
          </h2>
          <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 24, lineHeight: 1.6, maxWidth: 620 }}>
            Select a source and click <strong>Discover</strong>. Shakisha searches trusted databases
            for Rwanda gender data not yet in the catalog, validates every result, and adds new
            studies instantly — available to all CSOs immediately after the crawl.
          </p>

          {/* Source chips */}
          <div style={{ marginBottom: 20 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 10 }}>
              Source
            </div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {CRAWL_SOURCES.map((src) => (
                <button
                  key={src.key}
                  onClick={() => setSelectedSource(src.key)}
                  style={{
                    padding: "8px 16px",
                    borderRadius: 999,
                    fontSize: 13,
                    fontWeight: 600,
                    border: selectedSource === src.key ? "2px solid var(--coral)" : "2px solid var(--border)",
                    background: selectedSource === src.key ? "rgba(192,79,79,0.08)" : "var(--cream)",
                    color: selectedSource === src.key ? "var(--coral)" : "var(--charcoal)",
                    cursor: "pointer",
                    transition: "all 0.15s",
                  }}
                >
                  {src.icon} {src.label}
                </button>
              ))}
            </div>
            <p style={{ color: "var(--muted)", fontSize: 12, marginTop: 8, lineHeight: 1.5 }}>
              {selectedSourceDef.description}
            </p>
          </div>

          {/* Year filter */}
          <div style={{ marginBottom: 24 }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 8 }}>
              Time range
            </div>
            <select
              value={yearFrom}
              onChange={(e) => setYearFrom(Number(e.target.value))}
              style={{
                padding: "8px 14px",
                borderRadius: 8,
                border: "1.5px solid var(--border)",
                background: "var(--cream)",
                fontSize: 13,
                color: "var(--charcoal)",
                cursor: "pointer",
              }}
            >
              {YEAR_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>

          {/* Crawl button */}
          <button
            className="btn-primary"
            style={{ fontSize: 15, padding: "13px 32px", opacity: crawling ? 0.7 : 1 }}
            disabled={crawling}
            onClick={handleCrawl}
          >
            {crawling
              ? `Searching ${selectedSourceDef.icon} ${selectedSourceDef.label}…`
              : `Discover New Data from ${selectedSourceDef.icon} ${selectedSourceDef.label}`}
          </button>
          {crawling && (
            <p style={{ color: "var(--muted)", fontSize: 13, marginTop: 10 }}>
              Querying Tavily — searching trusted sources for Rwanda gender data…
            </p>
          )}

          {/* Error */}
          {crawlError && (
            <div style={{ marginTop: 16, background: "#FCE8E8", border: "1px solid #E8A0A0", borderRadius: 8, padding: "12px 16px", fontSize: 13, color: "var(--coral-dark)" }}>
              {crawlError}
            </div>
          )}

          {/* Results */}
          {crawlResult && (
            <div style={{ marginTop: 24 }}>
              {/* Summary bar */}
              <div style={{
                display: "flex", gap: 20, flexWrap: "wrap", alignItems: "center",
                background: crawlResult.new_count > 0 ? "var(--rw-green-light)" : "var(--cream-dark)",
                border: `1px solid ${crawlResult.new_count > 0 ? "var(--rw-green-light)" : "var(--border)"}`,
                borderRadius: 10, padding: "14px 20px", marginBottom: 16,
              }}>
                <span style={{ fontWeight: 700, fontSize: 15, color: crawlResult.new_count > 0 ? "var(--rw-green)" : "var(--muted)" }}>
                  {crawlResult.new_count > 0
                    ? `${crawlResult.new_count} new stud${crawlResult.new_count === 1 ? "y" : "ies"} added to catalog`
                    : "No new studies found — catalog is up to date"}
                </span>
                <span style={{ fontSize: 13, color: "var(--muted)" }}>
                  {crawlResult.total_found} found · {crawlResult.duplicate_count} already in catalog
                </span>
                <span style={{ fontSize: 13, color: "var(--muted)", marginLeft: "auto" }}>
                  Catalog now has {crawlResult.catalog_total.toLocaleString()} studies
                </span>
              </div>

              {/* Study list */}
              {crawlResult.studies.length > 0 ? (
                <div style={{ background: "var(--cream)", border: "1px solid var(--border)", borderRadius: 10, padding: "8px 20px" }}>
                  {crawlResult.studies.map((s) => (
                    <CrawlStudyRow key={s.study_id} s={s} />
                  ))}
                </div>
              ) : (
                <p style={{ color: "var(--muted)", fontSize: 13, fontStyle: "italic" }}>
                  No results matched Rwanda gender relevance criteria for the selected source and time range.
                </p>
              )}

              {crawlResult.new_count > 0 && (
                <p style={{ color: "var(--muted)", fontSize: 12, marginTop: 12, lineHeight: 1.5 }}>
                  New studies are now live in the catalog. Use the Discovery page to find and explore them.
                </p>
              )}
            </div>
          )}
        </div>

        {/* ── How it works ── */}
        <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "clamp(16px, 3vw, 24px) clamp(16px, 3vw, 32px)", marginBottom: 32 }}>
          <h2 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 18, fontWeight: 700, color: "var(--charcoal)", marginBottom: 12 }}>
            How on-demand crawling works
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 20 }}>
            {[
              { step: "1", title: "Select & run", body: "Choose a source and click Discover. Shakisha queries Tavily's real-time web index targeting only trusted Rwanda gender data domains." },
              { step: "2", title: "Filter & validate", body: "Every result is checked for Rwanda relevance and gender focus. Off-topic results (other countries, unrelated topics) are discarded automatically." },
              { step: "3", title: "Deduplicate", body: "Studies already in the catalog are identified and skipped. Only genuinely new resources are added, keeping the catalog clean." },
              { step: "4", title: "Instant availability", body: "New studies appear in the catalog immediately. Every CSO using Shakisha benefits from the crawl without needing to repeat it." },
            ].map(({ step, title, body }) => (
              <div key={step}>
                <div style={{ width: 28, height: 28, borderRadius: "50%", background: "var(--coral)", color: "white", fontSize: 13, fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 10 }}>
                  {step}
                </div>
                <div style={{ fontWeight: 700, fontSize: 13, color: "var(--charcoal)", marginBottom: 4 }}>{title}</div>
                <div style={{ fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>{body}</div>
              </div>
            ))}
          </div>
        </div>

        {/* ── Data sources ── */}
        <h2 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 22, fontWeight: 700, color: "var(--charcoal)", marginBottom: 16 }}>
          Data sources
        </h2>

        {pipelineError && (
          <div style={{ background: "#FCE8E8", border: "1px solid #E8A0A0", borderRadius: 8, padding: "12px 16px", color: "var(--coral-dark)", fontSize: 13, marginBottom: 16 }}>
            {pipelineError}
          </div>
        )}

        {pipelineLoading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 36 }}>
            {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 110, borderRadius: 12 }} />)}
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 36 }}>
            {(pipelineData?.sources ?? []).map((src) => (
              <div
                key={src.key}
                style={{
                  background: "var(--warm-white)",
                  border: "1px solid var(--border)",
                  borderLeft: src.active ? "4px solid var(--rw-green)" : "4px solid var(--border)",
                  borderRadius: 12,
                  padding: "20px 24px",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  gap: 20,
                  flexWrap: "wrap",
                }}
              >
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6, flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 700, fontSize: 15, color: "var(--charcoal)" }}>{src.name}</span>
                    <span style={{
                      fontSize: 11, fontWeight: 600, padding: "2px 10px", borderRadius: 999,
                      background: src.active ? "var(--rw-green-light)" : "var(--cream-dark)",
                      color: src.active ? "var(--rw-green)" : "var(--muted)",
                    }}>
                      {src.badge}
                    </span>
                  </div>
                  <p style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.6, margin: 0 }}>
                    {src.description}
                  </p>
                </div>
                <div style={{ textAlign: "right", minWidth: 110, flexShrink: 0 }}>
                  {src.active ? (
                    <>
                      <div style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 26, fontWeight: 700, color: "var(--coral)", lineHeight: 1 }}>
                        {src.study_count.toLocaleString()}
                      </div>
                      <div style={{ color: "var(--muted)", fontSize: 11, marginTop: 2 }}>studies</div>
                      {src.resource_count !== null && src.resource_count > 0 && (
                        <div style={{ color: "var(--muted)", fontSize: 11, marginTop: 2 }}>{src.resource_count.toLocaleString()} resources</div>
                      )}
                      <div style={{ color: "var(--muted)", fontSize: 11, marginTop: 4 }}>Last run: {src.last_ingested}</div>
                    </>
                  ) : (
                    <div style={{ color: "var(--muted)", fontSize: 13, fontStyle: "italic" }}>
                      Run a crawl to populate
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* ── Recently added ── */}
        <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px" }}>
          <h2 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 20, fontWeight: 700, color: "var(--charcoal)", marginBottom: 16 }}>
            Recently added studies
          </h2>
          {pipelineLoading ? (
            <div className="skeleton" style={{ height: 120, borderRadius: 8 }} />
          ) : !pipelineData?.recently_added.length ? (
            <p style={{ color: "var(--muted)", fontSize: 13, fontStyle: "italic" }}>
              No pipeline-ingested studies yet. Run an on-demand crawl above to populate this section.
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
              {pipelineData.recently_added.map((study) => (
                <div
                  key={study.study_id}
                  style={{
                    display: "flex", justifyContent: "space-between", alignItems: "flex-start",
                    gap: 16, paddingBottom: 12, paddingTop: 12,
                    borderBottom: "1px solid var(--border)",
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14, color: "var(--charcoal)", marginBottom: 3 }}>
                      {study.title}
                    </div>
                    <div style={{ color: "var(--muted)", fontSize: 12, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                      {[study.organization, study.year].filter((v) => v && v !== "—").join(" · ")}
                      <SourceAdapterBadge adapter={study.source_adapter} />
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
