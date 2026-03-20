"""
Merge all pipeline sources with the base NISR dataset into data/full/.

Sources merged (in priority order — NISR base wins on duplicates):
  1. data/full/                        — base NISR microdata catalog (authoritative)
  2. data/pipeline_sources/nisr_crawl/ — new studies from NISR crawler
  3. data/pipeline_sources/openalex/   — OpenAlex research papers

Run adapters first, then merge:
    python data_pipeline/nisr_crawler.py
    python data_pipeline/openalex_adapter.py
    python data_pipeline/build_dataset.py
    python data_pipeline/build_dataset.py --dry-run
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import pandas as pd

NISR_DIR = Path("data/full")
PIPELINE_SOURCES = [
    Path("data/pipeline_sources/nisr_crawl"),   # NISR crawler — new gender-relevant studies
    Path("data/pipeline_sources/openalex"),      # OpenAlex research papers
    # Path("data/pipeline_sources/worldbank"),
    # Path("data/pipeline_sources/ilo"),
]
OUTPUT_DIR = Path("data/full")          # write back to full — app reads from here
BACKUP_DIR = Path("data/full_backup")


def _load(directory: Path, filename: str) -> pd.DataFrame:
    path = directory / filename
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str)


def merge_and_write(dry_run: bool = False) -> None:
    print("=" * 60)
    print("Shakisha — Dataset Builder")
    print("=" * 60)

    # ── Backup existing full dataset ───────────────────────────────────────────
    if NISR_DIR.exists() and not dry_run:
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        shutil.copytree(NISR_DIR, BACKUP_DIR)
        print(f"Backed up existing data/full → {BACKUP_DIR}")

    # ── Load base NISR data ────────────────────────────────────────────────────
    nisr_studies   = _load(NISR_DIR, "studies.csv")
    nisr_resources = _load(NISR_DIR, "study_resources.csv")
    nisr_quality   = _load(NISR_DIR, "quality_report.csv")

    print(f"\nBase NISR: {len(nisr_studies)} studies, {len(nisr_resources)} resources")

    all_studies   = [nisr_studies]
    all_resources = [nisr_resources]
    all_quality   = [nisr_quality]

    # ── Merge each pipeline source ─────────────────────────────────────────────
    nisr_ids = set(nisr_studies["study_id"].astype(str).tolist()) if not nisr_studies.empty else set()

    for source_dir in PIPELINE_SOURCES:
        if not source_dir.exists():
            print(f"  Skipping {source_dir} (not found — run its adapter first)")
            continue

        src_studies   = _load(source_dir, "studies.csv")
        src_resources = _load(source_dir, "study_resources.csv")
        src_quality   = _load(source_dir, "quality_report.csv")

        if src_studies.empty:
            print(f"  Skipping {source_dir} (empty)")
            continue

        # Deduplicate: drop any pipeline study whose ID already exists in NISR
        before = len(src_studies)
        src_studies = src_studies[~src_studies["study_id"].astype(str).isin(nisr_ids)]
        dropped = before - len(src_studies)

        # Filter resources and quality to only the kept studies
        kept_ids = set(src_studies["study_id"].astype(str).tolist())
        if not src_resources.empty:
            src_resources = src_resources[src_resources["study_id"].astype(str).isin(kept_ids)]
        if not src_quality.empty:
            src_quality = src_quality[src_quality["study_id"].astype(str).isin(kept_ids)]

        print(f"  {source_dir.name}: {len(src_studies)} new studies added ({dropped} duplicates dropped)")

        all_studies.append(src_studies)
        all_resources.append(src_resources)
        all_quality.append(src_quality)

        # Add new IDs so next source doesn't duplicate them either
        nisr_ids.update(kept_ids)

    # ── Concatenate ────────────────────────────────────────────────────────────
    merged_studies   = pd.concat([df for df in all_studies   if not df.empty], ignore_index=True)
    merged_resources = pd.concat([df for df in all_resources if not df.empty], ignore_index=True)
    merged_quality   = pd.concat([df for df in all_quality   if not df.empty], ignore_index=True)

    print(f"\nMerged total: {len(merged_studies):,} studies, {len(merged_resources):,} resources")

    # ── Write ──────────────────────────────────────────────────────────────────
    if not dry_run:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        merged_studies.to_csv(OUTPUT_DIR   / "studies.csv",          index=False)
        merged_resources.to_csv(OUTPUT_DIR / "study_resources.csv",  index=False)
        merged_quality.to_csv(OUTPUT_DIR   / "quality_report.csv",   index=False)
        print(f"\nWritten to {OUTPUT_DIR}/")
        print("Restart the Shakisha app to see the expanded catalog.")
    else:
        print("\n[dry-run] No files written.")

    # ── Summary ────────────────────────────────────────────────────────────────
    by_collection = merged_studies.groupby(
        merged_studies.get("collection", pd.Series("Unknown", index=merged_studies.index))
    ).size().sort_values(ascending=False)
    print("\nStudies by collection:")
    for col, count in by_collection.items():
        print(f"  {col}: {count:,}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge all pipeline sources into data/full/")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be merged without writing")
    args = parser.parse_args()
    merge_and_write(dry_run=args.dry_run)
