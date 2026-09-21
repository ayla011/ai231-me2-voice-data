#!/usr/bin/env python3
"""Guided recording session for the AI231 ME2 voice-data pool.

Walks through schema/prompts.csv one utterance at a time, records N takes
of each (default 2), and saves 16kHz mono PCM16 wavs under
recordings/<speaker_id>/, appending metadata to
recordings/<speaker_id>/manifest.csv.

Usage:
  python scripts/record.py --speaker-id juandelacruz
  python scripts/record.py --speaker-id juandelacruz --takes 3
  python scripts/record.py --speaker-id juandelacruz --labels TIMER ALARM
  python scripts/record.py --speaker-id juandelacruz --resume   # skip prompts already recorded
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import sounddevice as sd
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 16000
MANIFEST_FIELDS = [
    "speaker_id", "prompt_id", "label", "type", "text", "slot_value",
    "take", "filename", "recorded_at",
]


def load_prompts(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def load_existing_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


def record_clip(duration: float) -> "any":
    print(f"  Recording for {duration:.1f}s... speak now.")
    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--speaker-id", required=True, help="your name or student number, no spaces (e.g. juandelacruz)")
    ap.add_argument("--prompts", default=str(REPO_ROOT / "schema/prompts.csv"))
    ap.add_argument("--takes", type=int, default=2, help="how many recordings per prompt")
    ap.add_argument("--duration", type=float, default=3.5, help="seconds per take")
    ap.add_argument("--labels", nargs="*", default=None, help="only record these labels (default: all)")
    ap.add_argument("--resume", action="store_true", help="skip (prompt_id, take) pairs already in your manifest")
    args = ap.parse_args()

    prompts = load_prompts(Path(args.prompts))
    if args.labels:
        wanted = set(args.labels)
        prompts = [p for p in prompts if p["label"] in wanted]
    if not prompts:
        sys.exit("No prompts matched --labels; check schema/prompts.csv for valid label names.")

    out_dir = REPO_ROOT / "recordings" / args.speaker_id
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.csv"
    existing = load_existing_manifest(manifest_path)
    done = {(r["prompt_id"], r["take"]) for r in existing} if args.resume else set()

    total_takes = len(prompts) * args.takes
    print(f"Speaker: {args.speaker_id}")
    print(f"{len(prompts)} prompts x {args.takes} takes = {total_takes} recordings.")
    print("For each take: Enter to record, 'r' to re-take, 's' to skip this prompt, 'q' to quit.\n")

    new_rows: list[dict] = []
    i = 0
    for prompt in prompts:
        i += 1
        skip_prompt = False
        for take in range(1, args.takes + 1):
            if (prompt["prompt_id"], str(take)) in done:
                continue
            print(f"[{i}/{len(prompts)}] ({prompt['label']}, take {take}/{args.takes}) say:")
            print(f"    \"{prompt['text']}\"")
            cmd = input("  > ").strip().lower()
            if cmd == "q":
                print("Quitting early.")
                _flush(existing, new_rows, manifest_path)
                return
            if cmd == "s":
                skip_prompt = True
                break

            while True:
                audio = record_clip(args.duration)
                redo = input("  Enter to accept, 'r' to re-take: ").strip().lower()
                if redo != "r":
                    break

            filename = f"{prompt['prompt_id']}_t{take}.wav"
            sf.write(str(out_dir / filename), audio, SAMPLE_RATE, subtype="PCM_16")
            new_rows.append({
                "speaker_id": args.speaker_id,
                "prompt_id": prompt["prompt_id"],
                "label": prompt["label"],
                "type": prompt["type"],
                "text": prompt["text"],
                "slot_value": prompt["slot_value"],
                "take": take,
                "filename": filename,
                "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            })
        if skip_prompt:
            continue

    _flush(existing, new_rows, manifest_path)


def _flush(existing: list[dict], new_rows: list[dict], manifest_path: Path) -> None:
    if not new_rows:
        print("\nNo new recordings.")
        return
    all_rows = existing + new_rows
    with manifest_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    print(f"\nSaved {len(new_rows)} new recordings. Manifest: {manifest_path}")
    print("Next: python scripts/validate.py --speaker-id " + new_rows[0]["speaker_id"])


if __name__ == "__main__":
    main()
