#!/usr/bin/env python3
"""Validate your recordings with whisper.cpp before uploading.

Two things are checked per clip:
  1. Machine-readable at all: the file loads, isn't near-silent, and
     whisper.cpp produces a non-empty transcript. If this fails, the mic
     probably didn't capture anything usable -- re-record.
  2. Rough match to the prompt: word error rate (WER) between what you
     were supposed to say and what whisper.cpp heard. High WER usually
     means a misread, mumble, clipped word, or too much background noise.

WER on the numeric/time prompts (TIMER, ALARM, TEMPERATURE, BRIGHTNESS)
will run higher than on plain-word prompts -- whisper.cpp often writes
"20%" for spoken "twenty percent", which won't string-match "20 percent"
even though the recording is fine. Skim `flag_wer` rows by ear before
re-recording; don't trust the number blindly for those labels.

Usage:
  python scripts/validate.py --speaker-id juandelacruz \
      --whisper-model ~/whisper.cpp/models/ggml-base.en.bin
"""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parents[1]
MIN_DURATION_SEC = 0.2
OUTPUT_FIELDS = [
    "speaker_id", "prompt_id", "label", "type", "text", "slot_value",
    "take", "filename", "recorded_at", "whisper_transcript", "wer", "status",
]


def normalize(text: str) -> list[str]:
    text = text.lower()
    text = text.replace("%", " percent")
    text = re.sub(r"(\d):(\d\d)", r"\1 \2", text)
    text = re.sub(r"[^a-z0-9' ]", " ", text)
    return text.split()


def word_error_rate(ref: list[str], hyp: list[str]) -> float:
    n, m = len(ref), len(hyp)
    if n == 0:
        return 0.0 if m == 0 else 1.0
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref[i - 1] == hyp[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[n][m] / n


def transcribe(whisper_bin: str, model: str, wav_path: Path) -> str:
    result = subprocess.run(
        [whisper_bin, "-m", model, "-f", str(wav_path), "-nt"],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--speaker-id", required=True)
    ap.add_argument("--whisper-bin", default="whisper-cli")
    ap.add_argument("--whisper-model", required=True)
    ap.add_argument("--threshold", type=float, default=0.5, help="WER above this flags the clip for re-recording")
    args = ap.parse_args()

    speaker_dir = REPO_ROOT / "recordings" / args.speaker_id
    manifest_path = speaker_dir / "manifest.csv"
    if not manifest_path.exists():
        sys.exit(f"No manifest at {manifest_path} -- run scripts/record.py first.")

    with manifest_path.open() as f:
        rows = list(csv.DictReader(f))

    print(f"Validating {len(rows)} clips for speaker_id={args.speaker_id!r}...\n")

    counts = {"pass": 0, "flag_silent": 0, "flag_wer": 0, "flag_corrupt": 0}
    for i, row in enumerate(rows):
        wav_path = speaker_dir / row["filename"]
        label_tag = f"[{i+1}/{len(rows)}] {row['filename']}"

        try:
            audio, sr = sf.read(str(wav_path))
            duration = len(audio) / sr
        except Exception as e:
            print(f"{label_tag}: CORRUPT/UNREADABLE ({e})")
            row.update(whisper_transcript="", wer="", status="flag_corrupt")
            counts["flag_corrupt"] += 1
            continue

        if duration < MIN_DURATION_SEC:
            print(f"{label_tag}: too short ({duration:.2f}s)")
            row.update(whisper_transcript="", wer="", status="flag_silent")
            counts["flag_silent"] += 1
            continue

        hyp_text = transcribe(args.whisper_bin, args.whisper_model, wav_path)
        if not hyp_text.strip():
            print(f"{label_tag}: whisper heard nothing -- likely silent/inaudible")
            row.update(whisper_transcript="", wer="1.0", status="flag_silent")
            counts["flag_silent"] += 1
            continue

        wer = word_error_rate(normalize(row["text"]), normalize(hyp_text))
        status = "flag_wer" if wer > args.threshold else "pass"
        counts[status] += 1
        flag = "  <-- FLAG" if status == "flag_wer" else ""
        print(f"{label_tag}: wer={wer:.2f}{flag}")
        print(f"    expected: \"{row['text']}\"")
        print(f"    whisper:  \"{hyp_text}\"")
        row.update(whisper_transcript=hyp_text, wer=f"{wer:.3f}", status=status)

    with manifest_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        w.writeheader()
        w.writerows(rows)

    total = len(rows)
    flagged = total - counts["pass"]
    print(f"\n{counts['pass']}/{total} passed. "
          f"{counts['flag_silent']} silent/inaudible, "
          f"{counts['flag_wer']} high-WER, "
          f"{counts['flag_corrupt']} corrupt.")
    if flagged:
        print("Re-record the flagged rows (status != pass in manifest.csv), "
              "then re-run this script -- it re-checks every row each time.")
    print(f"\nManifest updated: {manifest_path}")


if __name__ == "__main__":
    main()
