# Shakisha — AI-Powered Gender Data Discovery Platform

> **Shakisha** (Kinyarwanda: *"to search / to discover"*) — Find the gender data you need, understand it instantly, and turn it into advocacy.

**GRB Gender Data Resource Discovery Hackathon 2026**
`team-shakisha-gdrh-2026`

---

## Team

| Name | Role |
|---|---|
| Muhigiri Ashuza Albin | Developer & AI Engineer |
| Ingabire Vanessa | Researcher & UX |

---

## Project Objective

Civil Society Organizations (CSOs) and policy actors in Rwanda lose critical advocacy time searching for gender data across fragmented, PDF-heavy sources. **Shakisha** solves this by combining intelligent discovery with AI-generated policy output — so a CSO officer can go from a question to a ready-to-use advocacy brief in minutes, not hours.

**One platform. Three superpowers:**
- **Discover** — Natural language search over the full NISR gender data catalog + academic papers
- **Act** — AI-generated advocacy briefs from any dataset, ready for policymakers
- **Grow** — Live data pipeline that crawls NISR and pulls from OpenAlex to keep the catalog current

---

## User Persona

**Uwase Claudette** — Program Officer, Women's Rights CSO, Kigali

- Needs gender disaggregated data for a funding proposal due in 48 hours
- Knows the data exists somewhere in NISR but doesn't know which survey or report
- Has no time to read 40-page PDFs or navigate complex data portals
- Needs to know: *Is the data credible? Is it recent? Can she cite it?*

**What Shakisha gives her:**
1. She types a plain-language question
2. Gets a ranked list of relevant studies with quality indicators
3. Clicks one study → receives a structured advocacy brief with citations
4. Done in under 5 minutes

---

## Key Workflows

### Workflow 1 — Intelligent Discovery
```
User types: "women's labour force participation in rural Rwanda after 2018"
     ↓
AI interprets the query (Claude API)
     ↓
Filters the catalog by: keywords + year range + topic relevance
     ↓
Returns: ranked result cards with title, year, org, quality badge, source links
     ↓
User sees: why each result is relevant (AI-generated 2-line explanation)
```

### Workflow 2 — Advocacy Brief Generation
```
User selects a study from Discovery results
     ↓
Clicks "Generate Advocacy Brief"
     ↓
AI reads: study title, abstract, year, organization, resources, quality flags
     ↓
Outputs structured brief:
  - Policy context
  - Key findings (3 bullet points)
  - Data gaps and caveats
  - Recommended advocacy action
  - Proper citation (NISR format)
     ↓
User copies, exports to PDF, or saves the brief (stored in data/briefs/)
```

### Workflow 3 — Catalog Analytics
```
User opens Analytics page
     ↓
Sees: total studies, coverage by year, resource type breakdown
     ↓
Identifies: years/topics with no data → coverage gaps
     ↓
Uses gap insight to argue for new data collection in advocacy
```

### Workflow 4 — Trust Verification
```
User opens Data Quality page
     ↓
Sees: color-coded quality badges per study (good / warning / critical)
     ↓
Checks: which fields are missing, what quality caveats apply
     ↓
Validates: source URL availability (link checker)
     ↓
Confident citing: knows data limitations before presenting to stakeholders
```

