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
import time
import requests

logging.basicConfig(
    filename="/var/ossec/logs/integrations.log",
    level=logging.INFO,
    format="%(asctime)s n8n-queue-retry: %(message)s",
)

TOKEN_FILE = "/var/ossec/etc/n8n_token"
QUEUE_DIR = "/var/ossec/var/n8n_queue"
DEAD_LETTER_DIR = "/var/ossec/var/n8n_queue/dead-letter"
WEBHOOK_URL = "http://127.0.0.1:5678/webhook/wazuh-alert"
MAX_AGE_SECONDS = 24 * 60 * 60  # give up and quarantine after 24h of failed retries


def load_token() -> str:
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def quarantine(fpath: str) -> None:
    os.makedirs(DEAD_LETTER_DIR, exist_ok=True)
    dest = os.path.join(DEAD_LETTER_DIR, os.path.basename(fpath))
    os.replace(fpath, dest)
    logging.error(f"moved to dead-letter after exceeding {MAX_AGE_SECONDS}s of retries: {dest}")


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
    quarantined = 0
    for fpath in files:
        try:
            with open(fpath) as f:
                payload = json.load(f)
            # allow_redirects=False: a redirect must count as a failed
            # delivery, not be silently followed and misread as success.
            resp = requests.post(
                WEBHOOK_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=(3, 10),
                allow_redirects=False,
            )
            if 200 <= resp.status_code < 300:
                os.remove(fpath)
                sent += 1
                logging.info(f"drained queued alert {payload.get('event_id')} -> HTTP {resp.status_code}")
            elif time.time() - os.path.getmtime(fpath) > MAX_AGE_SECONDS:
                quarantine(fpath)
                quarantined += 1
            else:
                failed += 1
        except Exception as e:
            logging.warning(f"retry still failing for {fpath}: {e}")
            try:
                if time.time() - os.path.getmtime(fpath) > MAX_AGE_SECONDS:
                    quarantine(fpath)
                    quarantined += 1
                else:
                    failed += 1
            except FileNotFoundError:
                pass

    if sent or failed or quarantined:
        logging.info(f"queue drain pass: {sent} sent, {failed} still queued, {quarantined} quarantined")


if __name__ == "__main__":
    main()
