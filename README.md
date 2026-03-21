# Shakisha — AI-Powered Gender Data Discovery Platform

> **Shakisha** (Kinyarwanda: _"to search / to discover"_) — Find the gender data you need, understand it instantly, and turn it into advocacy.

**GDRD Gender Data Resource Discovery Hackathon 2026**
`team-shakisha-gdrd-2026` · March 19–20, 2026 · Kigali, Rwanda

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

- **Search** — Type a plain-language question in any form
- **Discover** — Get ranked results over the full NISR gender data catalog + academic papers
- **Validate** — Check data quality, source availability, and metadata completeness
- **Act** — Generate AI-powered advocacy briefs from any dataset, ready for policymakers
- **Grow** — Live data pipeline crawls NISR and pulls from OpenAlex to keep the catalog current

---

## Architecture

Shakisha ships as **two interfaces on a shared Python core**:

```
┌─────────────────────────────────────────────────────────────────────────┐
│              SHAKISHA — NEXT.JS FRONTEND (port 3000)                    │
│                                                                         │
│  Home · Discovery · Analytics · Data Quality · Brief · Pipeline         │
│  (modern web UI, fully responsive, mobile-friendly)                     │
└───────────────────────────┬─────────────────────────────────────────────┘
                            | /* proxied to FastAPI
┌───────────────────────────▼─────────────────────────────────────────────┐
│              SHAKISHA — FASTAPI BACKEND (port 8000)                     │
│                                                                         │
│  /api/search  /api/brief  /api/quality  /api/pipeline  /api/districts   │
└───────────────────────────┬─────────────────────────────────────────────┘
                            |
┌───────────────────────────▼─────────────────────────────────────────────┐
│                    PYTHON CORE MODULES (src/)                           │
│                                                                         │
│  loaders · filters · quality_badges · ai (Claude API) · domains         |
│  link_checker · brief_store                                             │
└───────────────────────────┬─────────────────────────────────────────────┘
                            |
┌───────────────────────────▼─────────────────────────────────────────────┐
│              SHAKISHA — STREAMLIT APP (port 8501)                       │
│                                                                         │
│  Alternative interface — same src/ modules, same data                   │
│  0_Home · 1_Discovery · 2_Dashboard · 3_Data_Quality                    |
│  4_Advocacy_Brief · 5_Pipeline                                          │
└─────────────────────────────────────────────────────────────────────────┘
                            |
┌───────────────────────────▼─────────────────────────────────────────────┐
│                       DATA LAYER                                        │
│                                                                         │
│  data/full/studies.csv          (~2,740 NISR studies)                   │
│  data/full/study_resources.csv  (~4,384 resources)                      │
│  data/full/quality_report.csv                                           │
│                                                                         │
│  Sources:  NISR Microdata (base) · NISR Crawler · OpenAlex papers       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Running Shakisha

There are **two ways** to run the app. The Next.js + FastAPI stack is the primary interface. The Streamlit app is the alternative if you prefer a simpler setup.

### Option A — Full Stack (Next.js + FastAPI) — recommended

**Requirements:** Python 3.10+, Node.js 18+

#### Step 1. Clone the repo

```bash
git clone https://github.com/Ashuza11/shakisha-grb-Resource-Discovery-challenge-2026.git
cd shakisha-grb-Resource-Discovery-challenge-2026/Shakisha-app
```

#### Step 2. Set up the Python backend

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows PowerShell

# Install Python dependencies
pip install -r requirements.txt
```

#### Step 3. (Optional) Set the Anthropic API key

AI features (brief generation, AI-powered search, relevance explanations) require an Anthropic API key. **The app works without it** — discovery, quality, analytics, and pipeline pages are fully functional.

```bash
# Option A: environment variable
export ANTHROPIC_API_KEY=sk-ant-...      # Linux / macOS
# $env:ANTHROPIC_API_KEY="sk-ant-..."   # Windows PowerShell

# Option B: .env file (copy the example and fill it in)
cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

If the key is missing, all AI-dependent features show a clear, friendly message instead of crashing.

#### Step 4. Start the FastAPI backend

```bash
# From Shakisha-app/ with the venv activated:
uvicorn api.main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`. You can verify it loaded correctly:

```bash
curl http://127.0.0.1:8000/api/health
# → {"status":"ok","data_loaded":true,...}
```

#### Step 5. Start the Next.js frontend

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000** in your browser.

---

### Option B — Streamlit only (simpler, no Node.js required)

```bash
cd shakisha-grb-Resource-Discovery-challenge-2026/Shakisha-app

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

