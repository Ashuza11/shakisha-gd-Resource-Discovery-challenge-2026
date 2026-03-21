# Shakisha App — Validation Record

Validation date: 2026-03-21

## Environment

- App directory: `Shakisha-app/`
- Virtual environment: `Shakisha-app/.venv`
- Python version: 3.10

## Commands executed

### 1. Dependency install

```bash
cd Shakisha-app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Test suite

```bash
pip install pytest
python -m pytest tests/ -v
```

Result: **PASS** — 11 tests, 0 failures

Tests cover:
- `test_filters.py` — keyword, year, organization, district, and resource-type filters
- `test_loaders.py` — CSV loading and column validation
- `test_quality_badges.py` — flag parsing and good/warning/critical classification
- `test_ai.py` — mocked Claude API calls (interpret_query, explain_study, advocacy_brief) with JSON fallback handling

### 3. Streamlit launch

```bash
streamlit run app.py --server.headless true --server.port 8501
```

Result: **PASS** — app loads at `http://localhost:8501`

Pages confirmed working:
- Home (`0_Home.py`) — live catalog stats, 6-domain roadmap, demo scenario
- Discovery (`1_Discovery.py`) — NLP search, domain filter, quality badges, result cards, paginated results
- Analytics (`2_Dashboard.py`) — year trend, coverage gap, resource types, district map
- Data Quality (`3_Data_Quality.py`) — quality table, missing field chart, link checker
- Advocacy Brief (`4_Advocacy_Brief.py`) — AI brief generation, PDF/TXT export, brief history (requires `ANTHROPIC_API_KEY`)
- Data Pipeline (`5_Pipeline.py`) — source status dashboard, pipeline run instructions

### 4. AI features (optional)

Set `ANTHROPIC_API_KEY` in environment or `.env` file to enable:
- Natural language query interpretation
- Per-study relevance explanation
- Structured advocacy brief generation

Without the key the app runs in keyword-only mode — all pages remain usable.

## Data modes

| Mode | Command | Studies loaded |
|---|---|---|
| Sample (default) | `streamlit run app.py` | 3 studies from `data/sample/` |
| Full dataset | `HACKATHON_DATA_DIR=data/full streamlit run app.py` | 2,740 studies, 4,384 resources |

Full dataset: pre-loaded in `data/full/` (already unzipped). `.env` sets `HACKATHON_DATA_DIR=data/full` by default.

## Known constraints

- AI brief generation requires an active internet connection and valid API key.
- Link checker runs on demand (max 10 studies per check) — no background monitoring.
- District-level geographic filter searches text fields; not all studies have explicit district annotations.
