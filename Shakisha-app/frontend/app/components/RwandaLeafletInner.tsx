"use client";

import { useEffect, useRef, useState } from "react";
import {
  MapContainer, TileLayer, GeoJSON, useMap,
} from "react-leaflet";
import L from "leaflet";
import type { PathOptions } from "leaflet";
import { ProvinceData, DistrictData } from "../lib/api";
import { RWANDA_BOUNDS, PROVINCE_BOUNDS, RWANDA_PROVINCES_GEO } from "./rwandaGeoData";

// ── Local GeoJSON files served from /public (no external dependency) ─────────
const ADM0_URL = "/rwanda-adm0.geojson";
const ADM1_URL = "/rwanda-adm1.geojson";
const ADM2_URL = "/rwanda-adm2.geojson";

// ── Province shapeName → internal key ────────────────────────────────────────
function shapeNameToKey(name: string): string {
  const n = name.toLowerCase();
  if (n.includes("kigali"))   return "kigali";
  if (n.includes("northern")) return "northern";
  if (n.includes("eastern"))  return "eastern";
  if (n.includes("southern")) return "southern";
  if (n.includes("western"))  return "western";
  return "";
}

// District name → province mapping (built from DISTRICT_MARKERS in rwandaGeoData)
import { DISTRICT_MARKERS } from "./rwandaGeoData";
const DISTRICT_TO_PROVINCE: Record<string, string> = Object.fromEntries(
  DISTRICT_MARKERS.map(d => [d.name.toLowerCase(), d.province])
);

// ── Colour ramps ──────────────────────────────────────────────────────────────
function interpolate(
  stops: Array<[number, [number, number, number]]>,
  t: number
): string {
  for (let i = 1; i < stops.length; i++) {
    const [lo, cLo] = stops[i - 1];
    const [hi, cHi] = stops[i];
    if (t <= hi) {
      const s = (t - lo) / (hi - lo);
      return `rgb(${Math.round(cLo[0] + (cHi[0] - cLo[0]) * s)},`
           + `${Math.round(cLo[1] + (cHi[1] - cLo[1]) * s)},`
           + `${Math.round(cLo[2] + (cHi[2] - cLo[2]) * s)})`;
    }
  }
  return `rgb(${stops.at(-1)![1].join(",")})`;
}

function provinceColor(count: number): string {
  return interpolate([
    [0,  [245, 237, 222]],
    [1,  [196, 224, 208]],
    [4,  [88,  163, 127]],
    [10, [32,   96,  61]],
    [20, [20,   58,  36]],
  ], Math.min(count, 20));
}

function districtColor(count: number, max: number): string {
  if (max === 0) return "rgb(240,220,200)";
  return interpolate([
    [0,   [240, 220, 200]],
    [0.3, [150, 200, 170]],
    [1,   [26,   77,  46]],
  ], Math.min(count / max, 1));
}

function getProvinceStyle(
  key: string, selected: string | null,
  provMap: Record<string, ProvinceData>
): PathOptions {
  const count      = provMap[key]?.specific_count ?? 0;
  const isSelected = selected === key;
  return {
    fillColor:   isSelected ? "#1A3A26" : provinceColor(count),
    fillOpacity: isSelected ? 0.85 : 0.75,
    color:       isSelected ? "#FFD700" : "#ffffff",
    weight:      isSelected ? 3 : 1.8,
  };
}

// ── Fly-to / lock controller ──────────────────────────────────────────────────
const RW_BOUNDS = RWANDA_BOUNDS as L.LatLngBoundsExpression;
// Slightly padded max bounds so the border doesn't sit right at the edge
const RW_MAX_BOUNDS: L.LatLngBoundsExpression = [
  [-2.95, 28.75],   // SW with padding
  [-0.95, 31.00],   // NE with padding
];

function MapController({ selectedKey }: { selectedKey: string | null }) {
  const map = useMap();

  useEffect(() => {
    const target = selectedKey
      ? PROVINCE_BOUNDS[selectedKey] as L.LatLngBoundsExpression
      : RW_BOUNDS;
    map.flyToBounds(target, { padding: [24, 24], duration: 0.7, easeLinearity: 0.45 });
  }, [selectedKey, map]);

  return null;
}

