# Contributing your recordings

Takes about 20-30 minutes for the full prompt list (62 prompts x 2
approved takes = 124 approved clips at 5s each). You can retry a take as
many times as you want before approving it — only approved takes count.

## 0. Prerequisites

- **Python 3.10 or newer**, already active as a conda env or a venv
  (e.g. the one VS Code creates when you pick an interpreter for this
  folder) — check with `python --version`. This is a hard requirement:
  `pywhispercpp` (below) fails to even import on 3.9 and older. If
  you're on an older default/base env, make a new one:
  `conda create -n voicedata python=3.10` or pick a 3.10+ interpreter in
  VS Code.
- `git`
- A working microphone, in as quiet a room as you can manage

No compiler, cmake, or manual whisper.cpp build needed — see step 2.

## 1. Clone

```
git clone https://github.com/ayla011/ai231-me2-voice-data.git
cd ai231-me2-voice-data
```

## 2. Set up (one-time)

With your conda env or venv active:

```
python setup.py
```

This pip-installs `requirements.txt` into whichever interpreter you had
active (it never creates a separate environment of its own) and
pre-downloads the default whisper model (`base.en`, ~140MB) so your
first recording session doesn't stall on a download. Windows, macOS, and
Linux all just work — the whisper binary comes prebuilt inside the
`pywhispercpp` package.

## 3. Record, transcribe, judge, approve

```
python scripts/record.py --speaker-id <yourid>
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
- `--model small.en` — use a bigger/more accurate whisper model instead
  of the default `base.en` (auto-downloaded on first use)

## 4. Upload

Once you're through the list, upload your entire `recordings/<yourid>/`
folder to the shared Drive, following `docs/drive_folder_structure.md`
exactly (folder name = your `speaker_id`). Don't commit recordings to
this git repo — see `.gitignore`; audio lives on Drive only.
