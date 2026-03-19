# Shakisha — AI-Powered Gender Data Discovery Platform

> **Shakisha** (Kinyarwanda: *"to search / to discover"*) — Find the gender data you need, understand it instantly, and turn it into advocacy.

**GRB Gender Data Resource Discovery Hackathon 2026**
`team-shakisha-gdrh-2026`

---

## Team

| Name | Role |
|---|---|
| Muhigiri Ashuza Albin | Developer & AI Engineer |
| Ingabire Vanessa | [customize] |

---

## Project Objective

Civil Society Organizations (CSOs) and policy actors in Rwanda lose critical advocacy time searching for gender data across fragmented, PDF-heavy sources. **Shakisha** solves this by combining intelligent discovery with AI-generated policy output — so a CSO officer can go from a question to a ready-to-use advocacy brief in minutes, not hours.

**One platform. Two superpowers:**
- **Discover** — Natural language search over the full NISR gender data catalog
- **Act** — AI-generated advocacy briefs from any dataset, ready for policymakers

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
Filters the NISR catalog by: keywords + year range + topic relevance
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
User copies or exports the brief
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
Sees: color-coded quality badges per study (🟢 good / 🟡 warning / 🔴 critical)
     ↓
Checks: which fields are missing, what quality caveats apply
     ↓
Validates: source URL availability (link checker)
     ↓
Confident citing: knows data limitations before presenting to stakeholders
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHAKISHA — STREAMLIT APP                      │
│                                                                  │
│  ┌──────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │  Home    │  │ Discovery  │  │ Analytics  │  │  Advocacy  │  │
│  │ page 0   │  │  page 1    │  │ page 2 + 3 │  │  Brief     │  │
│  │          │  │            │  │            │  │  page 4    │  │
│  │ value    │  │ NLP search │  │ coverage   │  │ AI-powered │  │
│  │ prop +   │  │ + result   │  │ gaps +     │  │ policy     │  │
│  │ demo     │  │ cards with │  │ quality    │  │ brief      │  │
│  │ guide    │  │ badges     │  │ trust view │  │ generator  │  │
│  └──────────┘  └─────┬──────┘  └────────────┘  └──────┬─────┘  │
│                       │   st.session_state.study_id    │        │
│                       └────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼─────────────────────┐
         ▼                    ▼                     ▼
   src/ai.py            src/filters.py        src/loaders.py
   (Claude API)         (pandas filtering)    (CSV loading)
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
   ┌─────▼──────────────────┐
   │       DATA LAYER        │
   │                         │
   │  studies.csv            │
   │  study_resources.csv    │  ← joined in-memory via pandas
   │  quality_report.csv     │
   │                         │
   │  Source: NISR Microdata │
   │  microdata.statistics   │
   │  .gov.rw                │
   └─────────────────────────┘
```

### Module Responsibilities

| Module | Responsibility |
|---|---|
| `src/loaders.py` | Load and validate all 3 CSVs; resolve data directory from env var |
| `src/filters.py` | Apply keyword, year, and resource-type filters to DataFrames |
| `src/quality_badges.py` | Parse semicolon-separated quality flags; classify good/warning/critical |
| `src/link_checker.py` | HTTP HEAD validation for source URLs (8s timeout) |
| `src/ai.py` | All Claude API calls — query interpretation, relevance explanation, advocacy brief |
| `pages/1_Discovery.py` | NLP search UI + filtered result cards |
| `pages/2_Dashboard.py` | Metrics, year trend, resource type breakdown, coverage gap chart |
| `pages/3_Data_Quality.py` | Visual quality badges, missing field heatmap, link checker UI |
| `pages/4_Advocacy_Brief.py` | Study detail + Claude-generated policy brief + export |

---

## Setup Steps

### Requirements
- Python 3.10+
- An Anthropic API key ([get one at console.anthropic.com](https://console.anthropic.com))

### 1. Clone the repository
```bash
git clone https://github.com/<your-org>/team-shakisha-gdrh-2026.git
cd team-shakisha-gdrh-2026/starter-app
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

The app opens at `http://localhost:8501`.

### 6. (Optional) Load the full dataset
```bash
# Unzip the full NISR catalog
unzip data/full-data.zip -d data/full

# Set the data directory
export HACKATHON_DATA_DIR=data/full

# Restart the app
streamlit run app.py
```

### 7. Run the test suite
```bash
python -m unittest discover -s tests -v
```

Expected: **5 tests passing, 0 failures**

---

## Project Structure

