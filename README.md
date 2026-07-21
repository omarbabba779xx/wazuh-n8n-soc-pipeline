# Wazuh → n8n → Gmail: Real-Time SOC Alert Pipeline

A self-hosted security automation pipeline that turns raw Wazuh detections into severity-classified, deduplicated email alerts — built and validated end-to-end in a local SOC lab, with a real Windows endpoint generating live findings.

![Architecture Diagram](assets/architecture.png)

---

## About

Most Wazuh-to-notification tutorials stop at "poll a JSON file every few seconds and forward it." This project does the opposite: it wires Wazuh's own **Integrator** module directly into an n8n workflow over an authenticated production webhook, so alerts move in real time and get validated and deduplicated before anyone sees them.

Alerts are durably queued to disk when the n8n webhook is unreachable at delivery time, and a systemd timer drains that queue automatically once n8n is back — this was tested by killing n8n mid-flight and confirming automatic recovery.

It was built, broken, and fixed on real infrastructure — including a genuine Windows endpoint agent, a controlled brute-force simulation, an accidental self-inflicted alert, and a real operational issue (a compliance-scan flood) diagnosed and resolved during lab validation. Every claim below is backed by a matched pair of screenshots: one from the Wazuh dashboard, one from the resulting email, same rule ID, same timestamp.

**Stack:** Wazuh 4.14.6 (manager + Windows agent) · Docker · n8n 2.31.4 (self-hosted, pinned) · Gmail API (OAuth2) · systemd

---

## Architecture

| Stage | Component | Responsibility |
|---|---|---|
| 1 | **Monitored host** | Linux manager + Windows endpoint agent generate raw events: auth logs, sudo activity, file integrity changes, compliance checks |
| 2 | **Wazuh Manager** | Decodes and classifies events, assigns a rule ID and severity level |
| 3 | **Wazuh Integrator** | Custom script fires on level ≥ 7, authenticates the request with a secret header token, and posts to the webhook — event-driven, not a polling loop |
| 4 | **n8n Webhook** | Header-token authenticated ingress, responds `202 Accepted` immediately after auth (before Normalize/Validate/Gmail run), then hands off to the processing chain |
| 5 | **Normalize** | Flattens the raw alert into a consistent shape, maps rule level to a severity label |
| 6 | **Validate** | Rejects malformed or incomplete payloads before they propagate |
| 7 | **Deduplicate** | Tracks event IDs already processed; repeats are dropped silently |
| 8 | **Severity Router** | Branches on severity label; low-severity and explicitly excluded noisy sources never generate an email |
| 9 | **Format** | Builds an HTML report; the subject line alone is enough to triage |
| 10 | **Gmail Delivery** | Sends via an authenticated OAuth2 account under a dedicated sender identity |

If the webhook is unreachable at step 4, the alert is written to a local disk queue instead of being dropped. A systemd timer retries every 60 seconds and drains the queue automatically the moment n8n comes back.

---

## Test Cases

Each case below pairs the Wazuh-side detection with the resulting notification — same rule ID, same timestamp, proving the pipeline end to end rather than a mocked demo.

### Case 1 — Controlled brute-force detection

A controlled SSH brute-force simulation against a non-existent user, run inside the authorized local lab, was detected natively by Wazuh (rule 5712, level 10) and forwarded automatically, with no manual intervention.

<table>
<tr>
<td><img src="assets/screenshots/01-wazuh-dashboard-rule5712.png" width="420"></td>
<td><img src="assets/screenshots/02-gmail-alert-rule5712.png" width="420"></td>
</tr>
<tr><td align="center">Wazuh dashboard — rule 5712</td><td align="center">Resulting alert email</td></tr>
</table>

### Case 2 — Deduplication verified

The same event ID was submitted twice in a row. The first execution ran the full chain to Gmail; the second was cleanly filtered at the deduplication step and never reached the inbox — one incident, one notification.

<table>
<tr>
<td><img src="assets/screenshots/03-n8n-execution-dedup-1st.png" width="420"></td>
<td><img src="assets/screenshots/04-gmail-dedup-test.png" width="420"></td>
</tr>
<tr><td align="center">n8n execution — full chain, first run</td><td align="center">Single resulting email</td></tr>
</table>

### Case 3 — An accidental, fully organic alert

While debugging an SSH key permission issue, three consecutive `sudo` password typos triggered a genuine Wazuh detection (rule 5404, "Three failed attempts to run sudo") with zero staging. It reached the inbox in real time.

<table>
<tr>
<td><img src="assets/screenshots/05-gmail-organic-rule5404.png" width="420"></td>
<td><img src="assets/screenshots/06-terminal-sudo-3fail-trigger.png" width="420"></td>
</tr>
<tr><td align="center">Alert email — unplanned, organic trigger</td><td align="center">The terminal session that caused it</td></tr>
</table>

