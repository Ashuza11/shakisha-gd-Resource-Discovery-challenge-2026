"use client";

import { useEffect, useRef, useState, useCallback, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api, Study, DomainConfig, QualityLevel } from "../lib/api";

// ── Constants ──────────────────────────────────────────────────────────────

const QUALITY_BADGE: Record<QualityLevel, { label: string; cls: string; stripe: string }> = {
  good:     { label: "Good quality",     cls: "badge-good",     stripe: "card-stripe-good" },
  warning:  { label: "Missing fields",   cls: "badge-warning",  stripe: "card-stripe-warning" },
  critical: { label: "Missing fields",   cls: "badge-critical", stripe: "card-stripe-critical" },
};

const SORT_OPTIONS = ["Newest first", "Oldest first", "By quality"];
const QUALITY_OPTIONS = ["all", "good", "warning", "critical"];
const PAGE_SIZE = 15;

// ── Sub-components ─────────────────────────────────────────────────────────

function Skeleton() {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="skeleton"
          style={{ height: 140, borderRadius: 12 }}
        />
      ))}
    </div>
  );
}

function StudyCard({
  study,
  query,
  onBrief,
}: {
  study: Study;
  query: string;
  onBrief: (id: string) => void;
}) {
  const badge = QUALITY_BADGE[study.quality_level] ?? QUALITY_BADGE.warning;
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loadingExplain, setLoadingExplain] = useState(false);
  const [showAbstract, setShowAbstract] = useState(false);
  const [showCitation, setShowCitation] = useState(false);

  async function handleExplain() {
    if (explanation) return;
    setLoadingExplain(true);
    try {
      const r = await api.explain(study.study_id, query);
      setExplanation(r.explanation);
    } catch {
      setExplanation("AI explanation unavailable.");
    } finally {
      setLoadingExplain(false);
    }
  }

  const citation = `${study.organization || "NISR"}. (${study.year || "n.d."}). ${study.title}. Retrieved from ${study.url || "https://microdata.statistics.gov.rw"}`;

  return (
    <div className={`study-card ${badge.stripe}`} style={{ padding: "20px 24px" }}>
      {/* Header row */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 8 }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)", marginBottom: 4, lineHeight: 1.4 }}>
            {study.title}
          </div>
          <div style={{ color: "var(--muted)", fontSize: 13 }}>
            {[study.organization, study.year, study.geographic_coverage].filter(Boolean).join(" · ")}
            {" · "}
            {study.resource_count} resource{study.resource_count !== 1 ? "s" : ""}
          </div>
        </div>
        <span className={`pill ${badge.cls}`} style={{ whiteSpace: "nowrap" }}>
          {badge.label}
        </span>
      </div>

      {/* Quality flags */}
      {study.quality_flags.length > 0 && (
        <div style={{ marginBottom: 10, display: "flex", gap: 6, flexWrap: "wrap" }}>
          {study.quality_flags.map((f, i) => (
            <span key={i} style={{ fontSize: 11, color: "var(--coral)", background: "#FCE8E8", padding: "2px 8px", borderRadius: 4 }}>
              {f}
            </span>
          ))}
        </div>
      )}

      {/* District tag */}
      {(study.geographic_unit?.toLowerCase().includes("district") ||
        study.geographic_coverage?.toLowerCase().includes("district")) && (
        <span className="pill pill-district" style={{ marginBottom: 10, display: "inline-flex" }}>
          📍 District-level estimates available
        </span>
      )}

      {/* Abstract */}
      {study.abstract && (
        <div style={{ marginBottom: 12 }}>
          <button className="btn-ghost" style={{ fontSize: 12, padding: "3px 10px" }} onClick={() => setShowAbstract(!showAbstract)}>
            {showAbstract ? "▲ Hide abstract" : "▼ Show abstract"}
          </button>
          {showAbstract && (
            <p style={{ color: "var(--muted)", fontSize: 13, marginTop: 8, lineHeight: 1.6 }}>
              {study.abstract.slice(0, 400)}{study.abstract.length > 400 ? "…" : ""}
            </p>
          )}
        </div>
      )}

      {/* AI explanation */}
      {query && (
        <div style={{ marginBottom: 12 }}>
          {!explanation ? (
            <button
              className="btn-ghost"
              style={{ fontSize: 12, padding: "3px 10px" }}
              onClick={handleExplain}
              disabled={loadingExplain}
            >
              {loadingExplain ? "Thinking…" : "✦ Why is this relevant?"}
            </button>
          ) : (
            <div
              style={{
                background: "rgba(192,79,79,0.06)",
                border: "1px solid rgba(192,79,79,0.15)",
                borderRadius: 8,
                padding: "10px 14px",
                fontSize: 13,
                color: "var(--charcoal)",
                lineHeight: 1.6,
              }}
            >
              <span style={{ fontWeight: 600, color: "var(--coral)" }}>✦ </span>
              {explanation}
            </div>
          )}
        </div>
      )}

      {/* Action row */}
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 }}>
        {study.url && (
          <a href={study.url} target="_blank" rel="noopener noreferrer" className="btn-icon">
            View source ↗
          </a>
        )}
        {study.get_microdata_url && (
          <a href={study.get_microdata_url} target="_blank" rel="noopener noreferrer" className="btn-icon">
            Get microdata ↗
          </a>
        )}
        <button className="btn-ghost" style={{ fontSize: 12 }} onClick={() => setShowCitation(!showCitation)}>
          {showCitation ? "Hide citation" : "Citation"}
        </button>
        <button className="btn-primary" style={{ marginLeft: "auto" }} onClick={() => onBrief(study.study_id)}>
          Generate brief →
        </button>
      </div>

      {showCitation && (
        <div className="citation-block" style={{ marginTop: 12 }}>
          {citation}
        </div>
      )}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────

