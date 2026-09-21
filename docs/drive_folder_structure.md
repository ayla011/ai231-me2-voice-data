# Shared Drive folder structure

Create one shared Drive folder (e.g. `AI231-ME2-Voice-Data`) and share it
with the class as **Editor, restricted to class members** — do not set it
to "anyone with the link." This folder holds actual voice recordings of
your classmates, which is different from the GitHub repo (code + schema
only, no voices) that's fine to keep public.

```
AI231-ME2-Voice-Data/              (shared Drive folder root)
  raw/
    <speaker_id>/                  one folder per contributor
      manifest.csv                 written by record.py -- every row is
                                    already status=approved (the contributor
                                    judged it live against the whisper.cpp
                                    transcript before it was ever saved)
      TIMER_V1_1_t1.wav
      TIMER_V1_1_t2.wav
      ALARM_V2_3_t1.wav
      ...
  _merged/                         maintainer-only output of
                                    scripts/build_master_manifest.py
                                    (master_manifest.csv + pooled stats)
```

## Rules that keep pooling painless later

- **`speaker_id` is the folder name, and it must exactly match** what you
  passed to `--speaker-id` in `record.py`. Use a fixed convention agreed
  by the group up front, e.g. `firstnamelastinitial` (`juandelacruz`) or
  your student number (`2024-12345`) — lowercase, no spaces, no special
  characters. Whatever you pick, don't change it mid-way; the merge
  script joins on this.
- Upload your **whole `recordings/<speaker_id>/` folder as-is** once
  you're done recording (`manifest.csv` already has
  `whisper_transcript` / `wer` / `status` filled in for every approved
  take) — don't hand-edit filenames or the CSV.
- If you go back and re-record something later, just re-upload that
  `.wav` plus the updated `manifest.csv` to overwrite what's there; no
  need to re-upload everything.
- One folder per person. If you record in two sessions (e.g. added more
  takes later), upload into the *same* `<speaker_id>/` folder, don't
  create a second one.
