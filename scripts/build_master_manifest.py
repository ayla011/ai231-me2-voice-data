#!/usr/bin/env python3
"""Maintainer-only: merge every classmate's manifest.csv (downloaded from
the shared Drive `raw/` folder) into one master CSV for the actual ME2
dataset build. Not needed by contributors.

Usage:
  python scripts/build_master_manifest.py --raw-dir ~/Drive/AI231-ME2-Voice-Data/raw \
      --out data/master_manifest.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", required=True, help="local sync of the shared Drive raw/ folder")
    ap.add_argument("--out", default="data/master_manifest.csv")
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    manifests = sorted(raw_dir.glob("*/manifest.csv"))
    if not manifests:
        raise SystemExit(f"No */manifest.csv found under {raw_dir}")

    all_rows = []
    status_counts = Counter()
    speaker_counts = Counter()
    fieldnames: list[str] | None = None
    for manifest_path in manifests:
        speaker_dir = manifest_path.parent.name
        with manifest_path.open() as f:
            reader = csv.DictReader(f)
            if fieldnames is None:
                fieldnames = reader.fieldnames + ["source_path"]
            for row in reader:
                if row.get("speaker_id") != speaker_dir:
                    print(f"WARNING: {manifest_path}: speaker_id={row.get('speaker_id')!r} "
                          f"!= folder name {speaker_dir!r}")
                row["source_path"] = str((manifest_path.parent / row["filename"]).relative_to(raw_dir))
                status_counts[row.get("status", "unvalidated")] += 1
                speaker_counts[speaker_dir] += 1
                all_rows.append(row)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(all_rows)

    print(f"Merged {len(manifests)} speakers, {len(all_rows)} rows -> {out_path}\n")
    print("By status:")
    for status, n in status_counts.most_common():
        print(f"  {status:>14}: {n}")
    print("\nBy speaker:")
    for speaker, n in sorted(speaker_counts.items()):
        print(f"  {speaker:>20}: {n}")

    non_pass = sum(n for s, n in status_counts.items() if s != "pass")
    if non_pass:
        print(f"\n{non_pass} rows are not status=pass -- filter those out before training, "
              "or ask the contributor to re-record.")


if __name__ == "__main__":
    main()
