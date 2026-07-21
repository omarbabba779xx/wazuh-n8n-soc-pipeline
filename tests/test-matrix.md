# Test Matrix

Status legend: ✅ executed and verified in this project · 🔧 fixed after review, not yet re-verified live · ⬜ not yet executed (recommended before production use)

| ID | Test | Status | Evidence |
|---|---|---|---|
| T01 | Wazuh dashboard reachable | ✅ | `assets/screenshots/01-wazuh-dashboard-rule5712.png` |
| T02 | Windows agent connects and reports Active | ✅ | Case 4, README |
| T03 | Wazuh generates a real alert (level ≥ 7) | ✅ | Rule 5712, Rule 5404, Rule 19007 |
| T04 | Authenticated webhook request accepted, responds immediately (202) | 🔧 | The live test used `responseMode: onReceived` with a 202 response; the first exported workflow JSON incorrectly used `responseNode` with no Respond-to-Webhook node. Fixed in the committed workflow — needs a live re-run to confirm |
| T05 | Webhook request without token rejected | ⬜ | Not exercised as a dedicated negative test |
| T06 | Malformed/empty payload rejected by Normalize/Validate | 🔧 | The original code defaulted missing `event_id`/`rule_id`/`agent_name` to `'unknown'` (and `rule_id` to the literal string `"undefined"`), so an empty payload could pass validation. Each required field (`event_id`, `rule.id`, `rule.level` as a finite number, `agent.name`) is now checked independently before any fallback — needs a live re-run with an empty payload to confirm |
| T07 | Medium severity correctly routed | ⬜ | Router logic verified by code review; no medium-level real alert was captured in this pass |
| T08 | High severity correctly routed | ✅ | Rule 5712, Rule 5404 |
| T09 | Critical severity correctly routed | ⬜ | No critical-level real alert was observed during testing |
| T10 | Gmail delivery succeeds | ✅ | All test cases in README |
| T11 | Duplicate event_id filtered | ✅ | Case 2, `n8n-execution-dedup-1st.png` + `gmail-dedup-test.png` |
| T12 | n8n stopped mid-flight | ✅ | Retry/queue test, see README |
| T13 | Alert queued to disk while n8n down | ✅ | `integrations.log`: `queued alert ... (n8n unreachable)` |
| T14 | n8n restarted | ✅ | Retry/queue test |
| T15 | Queued alert auto-delivered by systemd timer | ✅ | `integrations.log`: `drained queued alert ... -> HTTP 200` |
| T16 | No duplicate sent after queue drain | ✅ | Single queued file, single drain log line |
| T17 | Noisy source (SCA flood) identified | ✅ | Case 4 |
| T18 | Noise filter applied at source | 🔧 | The live fix during the incident stopped the Windows agent rather than committing a filter. `EXCLUDED_RULE_GROUPS` in `wazuh/custom-n8n` is the actual, reproducible fix — needs a live re-run against a real SCA scan to confirm |
| T19 | Latency measured with a defined methodology | ⬜ | Latency was observed qualitatively (low single-digit seconds) across test cases; no formal timestamp-diff benchmark across a fixed sample size was run |
| T20 | No secrets present in the published repository | ✅ | Manual `git log -p --all` review across the full history before making the repository public |
| T21 | HTTP 3xx not treated as a successful delivery | 🔧 | Original scripts checked `status >= 400` / `< 400` and `requests` follows redirects by default, so a `302` ending in a `200` would be misread as success. Both scripts now require `200 <= status < 300` **and** pass `allow_redirects=False` — needs a live re-run |
| T23 | Dead-letter quarantine counted separately from still-queued | 🔧 | A quarantined file was previously still counted as `failed` in the drain-pass log line, which was misleading. The replay script now tracks `sent` / `failed` / `quarantined` independently — needs a live re-run |
| T22 | Alert HTML is escaped before being emailed | 🔧 | Format Email now escapes all interpolated fields; not yet re-verified against a payload containing HTML characters |

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
