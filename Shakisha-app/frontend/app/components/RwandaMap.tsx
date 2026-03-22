"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
import { ProvinceData, DistrictData, GeoResolution } from "../lib/api";

// Leaflet uses browser-only APIs — must disable SSR
const RwandaLeafletInner = dynamic(
  () => import("./RwandaLeafletInner"),
  {
    ssr: false,
    loading: () => (
      <div style={{
        height: 580,
        background: "linear-gradient(135deg, #EDE8E0 0%, #D8D0C4 100%)",
        borderRadius: 12,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexDirection: "column",
        gap: 12,
      }}>
        <div style={{
          width: 40, height: 40, borderRadius: "50%",
          border: "3px solid #20603D", borderTopColor: "transparent",
          animation: "spin 0.8s linear infinite",
        }} />
        <div style={{ fontSize: 13, color: "#8A7A6A", fontWeight: 600 }}>Loading map…</div>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    ),
  }
);

// ── Colour helper (matches the Leaflet choropleth) ────────────────────────────
function gapColor(count: number): string {
  const stops: Array<[number, [number, number, number]]> = [
    [0,  [245, 237, 222]],
    [1,  [196, 224, 208]],
    [4,  [88,  163, 127]],
    [10, [32,   96,  61]],
    [20, [20,   58,  36]],
  ];
  const c = Math.min(count, 20);
  for (let i = 1; i < stops.length; i++) {
    const [lo, cLo] = stops[i - 1];
    const [hi, cHi] = stops[i];
    if (c <= hi) {
      const t = (c - lo) / (hi - lo);
      return `rgb(${Math.round(cLo[0] + (cHi[0] - cLo[0]) * t)},` +
             `${Math.round(cLo[1] + (cHi[1] - cLo[1]) * t)},` +
             `${Math.round(cLo[2] + (cHi[2] - cLo[2]) * t)})`;
    }
  }
  return "rgb(20,58,36)";
}

const DOMAIN_LABELS: Record<string, string> = {
  labour: "Labour", agriculture: "Agriculture", health: "Health",
  household: "Household", finance: "Finance", population: "Population",
};
const DOMAIN_COLORS: Record<string, string> = {
  labour: "#C04F4F", agriculture: "#20603D", health: "#2A9D8F",
  household: "#8B5E3C", finance: "#E8B800", population: "#264653",
};

interface Props {
  provinces:     ProvinceData[];
  districts:     DistrictData[];
  geoResolution: GeoResolution;
  nationalCount: number;
  totalStudies?: number;
  onProvinceSelect?: (key: string | null) => void;
}

