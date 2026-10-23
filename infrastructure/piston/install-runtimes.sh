#!/usr/bin/env sh
set -eu

PISTON_URL="${PISTON_URL:-http://localhost:2000}"
PISTON_URL="${PISTON_URL%/}"
STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-120}"

log() {
  printf '%s\n' "$*"
}

wait_for_piston() {
  elapsed=0
  until curl -fsS "$PISTON_URL/api/v2/runtimes" >/dev/null 2>&1; do
    if [ "$elapsed" -ge "$STARTUP_TIMEOUT" ]; then
      log "Piston is not reachable at $PISTON_URL after ${STARTUP_TIMEOUT}s." >&2
      log "Start it with: docker compose -f infrastructure/piston/docker-compose.yml up -d" >&2
      exit 1
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
}

runtime_installed() {
  language="$1"
  version="$2"
  curl -fsS "$PISTON_URL/api/v2/runtimes" |
    grep -F "\"language\":\"$language\",\"version\":\"$version\"" >/dev/null 2>&1
}

install_runtime() {
  language="$1"
  version="$2"

  if runtime_installed "$language" "$version"; then
    log "$language $version is already installed."
    return
  fi

  log "Installing $language $version..."
  curl -fsS -X POST "$PISTON_URL/api/v2/packages" \
    -H "Content-Type: application/json" \
    -d "{\"language\":\"$language\",\"version\":\"$version\"}" >/dev/null

  if ! runtime_installed "$language" "$version"; then
    log "Piston did not report $language $version after installation." >&2
    exit 1
  fi

  log "$language $version installed."
}

wait_for_piston
install_runtime python 3.12.0
install_runtime php 8.2.3
install_runtime typescript 5.0.3

log "Piston is ready at $PISTON_URL"
