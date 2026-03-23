# Shakisha — AI-Powered Gender Data Discovery Platform

> **Shakisha** (Kinyarwanda: _"to search / to discover"_) — Find the gender data you need, understand it instantly, and turn it into advocacy.

**GDRD Gender Data Resource Discovery Hackathon 2026**
`team-shakisha-gdrd-2026` · March 19–20, 2026 · Kigali, Rwanda

---

## Live Demo

| Interface                 | URL                                            | Status       |
| ------------------------- | ---------------------------------------------- | ------------ |
| **Frontend** (Next.js)    | `https://shakisha.vercel.app`                  | ⏳ Deploying |
| **Backend API** (FastAPI) | `https://shakisha-api.onrender.com`            | ⏳ Deploying |
| **API Health check**      | `https://shakisha-api.onrender.com/api/health` | ⏳ Deploying |

> Both services deploy automatically from the `main` branch on every push.

---

## Team

| Name                  | Role                    |
| --------------------- | ----------------------- |
| Muhigiri Ashuza Albin | Developer & AI Engineer |
| Ingabire Vanessa      | Researcher & UX         |

---

## Project Objective

Civil Society Organizations (CSOs) and policy actors in Rwanda lose critical advocacy time searching for gender data across fragmented, PDF-heavy sources. **Shakisha** solves this by combining intelligent discovery with AI-generated policy output — so a CSO officer can go from a question to a ready-to-use advocacy brief in minutes, not hours.

**One platform. Five steps:**

