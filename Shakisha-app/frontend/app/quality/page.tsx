"use client";

import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { api, QualityItem, QualityLevel, LinkCheckResult, DomainConfig } from "../lib/api";

const BADGE_STYLE: Record<QualityLevel, { cls: string; label: string }> = {
  good:     { cls: "badge-good",     label: "Good" },
  warning:  { cls: "badge-warning",  label: "Warning" },
  critical: { cls: "badge-critical", label: "Critical" },
};

const QUALITY_COLORS: Record<QualityLevel, string> = {
  good:     "#20603D",
  warning:  "#E8B800",
  critical: "#C04F4F",
};

export default function QualityPage() {
  const [domains,      setDomains]    = useState<Record<string, DomainConfig>>({});
  const [activeDomain, setActiveDomain] = useState("all");
  const [items, setItems]             = useState<QualityItem[]>([]);
  const [updatedAt, setUpdatedAt]     = useState("");
  const [loading, setLoading]         = useState(true);
  const [filter, setFilter]           = useState<"all" | QualityLevel>("all");
  const [search, setSearch]           = useState("");
  const [sortDesc, setSortDesc]       = useState(true);

  // Link checker state
  const [selectedIds, setSelectedIds]   = useState<string[]>([]);
  const [checkResults, setCheckResults] = useState<LinkCheckResult[]>([]);
  const [checking, setChecking]         = useState(false);

  // Load domains once
  useEffect(() => {
    api.domains().then(setDomains);
  }, []);

  // Re-fetch quality whenever domain changes
  useEffect(() => {
    setLoading(true);
    setSelectedIds([]);
    setCheckResults([]);
    setFilter("all");
    api.quality(activeDomain).then((r) => {
      setItems(r.items);
      setUpdatedAt(r.catalog_updated);
    }).finally(() => setLoading(false));
  }, [activeDomain]);

  async function handleLinkCheck() {
    if (!selectedIds.length) return;
    setChecking(true);
    try {
      const r = await api.linkCheck(selectedIds);
      setCheckResults(r.results);
    } finally {
      setChecking(false);
    }
  }

  // ── Derived ───────────────────────────────────────────────────────────────
  const total    = items.length;
  const good     = items.filter((i) => i.quality_level === "good").length;
  const warning  = items.filter((i) => i.quality_level === "warning").length;
  const critical = items.filter((i) => i.quality_level === "critical").length;

  let filtered = items.filter((i) => {
    if (filter !== "all" && i.quality_level !== filter) return false;
    if (search && !i.title.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });
  filtered = [...filtered].sort((a, b) =>
    sortDesc ? b.missing_field_count - a.missing_field_count : a.missing_field_count - b.missing_field_count
  );

  // Bar chart data — top 30 by missing count
  const chartData = [...items]
    .sort((a, b) => b.missing_field_count - a.missing_field_count)
    .slice(0, 30)
    .map((i) => ({ name: i.title.slice(0, 30), count: i.missing_field_count, level: i.quality_level }));

  const STATUS_ICON: Record<string, string> = {
    available:   "🟢 Available",
    error:       "🔴 Error",
    unreachable: "🔴 Unreachable",
    invalid:     "⚪ Invalid URL",
  };

  return (
    <div style={{ background: "var(--cream)", minHeight: "100vh" }}>
      <div className="page-wrap">
        <h1 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 32, fontWeight: 700, color: "var(--charcoal)", marginBottom: 4 }}>
          Data Quality
        </h1>
        <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 28 }}>
          Catalog last updated: <strong>{updatedAt || "—"}</strong>
        </p>

        {/* Domain filter */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 24 }}>
          <button
            className={`domain-chip ${activeDomain === "all" ? "domain-chip-active" : "domain-chip-inactive"}`}
            onClick={() => setActiveDomain("all")}
          >
            All domains
          </button>
          {Object.entries(domains)
            .filter(([, d]) => d.status === "active")
            .map(([key, d]) => (
              <button
                key={key}
                className={`domain-chip ${activeDomain === key ? "domain-chip-active" : "domain-chip-inactive"}`}
                onClick={() => setActiveDomain(key)}
              >
                {d.emoji} {d.name}
              </button>
            ))}
        </div>

        {/* Metric cards */}
        <div className="grid-4col" style={{ marginBottom: 28 }}>
          {[
            { label: "Total Studies", value: total, color: "var(--charcoal)" },
            { label: "Good ●", value: good, color: "var(--rw-green)" },
            { label: "Warning ●", value: warning, color: "#92620A" },
            { label: "Critical ●", value: critical, color: "var(--coral)" },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "20px 24px" }}>
              <div style={{ color: "var(--muted)", fontSize: 12, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 6 }}>
                {label}
              </div>
              <div style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 32, fontWeight: 700, color, lineHeight: 1 }}>
                {loading ? "—" : value.toLocaleString()}
              </div>
            </div>
          ))}
        </div>

        {/* Bar chart */}
        {!loading && (
          <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px", marginBottom: 28 }}>
            <div style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)", marginBottom: 20 }}>
              Missing field counts — top 30 studies
              {activeDomain !== "all" && domains[activeDomain] && (
                <span style={{ fontWeight: 400, fontSize: 13, color: "var(--muted)", marginLeft: 8 }}>
                  · {domains[activeDomain].emoji} {domains[activeDomain].name}
                </span>
              )}
            </div>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                <XAxis dataKey="name" tick={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} axisLine={false} />
                <Tooltip
                  contentStyle={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
                  formatter={(v) => [v, "Missing fields"]}
                  labelFormatter={(_, payload) => payload?.[0]?.payload?.name ?? ""}
                />
                <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={index} fill={QUALITY_COLORS[entry.level as QualityLevel] ?? "#999"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Quality table */}
        <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px", marginBottom: 28 }}>
          <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16, flexWrap: "wrap" }}>
            <div style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)", flex: 1 }}>Quality overview</div>
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter by title…"
              style={{ padding: "6px 12px", borderRadius: 8, border: "1.5px solid var(--border)", background: "var(--cream)", fontSize: 13, width: "min(220px, 100%)", minWidth: 120 }}
            />
            {(["all", "good", "warning", "critical"] as const).map((q) => (
              <button
                key={q}
                onClick={() => setFilter(q)}
                style={{
                  padding: "4px 12px",
                  borderRadius: 999,
                  fontSize: 12,
                  fontWeight: 600,
                  border: "none",
                  cursor: "pointer",
                  background: filter === q ? (q === "all" ? "var(--charcoal)" : QUALITY_COLORS[q as QualityLevel] ?? "#999") : "var(--cream-dark)",
                  color: filter === q ? "white" : "var(--muted)",
                }}
              >
                {q.charAt(0).toUpperCase() + q.slice(1)}
              </button>
            ))}
            <button
              className="btn-ghost"
              style={{ fontSize: 12 }}
              onClick={() => setSortDesc(!sortDesc)}
            >
              Missing fields {sortDesc ? "↓" : "↑"}
            </button>
          </div>

          {loading ? (
            <div className="skeleton" style={{ height: 240, borderRadius: 8 }} />
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--muted)", textAlign: "left" }}>
                    <th style={{ padding: "8px 12px", fontWeight: 600 }}>Study</th>
                    <th style={{ padding: "8px 12px", fontWeight: 600, width: 90 }}>Missing</th>
                    <th style={{ padding: "8px 12px", fontWeight: 600, width: 110 }}>Quality</th>
                    <th style={{ padding: "8px 12px", fontWeight: 600 }}>Caveats</th>
                    <th style={{ padding: "8px 12px", fontWeight: 600, width: 80 }}>Check</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.slice(0, 100).map((item) => {
                    const b = BADGE_STYLE[item.quality_level];
                    const isSelected = selectedIds.includes(item.study_id);
                    return (
                      <tr
                        key={item.study_id}
                        style={{ borderBottom: "1px solid var(--border)", background: isSelected ? "rgba(192,79,79,0.04)" : undefined }}
                      >
                        <td style={{ padding: "10px 12px", color: "var(--charcoal)", lineHeight: 1.4 }}>
                          {item.title.length > 70 ? item.title.slice(0, 70) + "…" : item.title}
                        </td>
                        <td style={{ padding: "10px 12px", textAlign: "center", fontWeight: 600 }}>
                          {item.missing_field_count}
                        </td>
                        <td style={{ padding: "10px 12px" }}>
                          <span className={`pill ${b.cls}`}>{b.label}</span>
                        </td>
                        <td style={{ padding: "10px 12px", color: "var(--muted)", fontSize: 12 }}>
                          {item.quality_flags.join(" · ") || "—"}
                        </td>
                        <td style={{ padding: "10px 12px" }}>
                          <input
                            type="checkbox"
                            checked={isSelected}
                            disabled={!isSelected && selectedIds.length >= 10}
                            onChange={() =>
                              setSelectedIds((prev) =>
                                isSelected ? prev.filter((id) => id !== item.study_id) : [...prev, item.study_id]
                              )
                            }
                          />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {filtered.length > 100 && (
                <p style={{ color: "var(--muted)", fontSize: 12, padding: "8px 12px" }}>
                  Showing first 100 of {filtered.length} results. Use the search or filter to narrow down.
                </p>
              )}
            </div>
          )}
        </div>

        {/* Link checker */}
        <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px" }}>
          <div style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)", marginBottom: 8 }}>
            Source link checker
          </div>
          <p style={{ color: "var(--muted)", fontSize: 13, marginBottom: 16 }}>
            Select up to 10 studies using the checkboxes above, then click Check Links.
          </p>
          <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
            <button
              className="btn-primary"
              disabled={!selectedIds.length || checking}
              onClick={handleLinkCheck}
            >
              {checking ? "Checking…" : `Check Links (${selectedIds.length} selected)`}
            </button>
            {selectedIds.length > 0 && (
              <button className="btn-ghost" style={{ fontSize: 12 }} onClick={() => { setSelectedIds([]); setCheckResults([]); }}>
                Clear selection
              </button>
            )}
          </div>

          {checkResults.length > 0 && (
            <div style={{ overflowX: "auto", WebkitOverflowScrolling: "touch" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13, minWidth: 500 }}>
              <thead>
                <tr style={{ borderBottom: "1px solid var(--border)", color: "var(--muted)", textAlign: "left" }}>
                  <th style={{ padding: "8px 12px" }}>Study</th>
                  <th style={{ padding: "8px 12px" }}>Status</th>
                  <th style={{ padding: "8px 12px" }}>HTTP</th>
                  <th style={{ padding: "8px 12px" }}>URL</th>
                </tr>
              </thead>
              <tbody>
                {checkResults.map((r) => (
                  <tr key={r.study_id} style={{ borderBottom: "1px solid var(--border)" }}>
                    <td style={{ padding: "10px 12px" }}>{r.title.length > 50 ? r.title.slice(0, 50) + "…" : r.title}</td>
                    <td style={{ padding: "10px 12px" }}>{STATUS_ICON[r.status] ?? r.status}</td>
                    <td style={{ padding: "10px 12px", color: "var(--muted)" }}>{r.http_code ?? "—"}</td>
                    <td style={{ padding: "10px 12px" }}>
                      {r.url ? (
                        <a href={r.url} target="_blank" rel="noopener noreferrer" style={{ color: "var(--coral)", fontSize: 12 }}>
                          {r.url.slice(0, 50)}{r.url.length > 50 ? "…" : ""}
                        </a>
                      ) : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
