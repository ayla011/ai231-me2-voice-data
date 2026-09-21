#!/usr/bin/env bash
# Builds whisper.cpp and downloads the small English model used by
# scripts/validate.py. Run once. Requires git, cmake, and a C++ compiler
# (macOS: Xcode Command Line Tools; Linux: build-essential).
#
# Usage: bash scripts/setup_whisper.sh [install_dir]
set -euo pipefail

INSTALL_DIR="${1:-$HOME/whisper.cpp}"

if [ ! -d "$INSTALL_DIR" ]; then
  git clone https://github.com/ggml-org/whisper.cpp.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"
cmake -B build
cmake --build build -j --config Release

bash ./models/download-ggml-model.sh base.en

BIN="$(find build -type f -name whisper-cli | head -n1)"
MODEL="$INSTALL_DIR/models/ggml-base.en.bin"

echo
echo "Done."
echo "whisper-cli:  $BIN"
echo "model:        $MODEL"
echo
echo "Add whisper-cli to your PATH, or pass it explicitly:"
echo "  python scripts/validate.py --speaker-id you --whisper-bin \"$BIN\" --whisper-model \"$MODEL\""