// ── Province label overlays ───────────────────────────────────────────────────
const LABEL_CENTERS: Record<string, [number, number]> = {
  northern: [-1.40, 29.85],
  eastern:  [-2.00, 30.52],
  southern: [-2.28, 29.50],
  western:  [-2.00, 29.17],
  kigali:   [-1.94, 30.05],
};

function ProvinceLabels({
  provinces, selected,
}: { provinces: ProvinceData[]; selected: string | null }) {
  const { Marker } = require("react-leaflet");
  return (
    <>
      {provinces.map(p => {
        const center = LABEL_CENTERS[p.key];
        if (!center) return null;
        const isSelected = selected === p.key;
        const dark = isSelected || p.specific_count >= 4;
        const icon = L.divIcon({
          className: "",
          html: `<div style="
            font-family:'Plus Jakarta Sans',sans-serif;
            font-size:${p.key === "kigali" ? "9" : "11"}px;
            font-weight:700;letter-spacing:0.04em;
            color:${dark ? "#fff" : "#2A1A0A"};
            text-shadow:${dark
              ? "0 1px 5px rgba(0,0,0,0.8)"
              : "0 0 6px rgba(255,255,255,1),0 0 12px rgba(255,255,255,0.8)"};
            white-space:nowrap;pointer-events:none;
            transform:translate(-50%,-50%);text-align:center;
            text-transform:uppercase;
          ">${p.name.replace(" Province", "").replace(" City", "\nCity")}</div>`,
          iconSize: [1, 1],
          iconAnchor: [0, 0],
        });
        return (
          <Marker
            key={p.key}
            position={center}
            icon={icon}
            interactive={false}
            zIndexOffset={500}
          />
        );
      })}
    </>
  );
}

// ── Hover tooltip ─────────────────────────────────────────────────────────────
interface HoverInfo {
  x: number; y: number;
  key: string;
  isDistrict?: boolean;
  districtName?: string;
  districtCount?: number;
}

// ── Main component ────────────────────────────────────────────────────────────
interface Props {
  provinces: ProvinceData[];
  districts: DistrictData[];
  selected:  string | null;
  onSelect:  (key: string | null) => void;
}