export default function RwandaMap({ provinces, districts, geoResolution, nationalCount, totalStudies, onProvinceSelect }: Props) {
  const [selected, setSelected] = useState<string | null>(null);

  function handleSelect(key: string | null) {
    setSelected(key);
    onProvinceSelect?.(key);
  }

  const provMap     = Object.fromEntries(provinces.map(p => [p.key, p]));
  const maxSpecific = Math.max(...provinces.map(p => p.specific_count), 1);
  const selectedProv = selected ? provMap[selected] : null;

  const activeDistricts = selected
    ? districts.filter(d => d.province === selected).sort((a, b) => b.study_count - a.study_count)
    : [];
  const topDomains = selectedProv
    ? Object.entries(selectedProv.domain_counts).sort(([, a], [, b]) => b - a).slice(0, 5)
    : [];

  const resTotal = Object.values(geoResolution).reduce((s, n) => s + n, 0);
  const resPct   = (n: number) => resTotal > 0 ? Math.round(n / resTotal * 100) : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

      {/* ── Leaflet map ──────────────────────────────────────────────────── */}
      <div style={{
        width: "100%",
        height: 580,
        borderRadius: 12,
        overflow: "hidden",
        boxShadow: "0 4px 24px rgba(0,0,0,0.15)",
        border: "1px solid var(--border)",
      }}>
        <RwandaLeafletInner
          provinces={provinces}
          districts={districts}
          selected={selected}
          onSelect={handleSelect}
        />
      </div>

      {/* ── Legend ───────────────────────────────────────────────────────── */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, justifyContent: "center", flexWrap: "wrap" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 12, color: "#8A7A6A", fontWeight: 600 }}>Data gap</span>
          <div style={{ width: 180, height: 10, borderRadius: 5, background: "linear-gradient(to right, #F5EDDE, #143A24)" }} />
          <span style={{ fontSize: 12, color: "#8A7A6A", fontWeight: 600 }}>Well covered</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#C04F4F" }} />
          <span style={{ fontSize: 11, color: "#8A7A6A" }}>Selected district</span>
          <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#20603D", marginLeft: 8 }} />
          <span style={{ fontSize: 11, color: "#8A7A6A" }}>Other districts</span>
        </div>
        <span style={{ fontSize: 11, color: "#A09080" }}>Click a province to zoom · Hover for details</span>
      </div>

      {/* ── Bottom panels ────────────────────────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

        {/* Province ranking */}
        <div style={{ background: "var(--cream)", border: "1px solid var(--border)", borderRadius: 12, padding: "16px 18px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--muted)", marginBottom: 10 }}>
            Province ranking — specific studies
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            {[...provinces].sort((a, b) => b.specific_count - a.specific_count).map(p => (
              <button
                key={p.key}
                onClick={() => handleSelect(selected === p.key ? null : p.key)}
                style={{
                  display: "flex", alignItems: "center", gap: 8,
                  background: selected === p.key ? "#EAF5EE" : "transparent",
                  border: selected === p.key ? "1px solid #20603D" : "1px solid transparent",
                  borderRadius: 8, padding: "7px 10px",
                  cursor: "pointer", textAlign: "left", width: "100%",
                  transition: "background 0.15s",
                }}
              >
                <div style={{
                  width: 12, height: 12, borderRadius: 3, flexShrink: 0,
                  background: gapColor(p.specific_count),
                  border: "1px solid rgba(0,0,0,0.12)",
                }} />
                <div style={{ flex: 1, fontSize: 12, fontWeight: 600, color: "var(--charcoal)" }}>
                  {p.name}
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                  <div style={{
                    height: 6,
                    width: p.specific_count > 0 ? Math.max(p.specific_count / maxSpecific * 64, 6) : 0,
                    background: "#20603D", borderRadius: 3,
                  }} />
                  <span style={{ fontSize: 12, color: "var(--muted)", minWidth: 18, textAlign: "right" }}>
                    {p.specific_count}
                  </span>
                </div>
                {p.specific_count === 0 && (
                  <span style={{ fontSize: 10, color: "#C04F4F", fontWeight: 700, background: "#FEE8E8", padding: "1px 6px", borderRadius: 4 }}>
                    GAP
                  </span>
                )}
              </button>
            ))}
          </div>
          <div style={{ marginTop: 10, padding: "8px 12px", background: "#FFF9F0", borderRadius: 8, border: "1px solid #EDD9A3" }}>
            <span style={{ fontSize: 11, color: "#8A6A2A", fontWeight: 700 }}>National: </span>
            <span style={{ fontSize: 11, color: "#8A6A2A" }}>{nationalCount.toLocaleString()} studies available in all provinces</span>
          </div>
        </div>

        {/* Geographic resolution */}
        <div style={{ background: "var(--cream)", border: "1px solid var(--border)", borderRadius: 12, padding: "16px 18px" }}>
          <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--muted)", marginBottom: 10 }}>
            Data resolution — all {totalStudies ?? "…"} studies
          </div>
          {([
            { label: "Sub-district", key: "sub_district", color: "#1A4D2E", note: "cell / sector" },
            { label: "District",     key: "district",     color: "#32A060", note: "" },
            { label: "Province",     key: "province",     color: "#88C4A0", note: "" },
            { label: "National",     key: "national",     color: "#C4E0D0", note: "" },
            { label: "Unspecified",  key: "unspecified",  color: "#D8D0C8", note: "" },
          ] as const).map(({ label, key, color, note }) => {
            const val = geoResolution[key as keyof GeoResolution];
            const pct = resPct(val);
            return (
              <div key={key} style={{ marginBottom: 9 }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                  <span style={{ fontSize: 12, color: "var(--charcoal)", fontWeight: 600 }}>
                    {label}
                    {note && <span style={{ fontSize: 10, color: "var(--muted)", marginLeft: 4 }}>({note})</span>}
                  </span>
                  <span style={{ fontSize: 12, color: "var(--muted)" }}>{val} · {pct}%</span>
                </div>
                <div style={{ height: 8, background: "#EDE8E0", borderRadius: 4, overflow: "hidden" }}>
                  <div style={{ width: `${pct}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.5s ease", minWidth: val > 0 ? 4 : 0 }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Province detail panel ─────────────────────────────────────────── */}
      {selectedProv && (
        <div style={{
          background: "var(--cream)",
          border: "1px solid var(--border)",
          borderRadius: 12,
          padding: "20px 24px",
          borderLeft: `4px solid ${gapColor(selectedProv.specific_count)}`,
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16, flexWrap: "wrap", gap: 10 }}>
            <div>
              <div style={{ fontSize: 17, fontWeight: 700, color: "var(--charcoal)" }}>{selectedProv.name}</div>
              <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 2 }}>
                {selectedProv.specific_count} province-specific · +{nationalCount.toLocaleString()} national studies
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              {selectedProv.specific_count === 0 && (
                <div style={{ background: "#FEE8E8", border: "1px solid #F5C6C6", borderRadius: 8, padding: "6px 12px" }}>
                  <span style={{ fontSize: 12, fontWeight: 700, color: "#C04F4F" }}>Data Gap — no targeted research</span>
                </div>
              )}
              <button
                onClick={() => handleSelect(null)}
                style={{ background: "transparent", border: "1px solid var(--border)", borderRadius: 6, padding: "4px 12px", cursor: "pointer", fontSize: 12, color: "var(--muted)" }}
              >
                Deselect ✕
              </button>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            {/* Domain breakdown */}
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--muted)", marginBottom: 8 }}>
                Domain breakdown (specific studies)
              </div>
              {topDomains.length > 0 ? topDomains.map(([dk, cnt]) => (
                <div key={dk} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <div style={{ width: 84, fontSize: 12, color: "var(--charcoal)", textAlign: "right", flexShrink: 0 }}>
                    {DOMAIN_LABELS[dk] ?? dk}
                  </div>
                  <div style={{ flex: 1, height: 8, background: "#EDE8E0", borderRadius: 4 }}>
                    <div style={{ width: `${(cnt / topDomains[0][1]) * 100}%`, height: "100%", background: DOMAIN_COLORS[dk] ?? "#888", borderRadius: 4 }} />
                  </div>
                  <span style={{ fontSize: 12, color: "var(--muted)", minWidth: 22, textAlign: "right" }}>{cnt}</span>
                </div>
              )) : (
                <p style={{ fontSize: 12, color: "var(--muted)", fontStyle: "italic" }}>
                  No domain-specific breakdown — all via national coverage.
                </p>
              )}
            </div>

            {/* Districts */}
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", color: "var(--muted)", marginBottom: 8 }}>
                Districts (hover on map to explore)
              </div>
              {activeDistricts.map(d => {
                const maxD = Math.max(...activeDistricts.map(x => x.study_count), 1);
                return (
                  <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                    <div style={{ width: 90, fontSize: 12, color: "var(--charcoal)", textAlign: "right", flexShrink: 0 }}>{d.name}</div>
                    <div style={{ flex: 1, height: 7, background: "#EDE8E0", borderRadius: 3 }}>
                      <div style={{
                        width: d.study_count > 0 ? `${Math.max((d.study_count / maxD) * 100, 5)}%` : "0%",
                        height: "100%", background: "#20603D", borderRadius: 3,
                      }} />
                    </div>
                    <span style={{ fontSize: 11, color: "var(--muted)", minWidth: 22, textAlign: "right" }}>{d.study_count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
