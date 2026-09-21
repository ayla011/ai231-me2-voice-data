# Contributing your recordings

Takes about 20-30 minutes for the full prompt list (62 prompts x 2
approved takes = 124 approved clips at 5s each). You can retry a take as
many times as you want before approving it — only approved takes count.

## 0. Prerequisites

- Python 3.10+ and `git`
- A working microphone, in as quiet a room as you can manage
- `cmake` and a C/C++ compiler (macOS: `xcode-select --install`; Linux:
  `sudo apt install build-essential cmake`; Windows: use WSL for this
  part, it's much less painful than native whisper.cpp builds)

## 1. Clone and install

```
git clone https://github.com/ayla011/ai231-me2-voice-data.git
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
and model paths it prints at the end — you'll pass them to `record.py`.

## 3. Record, transcribe, judge, approve

```
python scripts/record.py --speaker-id <yourid> \
    --whisper-bin ~/whisper.cpp/build/bin/whisper-cli \
    --whisper-model ~/whisper.cpp/models/ggml-base.en.bin
```

Use the `speaker_id` convention your group agreed on (see
`docs/drive_folder_structure.md`) — it becomes both your output folder
name and your Drive folder name, so get it right the first time.

For each prompt, one take at a time:

1. It prints the prompt. Press Enter, speak within the recording window.
2. whisper.cpp transcribes what it heard and shows it next to the
   expected text (with a rough WER, just as a hint).
3. You decide: `Enter` = keep this take, `r` = retry, `p` = play it back
   first, `s` = skip this prompt, `q` = stop (safe to resume later).

Nothing gets written to `manifest.csv` or saved as a `.wav` until you
press `Enter` to keep it — so **by the time a take is saved, you've
already approved it**. There's no separate validation pass; what you
upload is what's used.

For the numeric/time prompts (`TIMER`, `ALARM`, `TEMPERATURE`,
`BRIGHTNESS`), don't be surprised if whisper's transcript looks
"different" even when your recording is fine — it often writes "20%"
for spoken "20 percent". Trust your ear (use `p` to play it back) over
the WER number; the transcript is there to catch actual
silence/mumbles/misreads, not to gate on exact string matches.

Options:
- `--approved-takes 3` — how many approved recordings you want per
  prompt (default 2)
- `--labels TIMER ALARM` — only record specific intents (default: all)
- `--resume` — skip prompts that already have enough approved takes in
  your manifest (to redo a specific one anyway, delete its row from
  `manifest.csv` and its `.wav` first, then run with `--resume`)

## 4. Upload

Once you're through the list, upload your entire `recordings/<yourid>/`
folder to the shared Drive, following `docs/drive_folder_structure.md`
exactly (folder name = your `speaker_id`). Don't commit recordings to
this git repo — see `.gitignore`; audio lives on Drive only.