### Case 4 — Real Windows endpoint, and a lesson in tuning

A genuine Wazuh agent was deployed on a Windows 11 host and connected to the manager. Its built-in Security Configuration Assessment module ran a full CIS benchmark scan — 482 checks, 350 of them failing, many at level 7 and above.

Because deduplication keys on event ID and every individual check has a unique one, every failed check produced its own independent, valid alert. Deduplication by event ID is correct for suppressing a retransmitted copy of the same incident, but it cannot collapse a batch of genuinely distinct sub-events from one noisy source — that filtering has to happen upstream, at the Integrator or rule-group level, not in the dedup step. The pipeline behaved exactly as configured; the volume exposed a missing scope filter on a source that was never meant to page anyone. It's included here deliberately: a pipeline that never gets stress-tested by its own data hasn't really been tested.

<table>
<tr>
<td><img src="assets/screenshots/07-gmail-sca-flood-rule19007.png" width="420"></td>
<td><img src="assets/screenshots/08-wazuh-dashboard-sca-rule19007.png" width="420"></td>
</tr>
<tr><td align="center">Resulting inbox volume — rule 19007</td><td align="center">Matching Wazuh dashboard events</td></tr>
</table>

**Fix:** during the incident, the immediate action was to stop the flood at the source. The durable fix — excluding the `sca` rule group from the real-time forwarding path while leaving it visible in Wazuh Dashboard for periodic review — is implemented in `wazuh/custom-n8n` (`EXCLUDED_RULE_GROUPS`), committed after the fact.

---

## Lessons Learned

- **Event-driven beats polling.** Wiring the Integrator directly kept observed alert latency in the low single-digit seconds across every test case, with no wasted cycles re-reading a log file.
- **Deduplication needs a scope, not just a key.** Keying on event ID alone is correct for genuine incidents, but a noisy source that mints a fresh ID per sub-check will bypass it entirely — the fix belongs at the source filter, not the dedup logic.
- **A downtime test is only real if you kill the service mid-flight.** Simulating queue behavior in code proves nothing; stopping the container and watching the disk queue drain automatically on restart does.
- **The best failure mode is a loud one.** The compliance-scan flood was diagnosed and root-caused within minutes because the pipeline surfaced every alert individually instead of swallowing errors silently.

---

## Security Controls

- The n8n production webhook requires header-token authentication — not a token embedded in the URL.
- The Wazuh Integrator script reads the token from `/var/ossec/etc/n8n_token` (`640`, `root:wazuh`); it is never hardcoded in the script or logged.
- Gmail delivery uses OAuth2 — no application password stored in plaintext.
- n8n listens on `127.0.0.1` only; remote access goes through an SSH tunnel, never a direct network exposure.
- Host firewall is default-deny with explicit allow rules scoped to required ports.
- Secrets, tokens, and credential IDs are excluded from this repository (`.gitignore`, `.env.example` placeholders); the committed n8n workflow and integration files use `REPLACE_WITH_*` placeholders in place of real credential references.
- Screenshots were reviewed before publication; the only IP addresses visible are private RFC1918 lab addresses.

---

## Getting Started

See [`docs/installation.md`](docs/installation.md) for the full setup procedure and [`docs/troubleshooting.md`](docs/troubleshooting.md) if something doesn't come up cleanly.

## Testing

[`tests/test-matrix.md`](tests/test-matrix.md) tracks what has actually been verified versus what's still recommended. Reproduce the covered cases with `tests/test-webhook.sh` and the sample payloads in `tests/`.

## Repository Structure

```
.
├── README.md
├── .env.example
├── .gitignore
├── docker/
│   └── docker-compose.yml
├── wazuh/
│   ├── custom-n8n
│   └── ossec-integration.xml.example
├── n8n/
│   └── wazuh-alert-processing.workflow.json
├── replay/
│   ├── replay-wazuh-n8n.py
│   ├── wazuh-n8n-replay.service
│   └── wazuh-n8n-replay.timer
├── tests/
│   ├── sample-medium-alert.json
│   ├── sample-high-alert.json
│   ├── sample-critical-alert.json
│   ├── test-webhook.sh
│   └── test-matrix.md
├── docs/
│   ├── installation.md
│   └── troubleshooting.md
└── assets/
    ├── architecture.png
    └── screenshots/
        ├── 01-wazuh-dashboard-rule5712.png
        ├── 02-gmail-alert-rule5712.png
        ├── 03-n8n-execution-dedup-1st.png
        ├── 04-gmail-dedup-test.png
        ├── 05-gmail-organic-rule5404.png
        ├── 06-terminal-sudo-3fail-trigger.png
        ├── 07-gmail-sca-flood-rule19007.png
        └── 08-wazuh-dashboard-sca-rule19007.png
```
