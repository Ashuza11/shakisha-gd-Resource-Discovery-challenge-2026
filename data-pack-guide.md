# Data Pack Guide (Participants)

## Baseline data

Use data that is bundled in this repository:

- `starter-app/data/sample/studies.csv` (main index)
- `starter-app/data/sample/study_resources.csv` (linked resources)
- `starter-app/data/sample/quality_report.csv` (quality overlays)
- optional full dataset: `starter-app/data/full-data.zip`

Read field definitions in `data-dictionary.md`.

## Recommended workflow

1. Load `studies.csv` as your primary table.
2. Join `study_resources.csv` on `study_id`.
3. Join `quality_report.csv` on `study_id`.
4. Expose filters for year, geography, resource type, and quality flags.
5. Show source URLs and access status clearly.

## Direct NISR retrieval flow

Use this for high-value resources in demo scenarios:

1. Identify candidate in your app.
2. Open `url` or `get_microdata_url`.
3. Confirm availability status.
4. Record provenance fields (see shared policy).

## Practical tips

- If files feel large, start with a subset for iteration.
- Start with sample data first, then switch to full-data zip when stable.
- Keep null-safe logic for missing metadata fields.
- Surface uncertainty in UI rather than hiding it.
