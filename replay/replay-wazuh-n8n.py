#!/usr/bin/env python3
"""
Drains the local disk queue built by wazuh/custom-n8n when the n8n
webhook was unreachable. Run periodically by wazuh-n8n-replay.timer.

Install at:
  /var/ossec/integrations/n8n_queue_retry.py
"""
import json
import logging
import os
import glob
import requests

logging.basicConfig(
    filename="/var/ossec/logs/integrations.log",
    level=logging.INFO,
    format="%(asctime)s n8n-queue-retry: %(message)s",
)

TOKEN_FILE = "/var/ossec/etc/n8n_token"
QUEUE_DIR = "/var/ossec/var/n8n_queue"
WEBHOOK_URL = "http://127.0.0.1:5678/webhook/wazuh-alert"


def load_token() -> str:
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def main() -> None:
    if not os.path.isdir(QUEUE_DIR):
        return

    files = sorted(glob.glob(os.path.join(QUEUE_DIR, "*.json")))
    if not files:
        return

    token = load_token()
    headers = {"Content-Type": "application/json", "X-Wazuh-Token": token}

    sent = 0
    failed = 0
    for fpath in files:
        try:
            with open(fpath) as f:
                payload = json.load(f)
            resp = requests.post(WEBHOOK_URL, headers=headers, data=json.dumps(payload), timeout=10)
            if resp.status_code < 400:
                os.remove(fpath)
                sent += 1
                logging.info(f"drained queued alert {payload.get('event_id')} -> HTTP {resp.status_code}")
            else:
                failed += 1
        except Exception as e:
            failed += 1
            logging.warning(f"retry still failing for {fpath}: {e}")

    if sent or failed:
        logging.info(f"queue drain pass: {sent} sent, {failed} still queued")


if __name__ == "__main__":
    main()
