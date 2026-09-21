# AI231 ME2 — Voice Data Pool

Recording tool for pooling classmates' voice samples for the AI231
Machine Exercise 2 (on-device Voice Command Model) group dataset. Every
contributor reads the same fixed prompt list; for each take, whisper.cpp
transcribes it immediately and the contributor judges on the spot
whether to keep it or retry. Nothing gets saved until approved, so
everything that reaches the shared pool is already clean.

No compiler, cmake, or manual whisper.cpp build required — the whisper
model runs through [pywhispercpp](https://github.com/absadiki/pywhispercpp),
which ships prebuilt binaries for Windows, macOS, and Linux and downloads
the model automatically on first run.

**Scope & privacy:** this repo (code, prompt schema, docs) is public and
contains no one's voice. The actual recordings go to a separate,
access-restricted Drive folder — never here. See
`docs/drive_folder_structure.md`.

## Quickstart

Activate whatever Python environment you're recording with (a conda env,
or the venv VS Code creates when you pick an interpreter) — `setup.py`
installs into that same one, so there's no separate venv to set up
first.

```
git clone https://github.com/ayla011/ai231-me2-voice-data.git
cd ai231-me2-voice-data
python setup.py                               # installs deps + downloads the model, once

python scripts/record.py --speaker-id <yourid>
```

Then upload `recordings/<yourid>/` to the shared Drive folder (see
below). Full walkthrough: **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Uploading your recordings

1. After `record.py` finishes (everything in it is already approved),
   you'll have a folder at `recordings/<your-speaker-id>/` with your
   `.wav` files and one `manifest.csv`.
2. Go to the shared Drive folder: **`AI231-ME2-Voice-Data/raw/`**
3. Upload your entire `recordings/<your-speaker-id>/` folder into
   `raw/`, so it lands as:
   ```
   AI231-ME2-Voice-Data/raw/<your-speaker-id>/
     manifest.csv
     *.wav
   ```
4. **Your Drive folder name must exactly match the `--speaker-id` you
   used when recording** — lowercase, no spaces (e.g. `juandelacruz` or
   your student number `2024-12345`), matching whatever convention the
   group agreed on. This is what lets everyone's data merge
   automatically later.
5. Don't rename files or hand-edit `manifest.csv` afterward.
6. Recording more later? Upload into that *same* folder to add/overwrite
   files — don't create a second folder for yourself.
7. Nothing goes to GitHub — this repo is code/schema only. Drive is
   audio only.

The Drive folder itself should be shared as **Editor, restricted to
class members** — not "anyone with the link" — since it holds actual
voice recordings. Full layout and maintainer-side details:
**[docs/drive_folder_structure.md](docs/drive_folder_structure.md)**.

## Layout

```
setup.py                     one-shot installer: pip installs requirements
                              into whatever interpreter is active (conda/
                              venv/VS Code) and pre-downloads the model
schema/prompts.csv          62 prompts: 13 fixed intents (2 phrasings each)
                             + 6 slotted intents (2 phrasings x 3 example
                             values each). One row = one utterance to say.
scripts/
  record.py                  record -> whisper transcribes -> you approve -> saved,
                              one prompt at a time, into recordings/<speaker_id>/
  build_master_manifest.py   maintainer-only: merges every contributor's
                              manifest.csv (from Drive) into one master CSV
docs/drive_folder_structure.md   how the shared Drive folder is organized
CONTRIBUTING.md                   step-by-step contributor guide
```

## How the live QA works

`record.py` records one take, transcribes it with whisper.cpp right
away, and shows you both the expected prompt and what whisper heard
(plus a rough WER as a hint). You decide whether to keep it, retry, or
play it back first — nothing is written to disk or to `manifest.csv`
until you approve it. That's the whole validation step: by construction,
every row in an uploaded `manifest.csv` has `status=approved`. There's
no separate batch QA pass to run before uploading. whisper.cpp here is
strictly a live QA aid for this pooling step, not the model being built.

## Prompt schema source

`schema/prompts.csv` is generated from the group's shared prompt sheet
(the 2-variation / 3-example-value table). If the schema changes, edit
that CSV directly — it's the single source of truth all scripts read
from.
