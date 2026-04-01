#!/usr/bin/env bash
# =============================================================================
# seed-dev.sh — Run the CartSnitch seed runner against the dev database.
#
# Usage:
#   ./seed-dev.sh              Run full seed against dev
#   ./seed-dev.sh --dry-run    Show planned record counts without writing
#   ./seed-dev.sh --help       Show this help
#
# Prerequisites:
#   - kubectl configured for the cartsnitch-dev cluster
#   - Namespace cartsnitch-dev exists (CNPG Postgres must be running)
#
# What it does:
#   1. Starts a background port-forward to cartsnitch-pg-rw:5432
#   2. Waits for the tunnel to be ready
#   3. Runs python -m cartsnitch_common.seed with --database-url pointing
#      to localhost:<forwarded-port>/cartsnitch
#   4. Cleans up the port-forward on exit (normal, interrupt, or error)
# =============================================================================

set -euo pipefail

# --- Config -------------------------------------------------------------------
readonly NAMESPACE="cartsnitch-dev"
readonly SVC_NAME="cartsnitch-pg-rw"
readonly LOCAL_PORT="5433"          # use a non-privileged port to avoid conflicts
readonly DB_NAME="cartsnitch"
readonly PG_USER="cartsnitch"
# Retrieve password from the CNPG credentials secret
readonly PG_PASSWORD="$(
  kubectl get secret cartsnitch-pg-credentials \
    -n "$NAMESPACE" \
    -o jsonpath='{.data.password}' \
  | base64 -d
)"
readonly DB_URL="postgresql://${PG_USER}:${PG_PASSWORD}@localhost:${LOCAL_PORT}/${DB_NAME}"

# --- Helpers ------------------------------------------------------------------
log()  { echo "[seed-dev] $*"; }
fail() { log "ERROR: $*" >&2; exit 1; }

# Cleanup port-forward and exit.
cleanup() {
  if [[ -n "${PF_PID:-}" ]]; then
    log "Stopping port-forward (PID $PF_PID)..."
    kill "$PF_PID" 2>/dev/null || true
    wait "$PF_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

# --- Args ---------------------------------------------------------------------
DRY_RUN=""
HELP_FLAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)  DRY_RUN="--dry-run"; shift ;;
    --help)     HELP_FLAG="1"; shift ;;
    *)          fail "Unknown argument: $1";;
  esac
done

if [[ -n "$HELP_FLAG" ]]; then
  sed -n '3,/^# ---/p' "$0" | head -n -1 | sed 's/^# //'
  echo ""
  echo "Additional arguments are passed through to the seed runner."
  echo "Common seed-runner options:"
  echo "  --dry-run          Show planned record counts without writing"
  echo "  --seed N           Set random seed (default: 42)"
  exit 0
fi

# --- Prerequisites ------------------------------------------------------------
if ! command -v kubectl &>/dev/null; then
  fail "kubectl not found — must be installed and configured."
fi

# --- Port-forward -------------------------------------------------------------
log "Starting port-forward ${SVC_NAME}:5432 -> localhost:${LOCAL_PORT} ..."
kubectl port-forward \
  -n "$NAMESPACE" \
  svc/"$SVC_NAME" \
  "${LOCAL_PORT}:5432" \
  &>/dev/null &
PF_PID=$!

# Give the tunnel a moment to establish
sleep 2

# Verify the tunnel is up
if ! kill -0 "$PF_PID" 2>/dev/null; then
  fail "Port-forward failed to start."
fi
log "Port-forward active (PID $PF_PID) on localhost:${LOCAL_PORT}"

# --- Seed --------------------------------------------------------------------
log "Running seed against dev database..."
set -x
python -m cartsnitch_common.seed --database-url "$DB_URL" $DRY_RUN
set +x

log "Done."