### Workflow 5 — Data Pipeline
```
Maintainer runs: python data_pipeline/nisr_crawler.py
     ↓
Crawler fetches new gender-relevant studies from NISR microdata portal
(skips studies already in the catalog — incremental, safe to re-run)
     ↓
Maintainer runs: python data_pipeline/openalex_adapter.py
     ↓
Adapter pulls academic papers from OpenAlex (no API key required)
     ↓
Maintainer runs: python data_pipeline/build_dataset.py
     ↓
Sources merged into data/full/ — NISR base wins on duplicates
     ↓
Restart app → expanded catalog live immediately
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                      SHAKISHA — STREAMLIT APP                         │
│                                                                       │
│  ┌──────────┐  ┌────────────┐  ┌────────────┐  ┌────────┐  ┌──────┐  │
│  │  Home    │  │ Discovery  │  │ Analytics  │  │Advocacy│  │Data  │  │
│  │ page 0   │  │  page 1    │  │ page 2 + 3 │  │Brief   │  │Pipe- │  │
│  │          │  │            │  │            │  │page 4  │  │line  │  │
│  │ value    │  │ NLP search │  │ coverage   │  │AI brief│  │page 5│  │
│  │ prop +   │  │ + result   │  │ gaps +     │  │+ PDF   │  │source│  │
│  │ demo     │  │ cards with │  │ quality    │  │export  │  │status│  │
│  │ guide    │  │ badges     │  │ trust view │  │        │  │      │  │
│  └──────────┘  └─────┬──────┘  └────────────┘  └───┬────┘  └──────┘  │
│                       │   st.session_state.study_id │                 │
│                       └─────────────────────────────┘                 │
└──────────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼──────────────────────┐
         ▼                    ▼                      ▼
   src/ai.py            src/filters.py         src/loaders.py
   (Claude API)         (pandas filtering)     (CSV loading)
   src/domains.py       src/brief_store.py     src/quality_badges.py
   (domain registry)    (brief persistence)    src/link_checker.py
         │
   ┌─────▼──────────────────┐
   │      CLAUDE API         │
   │  model: haiku-4-5       │
   │                         │
   │  interpret_query()      │  ← NLP → filter params + intent
   │  explain_study()        │  ← why this study is relevant
   │  advocacy_brief()       │  ← structured policy output
   └─────────────────────────┘
         │
   ┌─────▼────────────────────────────────────────────────┐
   │                    DATA LAYER                          │
   │                                                        │
   │  data/full/studies.csv          (~2,740 studies)       │
   │  data/full/study_resources.csv  (~4,384 resources)     │
   │  data/full/quality_report.csv                          │
   │                                                        │
   │  Sources:                                              │
   │    NISR Microdata (authoritative base)                 │
   │    NISR Crawler (incremental — new studies)            │
   │    OpenAlex (peer-reviewed research papers)            │
   └────────────────────────────────────────────────────────┘
         │
   ┌─────▼──────────────────────────────────────────────────┐
   │                 DATA PIPELINE                           │
   │                                                         │
   │  data_pipeline/nisr_crawler.py    ← crawl NISR portal  │
   │  data_pipeline/openalex_adapter.py ← fetch OpenAlex    │
   │  data_pipeline/build_dataset.py   ← merge all sources  │
   └─────────────────────────────────────────────────────────┘
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `src/loaders.py` | Load and validate all 3 CSVs; resolve data directory from env var |
| `src/filters.py` | Apply keyword, year, and resource-type filters to DataFrames |
| `src/quality_badges.py` | Parse semicolon-separated quality flags; classify good/warning/critical |
| `src/link_checker.py` | HTTP HEAD validation for source URLs (8s timeout) |
| `src/ai.py` | All Claude API calls — query interpretation, relevance explanation, advocacy brief |
| `src/domains.py` | Domain registry (Labour, Agriculture, Health, etc.) with keywords and advocacy context |
| `src/brief_store.py` | Persist, list, load, and delete generated briefs as JSON in `data/briefs/` |
| `pages/0_Home.py` | Landing page — value proposition and demo guide |
| `pages/1_Discovery.py` | NLP search UI + filtered result cards |
| `pages/2_Dashboard.py` | Metrics, year trend, resource type breakdown, coverage gap chart |
| `pages/3_Data_Quality.py` | Visual quality badges, missing field heatmap, link checker UI |
| `pages/4_Advocacy_Brief.py` | Study detail + Claude-generated policy brief + PDF export |
| `pages/5_Pipeline.py` | Data pipeline status dashboard — source cards, run commands, recent ingestions |
| `data_pipeline/nisr_crawler.py` | Crawl `microdata.statistics.gov.rw` for new gender-relevant studies (incremental, resumable) |
| `data_pipeline/openalex_adapter.py` | Fetch peer-reviewed Rwanda gender/labour/agriculture papers from OpenAlex API |
| `data_pipeline/build_dataset.py` | Merge all pipeline sources into `data/full/`; NISR base wins on duplicates |

---

## Setup Steps

### Requirements
- Python 3.10+
- An Anthropic API key ([get one at console.anthropic.com](https://console.anthropic.com))

### 1. Clone the repository
```bash
git clone https://github.com/<your-org>/team-shakisha-gdrh-2026.git
cd team-shakisha-gdrh-2026/Shakisha-app
```

### 2. Create and activate a virtual environment
```bash
# Linux / macOS
python -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

Dependencies include: `streamlit`, `pandas`, `plotly`, `anthropic`, `requests`, `python-dotenv`, `fpdf2` (PDF export), `beautifulsoup4` + `lxml` (NISR crawler).

### 4. Set your API key
```bash
# Linux / macOS
export ANTHROPIC_API_KEY=your_key_here

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="your_key_here"
```

