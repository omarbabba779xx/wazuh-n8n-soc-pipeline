#!/usr/bin/env bash
# Sends a sample alert to the n8n webhook to verify the pipeline end to end.
#
# Usage (from the repository root):
#   tests/test-webhook.sh tests/sample-high-alert.json
#
# Reads WAZUH_N8N_WEBHOOK_URL / WAZUH_N8N_TOKEN from the environment if set,
# otherwise auto-loads them from a .env file at the repository root.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -z "${WAZUH_N8N_TOKEN:-}" ] && [ -f "$REPO_ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_ROOT/.env"
  set +a
fi

PAYLOAD_FILE="${1:-$SCRIPT_DIR/sample-high-alert.json}"
WEBHOOK_URL="${WAZUH_N8N_WEBHOOK_URL:-http://127.0.0.1:5678/webhook/wazuh-alert}"
TOKEN="${WAZUH_N8N_TOKEN:?Set WAZUH_N8N_TOKEN (env var or repo-root .env) before running this script}"

curl -s -o /tmp/webhook_response.json -w 'HTTP:%{http_code}\n' \
  -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -H "X-Wazuh-Token: $TOKEN" \
  --data @"$PAYLOAD_FILE"

cat /tmp/webhook_response.json
echo
