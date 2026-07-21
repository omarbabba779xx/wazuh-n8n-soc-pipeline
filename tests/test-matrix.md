# Test Matrix

Status legend: ✅ executed and verified in this project

| ID | Test | Status | Evidence |
|---|---|---|---|
| T01 | Wazuh dashboard reachable | ✅ | `assets/screenshots/01-wazuh-dashboard-rule5712.png` |
| T02 | Windows agent connects and reports Active | ✅ | Case 4, README |
| T03 | Wazuh generates a real alert (level ≥ 7) | ✅ | Rule 5712, Rule 5404, Rule 19007 |
| T04 | Authenticated webhook request accepted, full chain executes | ✅ | Request accepted, Normalize → Validate → Router → Format → Gmail all executed, email delivered (subject `[WAZUH][HIGH][L10][RULE 999010]...`) |
| T06 | Malformed/empty payload rejected by Normalize/Validate | ✅ | Each required field (`event_id`, `rule.id`, `rule.level` as a finite number, `agent.name`) is checked independently before any fallback is applied |
| T08 | High severity correctly routed | ✅ | Rule 5712, Rule 5404 |
| T10 | Gmail delivery succeeds | ✅ | All test cases in README |
| T11 | Duplicate event_id filtered | ✅ | Case 2, `n8n-execution-dedup-1st.png` + `gmail-dedup-test.png` |
| T12 | n8n stopped mid-flight | ✅ | Retry/queue test, see README |
| T13 | Alert queued to disk while n8n down | ✅ | `integrations.log`: `queued alert ... (n8n unreachable)` |
| T14 | n8n restarted | ✅ | Retry/queue test |
| T15 | Queued alert auto-delivered by systemd timer | ✅ | `integrations.log`: `drained queued alert ... -> HTTP 200` |
| T16 | No duplicate sent after queue drain | ✅ | Single queued file, single drain log line |
| T17 | Noisy source (SCA flood) identified | ✅ | Case 4 |
| T18 | Noise filter applied at source | ✅ | `EXCLUDED_RULE_GROUPS` in `wazuh/custom-n8n` filters the `sca` rule group before forwarding |
| T20 | No secrets present in the published repository | ✅ | Manual `git log -p --all` review across the full history before making the repository public |
| T21 | HTTP 3xx not treated as a successful delivery | ✅ | Both scripts require `200 <= status < 300` and pass `allow_redirects=False` |
| T22 | Alert HTML is escaped before being emailed | ✅ | `escapeHtml()` applied to all interpolated fields; resulting email rendered cleanly |
| T23 | Dead-letter quarantine counted separately from still-queued | ✅ | The replay script tracks `sent` / `failed` / `quarantined` independently |

## Running the tests you can reproduce

Run from the repository root (or `cd tests` first and drop the `tests/` prefix below):

```bash
export WAZUH_N8N_TOKEN=your_token   # or rely on a repo-root .env, auto-loaded
tests/test-webhook.sh tests/sample-high-alert.json
tests/test-webhook.sh tests/sample-medium-alert.json
tests/test-webhook.sh tests/sample-critical-alert.json

# send the same file twice to verify dedup (T11)
tests/test-webhook.sh tests/sample-high-alert.json
tests/test-webhook.sh tests/sample-high-alert.json
```

Check the n8n Executions tab and the destination inbox after each run.
