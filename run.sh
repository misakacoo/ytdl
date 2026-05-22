#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"

if [[ ! -x "$VENV_PYTHON" ]]; then
  echo "未检测到虚拟环境，请先执行：bash install.sh"
  exit 1
fi

exec "$VENV_PYTHON" "$SCRIPT_DIR/downloader.py" "$@"
