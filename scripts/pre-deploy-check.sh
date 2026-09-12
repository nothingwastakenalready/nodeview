#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$project_dir"
python_bin="${PYTHON:-python3}"
if [ -x "$project_dir/.venv/bin/python" ]; then
  python_bin="$project_dir/.venv/bin/python"
fi

"$python_bin" -m pytest

cd "$project_dir/web"
npm test
npm run build

cd "$project_dir"
docker compose config >/dev/null