Alternatively, copy `.env.example` to `.env` and fill in your key.

### 5. Run the app
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`. The full dataset (~2,740 studies) is loaded by default from `data/full/`.

### 6. Run the test suite
```bash
python -m unittest discover -s tests -v
```

---

## Project Structure

```
Shakisha-app/
├── app.py                          # Entry point — navigation setup + logo
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .streamlit/
│   └── config.toml                 # Streamlit theme and server config
├── pages/
│   ├── 0_Home.py                   # Landing page
│   ├── 1_Discovery.py              # NLP search + result cards
│   ├── 2_Dashboard.py              # Analytics and coverage charts
│   ├── 3_Data_Quality.py           # Quality badges and trust signals
│   ├── 4_Advocacy_Brief.py         # AI-powered policy brief + PDF export
│   └── 5_Pipeline.py               # Data pipeline status and run commands
├── src/
│   ├── loaders.py                  # CSV loading and validation
│   ├── filters.py                  # Study and resource filtering
│   ├── quality_badges.py           # Quality flag parsing and classification
│   ├── link_checker.py             # HTTP URL validation
│   ├── ai.py                       # Claude API integration
│   ├── domains.py                  # Domain registry with keywords and advocacy context
│   └── brief_store.py              # Persist and retrieve generated briefs (data/briefs/)
├── data_pipeline/
│   ├── nisr_crawler.py             # Crawl NISR portal for new gender-relevant studies
│   ├── openalex_adapter.py         # Fetch Rwanda research papers from OpenAlex
│   └── build_dataset.py            # Merge all pipeline sources into data/full/
├── data/
│   ├── full/                       # Live catalog (~2,740 studies, ~4,384 resources)
│   │   ├── studies.csv
│   │   ├── study_resources.csv
│   │   └── quality_report.csv
│   ├── full_backup/                # Auto-backup created by build_dataset.py before each merge
│   ├── pipeline_sources/
│   │   ├── nisr_crawl/             # Output from nisr_crawler.py
│   │   └── openalex/               # Output from openalex_adapter.py
│   ├── sample/                     # 3-study quick-start dataset
│   │   ├── studies.csv
│   │   ├── study_resources.csv
│   │   └── quality_report.csv
│   ├── briefs/                     # Generated advocacy briefs (JSON, created at runtime)
│   └── full-data.zip               # Original NISR baseline archive
└── tests/
    ├── test_loaders.py
    ├── test_filters.py
    ├── test_quality_badges.py
    └── test_ai.py                  # Mocked Claude API tests
```

---

## Data and Provenance

| Item | Detail |
|---|---|
| **Primary source** | NISR Microdata Catalog — `microdata.statistics.gov.rw` |
| **Secondary source** | OpenAlex open-access research API — no API key required |
| **Files used** | `studies.csv`, `study_resources.csv`, `quality_report.csv` |
| **Current catalog size** | ~2,740 studies, ~4,384 resources |
| **NISR base** | Rwanda surveys, censuses, and administrative records (authoritative) |
| **OpenAlex** | Peer-reviewed academic papers on Rwanda gender, labour, agriculture, and land rights |
| **Incremental crawl** | `nisr_crawler.py` skips study IDs already present — safe to re-run without duplicating |
| **Provenance columns** | Each pipeline-ingested study carries `ingested_at` (date) and `source_adapter` (e.g. `nisr_crawl`, `openalex`) |
| **Auto-backup** | `build_dataset.py` backs up `data/full/` to `data/full_backup/` before every merge |

**Citation format used throughout:**
`Source: <Institution>, <Study Title>, <Year>. Available at: <URL>`

---

## Data Pipeline — Refreshing the Catalog

The pipeline is designed to be run on demand. Each adapter only adds new data; the NISR base catalog always takes priority on duplicates.

```bash
# 1. Crawl new NISR studies (skips existing ones automatically)
python data_pipeline/nisr_crawler.py

# Optional flags:
#   --max-pages 5       limit to first 5 catalog pages
#   --max-studies 50    limit total studies fetched
#   --dry-run           list matching studies without writing
#   --strict            apply strict abstract quality fixes

# 2. Fetch latest OpenAlex research papers
python data_pipeline/openalex_adapter.py

# Optional flags:
#   --max-per-query 200   limit results per search query
#   --dry-run             print API calls without writing

# 3. Merge all sources into the live catalog
python data_pipeline/build_dataset.py

