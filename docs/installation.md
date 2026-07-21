# Installation

## Prerequisites

- Ubuntu Server 24.04 LTS (Wazuh manager host)
- Wazuh Manager 4.14.x
- Wazuh Windows Agent 4.14.x (optional, for endpoint coverage)
- Docker Engine + Docker Compose
- Python 3
- A Gmail account with API access (OAuth2 client)

## Steps

1. Clone this repository.
2. Copy `.env.example` to `.env` and fill in real values:
   - `N8N_ENCRYPTION_KEY` — generate with `openssl rand -hex 32`
   - `WAZUH_N8N_TOKEN` — generate with `openssl rand -hex 32`
3. Start n8n:
   ```bash
   cd docker
   docker compose up -d
   ```
4. Open n8n (via SSH tunnel if bound to `127.0.0.1`), create an owner account.
5. Import `n8n/wazuh-alert-processing.workflow.json`. Fill in:
   - a Header Auth credential (name `X-Wazuh-Token`, value = your token)
   - a Gmail OAuth2 credential
   - the recipient email address in the Gmail node
6. Publish/activate the workflow.
7. On the Wazuh manager:
   ```bash
   cp wazuh/custom-n8n /var/ossec/integrations/custom-n8n
   chown root:wazuh /var/ossec/integrations/custom-n8n
   chmod 750 /var/ossec/integrations/custom-n8n

   echo "YOUR_TOKEN" > /var/ossec/etc/n8n_token
   chown root:wazuh /var/ossec/etc/n8n_token
   chmod 640 /var/ossec/etc/n8n_token
   ```
8. Append the contents of `wazuh/ossec-integration.xml.example` to `/var/ossec/etc/ossec.conf`.
9. Restart the manager: `systemctl restart wazuh-manager` (or `/var/ossec/bin/wazuh-control restart`).
10. Install the failure-recovery timer:
    ```bash
    cp replay/replay-wazuh-n8n.py /var/ossec/integrations/n8n_queue_retry.py
    cp replay/wazuh-n8n-replay.service /etc/systemd/system/
    cp replay/wazuh-n8n-replay.timer /etc/systemd/system/
    systemctl daemon-reload
    systemctl enable --now wazuh-n8n-replay.timer
    ```
11. Trigger a test alert on the manager (e.g. a few failed `sudo` attempts) and confirm it arrives in n8n's Executions tab, then in the inbox.

## Notes

- The n8n webhook should stay bound to `127.0.0.1`; expose it only through an SSH tunnel or reverse proxy with its own auth.
- `wazuh/ossec-integration.xml.example` sets the forwarding threshold at rule level 7. Adjust per environment — a noisy source (e.g. a full compliance scan) can flood the pipeline at that threshold and should be excluded at the Integrator or rule-group level rather than relying on deduplication alone.
