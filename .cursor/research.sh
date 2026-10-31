#!/usr/bin/env bash
# Research entrypoint for the Cursor Cloud image.
# Forces the cookie lock, keeps Polymarket out of the source list, and
# refuses commands that install remote CLIs, probe Polymarket, or publish.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENGINE="${ROOT}/skills/last30days/scripts/last30days.py"

for arg in "$@"; do
  lower="$(printf '%s' "$arg" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    setup|doctor|--publish-html|--allow-browser-cookies|--probe)
      printf 'refused: %s is disabled in the Cursor Cloud research profile\n' "$arg" >&2
      exit 2
      ;;
  esac
done

export FROM_BROWSER=off
export BROWSER_CONSENT=false
export AGENTCOOKIE=off
export LAST30DAYS_SKIP_KEYCHAIN=1
export LAST30DAYS_TRUSTPILOT_NO_BROWSER=1
export LAST30DAYS_NATIVE_SEARCH=1
export LAST30DAYS_MEMORY_DIR="${LAST30DAYS_MEMORY_DIR:-/workspace/.last30days-out}"

case ",${EXCLUDE_SOURCES:-}," in
  *,polymarket,*) ;;
  *) EXCLUDE_SOURCES="${EXCLUDE_SOURCES:+${EXCLUDE_SOURCES},}polymarket" ;;
esac
export EXCLUDE_SOURCES

mkdir -p "$LAST30DAYS_MEMORY_DIR"

PYTHON="${LAST30DAYS_PYTHON:-python3}"
exec "$PYTHON" "$ENGINE" --no-browser-cookies "$@"
