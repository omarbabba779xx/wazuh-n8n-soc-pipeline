#!/usr/bin/env bash
# Sends a sample alert to the n8n webhook to verify the pipeline end to end.
#
# Usage:
#   WAZUH_N8N_TOKEN=your_token ./test-webhook.sh sample-high-alert.json
#
set -euo pipefail

PAYLOAD_FILE="${1:-sample-high-alert.json}"
WEBHOOK_URL="${WAZUH_N8N_WEBHOOK_URL:-http://127.0.0.1:5678/webhook/wazuh-alert}"
TOKEN="${WAZUH_N8N_TOKEN:?Set WAZUH_N8N_TOKEN before running this script}"

curl -s -o /tmp/webhook_response.json -w 'HTTP:%{http_code}\n' \
  -X POST "$WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -H "X-Wazuh-Token: $TOKEN" \
  --data @"$PAYLOAD_FILE"

cat /tmp/webhook_response.json
echo