export default function RwandaLeafletInner({ provinces, districts, selected, onSelect }: Props) {
  const [adm0Geo,    setAdm0Geo]    = useState<any>(null);
  const [adm1Geo,    setAdm1Geo]    = useState<any>(RWANDA_PROVINCES_GEO); // fallback
  const [adm2Geo,    setAdm2Geo]    = useState<any>(null);
  const [geoReady,   setGeoReady]   = useState(false);
  const [hover,      setHover]      = useState<HoverInfo | null>(null);
  const containerRef                = useRef<HTMLDivElement>(null);

  const provMap   = Object.fromEntries(provinces.map(p => [p.key, p]));
  const distMap   = Object.fromEntries(districts.map(d => [d.name, d]));
  const nationalCount = (provinces[0]?.total_count ?? 0) - (provinces[0]?.specific_count ?? 0);

  // ── Fetch all 3 boundary levels in parallel from raw GitHub CDN ─────────────
  useEffect(() => {
    Promise.all([
      fetch(ADM0_URL).then(r => r.json()),
      fetch(ADM1_URL).then(r => r.json()),
      fetch(ADM2_URL).then(r => r.json()),
    ]).then(([adm0, adm1, adm2]) => {
      // Tag ADM1 with internal province keys
      adm1.features.forEach((f: any) => {
        f.properties.key = shapeNameToKey(f.properties.shapeName ?? "");
      });

      // Tag ADM2 with province + study count
      adm2.features.forEach((f: any) => {
        const name = (f.properties.shapeName ?? "").trim();
        f.properties.districtName  = name;
        f.properties.province      = DISTRICT_TO_PROVINCE[name.toLowerCase()] ?? "";
        f.properties.study_count   = distMap[name]?.study_count ?? 0;
      });

      setAdm0Geo(adm0);
      setAdm1Geo(adm1);
      setAdm2Geo(adm2);
      setGeoReady(true);
    }).catch(() => {
      // Fallback: stay with approximate province data, skip ADM0/ADM2
      setGeoReady(true);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Max district count for relative coloring (per selected province)
  const selectedDistricts = districts.filter(d => d.province === selected);
  const maxDistCount      = Math.max(...selectedDistricts.map(d => d.study_count), 1);

  // Precompute global max for unselected-province district coloring
  const globalMaxDist = Math.max(...districts.map(d => d.study_count), 1);

  // Keys force layer remount when selection changes (avoids stale closure styles)
  const adm1Key = `adm1-${selected ?? "none"}-${geoReady}`;
  const adm2Key = `adm2-${selected ?? "none"}-${geoReady}`;

  function moveHover(e: any) {
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    return { x: e.originalEvent.clientX - rect.left, y: e.originalEvent.clientY - rect.top };
  }

  return (
    <div
      ref={containerRef}
      style={{ position: "relative", width: "100%", height: "100%" }}
      onMouseLeave={() => setHover(null)}
    >
      <MapContainer
        bounds={RW_BOUNDS}
        boundsOptions={{ padding: [8, 8] }}
        minZoom={7}
        maxZoom={13}
        maxBounds={RW_MAX_BOUNDS}
        maxBoundsViscosity={1.0}
        style={{ height: "100%", width: "100%" }}
        zoomControl
        scrollWheelZoom
      >
        {/* CartoDB Positron — clean neutral basemap */}
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          subdomains="abcd"
          maxZoom={13}
        />

        {/* ── ADM2: All district boundaries (always visible) ─────────────── */}
        {adm2Geo && (
          <GeoJSON
            key={adm2Key}
            data={adm2Geo}
            style={(f: any) => {
              const prov  = f?.properties?.province as string;
              const name  = f?.properties?.districtName as string;
              const count = distMap[name]?.study_count ?? 0;
              const isInSelected = selected && prov === selected;
              const max   = isInSelected ? maxDistCount : globalMaxDist;

              return isInSelected
                ? {
                    fillColor:   districtColor(count, max),
                    fillOpacity: 0.70,
                    color:       "#fff",
                    weight:      1.5,
                  }
                : {
                    fillColor:   "transparent",
                    fillOpacity: 0,
                    color:       selected ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.35)",
                    weight:      0.8,
                  };
            }}
            onEachFeature={(f: any, layer: L.Path) => {
              const name  = f.properties.districtName as string;
              const prov  = f.properties.province as string;
              const count = f.properties.study_count as number;

              layer.on({
                mouseover(e: any) {
                  const pos = moveHover(e);
                  if (!pos) return;
                  const inSelected = selected && prov === selected;
                  layer.setStyle({
                    fillOpacity: inSelected ? 0.90 : 0.55,
                    fillColor:   inSelected
                      ? districtColor(count, maxDistCount)
                      : "rgba(200,230,215,0.6)",
                    weight:      inSelected ? 2.5 : 1.5,
                    color:       "#FFD700",
                  });
                  layer.bringToFront();
                  setHover({ ...pos, key: prov, isDistrict: true, districtName: name, districtCount: count });
                },
                mousemove(e: any) {
                  const pos = moveHover(e);
                  if (pos) setHover(h => h ? { ...h, ...pos } : null);
                },
                mouseout() {
                  const inSelected = selected && prov === selected;
                  layer.setStyle(
                    inSelected
                      ? { fillColor: districtColor(count, maxDistCount), fillOpacity: 0.70, color: "#fff", weight: 1.5 }
                      : { fillColor: "transparent", fillOpacity: 0, color: selected ? "rgba(255,255,255,0.15)" : "rgba(255,255,255,0.35)", weight: 0.8 }
                  );
                  setHover(null);
                },
                click() {
                  if (prov) onSelect(selected === prov ? null : prov);
                },
              });
            }}
          />
        )}

        {/* ── ADM1: Province choropleth ─────────────────────────────────────── */}
        <GeoJSON
          key={adm1Key}
          data={adm1Geo}
          style={(f: any) => getProvinceStyle(f?.properties?.key ?? "", selected, provMap)}
          onEachFeature={(f: any, layer: L.Path) => {
            const key = f.properties.key as string;
            layer.on({
              mouseover(e: any) {
                const pos = moveHover(e);
                if (!pos) return;
                layer.setStyle({
                  fillColor:   key === selected ? "#244A30" : "#4A9D6F",
                  fillOpacity: 0.92,
                  color:       key === selected ? "#FFD700" : "#fff",
                  weight:      key === selected ? 3.5 : 2.5,
                });
                layer.bringToFront();
                // Don't show province tooltip if we're inside a district hover
                setHover({ ...pos, key });
              },
              mousemove(e: any) {
                const pos = moveHover(e);
                if (pos) setHover(h => h && !h.isDistrict ? { ...h, ...pos } : h);
              },
              mouseout() {
                layer.setStyle(getProvinceStyle(key, selected, provMap));
                setHover(null);
              },
              click() { onSelect(selected === key ? null : key); },
            });
          }}
        />

        {/* ── ADM0: Country outline on top — clean crisp border ─────────────── */}
        {adm0Geo && (
          <GeoJSON
            key={`adm0-${geoReady}`}
            data={adm0Geo}
            style={{
              fillColor:   "transparent",
              fillOpacity: 0,
              color:       "#1A3A26",
              weight:      2.5,
              dashArray:   undefined,
            }}
            interactive={false}
          />
        )}

        {/* ── Province labels ───────────────────────────────────────────────── */}
        <ProvinceLabels provinces={provinces} selected={selected} />

        <MapController selectedKey={selected} />
      </MapContainer>

      {/* ── Custom hover tooltip ──────────────────────────────────────────── */}
      {hover && (() => {
        const containerW = containerRef.current?.clientWidth ?? 600;
        const tooltipW   = 210;
        const left = Math.min(hover.x + 18, containerW - tooltipW - 8);
        const top  = hover.y - 16;
        const prov = provMap[hover.key];
        const borderColor = hover.isDistrict
          ? "#C04F4F"
          : provinceColor(prov?.specific_count ?? 0);

        return (
          <div style={{
            position:      "absolute",
            left, top,
            pointerEvents: "none",
            zIndex:        1000,
            background:    "#18181A",
            color:         "#fff",
            borderRadius:  10,
            padding:       "11px 15px",
            minWidth:      tooltipW,
            boxShadow:     "0 8px 32px rgba(0,0,0,0.5)",
            borderLeft:    `4px solid ${borderColor}`,
          }}>
            {hover.isDistrict ? (
              <>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 3 }}>
                  {hover.districtName} district
                </div>
                <div style={{ fontSize: 12, color: "#aaa" }}>
                  {hover.districtCount === 0
                    ? "No district-specific studies"
                    : `${hover.districtCount} study${hover.districtCount !== 1 ? "s" : ""}`}
                </div>
                {hover.districtCount === 0 && (
                  <div style={{ marginTop: 5, fontSize: 11, color: "#FF8080", fontWeight: 600 }}>
                    ⚠ District-level data gap
                  </div>
                )}
              </>
            ) : (
              <>
                <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 3 }}>
                  {prov?.name ?? hover.key}
                </div>
                <div style={{ fontSize: 12, color: "#bbb", marginBottom: 2 }}>
                  {(prov?.specific_count ?? 0) === 0
                    ? "No province-specific studies"
                    : `${prov!.specific_count} specific study${prov!.specific_count !== 1 ? "s" : ""}`}
                </div>
                <div style={{ fontSize: 12, color: "#888" }}>+{nationalCount} national</div>
                {(prov?.specific_count ?? 0) === 0 && (
                  <div style={{ marginTop: 5, fontSize: 11, color: "#FF8080", fontWeight: 600 }}>
                    ⚠ Data gap — no targeted research
                  </div>
                )}
                <div style={{ marginTop: 7, fontSize: 11, color: "#666" }}>
                  Click to {selected === hover.key ? "deselect" : "zoom in & explore districts"}
                </div>
              </>
            )}
          </div>
        );
      })()}

      {/* ── Loading badge ─────────────────────────────────────────────────── */}
      {!geoReady && (
        <div style={{
          position:       "absolute",
          bottom:         12,
          left:           "50%",
          transform:      "translateX(-50%)",
          background:     "rgba(26,26,24,0.82)",
          color:          "#ccc",
          fontSize:       11,
          padding:        "5px 14px",
          borderRadius:   20,
          zIndex:         900,
          backdropFilter: "blur(4px)",
          display:        "flex",
          alignItems:     "center",
          gap:            8,
        }}>
          <span style={{
            display:      "inline-block",
            width:        10, height: 10,
            borderRadius: "50%",
            border:       "2px solid #aaa",
            borderTopColor: "transparent",
            animation:    "spin 0.8s linear infinite",
          }} />
          Loading official boundaries…
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}
    </div>
  );
}