# Optional — only needed for AI features
export ANTHROPIC_API_KEY=sk-ant-...

streamlit run app.py
```

Opens at **http://localhost:8501**.

---

## What Works Without an API Key

| Feature                    | No API key             | With API key                            |
| -------------------------- | ---------------------- | --------------------------------------- |
| Search (keyword + filters) | Full                   | Full + AI query interpretation          |
| Discovery page             | Full                   | Full + per-study relevance explanations |
| Analytics                  | Full                   | Full                                    |
| Data Quality               | Full                   | Full                                    |
| Pipeline status            | Full                   | Full                                    |
| Advocacy Brief Generator   | Shows friendly message | Generates AI brief                      |

---

## Next.js App — Pages

| Page         | URL          | Description                                                                             |
| ------------ | ------------ | --------------------------------------------------------------------------------------- |
| Home         | `/`          | Hero with animated tagline, NISR preview cards, domain coverage, how-it-works           |
| Discovery    | `/discovery` | Natural language search, domain chips, advanced filters (district, year, resource type) |
| Analytics    | `/analytics` | Study count by year, resource type breakdown, coverage gap chart                        |
| Data Quality | `/quality`   | Quality badges, missing field breakdown, source URL checker                             |
| Brief        | `/brief`     | Select a study → generate a structured advocacy brief, download as .txt                 |
| Pipeline     | `/pipeline`  | Data pipeline source status, study counts per source, recently ingested studies         |

---

## Key Workflows

### Workflow 1 — Intelligent Discovery

```
User types: "women's labour force participation in rural Rwanda after 2018"
     ↓
AI interprets the query (Claude API) → extracts keywords + year range
     ↓
Filters the 2,740-study catalog by keyword, domain, year, district, resource type
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
  - Policy context (referencing Vision 2050, NST1, National Gender Policy)
  - Key findings (3 bullet points)
  - Data gaps and caveats
  - Recommended advocacy action
  - Proper citation
     ↓
User downloads .txt brief or exports PDF (Streamlit)
```

### Workflow 3 — Pipeline Status

```
User opens Pipeline page
     ↓
Sees: all data sources (NISR base, NISR crawler, OpenAlex), their study counts, last run
     ↓
Maintainer can run adapters on-demand to refresh the catalog
```

---

## Project Structure

```
shakisha-grb-Resource-Discovery-challenge-2026/
├── README.md
└── Shakisha-app/
    ├── app.py                           # Streamlit entry point
    ├── requirements.txt                 # Python dependencies (shared by API + Streamlit)
    ├── .env.example                     # Environment variable template
    ├── api/
    │   └── main.py                      # FastAPI backend (wraps src/ modules)
    ├── frontend/                        # Next.js app (React 19, Tailwind)
    │   ├── app/
    │   │   ├── layout.tsx               # Root layout: nav, Imigongo band, footer
    │   │   ├── page.tsx                 # Home page
    │   │   ├── discovery/page.tsx       # Search + filters
    │   │   ├── analytics/page.tsx       # Charts and coverage
    │   │   ├── quality/page.tsx         # Quality dashboard
    │   │   ├── brief/page.tsx           # Advocacy brief generator
    │   │   ├── pipeline/page.tsx        # Pipeline status
    │   │   ├── components/Nav.tsx       # Responsive navigation (slide drawer on mobile)
    │   │   ├── lib/api.ts               # Typed API client
    │   │   └── globals.css              # Design tokens + responsive utilities
    │   ├── next.config.ts               # Proxies /api/* → FastAPI on :8000
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
    │   ├── quality_badges.py            # Quality flag parsing and classification
    │   ├── link_checker.py              # HTTP URL validation
    │   ├── ai.py                        # Claude API integration (interpret, explain, brief)
    │   ├── domains.py                   # Domain registry (Labour, Agriculture, Health, etc.)
    │   └── brief_store.py               # Persist and retrieve generated briefs
    ├── data_pipeline/
    │   ├── nisr_crawler.py              # Crawl NISR portal for new gender-relevant studies
    │   ├── openalex_adapter.py          # Fetch Rwanda research papers from OpenAlex
    │   └── build_dataset.py             # Merge all pipeline sources into data/full/
    ├── data/
    │   ├── full/                        # Live catalog (~2,740 studies, ~4,384 resources)
    │   │   ├── studies.csv
    │   │   ├── study_resources.csv
    │   │   └── quality_report.csv
    │   ├── pipeline_sources/
    │   │   ├── nisr_crawl/              # Output from nisr_crawler.py
    │   │   └── openalex/               # Output from openalex_adapter.py
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

