# Starter App Validation

Validation date: 2026-03-18

## Environment used

- Isolated virtual environment: `participants/starter-app/.venv`
- Python executable: `.venv/Scripts/python`

## Commands executed

### 1) Dependency install

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```

### 2) Basic tests

```bash
.venv/Scripts/python -m unittest discover -s tests -v
```

Result: **PASS** (5 tests, 0 failures)

### 3) Streamlit launch check

```bash
.venv/Scripts/streamlit run app.py --server.headless true --server.port 8510
```

Result: **PASS** (Local URL started successfully)

## Known constraints

- Default mode uses sample data from `data/sample/`.
- Full dataset is provided as `data/full-data.zip` and must be unzipped before use.
- Crawler refresh is optional and not required for MVP or judging.
