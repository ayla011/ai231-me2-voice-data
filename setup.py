#!/usr/bin/env python3
"""One-shot setup for the AI231 ME2 voice-data pool.

This is NOT a packaging setup.py (nothing here gets installed as a
package) -- it's a plain bootstrap script. Run it with whatever Python
environment you intend to record with already active: a conda env, a
venv created by VS Code's Python extension, or a plain `venv`. It
installs into that same interpreter (via `sys.executable`), so it never
creates or fights with a separate environment of its own.

Usage:
  conda activate myenv            # or select your venv's interpreter in VS Code
  python setup.py

What it does:
  1. Checks the Python version (3.10+).
  2. pip installs -r requirements.txt into the active interpreter.
  3. Pre-downloads the default whisper model (base.en) so your first
     recording session doesn't stall on a download mid-prompt.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
MIN_PYTHON = (3, 10)
DEFAULT_MODEL = "base.en"


def main():
    if sys.version_info < MIN_PYTHON:
        sys.exit(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ required, "
            f"found {sys.version_info.major}.{sys.version_info.minor}.\n"
            f"pywhispercpp itself fails to import on 3.9 and older (it uses "
            f"newer type-hint syntax internally) -- this isn't optional.\n"
            f"Fix: conda create -n voicedata python=3.10 (or newer), or in VS "
            f"Code create/select a 3.10+ venv for this folder. Then re-run "
            f"'python setup.py'."
        )

    print(f"Using interpreter: {sys.executable}\n")

    print("Installing dependencies...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(REPO_ROOT / "requirements.txt")],
        check=True,
    )

    print("\nPre-downloading the whisper model (one-time, ~140MB for base.en)...")
    from pywhispercpp.model import Model  # noqa: E402  (import after install)

    Model(DEFAULT_MODEL, redirect_whispercpp_logs_to=False)

    print("\nSetup complete. Next:")
    print(f"  python scripts/record.py --speaker-id <yourid>")


if __name__ == "__main__":
    main()
