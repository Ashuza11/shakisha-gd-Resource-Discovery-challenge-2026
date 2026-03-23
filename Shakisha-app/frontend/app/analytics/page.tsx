"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from "recharts";
import { api, DomainConfig, Study, GeographicData } from "../lib/api";
import RwandaMap from "../components/RwandaMap";

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
  const [domains,     setDomains]   = useState<Record<string, DomainConfig>>({});
  const [studies,     setStudies]   = useState<Study[]>([]);
  const [geoData,     setGeoData]   = useState<GeographicData | null>(null);
  const [loading,     setLoading]   = useState(true);
  const [geoLoading,  setGeoLoading] = useState(true);
  const [activeDomain, setActiveDomain] = useState("labour");

  // Load geographic data once (cross-domain)
  useEffect(() => {
    api.geographic()
      .then(setGeoData)
      .finally(() => setGeoLoading(false));
  }, []);

  // Load domain-filtered studies
  useEffect(() => {
    setLoading(true);
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

  const DOMAIN_SHORT: Record<string, string> = {
    labour:      "Labour",
    agriculture: "Agri.",
    health:      "Health",
    household:   "Household",
    finance:     "Finance",
    population:  "Census",
  };

  const domainCountsChart = Object.entries(domains)
    .filter(([, d]) => d.status === "active")
    .map(([key, d], i) => ({
      name:     DOMAIN_SHORT[key] ?? key,
      fullName: d.name,
      count:    d.study_count,
      fill:     DOMAIN_COLORS[i % DOMAIN_COLORS.length],
    }));

  const activeDomainCfg = domains[activeDomain];
  const goodCount = qualityCounts.find((q) => q.name === "good")?.value ?? 0;
  const years = yearCounts.map((y) => parseInt(y.year)).filter(Boolean);
  const yearSpan = years.length ? `${Math.min(...years)}–${Math.max(...years)}` : "—";

  // Domain-filtered geographic data — derived from existing geoData, no extra fetch
  const domainProvinces = geoData
    ? geoData.provinces.map(p => ({
        ...p,
        specific_count: p.domain_counts[activeDomain] ?? 0,
        total_count:    (p.domain_counts[activeDomain] ?? 0) + (geoData.national_domains[activeDomain] ?? 0),
      }))
    : [];
  const domainNationalCount = geoData?.national_domains[activeDomain] ?? 0;

  // Geo resolution for the stacked bar
  const resolutionData = geoData ? [
    { name: "Sub-district", value: geoData.geo_resolution.sub_district, fill: "#1A4D2E" },
    { name: "District",     value: geoData.geo_resolution.district,     fill: "#32A060" },
    { name: "Province",     value: geoData.geo_resolution.province,     fill: "#88C4A0" },
    { name: "National",     value: geoData.geo_resolution.national,     fill: "#C4E0D0" },
    { name: "Unspecified",  value: geoData.geo_resolution.unspecified,  fill: "#D0C8BC" },
  ] : [];

  return (
    <div style={{ background: "var(--cream)", minHeight: "100vh" }}>
      <div className="page-wrap">
        <h1 style={{ fontFamily: "'Playfair Display', Georgia, serif", fontSize: 32, fontWeight: 700, color: "var(--charcoal)", marginBottom: 8 }}>
          Analytics
        </h1>
        <p style={{ color: "var(--muted)", fontSize: 14, marginBottom: 28 }}>
          Catalog trends, quality distribution, geographic coverage gaps, and domain breakdown.
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
          <MetricCard
            label="Province-specific studies"
            value={geoLoading ? "—" : domainProvinces.reduce((s, p) => s + p.specific_count, 0)}
            sub={`${activeDomainCfg?.name ?? ""} · vs. national`}
          />
        </div>

        {/* ── Geographic Coverage Map ─────────────────────────────────────── */}
        <div
          style={{
            background: "var(--warm-white)",
            border: "1px solid var(--border)",
            borderRadius: 16,
            padding: "clamp(16px, 3vw, 32px)",
            marginBottom: 20,
            isolation: "isolate",   /* keeps Leaflet z-indexes from escaping this container */
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 20, flexWrap: "wrap", gap: 8 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 18, color: "var(--charcoal)", marginBottom: 4 }}>
                Geographic Coverage — {activeDomainCfg?.emoji} {activeDomainCfg?.name}
              </div>
              <p style={{ fontSize: 13, color: "var(--muted)", maxWidth: 560, lineHeight: 1.6, margin: 0 }}>
                Choropleth shows <strong>province-specific studies</strong> for this domain.
                {domainNationalCount > 0 && <> +{domainNationalCount} national-level {activeDomainCfg?.name.toLowerCase()} studies cover all provinces equally.</>}
                <span style={{ color: "#C04F4F", fontWeight: 600 }}> Warm = data gap.</span>
              </p>
            </div>
            {!geoLoading && domainProvinces.length > 0 && (
              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {domainProvinces
                  .filter(p => p.specific_count === 0)
                  .map(p => (
                    <span key={p.key} style={{
                      fontSize: 11, fontWeight: 700, color: "#C04F4F",
                      background: "#FEE8E8", border: "1px solid #F5C6C6",
                      padding: "3px 8px", borderRadius: 6,
                    }}>
                      {p.name}: 0
                    </span>
                  ))}
              </div>
            )}
          </div>

          {geoLoading ? (
            <div className="skeleton" style={{ height: 320, borderRadius: 12 }} />
          ) : geoData ? (
            <RwandaMap
              provinces={domainProvinces}
              districts={geoData.districts}
              geoResolution={geoData.geo_resolution}
              nationalCount={domainNationalCount}
              totalStudies={geoData.total_studies}
            />
          ) : (
            <div style={{ color: "var(--muted)", padding: 24 }}>Geographic data unavailable.</div>
          )}
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
                    <YAxis type="category" dataKey="name" width={120} tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} />
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
                    <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13 }}
                      formatter={(value, _name, props) => [value, props.payload.fullName]}
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

            {/* Row 3: Geographic resolution breakdown */}
            {!geoLoading && resolutionData.length > 0 && (
              <div style={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 12, padding: "24px", marginBottom: 20 }}>
                <div style={{ fontWeight: 700, fontSize: 16, color: "var(--charcoal)", marginBottom: 6 }}>
                  Data resolution breakdown — all {geoData?.total_studies ?? "…"} studies
                </div>
                <p style={{ fontSize: 13, color: "var(--muted)", marginBottom: 20 }}>
                  How granular is the geographic coverage? Sub-district data enables the most targeted policy recommendations.
                </p>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={resolutionData} layout="vertical" margin={{ top: 0, right: 40, bottom: 0, left: 20 }}>
                    <XAxis type="number" tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} />
                    <YAxis type="category" dataKey="name" width={100} tick={{ fontSize: 11, fill: "#8A6A5A" }} tickLine={false} />
                    <Tooltip
                      contentStyle={{ background: "var(--warm-white)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 13 }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]} name="Studies">
                      {resolutionData.map((entry, index) => (
                        <Cell key={index} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
