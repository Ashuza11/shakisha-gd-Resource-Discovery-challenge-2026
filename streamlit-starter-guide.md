# Streamlit Starter Guide (Runnable Baseline)

## Minimum technical requirement

All teams must submit a **runnable Streamlit app**.
Use the provided starter in `starter-app/` as the baseline.

## Provided starter structure

```text
starter-app/
  app.py
  README.md
  VALIDATION.md
  requirements.txt
  .venv/                    # created locally during setup
  .streamlit/
    config.toml
  data/
    sample/
      studies.csv
      study_resources.csv
      quality_report.csv
    full-data.zip
  pages/
    1_Discovery.py
    2_Dashboard.py
    3_Data_Quality.py
  src/
    loaders.py
    filters.py
    link_checker.py
    quality_badges.py
  tests/
    test_loaders.py
    test_filters.py
    test_quality_badges.py
```

## Setup commands (copy/paste)

```bash
cd starter-app
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/streamlit run app.py
```

## Optional: run tests before coding

```bash
.venv/Scripts/python -m unittest discover -s tests -v
```

## Data mode options

- Default startup: sample dataset in `data/sample/`
- Full data mode:
  1. unzip `data/full-data.zip` into `data/full/`
  2. set env var `HACKATHON_DATA_DIR=data/full`
  3. run Streamlit again

## MVP feature checklist

- [ ] Data loading works
- [ ] Search/filter interface exists
- [ ] Results/detail view displays metadata
- [ ] Source and access links are visible
- [ ] Quality caveats are visible
- [ ] One advocacy use case can be demonstrated

## Optional (advanced)

- district comparison charts
- trend lines over time
- export shortlist/report
- optional crawler refresh utility

Note: crawler code is optional and should not delay MVP delivery.