## Data Pipeline — Refreshing the Catalog

The pipeline runs on-demand. Each adapter only adds new data; the NISR base catalog always takes priority on duplicates.

```bash
# 1. Crawl new NISR studies (skips existing ones automatically)
python data_pipeline/nisr_crawler.py

# 2. Fetch latest OpenAlex research papers
python data_pipeline/openalex_adapter.py

# 3. Merge all sources into the live catalog
python data_pipeline/build_dataset.py

# Restart the app to reflect the updated catalog
```

---

## Data and Provenance

| Item                     | Detail                                                                  |
| ------------------------ | ----------------------------------------------------------------------- |
| **Primary source**       | NISR Microdata Catalog — `microdata.statistics.gov.rw`                  |
| **Secondary source**     | OpenAlex open-access research API — no API key required                 |
| **Current catalog size** | ~2,740 studies, ~4,384 resources                                        |
| **Provenance columns**   | Each pipeline-ingested study carries `ingested_at` and `source_adapter` |
| **Auto-backup**          | `build_dataset.py` backs up `data/full/` before every merge             |

---

## Demo Scenario

**Context:** A CSO officer is preparing a brief for the Ministry of Gender on women's economic participation gaps.

**Step 1 — Search**

> Types: _"surveys on women economic participation Rwanda"_
> Shakisha returns: DHS 2014–2015, EICV surveys — with quality badges

**Step 2 — Evaluate**

> Sees: DHS 2014-2015 has 19 resources, quality: warning (2 missing fields)
> Clicks source link → confirms data is accessible on NISR portal

**Step 3 — Generate Brief**

> Clicks: "Generate Advocacy Brief"
> Receives in ~10 seconds:
>
> - _Policy context:_ "Rwanda's Vision 2050 targets gender parity..."
> - _Key findings:_ Women's LFP at 86%, but 40% in informal sector...
> - _Data gap:_ No district-level disaggregation available post-2018
> - _Recommendation:_ Advocate for updated EICV with gender module
> - _Citation:_ NISR, DHS 2014-2015. Available at: [URL]

**Step 4 — Use**

> Downloads brief as .txt (Next.js) or PDF (Streamlit) → pastes into proposal → done in 4 minutes

---

## Scoring Alignment

| Criterion        | Weight | How Shakisha Addresses It                                                                                                                                            |
| ---------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Coverage         | 30%    | ~2,740 NISR studies + OpenAlex papers; 6 filter dimensions (keyword, domain, year, district, resource type, quality); incremental crawler adds new studies on demand |
| Usability        | 25%    | Natural language search; responsive Next.js UI; quality badges on every result; .txt and PDF brief export                                                            |
| Trustworthiness  | 20%    | Quality badge per study; source URL checker; citation auto-generated; `ingested_at` + `source_adapter` provenance on all pipeline-ingested records                   |
| Maintainability  | 15%    | Clean `src/` module structure; separate `data_pipeline/` layer; 11 tests all pass; `.env.example` provided; auto-backup before every merge                           |
| Policy Relevance | 10%    | Advocacy Brief page produces a concrete, citable, ready-to-use policy output grounded in Rwanda Vision 2050, NST1, and the National Gender Policy                    |

---

_Built at the GDRD Gender Data Resource Discovery Hackathon — March 19–20, 2026, Kigali, Rwanda._
