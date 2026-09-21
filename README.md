# AI231 ME2 — Voice Data Pool

Recording tool for pooling classmates' voice samples for the AI231
Machine Exercise 2 (on-device Voice Command Model) group dataset. Every
contributor reads the same fixed prompt list, records locally, and
whisper.cpp checks each clip is actually machine-readable before it goes
into the shared pool.

**Scope & privacy:** this repo (code, prompt schema, docs) is public and
contains no one's voice. The actual recordings go to a separate,
access-restricted Drive folder — never here. See
`docs/drive_folder_structure.md`.

## Quickstart

```
git clone <this repo's URL>
cd ai231-me2-voice-data
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
bash scripts/setup_whisper.sh                 # one-time whisper.cpp build

python scripts/record.py --speaker-id <yourid>
python scripts/validate.py --speaker-id <yourid> \
    --whisper-bin ~/whisper.cpp/build/bin/whisper-cli \
    --whisper-model ~/whisper.cpp/models/ggml-base.en.bin
```

Then upload `recordings/<yourid>/` to the shared Drive folder. Full
walkthrough: **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Layout

```
schema/prompts.csv          62 prompts: 13 fixed intents (2 phrasings each)
                             + 6 slotted intents (2 phrasings x 3 example
                             values each). One row = one utterance to say.
scripts/
  setup_whisper.sh           builds whisper.cpp + downloads the base.en model
  record.py                  guided recording session -> recordings/<speaker_id>/
  validate.py                whisper.cpp QA pass: flags silent/corrupt/high-WER clips
  build_master_manifest.py   maintainer-only: merges every contributor's
                              manifest.csv (from Drive) into one master CSV
docs/drive_folder_structure.md   how the shared Drive folder is organized
CONTRIBUTING.md                   step-by-step contributor guide
```

## How validation works

`validate.py` transcribes each clip with whisper.cpp and checks two
things: that whisper produces *any* real transcript (catches silent,
corrupted, or badly-clipped recordings — "is this machine-readable at
all"), and the word-error-rate against the expected prompt text (catches
misreads, mumbles, wrong intent). Clips are written back into
`manifest.csv` as `pass`, `flag_silent`, `flag_wer`, or `flag_corrupt`.
whisper.cpp here is strictly a QA tool for this pooling step, not the
model being built.

## Prompt schema source

`schema/prompts.csv` is generated from the group's shared prompt sheet
(the 2-variation / 3-example-value table). If the schema changes, edit
that CSV directly — it's the single source of truth all scripts read
from.
