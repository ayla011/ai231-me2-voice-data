# Contributing your recordings

Takes about 20-30 minutes for the full prompt list (62 prompts x 2 takes
= 124 clips at ~4s each, plus a few re-takes).

## 0. Prerequisites

- Python 3.10+ and `git`
- A working microphone, in as quiet a room as you can manage
- `cmake` and a C/C++ compiler (macOS: `xcode-select --install`; Linux:
  `sudo apt install build-essential cmake`; Windows: use WSL for this
  part, it's much less painful than native whisper.cpp builds)

## 1. Clone and install

```
git clone <this repo's URL>
cd ai231-me2-voice-data
python3 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Build whisper.cpp (one-time)

```
bash scripts/setup_whisper.sh
```

This clones+builds `whisper.cpp` into `~/whisper.cpp` and downloads the
`base.en` model (~140MB). Takes a few minutes. Note the `whisper-cli`
and model paths it prints at the end — you'll pass them to `validate.py`.

## 3. Record

```
python scripts/record.py --speaker-id <yourid>
```

Use the `speaker_id` convention your group agreed on (see
`docs/drive_folder_structure.md`) — it becomes both your output folder
name and your Drive folder name, so get it right the first time.

For each prompt: read it naturally (don't over-enunciate), press Enter,
speak within the recording window, then Enter to accept or `r` to
re-take. `s` skips a prompt, `q` stops and saves what you have so far —
safe to resume later with `--resume`.

Options:
- `--takes 3` — more takes per prompt (default 2)
- `--labels TIMER ALARM` — only record specific intents (default: all)
- `--resume` — skip prompts you've already recorded (checked against
  your `manifest.csv`)

## 4. Validate

```
python scripts/validate.py --speaker-id <yourid> \
    --whisper-bin ~/whisper.cpp/build/bin/whisper-cli \
    --whisper-model ~/whisper.cpp/models/ggml-base.en.bin
```

This transcribes every clip with whisper.cpp and writes
`whisper_transcript`, `wer`, and `status` into your `manifest.csv`:

- `pass` — good, nothing to do
- `flag_silent` — whisper heard nothing; the clip is likely empty or the
  mic wasn't capturing. Re-record it.
- `flag_wer` — whisper's transcript is quite different from the prompt.
  Listen to the clip yourself first — for the numeric/time prompts
  (`TIMER`, `ALARM`, `TEMPERATURE`, `BRIGHTNESS`) this can be a
  formatting artifact (whisper writes "20%" for "20 percent"), not an
  actual misread. Only re-record if it's genuinely wrong.
- `flag_corrupt` — the file didn't load at all. Re-record it.

To re-record just the flagged ones: delete that row from `manifest.csv`
and its `.wav` file, then run:

```
python scripts/record.py --speaker-id <yourid> --resume
```

It'll skip everything already in your manifest and only prompt you for
what's missing. Re-run `validate.py` afterward.

## 5. Upload

Once you're happy with your `pass` rate, upload your entire
`recordings/<yourid>/` folder to the shared Drive, following
`docs/drive_folder_structure.md` exactly (folder name = your
`speaker_id`). Don't commit recordings to this git repo — see
`.gitignore`; audio lives on Drive only.
