# Troubleshooting

## Webhook returns 404

- Confirm the workflow is published/active in n8n — a paused workflow only serves `/webhook-test/...`, not the production `/webhook/...` path.
- Confirm the path matches (`wazuh-alert` by default).

## Webhook returns 401/403

- Check the token value in `/var/ossec/etc/n8n_token` matches the Header Auth credential in n8n exactly (no trailing newline/whitespace).
- Confirm the header name is `X-Wazuh-Token` on both sides.

## No email arrives

- Check the n8n Executions tab for the run — confirm every node shows green.
- Check the Severity Router output — an alert below the medium threshold, or from an excluded source (e.g. `location: sca`), is expected to stop there.
- Confirm the Gmail OAuth2 credential is still connected (tokens can expire/be revoked).

## Duplicate emails for what looks like one incident

- Check `event_id` on both alerts — if the source assigns a new ID per sub-event (e.g. a compliance scan with one ID per check), deduplication by event ID will not collapse them. Filter at the Integrator (`ossec-integration.xml.example`) or by rule group instead.

## Alerts stuck in the local queue

```bash
systemctl status wazuh-n8n-replay.timer
systemctl status wazuh-n8n-replay.service
journalctl -u wazuh-n8n-replay.service -n 50
tail -f /var/ossec/logs/integrations.log
docker compose -f docker/docker-compose.yml ps
curl -I http://127.0.0.1:5678
```

## Pre-publish checklist (before making the repository public)

Search the full history, not just the latest commit, for:

```
tokens, client IDs, client secrets, personal email addresses,
public/non-lab IP addresses, usernames, hostnames, private keys, .env files
```

Removing a secret in a new commit does **not** remove it from git history. If a real secret was ever committed:

1. Revoke it immediately.
2. Issue a new one.
3. Rewrite history to purge the old value (e.g. `git filter-repo`).
4. Force-push only after confirming no one else has already pulled the exposed history.