function DiscoveryContent() {
  const router = useRouter();
  const params = useSearchParams();

  const initialDomain = params.get("domain") ?? "labour";
  const initialQuery  = params.get("q") ?? "";

  const [domains, setDomains]         = useState<Record<string, DomainConfig>>({});
  const [orgs, setOrgs]               = useState<string[]>([]);
  const [districts, setDistricts]     = useState<string[]>([]);
  const [resourceTypes, setResourceTypes] = useState<string[]>([]);
  const [selectedDomain, setSelectedDomain] = useState(initialDomain);
  const [query, setQuery]             = useState(initialQuery);
  const [inputValue, setInputValue]   = useState(initialQuery);
  const [org, setOrg]                 = useState("");
  const [district, setDistrict]       = useState("");
  const [resourceType, setResourceType] = useState("all");
  const [yearMin, setYearMin]         = useState<string>("");
  const [yearMax, setYearMax]         = useState<string>("");
  const [qualityFilter, setQuality]   = useState("all");
  const [sortOrder, setSort]          = useState("Newest first");
  const [results, setResults]         = useState<Study[]>([]);
  const [totalInDomain, setTotalInDomain] = useState(0);
  const [aiExplanation, setAiExplanation] = useState("");
  const [loading, setLoading]         = useState(false);
  const [page, setPage]               = useState(1);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const searchTimeout                 = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    api.domains().then(setDomains).catch(() => {});
    api.organizations().then(setOrgs).catch(() => {});
    api.districts().then(setDistricts).catch(() => {});
    api.resourceTypes().then(setResourceTypes).catch(() => {});
  }, []);

  const doSearch = useCallback(async (
    domain: string, q: string, o: string, qf: string, so: string,
    dist: string, rt: string, yMin: string, yMax: string
  ) => {
    setLoading(true);
    setPage(1);
    try {
      const r = await api.search({
        query: q,
        domain,
        organization: o,
        quality_filter: qf,
        sort_order: so,
        district: dist,
        resource_type: rt,
        year_min: yMin ? parseInt(yMin) : null,
        year_max: yMax ? parseInt(yMax) : null,
        use_ai: true,
      });
      setResults(r.results);
      setTotalInDomain(r.total_in_domain);
      setAiExplanation(r.ai_explanation);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, []);

  // Trigger search when domain/filters change
  useEffect(() => {
    doSearch(selectedDomain, query, org, qualityFilter, sortOrder, district, resourceType, yearMin, yearMax);
  }, [selectedDomain, org, qualityFilter, sortOrder, district, resourceType, yearMin, yearMax, doSearch]);

  // Debounce free-text query
  useEffect(() => {
    if (searchTimeout.current !== null) clearTimeout(searchTimeout.current);
    searchTimeout.current = setTimeout(() => {
      setQuery(inputValue);
      doSearch(selectedDomain, inputValue, org, qualityFilter, sortOrder, district, resourceType, yearMin, yearMax);
    }, 600);
    return () => { if (searchTimeout.current !== null) clearTimeout(searchTimeout.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [inputValue]);

  function handleBrief(study_id: string) {
    router.push(`/brief?study=${study_id}`);
  }

  const activeDomains = Object.entries(domains).filter(([, d]) => d.status === "active");
  const visible = results.slice(0, page * PAGE_SIZE);
  const domainCfg = domains[selectedDomain];

  return (
    <div style={{ background: "var(--cream)", minHeight: "100vh" }}>
      <div className="page-wrap">

        {/* ── Domain chips ── */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 24 }}>
          {activeDomains.map(([key, d]) => (
            <button
              key={key}
              className={`domain-chip ${selectedDomain === key ? "domain-chip-active" : "domain-chip-inactive"}`}
              onClick={() => { setSelectedDomain(key); setPage(1); }}
            >
              <span>{d.emoji}</span>
              <span>{d.name}</span>
            </button>
          ))}
        </div>

        {/* ── Advocacy context ── */}
        {domainCfg && (
          <div
            style={{
              background: "rgba(32,96,61,0.07)",
              border: "1px solid var(--rw-green-light)",
              borderRadius: 8,
              padding: "10px 16px",
              fontSize: 13,
              color: "var(--rw-green)",
              marginBottom: 20,
            }}
          >
            <strong>Advocacy focus:</strong> {domainCfg.advocacy_context}
          </div>
        )}

        {/* ── Search bar ── */}
        <div style={{ position: "relative", marginBottom: 16 }}>
          <input
            className="search-input"
            placeholder="e.g. women's workforce participation after 2019…"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { if (searchTimeout.current !== null) clearTimeout(searchTimeout.current); setQuery(inputValue); doSearch(selectedDomain, inputValue, org, qualityFilter, sortOrder); } }}
          />
          {loading && (
            <span style={{ position: "absolute", right: 16, top: "50%", transform: "translateY(-50%)", color: "var(--muted)", fontSize: 13 }}>
              Searching…
            </span>
          )}
        </div>

        {/* ── Filter row ── */}
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 12, alignItems: "center" }}>
          <select
            value={org}
            onChange={(e) => setOrg(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--warm-white)", fontSize: 13, color: "var(--charcoal)" }}
          >
            <option value="">All organizations</option>
            {orgs.map((o) => <option key={o} value={o}>{o.length > 50 ? o.slice(0, 50) + "…" : o}</option>)}
          </select>

          <select
            value={qualityFilter}
            onChange={(e) => setQuality(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--warm-white)", fontSize: 13, color: "var(--charcoal)" }}
          >
            {QUALITY_OPTIONS.map((q) => (
              <option key={q} value={q}>
                {q === "all" ? "All quality levels" : q.charAt(0).toUpperCase() + q.slice(1)}
              </option>
            ))}
          </select>

          <select
            value={sortOrder}
            onChange={(e) => setSort(e.target.value)}
            style={{ padding: "8px 12px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--warm-white)", fontSize: 13, color: "var(--charcoal)" }}
          >
            {SORT_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
          </select>

          <button
            className="btn-ghost"
            style={{ fontSize: 12 }}
            onClick={() => setShowAdvanced((v) => !v)}
          >
            {showAdvanced ? "▲ Less filters" : "▼ More filters"}
          </button>

          {(inputValue || org || qualityFilter !== "all" || district || resourceType !== "all" || yearMin || yearMax) && (
            <button
              className="btn-ghost"
              style={{ fontSize: 12, color: "var(--coral)" }}
              onClick={() => {
                setInputValue(""); setQuery(""); setOrg(""); setQuality("all");
                setDistrict(""); setResourceType("all"); setYearMin(""); setYearMax("");
              }}
            >
              ✕ Clear all
            </button>
          )}
        </div>

        {/* ── Advanced filters ── */}
        {showAdvanced && (
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap", marginBottom: 16, padding: "14px 16px", background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 10, alignItems: "center" }}>
            <select
              value={district}
              onChange={(e) => setDistrict(e.target.value === "All Rwanda" ? "" : e.target.value)}
              style={{ padding: "7px 12px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--cream)", fontSize: 13, color: "var(--charcoal)" }}
            >
              {districts.map((d) => <option key={d} value={d === "All Rwanda" ? "" : d}>{d}</option>)}
            </select>

            <select
              value={resourceType}
              onChange={(e) => setResourceType(e.target.value)}
              style={{ padding: "7px 12px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--cream)", fontSize: 13, color: "var(--charcoal)" }}
            >
              <option value="all">All resource types</option>
              {resourceTypes.map((t) => <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>)}
            </select>

            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ fontSize: 12, color: "var(--muted)", whiteSpace: "nowrap" }}>Year:</span>
              <input
                type="number"
                placeholder="From"
                value={yearMin}
                onChange={(e) => setYearMin(e.target.value)}
                style={{ width: 80, padding: "7px 10px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--cream)", fontSize: 13, color: "var(--charcoal)" }}
              />
              <span style={{ fontSize: 12, color: "var(--muted)" }}>–</span>
              <input
                type="number"
                placeholder="To"
                value={yearMax}
                onChange={(e) => setYearMax(e.target.value)}
                style={{ width: 80, padding: "7px 10px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--cream)", fontSize: 13, color: "var(--charcoal)" }}
              />
            </div>
          </div>
        )}

        <div style={{ marginBottom: 24 }} />

        {/* ── AI explanation banner ── */}
        {aiExplanation && !loading && (
          <div
            style={{
              background: "rgba(192,79,79,0.06)",
              border: "1px solid rgba(192,79,79,0.2)",
              borderRadius: 8,
              padding: "10px 16px",
              fontSize: 13,
              color: "var(--charcoal)",
              marginBottom: 16,
            }}
          >
            <strong style={{ color: "var(--coral)" }}>✦ Search intent:</strong> {aiExplanation}
          </div>
        )}

        {/* ── Results header ── */}
        <div style={{ marginBottom: 16, color: "var(--muted)", fontSize: 14 }}>
          {loading ? (
            "Searching…"
          ) : (
            <>
              <strong style={{ color: "var(--charcoal)" }}>{results.length}</strong> of{" "}
              <strong style={{ color: "var(--charcoal)" }}>{totalInDomain}</strong> studies in{" "}
              {domainCfg ? `${domainCfg.emoji} ${domainCfg.name}` : selectedDomain}
            </>
          )}
        </div>

        {/* ── Study cards ── */}
        {loading ? (
          <Skeleton />
        ) : results.length === 0 ? (
          <div
            style={{
              textAlign: "center",
              padding: "64px 24px",
              color: "var(--muted)",
            }}
          >
            <div style={{ fontSize: 36, marginBottom: 16 }}>🔍</div>
            <div style={{ fontWeight: 600, fontSize: 18, marginBottom: 8 }}>No results found</div>
            <div style={{ fontSize: 14 }}>Try different keywords or broaden your filters.</div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {visible.map((study) => (
              <StudyCard
                key={study.study_id}
                study={study}
                query={query}
                onBrief={handleBrief}
              />
            ))}

            {/* Load more */}
            {visible.length < results.length && (
              <div style={{ textAlign: "center", paddingTop: 8 }}>
                <button
                  className="btn-ghost"
                  style={{ fontSize: 14, padding: "10px 28px" }}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Show more ({results.length - visible.length} remaining)
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default function DiscoveryPage() {
  return (
    <Suspense fallback={<div style={{ padding: 48, color: "var(--muted)" }}>Loading…</div>}>
      <DiscoveryContent />
    </Suspense>
  );
}