- **Search** — Type a plain-language question in any form (English or French)
- **Discover** — Get ranked results over 1,362 Rwanda gender studies across 6 domains
- **Validate** — Check data quality, source availability, and metadata completeness
- **Act** — Generate AI-powered advocacy briefs from any dataset, ready for policymakers
- **Grow** — Live data pipeline crawls NISR and pulls from OpenAlex + Tavily to keep the catalog current

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│         SHAKISHA — NEXT.JS FRONTEND                                     │
│         Deployed: https://shakisha.vercel.app                           │
│                                                                         │
│  Home · Discovery · Analytics · Data Quality · Brief · Pipeline         │
│  (responsive, mobile-friendly, Leaflet map, Recharts analytics)         │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │  /api/* proxied to FastAPI
┌───────────────────────────▼─────────────────────────────────────────────┐
│         SHAKISHA — FASTAPI BACKEND                                      │
│         Deployed: https://shakisha-api.onrender.com                     │
│                                                                         │
│  /api/search   /api/brief    /api/quality   /api/pipeline               │
│  /api/stats    /api/domains  /api/geographic /api/districts             │
│                                      [coming soon]                      │
│  /api/crawl    — Tavily real-time on-demand crawl                       │
│  /api/ask      — Tavily source Q&A chat endpoint                        │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────────┐
│                    PYTHON CORE MODULES (src/)                           │
│                                                                         │
│  loaders · filters · quality_badges · ai (Claude API) · domains         │
│  link_checker · brief_store                                             │
└───────────────────────────┬─────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────────┐
│                       DATA LAYER                                        │
│                                                                         │
│  data/full/studies.csv           1,362 gender studies                   │
│  data/full/study_resources.csv   2,205 resources                        │
│  data/full/quality_report.csv    per-study quality assessment           │
│                                                                         │
│  Sources:  NISR Microdata (base) · NISR Crawler · OpenAlex · Tavily*    │
│            (* Tavily real-time crawl — coming soon)                     │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Running Shakisha Locally

**Requirements:** Python 3.10+, Node.js 18+

### Step 1 — Clone the repository

```bash
git clone https://github.com/Ashuza11/shakisha-grb-Resource-Discovery-challenge-2026.git
cd shakisha-grb-Resource-Discovery-challenge-2026/Shakisha-app
```

### Step 2 — Set up the Python backend

```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows PowerShell

pip install -r requirements.txt
```

### Step 3 — Configure API keys

Copy the environment template and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Required for AI features (brief generation, AI search, relevance explanations)
ANTHROPIC_API_KEY=sk-ant-...

# Required for Tavily-powered real-time crawling and source Q&A (coming soon)
TAVILY_API_KEY=tvly-...
```

> The app works without any API key — discovery, quality, analytics, and pipeline pages are fully functional.

| Feature                    | No keys             | Anthropic only                 | Anthropic + Tavily |
| -------------------------- | ------------------- | ------------------------------ | ------------------ |
| Search (keyword + filters) | ✅ Full             | ✅ + AI query interpretation   | ✅                 |
| Discovery page             | ✅ Full             | ✅ + per-study AI explanations | ✅                 |
| Analytics & Map            | ✅ Full             | ✅                             | ✅                 |
| Data Quality               | ✅ Full             | ✅                             | ✅                 |
| Advocacy Brief Generator   | ❌ Friendly message | ✅ Full                        | ✅                 |
| On-demand real-time crawl  | ❌                  | ❌                             | ✅ Coming soon     |
| Source Q&A chat            | ❌                  | ❌                             | ✅ Coming soon     |

### Step 4 — Start the backend

```bash
# From Shakisha-app/ with the venv activated:
uvicorn api.main:app --reload --port 8000
```

Verify it loaded:

```bash
curl http://127.0.0.1:8000/api/health
# → {"status":"ok","data_loaded":true,"study_count":1362}
```

### Step 5 — Start the frontend

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**.

---

### Alternative — Streamlit only (no Node.js required)

```bash
cd Shakisha-app
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # optional
streamlit run app.py
# Opens at http://localhost:8501
```

---

## Pages Reference

| Page             | URL          | What it does                                                                                   |
| ---------------- | ------------ | ---------------------------------------------------------------------------------------------- |
| **Home**         | `/`          | Hero with animated tagline, live catalog stats, domain coverage, how-it-works                  |
| **Discovery**    | `/discovery` | Natural language search, 6 domain filters, year/district/resource-type filters, quality badges |
| **Analytics**    | `/analytics` | Interactive Rwanda map, study trends by year, quality distribution, org breakdown              |
| **Data Quality** | `/quality`   | Per-study quality badges, missing field analysis, source URL checker                           |
| **Brief**        | `/brief`     | Select any study → generate a structured advocacy brief → download as .txt                     |
| **Pipeline**     | `/pipeline`  | Source status, study counts per source, last crawl time, pipeline health                       |

---

## Catalog Coverage

| Dimension            | Detail                                                                |
| -------------------- | --------------------------------------------------------------------- |
| **Total studies**    | 1,362                                                                 |
| **Total resources**  | 2,205                                                                 |
| **Year range**       | 1991 – 2026                                                           |
| **Geographic focus** | Rwanda — 100% (all studies verified for Rwanda relevance)             |
| **Domains**          | 6 active: Labour, Agriculture, Health, Household, Finance, Population |

### Studies by domain

| Domain                 | Studies | Key data sources                                |
| ---------------------- | ------- | ----------------------------------------------- |
| Gender (cross-cutting) | 320     | NISR, OpenAlex gender policy papers             |
| Agriculture            | 264     | NISR Agricultural Surveys, land rights research |
| Health                 | 255     | DHS surveys, maternal health studies            |
| Labour                 | 169     | NISR Labour Force Survey, enterprise censuses   |
| Population             | 121     | NISR Census, migration & education studies      |
| Household              | 118     | EICV surveys (EICV1–7), poverty analysis        |
| Finance                | 42      | FinScope surveys, microfinance research         |
| NISR Official Surveys  | 73      | Base catalog — microdata with full metadata     |

### Sources

| Source                     | Description                                                    | Study count |
| -------------------------- | -------------------------------------------------------------- | ----------- |
| **NISR Microdata Catalog** | Official Rwanda statistical surveys — microdata, full metadata | 73          |
| **OpenAlex**               | Open-access academic research papers (peer-reviewed)           | 1,289       |
| **Tavily** _(coming soon)_ | Real-time on-demand crawl of web, reports, PDFs                | —           |

---

## Data Pipeline

The pipeline runs on-demand. Each adapter only adds new data — existing studies are never overwritten. A backup of `data/full/` is created automatically before every merge.

```bash
cd Shakisha-app
source .venv/bin/activate

# 1. Crawl new studies from NISR portal (skips already-harvested IDs)
python3 data_pipeline/nisr_crawler.py

# 2. Fetch Rwanda gender research papers from OpenAlex (all 6 domains)
python3 data_pipeline/openalex_adapter.py

# 3. Merge all sources, deduplicate, write to data/full/
python3 data_pipeline/build_dataset.py

# Restart the backend to serve the updated catalog
```

### Deduplication guarantees

Three independent layers prevent duplicates:

1. **NISR crawler** — loads all existing `study_id` values from `data/full/studies.csv` at startup; skips any study already cataloged.
2. **OpenAlex adapter** — pre-loads existing IDs from `data/full/` before fetching; uses a `seen_ids` set to prevent the same paper appearing from multiple queries in one run.
3. **`build_dataset.py`** — final merge safety net; drops any pipeline study whose ID already exists in the base NISR catalog before writing.

### Rwanda relevance filter

Every OpenAlex study must pass a three-tier Rwanda focus check before being added:

1. "Rwanda" appears in the study title → strong signal, always keep
2. A Rwanda place name (Kigali, Musanze, Huye, Rubavu, etc.) appears in the title → keep
3. "Rwanda" appears in the **opening 300 characters** of the abstract → Rwanda is the stated subject

Studies that only mention Rwanda as one of many countries in a multi-country analysis are excluded.

---

## Tavily Integration _(Coming Soon)_

Shakisha integrates [Tavily](https://docs.tavily.com/welcome) — a search API purpose-built for AI applications — to add two high-impact features:

### Feature 1 — On-Demand Real-Time Crawl

The current pipeline runs manually. With Tavily, maintainers and power users will be able to trigger a live search directly from the **Pipeline page**:

```
User types: "Rwanda women entrepreneurship 2025 new report"
        ↓
Tavily searches the live web (gov sites, UN, World Bank, NISR, journals)
        ↓
Results are normalized to the Shakisha study schema
        ↓
Deduplicated against the existing catalog
        ↓
New studies appear in the catalog within seconds
```

**API endpoint (planned):** `POST /api/crawl`

```json
{
  "query": "Rwanda women entrepreneurship 2025",
  "domain": "labour",
  "max_results": 10
}
```

### Feature 2 — Source Q&A Chat ("Ask about this source")

Every source card on the **Discovery page** will have an **"Ask"** button. Clicking it opens a chat panel where the user can ask specific questions about that study's content, and get answers grounded in the actual document — powered by Tavily's document extraction and Claude's reasoning:

```
User finds: "Rwanda FinScope 2020 — Financial Inclusion in Rwanda"
User clicks: "Ask about this source"
User types:  "What percentage of rural women have a mobile money account?"
        ↓
Tavily fetches and extracts the full document content
        ↓
Claude answers with a cited quote from the actual report
        ↓
Response: "According to FinScope 2020, 42% of rural women use mobile money,
           up from 28% in 2016 (FinScope Rwanda 2020, p. 34)."
```

**API endpoint (planned):** `POST /api/ask`

```json
{
  "study_id": "36",
  "question": "What percentage of rural women have a mobile money account?",
  "source_url": "https://microdata.statistics.gov.rw/..."
}
```

---

## Key Workflows

### Workflow 1 — Intelligent Discovery

```
User types: "women's labour force participation in rural Rwanda after 2018"
     ↓
AI interprets the query (Claude API) → extracts keywords + year range
     ↓
Filters the 1,362-study catalog by keyword, domain, year, district, resource type
     ↓
Returns: ranked result cards with title, year, org, quality badge, source links
```

### Workflow 2 — Advocacy Brief Generation

```
User selects a study from Discovery
     ↓
Clicks "Generate Advocacy Brief"
     ↓
AI reads: study title, abstract, year, organization, resources, quality flags
     ↓
Outputs structured brief:
  - Policy context (Rwanda Vision 2050, NST1, National Gender Policy)
  - Key findings (3 bullet points)
  - Data gaps and caveats
  - Recommended advocacy action
  - Proper citation (APA format)
     ↓
User downloads .txt brief or exports PDF (Streamlit)
```

### Workflow 3 — Geographic Coverage Analysis

```
User opens Analytics page
     ↓
Selects a domain (e.g. "Health")
     ↓
Interactive Rwanda map updates choropleth colours:
  - Deep green = province well-covered by this domain
  - Warm sand  = data gap (no province-specific studies)
     ↓
Click a province → zooms in, shows all 30 districts
Hover any district → tooltip with study count and gap warning
```

### Workflow 4 — Source Q&A _(coming soon)_

```
User finds a study
     ↓
Clicks "Ask about this source"
     ↓
Types a specific question about the data
     ↓
Receives a cited, grounded answer from the actual document
```

---

## Deployment

### Frontend — Vercel

The Next.js frontend deploys to Vercel automatically from `main`:

```
Production URL: https://shakisha.vercel.app
Framework:      Next.js (auto-detected)
Build command:  npm run build
Output dir:     .next
Env vars:       NEXT_PUBLIC_API_URL=https://shakisha-api.onrender.com
```

### Backend — Render

The FastAPI backend deploys to Render as a Web Service:

```
Production URL: https://shakisha-api.onrender.com
Runtime:        Python 3.11
Start command:  uvicorn api.main:app --host 0.0.0.0 --port $PORT
Build command:  pip install -r requirements.txt
Env vars:       ANTHROPIC_API_KEY=<secret>
                TAVILY_API_KEY=<secret>
```

### Environment variables summary

| Variable              | Required for                                    | Where to get                                           |
| --------------------- | ----------------------------------------------- | ------------------------------------------------------ |
| `ANTHROPIC_API_KEY`   | AI search, briefs, explanations                 | [console.anthropic.com](https://console.anthropic.com) |
| `TAVILY_API_KEY`      | Real-time crawl, source Q&A                     | [app.tavily.com](https://app.tavily.com)               |
| `NEXT_PUBLIC_API_URL` | Frontend → backend connection (production only) | Set to your Render URL                                 |

---

## Project Structure

```
shakisha-grb-Resource-Discovery-challenge-2026/
├── README.md
└── Shakisha-app/
    ├── app.py                           # Streamlit entry point
    ├── requirements.txt                 # Python deps (shared by API + Streamlit)
    ├── .env.example                     # API key template
    ├── api/
    │   └── main.py                      # FastAPI — all /api/* endpoints
    ├── frontend/                        # Next.js 16 (React 19, TypeScript)
    │   ├── app/
    │   │   ├── layout.tsx               # Root layout: nav, Imigongo band, footer
    │   │   ├── page.tsx                 # Home page
    │   │   ├── discovery/page.tsx       # Search + filters
    │   │   ├── analytics/page.tsx       # Charts, interactive Rwanda map
    │   │   ├── quality/page.tsx         # Quality dashboard
    │   │   ├── brief/page.tsx           # Advocacy brief generator
    │   │   ├── pipeline/page.tsx        # Pipeline status
    │   │   ├── components/
    │   │   │   ├── Nav.tsx              # Responsive nav (hamburger on mobile)
    │   │   │   ├── RwandaMap.tsx        # Choropleth map wrapper
    │   │   │   ├── RwandaLeafletInner.tsx # Leaflet map (SSR-disabled)
    │   │   │   └── rwandaGeoData.ts     # Province/district coordinates
    │   │   ├── lib/api.ts               # Typed API client
    │   │   └── globals.css              # Design tokens + responsive utilities
    │   ├── public/
    │   │   ├── rwanda-adm0.geojson      # Country outline (geoBoundaries official)
    │   │   ├── rwanda-adm1.geojson      # Province boundaries (official)
    │   │   └── rwanda-adm2.geojson      # District boundaries — all 30 districts
    │   ├── next.config.ts               # Proxies /api/* → FastAPI :8000
    │   └── package.json
    ├── pages/                           # Streamlit pages (alternative interface)
    │   ├── 0_Home.py
    │   ├── 1_Discovery.py
    │   ├── 2_Dashboard.py
    │   ├── 3_Data_Quality.py
    │   ├── 4_Advocacy_Brief.py
    │   └── 5_Pipeline.py
    ├── src/                             # Shared Python core
    │   ├── loaders.py                   # CSV loading and validation
    │   ├── filters.py                   # Study and resource filtering
    │   ├── quality_badges.py            # Quality flag parsing
    │   ├── link_checker.py              # HTTP URL validation
    │   ├── ai.py                        # Claude API (interpret, explain, brief)
    │   ├── domains.py                   # Domain registry (6 active domains)
    │   └── brief_store.py              # Persist and retrieve generated briefs
    ├── data_pipeline/
    │   ├── nisr_crawler.py              # Crawl NISR portal for new studies
    │   │                                  # 41 gender keywords · 70 domain keywords
    │   │                                  # checkpoint-resumable · dedup-safe
    │   ├── openalex_adapter.py          # Fetch Rwanda papers from OpenAlex
    │   │                                  # 21 queries across all 6 domains
    │   │                                  # pre-loads existing IDs to skip duplicates
    │   └── build_dataset.py             # Merge all sources → data/full/
    │                                      # 3-layer deduplication · auto-backup
    ├── data/
    │   ├── full/                        # Live catalog
    │   │   ├── studies.csv              # 1,362 studies
    │   │   ├── study_resources.csv      # 2,205 resources
    │   │   └── quality_report.csv
    │   ├── pipeline_sources/
    │   │   ├── nisr_crawl/              # Output from nisr_crawler.py
    │   │   └── openalex/                # Output from openalex_adapter.py
    │   └── sample/                      # 3-study quick-start dataset
    └── tests/
        ├── test_loaders.py
        ├── test_filters.py
        ├── test_quality_badges.py
        └── test_ai.py                   # Mocked Claude API tests
```

---

## Running the Test Suite

All tests use mocks — no API key required.

```bash
cd Shakisha-app
source .venv/bin/activate
python -m pytest tests/ -v
# → 11 passed
```

---

## Design System

Shakisha uses a custom Rwanda-inspired design system:

| Token         | Value     | Usage                                 |
| ------------- | --------- | ------------------------------------- |
| `--rw-green`  | `#20603D` | Primary brand, Rwanda flag green      |
| `--coral`     | `#C04F4F` | CTAs, data gap warnings               |
| `--rw-yellow` | `#E8B800` | Warnings, quality flags               |
| `--cream`     | `#FAF5EF` | Page background (warm, not cold grey) |
| `--charcoal`  | `#1A1A1A` | Body text                             |

Typography: **Playfair Display** (headings) · **Plus Jakarta Sans** (body) · **JetBrains Mono** (code/citations)

The Imigongo geometric pattern (traditional Rwandan art) is used as a section divider throughout the app.

---

## Demo Scenario

**Context:** A CSO officer is preparing a brief for the Ministry of Gender on women's economic participation gaps.

**Step 1 — Search**

> Types: _"surveys on women economic participation Rwanda 2020"_
> Shakisha returns: FinScope 2020, Labour Force Survey, EICV5 — with quality badges

**Step 2 — Evaluate**

> Sees: FinScope 2020 has complete metadata, quality: good (0 missing fields)
> Analytics map shows Eastern Province has the most province-specific finance studies (19)

**Step 3 — Ask** _(coming soon)_

> Clicks "Ask about this source" on FinScope 2020
> Types: "What is the mobile money adoption gap between men and women?"
> Gets: cited answer from the actual FinScope 2020 report within seconds

**Step 4 — Brief**

> Clicks "Generate Advocacy Brief"
> Receives in ~10 seconds:
>
> - _Policy context:_ "Rwanda's Vision 2050 targets financial inclusion for 90% of adults..."
> - _Key findings:_ 42% rural women use mobile money vs 61% rural men
> - _Data gap:_ No district-level disaggregation for women's finance post-2020
> - _Recommendation:_ Commission FinScope 2024 with district-level gender module
> - _Citation:_ NISR, FinScope Rwanda 2020. Available at: [URL]

**Step 5 — Use**

> Downloads brief as .txt → pastes into Ministry proposal → done in under 5 minutes

---

## Scoring Alignment

| Criterion            | Weight | How Shakisha Addresses It                                                                                                                                                                     |
| -------------------- | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Coverage**         | 30%    | 1,362 studies across 6 domains; 21 OpenAlex queries spanning all domains; NISR crawler with 111 gender/domain keywords; Tavily real-time crawl _(coming soon)_ adds live coverage on demand   |
| **Usability**        | 25%    | Natural language search; interactive Leaflet choropleth map locked to Rwanda; domain-aware province coloring; responsive Next.js UI; quality badge on every result                            |
| **Trustworthiness**  | 20%    | Three-layer deduplication; Rwanda relevance verified per study; quality badge system; source URL checker; `ingested_at` + `source_adapter` provenance columns; auto-backup before every merge |
| **Maintainability**  | 15%    | Clean `src/` core; separate `data_pipeline/` layer; 11 passing tests; `.env.example`; Render + Vercel deployment configs; documented pipeline commands                                        |
| **Policy Relevance** | 10%    | Advocacy Brief grounded in Rwanda Vision 2050, NST1, and National Gender Policy; Source Q&A _(coming soon)_ lets CSOs interrogate individual reports without reading PDFs                     |

---

## API Reference

All endpoints are served from `http://localhost:8000` (local) or `https://shakisha-api.onrender.com` (production).

| Method | Endpoint          | Description                                                                  |
| ------ | ----------------- | ---------------------------------------------------------------------------- |
| `GET`  | `/api/health`     | Health check — confirms data is loaded                                       |
| `GET`  | `/api/stats`      | Catalog summary (study count, resource count, domains)                       |
| `GET`  | `/api/domains`    | All 6 domains with name, emoji, study count, status                          |
| `POST` | `/api/search`     | Search studies — body: `{query, domain, sort_order, use_ai, ...}`            |
| `GET`  | `/api/quality`    | Full quality report for all studies                                          |
| `GET`  | `/api/geographic` | Province + district study counts, geo resolution breakdown                   |
| `GET`  | `/api/districts`  | All 30 districts with province and study count                               |
| `GET`  | `/api/pipeline`   | Pipeline source status and study counts                                      |
| `POST` | `/api/brief`      | Generate advocacy brief — body: `{study_id}`                                 |
| `POST` | `/api/crawl`      | _(coming soon)_ Tavily real-time search and ingest                           |
| `POST` | `/api/ask`        | _(coming soon)_ Tavily source Q&A — body: `{study_id, question, source_url}` |

---

_Built at the GDRD Gender Data Resource Discovery Hackathon — March 19–20, 2026, Kigali, Rwanda._
