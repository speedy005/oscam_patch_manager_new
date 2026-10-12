#!/bin/sh
# Linux/macOS launcher for the cross-platform Python installer.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
    exec python3 "$SCRIPT_DIR/installer.py" "$@"
fi
if command -v python >/dev/null 2>&1; then
    exec python "$SCRIPT_DIR/installer.py" "$@"
fi
echo "Python 3 was not found. Please install Python 3 and run this script again." >&2
exit 1
