#!/usr/bin/env python3
"""Guided recording session for the AI231 ME2 voice-data pool.

Walks through schema/prompts.csv one utterance at a time. For each take:
record -> whisper.cpp transcribes it immediately -> you judge whether to
keep it or retry, right there. Nothing is saved until you approve it, so
whatever ends up in your manifest.csv is already the clean, final take --
there's no separate validation pass before upload.

Usage:
  python scripts/record.py --speaker-id juandelacruz \
      --whisper-bin ~/whisper.cpp/build/bin/whisper-cli \
      --whisper-model ~/whisper.cpp/models/ggml-base.en.bin
  python scripts/record.py --speaker-id juandelacruz --approved-takes 3 ...
  python scripts/record.py --speaker-id juandelacruz --labels TIMER ALARM ...
  python scripts/record.py --speaker-id juandelacruz --resume ...   # skip prompts already fully approved
"""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import sounddevice as sd
import soundfile as sf

REPO_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_RATE = 16000
MANIFEST_FIELDS = [
    "speaker_id", "prompt_id", "label", "type", "text", "slot_value",
    "take", "filename", "recorded_at", "whisper_transcript", "wer", "status",
]


def load_prompts(path: Path) -> list[dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def load_existing_manifest(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open() as f:
        return list(csv.DictReader(f))


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


def resolve_whisper_bin(path_str: str) -> str:
    p = Path(path_str).expanduser()
    if p.is_file():
        return str(p)
    which = shutil.which(path_str)
    if which:
        return which

    search_root = Path.home() / "whisper.cpp"
    if search_root.exists():
        for name in ("whisper-cli", "whisper-cli.exe", "main", "main.exe"):
            hits = list(search_root.rglob(name))
            if hits:
                print(f"Note: '{path_str}' not found; using discovered binary instead: {hits[0]}")
                return str(hits[0])

    sys.exit(
        f"whisper.cpp binary not found: '{path_str}'\n"
        f"Run: bash scripts/setup_whisper.sh\n"
        f"It prints the real 'whisper-cli:' path at the end -- pass that with --whisper-bin.\n"
        f"Or search yourself: find ~/whisper.cpp -iname 'whisper-cli*' -o -iname 'main*'"
    )


def resolve_whisper_model(path_str: str) -> str:
    p = Path(path_str).expanduser()
    if p.is_file():
        return str(p)
    sys.exit(
        f"whisper.cpp model not found: '{path_str}'\n"
        f"Run: bash scripts/setup_whisper.sh (downloads models/ggml-base.en.bin)"
    )


def record_clip(duration: float):
    print(f"  Recording for {duration:.1f}s... speak now.")
    audio = sd.rec(int(duration * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="float32")
    sd.wait()
    return audio.flatten()


def transcribe(whisper_bin: str, model: str, audio, tmp_path: Path) -> str:
    sf.write(str(tmp_path), audio, SAMPLE_RATE, subtype="PCM_16")
    result = subprocess.run(
        [whisper_bin, "-m", model, "-f", str(tmp_path), "-nt"],
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def record_and_approve(prompt: dict, take: int, args) -> dict | None:
    """Record/transcribe/judge loop for one take. Returns the manifest
    row once approved, {"__quit__": True} on quit, or None if skipped."""
    tmp_path = REPO_ROOT / ".tmp_take.wav"
    expected_words = normalize(prompt["text"])

    while True:
        cmd = input("  [Enter to record, s=skip prompt, q=quit] > ").strip().lower()
        if cmd == "q":
            return {"__quit__": True}
        if cmd == "s":
            return None

        audio = record_clip(args.duration)
        print("  Transcribing...")
        hyp_text = transcribe(args.whisper_bin, args.whisper_model, audio, tmp_path)
        wer = word_error_rate(expected_words, normalize(hyp_text)) if hyp_text else 1.0
        print(f"    expected: \"{prompt['text']}\"")
        print(f"    whisper:  \"{hyp_text or '(nothing heard)'}\"  (wer={wer:.2f})")

        decision = input("  [Enter=keep, r=retry, p=play back, s=skip prompt, q=quit] > ").strip().lower()
        if decision == "p":
            sd.play(audio, SAMPLE_RATE)
            sd.wait()
            decision = input("  [Enter=keep, r=retry, s=skip prompt, q=quit] > ").strip().lower()
        if decision == "q":
            return {"__quit__": True}
        if decision == "s":
            return None
        if decision == "r":
            continue

        filename = f"{prompt['prompt_id']}_t{take}.wav"
        out_dir = REPO_ROOT / "recordings" / args.speaker_id
        sf.write(str(out_dir / filename), audio, SAMPLE_RATE, subtype="PCM_16")
        return {
            "speaker_id": args.speaker_id,
            "prompt_id": prompt["prompt_id"],
            "label": prompt["label"],
            "type": prompt["type"],
            "text": prompt["text"],
            "slot_value": prompt["slot_value"],
            "take": take,
            "filename": filename,
            "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "whisper_transcript": hyp_text,
            "wer": f"{wer:.3f}",
            "status": "approved",
        }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--speaker-id", required=True, help="your name or student number, no spaces (e.g. juandelacruz)")
    ap.add_argument("--prompts", default=str(REPO_ROOT / "schema/prompts.csv"))
    ap.add_argument("--whisper-bin", default="whisper-cli")
    ap.add_argument("--whisper-model", required=True)
    ap.add_argument("--approved-takes", type=int, default=2, help="approved recordings wanted per prompt")
    ap.add_argument("--duration", type=float, default=5.0, help="seconds per take")
    ap.add_argument("--labels", nargs="*", default=None, help="only record these labels (default: all)")
    ap.add_argument("--resume", action="store_true", help="skip prompts already fully approved in your manifest")
    args = ap.parse_args()

    args.whisper_bin = resolve_whisper_bin(args.whisper_bin)
    args.whisper_model = resolve_whisper_model(args.whisper_model)

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
    approved_counts: dict[str, int] = {}
    for row in existing:
        approved_counts[row["prompt_id"]] = approved_counts.get(row["prompt_id"], 0) + 1

    print(f"Speaker: {args.speaker_id}")
    print(f"{len(prompts)} prompts, {args.approved_takes} approved takes each.\n")

    new_rows: list[dict] = []
    quit_early = False
    for i, prompt in enumerate(prompts, start=1):
        already = approved_counts.get(prompt["prompt_id"], 0)
        if args.resume and already >= args.approved_takes:
            continue
        for take in range(already + 1, args.approved_takes + 1):
            print(f"[{i}/{len(prompts)}] ({prompt['label']}, take {take}/{args.approved_takes}) say:")
            print(f"    \"{prompt['text']}\"")
            row = record_and_approve(prompt, take, args)
            if row is None:
                break  # skipped -- move to next prompt
            if row.get("__quit__"):
                quit_early = True
                break
            new_rows.append(row)
            print("  approved.\n")
        if quit_early:
            break

    tmp_path = REPO_ROOT / ".tmp_take.wav"
    if tmp_path.exists():
        tmp_path.unlink()

    if not new_rows:
        print("\nNo new recordings.")
        return

    all_rows = existing + new_rows
    with manifest_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    print(f"\nSaved {len(new_rows)} new approved recordings. Manifest: {manifest_path}")
    if quit_early:
        print(f"Resume later with: python scripts/record.py --speaker-id {args.speaker_id} --resume "
              f"--whisper-bin {args.whisper_bin} --whisper-model {args.whisper_model}")


if __name__ == "__main__":
    main()
