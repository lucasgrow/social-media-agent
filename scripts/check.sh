#!/usr/bin/env bash
# scripts/check.sh — run quality gates locally before commit
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."

echo "==> ruff lint"
.venv/bin/ruff check .

echo "==> pytest"
.venv/bin/pytest -v

echo "==> OK: all checks passed"