```
starter-app/
├── app.py                      # Entry point — Home page
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── .streamlit/
│   └── config.toml             # Streamlit theme and server config
├── pages/
│   ├── 1_Discovery.py          # NLP search + result cards
│   ├── 2_Dashboard.py          # Analytics and coverage charts
│   ├── 3_Data_Quality.py       # Quality badges and trust signals
│   └── 4_Advocacy_Brief.py     # AI-powered policy brief generator
├── src/
│   ├── loaders.py              # CSV loading and validation
│   ├── filters.py              # Study and resource filtering
│   ├── quality_badges.py       # Quality flag parsing and classification
│   ├── link_checker.py         # HTTP URL validation
│   └── ai.py                   # Claude API integration
├── data/
│   ├── sample/                 # 3-study quick-start dataset
│   │   ├── studies.csv
│   │   ├── study_resources.csv
│   │   └── quality_report.csv
│   └── full-data.zip           # Full NISR catalog (~50–100 studies)
└── tests/
    ├── test_loaders.py
    ├── test_filters.py
    ├── test_quality_badges.py
    └── test_ai.py              # Mocked Claude API tests
```

---

## Data and Provenance

| Item | Detail |
|---|---|
| **Primary source** | NISR Microdata Catalog — `microdata.statistics.gov.rw` |
| **Files used** | `studies.csv`, `study_resources.csv`, `quality_report.csv` |
| **Sample data** | 3 studies (Agricultural HH Survey 2017, DHS 2014-2015, RPHC 2022) |
| **Full data** | ~50–100 NISR studies across surveys, censuses, and administrative records |
| **Access status** | Baseline CSVs provided by hackathon organizers; NISR links validated during event |
| **Provenance log** | Each study displays: source institution, source URL, access status, and access timestamp |

**Citation format used throughout:**
`Source: <Institution>, <Study Title>, <Year>. Available at: <URL>`

---

## Demo Scenario — Advocacy Use Case

**Context:** A CSO officer is preparing a brief for the Ministry of Gender on women's economic participation gaps.

**Step 1 — Search**
> Types: *"surveys on women economic participation Rwanda"*
> Shakisha returns: DHS 2014-2015, EICV surveys — with quality badges and relevance explanations

**Step 2 — Evaluate**
> Sees: DHS 2014-2015 has 19 resources, quality: 🟡 warning (2 missing fields)
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
> Copies brief → pastes into funding proposal → done in 4 minutes

---

## Limitations

| Limitation | Impact |
|---|---|
| Data is pre-collected from NISR (no real-time crawl) | Catalog may not reflect resources added after the hackathon event |
| AI briefs are based on study abstracts only (not full PDFs) | Findings are summaries, not full analysis |
| Link checker is on-demand — no background monitoring | A link may appear available but return errors on actual download |
| No user authentication | Any user can access all studies; no personalization |
| Claude API requires an internet connection and API key | App does not run fully offline |
| District-level disaggregation not available in current dataset | Cannot filter or visualize by Rwanda district |

---

## Next Steps

| Priority | Feature |
|---|---|
| High | Real-time NISR catalog sync via scheduled crawler |
| High | District-level data integration for geographic filtering |
| Medium | PDF content extraction for deeper AI analysis |
| Medium | User accounts and saved search history |
| Medium | Batch export (multiple studies as a single policy report) |
| Low | Multilingual support (Kinyarwanda + French + English) |
| Low | Offline mode with cached data snapshot |

---

## Architecture Note

Shakisha is built as a pure Python/Streamlit application on top of the provided hackathon starter. The AI layer (`src/ai.py`) calls the Claude API (`claude-haiku-4-5`) for three tasks: interpreting natural language queries into structured filters, generating per-study relevance explanations, and producing structured advocacy briefs. All data manipulation is done in-memory with pandas — no external database is required. The link checker (`src/link_checker.py`) runs optional HTTP HEAD validation on demand. Session state (`st.session_state`) is used to pass the selected study ID from the Discovery page to the Advocacy Brief page, enabling a seamless single-page-to-brief flow without page reloads.

---

## Scoring Alignment

| Criterion | Weight | How Shakisha Addresses It |
|---|---|---|
| Coverage | 30% | Full NISR catalog loaded; 5 filter dimensions (keyword, year, org, type, quality level) |
| Usability | 25% | Natural language search replaces keyword guessing; result cards replace raw tables |
| Trustworthiness | 20% | Quality badges on every result; source URLs and access status visible; citation auto-generated |
| Maintainability | 15% | Clean `src/` module structure; all existing tests pass; `.env.example` provided |
| Policy Relevance | 10% | Advocacy Brief page produces a concrete, citable, ready-to-use policy output |

---

*Built at the GRB Gender Data Resource Discovery Hackathon — March 19–20, 2026, Kigali, Rwanda.*
