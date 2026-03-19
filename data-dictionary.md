# Data Dictionary

This repository includes two data modes:

- quick-start sample data in `starter-app/data/sample/`
- full dataset in `starter-app/data/full-data.zip`

## studies.csv

- `study_id`: unique study identifier
- `title`: study title
- `year`: publication/production year
- `organization`: owner/publisher
- `url`: study page URL
- `get_microdata_url`: microdata access link
- `abstract`: summary
- `quality_flags`: metadata flags

## study_resources.csv

- `study_id`: foreign key to studies
- `type`: resource type (`pdf`, `doc`, etc.)
- `name`: resource name
- `url`: resource URL
- `filename`: file name
- `quality_flags`: resource-level flags

## quality_report.csv

- `study_id`: study identifier
- `title`: study title
- `quality_flags`: semicolon-separated quality flags
- `missing_field_count`: count of missing fields
- `resource_count`: linked resource count
- `resource_quality_flags`: rollup quality notes
