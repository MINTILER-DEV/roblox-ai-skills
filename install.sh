#!/usr/bin/env bash
# Install the Roblox skills and custom agents for Codex (macOS / Linux / Git Bash).
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
if command -v python3 >/dev/null 2>&1; then
  python3 "$here/scripts/install.py" "$@"
elif command -v python >/dev/null 2>&1; then
  python "$here/scripts/install.py" "$@"
else
  echo "Python 3.11+ is required. Install it from https://www.python.org/downloads/." >&2
  exit 1
fi
