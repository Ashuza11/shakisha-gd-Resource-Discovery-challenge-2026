"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { api, DomainConfig, Study } from "../lib/api";

const QUALITY_COLORS: Record<string, string> = {
  good:     "#20603D",
  warning:  "#E8B800",
  critical: "#C04F4F",
};

const DOMAIN_COLORS = [
  "#C04F4F", "#20603D", "#E8B800", "#8B5E3C", "#2A9D8F", "#264653",
];

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

export default function AnalyticsPage() {
  const [domains, setDomains]   = useState<Record<string, DomainConfig>>({});
  const [studies, setStudies]   = useState<Study[]>([]);
  const [loading, setLoading]   = useState(true);
  const [activeDomain, setActiveDomain] = useState("labour");

  useEffect(() => {
    Promise.all([
      api.domains().then(setDomains),
      api.search({ domain: activeDomain, query: "", sort_order: "Newest first", use_ai: false })
        .then((r) => setStudies(r.results)),
    ]).finally(() => setLoading(false));
  }, [activeDomain]);

  // ── Derived data ────────────────────────────────────────────────────────
  const yearCounts = (() => {
    const m: Record<string, number> = {};
    studies.forEach((s) => { if (s.year) m[s.year] = (m[s.year] ?? 0) + 1; });
    return Object.entries(m)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([year, count]) => ({ year, count }));
  })();

  const qualityCounts = (() => {
    const m: Record<string, number> = { good: 0, warning: 0, critical: 0 };
    studies.forEach((s) => { m[s.quality_level] = (m[s.quality_level] ?? 0) + 1; });
    return Object.entries(m).map(([name, value]) => ({ name, value }));
  })();

  const orgCounts = (() => {
    const m: Record<string, number> = {};
    studies.forEach((s) => {
      const o = s.organization || "Unknown";
      m[o] = (m[o] ?? 0) + 1;
    });
    return Object.entries(m)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 8)
      .map(([name, count]) => ({ name: name.length > 45 ? name.slice(0, 45) + "…" : name, count }));
  })();

  const domainCountsChart = Object.entries(domains)
    .filter(([, d]) => d.status === "active")
    .map(([key, d], i) => ({
      name: d.name.replace("& ", "&\n"),
      count: d.study_count,
      fill: DOMAIN_COLORS[i % DOMAIN_COLORS.length],
    }));

  const activeDomainCfg = domains[activeDomain];
  const goodCount = qualityCounts.find((q) => q.name === "good")?.value ?? 0;
  const years = yearCounts.map((y) => parseInt(y.year)).filter(Boolean);
  const yearSpan = years.length ? `${Math.min(...years)}–${Math.max(...years)}` : "—";

  return (
    <div style={{ background: "var(--cream)", minHeight: "100vh" }}>
      <div className="page-wrap">
        <h1 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 32, fontWeight: 700, color: "var(--charcoal)", marginBottom: 8 }}>
          Analytics
        </h1>
        <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 28 }}>
          Catalog trends, quality distribution, and coverage gaps across domains.
        </p>

        {/* Domain selector tabs */}
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 28 }}>
          {Object.entries(domains)
            .filter(([, d]) => d.status === "active")
            .map(([key, d]) => (
              <button
                key={key}
                className={`domain-chip ${activeDomain === key ? "domain-chip-active" : "domain-chip-inactive"}`}
                onClick={() => { setActiveDomain(key); setLoading(true); }}
              >
                {d.emoji} {d.name}
              </button>
            ))}
        </div>

        {/* Metrics */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 32 }}>
          <MetricCard label="Studies (this domain)" value={loading ? "—" : studies.length.toLocaleString()} />
          <MetricCard label="High quality" value={loading ? "—" : goodCount} sub="Missing 0 fields" />
          <MetricCard label="Year coverage" value={loading ? "—" : yearSpan} />
          <MetricCard label="Total resources" value={loading ? "—" : studies.reduce((a, s) => a + s.resource_count, 0).toLocaleString()} />
        </div>

        {loading ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {[1, 2, 3].map((i) => <div key={i} className="skeleton" style={{ height: 300, borderRadius: 12 }} />)}
          </div>
        ) : (
          <>
            {/* Row 1: Year trend + Quality donut */}
            <div className="grid-2-1col" style={{ marginBottom: 20 }}>
              <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px" }}>
                <div style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)", marginBottom: 20 }}>
                  {activeDomainCfg?.emoji} {activeDomainCfg?.name} — studies by year
                </div>
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={yearCounts} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                    <XAxis dataKey="year" tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13 }}
                    />
                    <Bar dataKey="count" fill="#C04F4F" radius={[4, 4, 0, 0]} name="Studies" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px" }}>
                <div style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)", marginBottom: 20 }}>
                  Data quality
                </div>
                <ResponsiveContainer width="100%" height={240}>
                  <PieChart>
                    <Pie
                      data={qualityCounts}
                      cx="50%"
                      cy="45%"
                      innerRadius={60}
                      outerRadius={90}
                      dataKey="value"
                      nameKey="name"
                    >
                      {qualityCounts.map((entry, index) => (
                        <Cell key={index} fill={QUALITY_COLORS[entry.name] ?? "#999"} />
                      ))}
                    </Pie>
                    <Legend
                      formatter={(value) => value.charAt(0).toUpperCase() + value.slice(1)}
                      iconType="circle"
                      iconSize={10}
                      wrapperStyle={{ fontSize: 13 }}
                    />
                    <Tooltip
                      contentStyle={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13 }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Row 2: Org breakdown + Domain overview */}
            <div className="grid-2col" style={{ marginBottom: 20 }}>
              <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px" }}>
                <div style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)", marginBottom: 20 }}>
                  Studies by organization
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={orgCounts} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 0 }}>
                    <XAxis type="number" tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} />
                    <YAxis type="category" dataKey="name" width={180} tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} />
                    <Tooltip
                      contentStyle={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13 }}
                    />
                    <Bar dataKey="count" fill="#20603D" radius={[0, 4, 4, 0]} name="Studies" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px" }}>
                <div style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)", marginBottom: 20 }}>
                  All domains — study counts
                </div>
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={domainCountsChart} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                    <XAxis dataKey="name" tick={{ fontSize: 10, fill: "#8A6A5A" }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13 }}
                    />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]} name="Studies">
                      {domainCountsChart.map((entry, index) => (
                        <Cell key={index} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