# Restart the app to reflect the updated catalog
```

The **Data Pipeline** page in the app (`pages/5_Pipeline.py`) shows the live status of each source, the last run date, and study counts — without needing to touch the terminal.

---

## Demo Scenario — Advocacy Use Case

**Context:** A CSO officer is preparing a brief for the Ministry of Gender on women's economic participation gaps.

**Step 1 — Search**
> Types: *"surveys on women economic participation Rwanda"*
> Shakisha returns: DHS 2014-2015, EICV surveys — with quality badges and relevance explanations

**Step 2 — Evaluate**
> Sees: DHS 2014-2015 has 19 resources, quality: warning (2 missing fields)
> Clicks: source link → confirms data is accessible on NISR portal

**Step 3 — Generate Brief**
> Clicks: "Generate Advocacy Brief"
> Receives in 10 seconds:
> - *Policy context:* "Rwanda's Vision 2050 targets gender parity..."
> - *Key findings:* Women's LFP at 86%, but 40% in informal sector...
> - *Data gap:* No district-level disaggregation available post-2018
> - *Recommendation:* Advocate for updated EICV with gender module
> - *Citation:* NISR, DHS 2014-2015. Available at: [URL]

**Step 4 — Use**
> Copies brief or exports as PDF → pastes into funding proposal → done in 4 minutes

---

## Limitations

| Limitation | Impact |
|---|---|
| NISR crawler requires internet access to microdata portal | Catalog refresh not possible in offline/restricted network environments |
| AI briefs are based on study abstracts only (not full PDFs) | Findings are summaries, not full analysis |
| Link checker is on-demand — no background monitoring | A link may appear available but return errors on actual download |
| No user authentication | Any user can access all studies; no personalization |
| Claude API requires an internet connection and API key | App does not run fully offline |
| District-level disaggregation not available in current dataset | Cannot filter or visualize by Rwanda district |
| OpenAlex papers are academic articles, not microdata | May not have raw data files attached — linked by DOI only |

---

## Next Steps

| Priority | Feature |
|---|---|
| High | District-level data integration for geographic filtering |
| High | PDF content extraction for deeper AI analysis |
| Medium | Scheduled/automated pipeline runs (cron or GitHub Actions) |
| Medium | User accounts and saved search history |
| Medium | Batch export (multiple studies as a single policy report) |
| Medium | World Bank and ILO adapters (stubs visible in Pipeline page) |
| Low | Multilingual support (Kinyarwanda + French + English) |
| Low | Offline mode with cached data snapshot |

---

## Architecture Note

Shakisha is built as a pure Python/Streamlit application. The AI layer (`src/ai.py`) calls the Claude API (`claude-haiku-4-5`) for three tasks: interpreting natural language queries into structured filters, generating per-study relevance explanations, and producing structured advocacy briefs. Generated briefs are persisted to disk via `src/brief_store.py` and can be exported as PDF using `fpdf2`. Domain classification logic lives in `src/domains.py`, which drives the domain filter UI and the NISR crawler's relevance filter.

The data pipeline (`data_pipeline/`) is a separate, command-line-runnable layer. `nisr_crawler.py` crawls the live NISR microdata portal with gender/domain relevance filtering and checkpoint-based resumption. `openalex_adapter.py` fetches peer-reviewed papers via the OpenAlex REST API (no key required). `build_dataset.py` merges all sources, with NISR base winning on duplicate study IDs, and auto-backs up before writing. All data manipulation is done in-memory with pandas — no external database is required.

Session state (`st.session_state`) passes the selected study ID from the Discovery page to the Advocacy Brief page, enabling a seamless single-page-to-brief flow without page reloads.

---

## Scoring Alignment

| Criterion | Weight | How Shakisha Addresses It |
|---|---|---|
| Coverage | 30% | ~2,740 studies from NISR + OpenAlex; 5 filter dimensions (keyword, year, org, type, quality level); incremental crawler adds new studies on demand |
| Usability | 25% | Natural language search replaces keyword guessing; result cards replace raw tables; PDF export for immediate use |
| Trustworthiness | 20% | Quality badges on every result; source URLs and access status visible; citation auto-generated; `ingested_at` and `source_adapter` provenance on all pipeline-ingested records |
| Maintainability | 15% | Clean `src/` module structure; separate `data_pipeline/` layer; all tests pass; `.env.example` provided; auto-backup before every merge |
| Policy Relevance | 10% | Advocacy Brief page produces a concrete, citable, ready-to-use policy output with PDF export |

---

*Built at the GRB Gender Data Resource Discovery Hackathon — March 19–20, 2026, Kigali, Rwanda.*
