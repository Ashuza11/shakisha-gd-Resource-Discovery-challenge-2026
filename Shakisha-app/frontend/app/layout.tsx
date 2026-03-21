import type { Metadata } from "next";
import "./globals.css";
import Nav from "./components/Nav";

export const metadata: Metadata = {
  title: "Shakisha — Gender Data Discovery",
  description:
    "AI-powered gender data discovery for Rwanda. Search 2,740 NISR studies, evaluate quality, and generate advocacy briefs instantly.",
};

// ── Imigongo decorative top band ────────────────────────────────────────────
function ImigongoBand() {
  return (
    <div aria-hidden="true" style={{ width: "100%", height: 20, overflow: "hidden", lineHeight: 0, flexShrink: 0 }}>
      <svg
        width="100%"
        height="20"
        viewBox="0 0 800 20"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <pattern id="imi-top" x="0" y="0" width="40" height="20" patternUnits="userSpaceOnUse">
            <rect width="40" height="20" fill="#1A1A1A" />
            <polygon points="0,0 20,10 40,0" fill="#C04F4F" />
            <polygon points="0,20 20,10 40,20" fill="#8B5E3C" opacity="0.85" />
            <polygon points="8,0 20,6 32,0" fill="#FAF5EF" opacity="0.12" />
          </pattern>
        </defs>
        <rect width="100%" height="20" fill="url(#imi-top)" />
      </svg>
    </div>
  );
}

// ── Root layout ──────────────────────────────────────────────────────────────
export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col">
        <ImigongoBand />
        <Nav />
        <main className="flex-1">{children}</main>

        {/* ── Footer ────────────────────────────────────────────────────── */}
        <footer style={{ background: "var(--charcoal)", color: "var(--cream-dark)", padding: "48px 24px 24px" }}>
          <div style={{ maxWidth: 1200, margin: "0 auto" }}>

            {/* Top row */}
            <div className="footer-grid">

              {/* Brand column */}
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                  <svg width="22" height="34" viewBox="0 0 32 50" fill="none">
                    <circle cx="16" cy="13" r="11" stroke="#C04F4F" strokeWidth="2" fill="none" />
                    <circle cx="11" cy="8"  r="1.8" fill="#C04F4F" />
                    <circle cx="21" cy="8"  r="1.8" fill="#C04F4F" />
                    <circle cx="11" cy="18" r="1.8" fill="#C04F4F" />
                    <circle cx="21" cy="18" r="1.8" fill="#C04F4F" />
                    <line x1="16" y1="24" x2="16" y2="40" stroke="#C04F4F" strokeWidth="2" strokeLinecap="round" />
                    <line x1="9"  y1="34" x2="23" y2="34" stroke="#C04F4F" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                  <div>
                    <div style={{ fontFamily: "'Playfair Display', Georgia, serif", fontWeight: 700, fontSize: 18, letterSpacing: "0.08em", color: "var(--cream)" }}>
                      SHAKISHA
                    </div>
                    <div style={{ fontSize: 10, color: "#8A6A5A", letterSpacing: "0.06em" }}>
                      Gender Data Discovery
                    </div>
                  </div>
                </div>
                <p style={{ fontSize: 13, color: "#8A6A5A", lineHeight: 1.7, maxWidth: 300 }}>
                  AI-powered discovery over Rwanda&rsquo;s NISR gender microdata catalog. Search in plain language, evaluate data quality, and generate advocacy briefs.
                </p>
                <p style={{ fontSize: 11, color: "#5A4A44", marginTop: 14, lineHeight: 1.5 }}>
                  GDRD Gender Data Resource Discovery Hackathon<br />
                  March 19–20, 2026 &middot; Kigali, Rwanda
                </p>
              </div>

              {/* Data partner */}
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.12em", color: "#5A4A44", textTransform: "uppercase", marginBottom: 18 }}>
                  Data Partner
                </div>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src="/parteners/nisr.jpg"
                  alt="National Institute of Statistics of Rwanda"
                  style={{ height: 44, objectFit: "contain", objectPosition: "left", marginBottom: 12 }}
                />
                <p style={{ fontSize: 11, color: "#5A4A44", marginTop: 12, lineHeight: 1.6 }}>
                  The complete NISR microdata catalog — 2,740 studies across labour, agriculture, health, household, finance and population.
                </p>
              </div>

              {/* Organized by */}
              <div>
                <div style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.12em", color: "#5A4A44", textTransform: "uppercase", marginBottom: 18 }}>
                  Organized by
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                  {/* German Corporation — funder, shown first and larger */}
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src="/parteners/German-coporation.png"
                    alt="German Corporation for International Cooperation"
                    style={{ height: 52, objectFit: "contain", objectPosition: "left" }}
                  />
                  {/* GIZ — implementing agency */}
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src="/parteners/GIZ.svg"
                    alt="GIZ — Deutsche Gesellschaft für Internationale Zusammenarbeit"
                    style={{ height: 36, objectFit: "contain", objectPosition: "left" }}
                  />
                </div>
              </div>
            </div>

            {/* Bottom bar */}
            <div
              style={{
                borderTop: "1px solid rgba(255,255,255,0.07)",
                marginTop: 40,
                paddingTop: 20,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                flexWrap: "wrap",
                gap: 12,
              }}
            >
              <span style={{ fontSize: 12, color: "#5A4A44" }}>
                &copy; 2026 Shakisha &middot; Data: National Institute of Statistics of Rwanda
              </span>
              <a
                href="https://microdata.statistics.gov.rw/"
                target="_blank"
                rel="noopener noreferrer"
                style={{ fontSize: 12, color: "var(--coral)", textDecoration: "none" }}
              >
                microdata.statistics.gov.rw ↗
              </a>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
