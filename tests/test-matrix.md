# Test Matrix

Status legend: ✅ executed and verified in this project · ⬜ not yet executed (recommended before production use)

| ID | Test | Status | Evidence |
|---|---|---|---|
| T01 | Wazuh dashboard reachable | ✅ | `assets/screenshots/01-wazuh-dashboard-rule5712.png` |
| T02 | Windows agent connects and reports Active | ✅ | Case 4, README |
| T03 | Wazuh generates a real alert (level ≥ 7) | ✅ | Rule 5712, Rule 5404, Rule 19007 |
| T04 | Authenticated webhook request accepted (200/202) | ✅ | Integrator log, `integrations.log` |
| T05 | Webhook request without token rejected | ⬜ | Not exercised as a dedicated negative test |
| T06 | Malformed payload rejected by Validate node | ⬜ | Validate node exists and was manually verified for missing `event_id`/`level`/`rule_id`/`agent_name`, but no automated negative-path screenshot was captured |
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
| T18 | Noise filter applied at source | ✅ | SCA excluded from Integrator forwarding path |
| T19 | Latency measured with a defined methodology | ⬜ | Latency was observed qualitatively (low single-digit seconds) across test cases; no formal timestamp-diff benchmark across a fixed sample size was run |
| T20 | No secrets present in the published repository | ✅ | Manual review before making the repository public; see `docs/troubleshooting.md` for the pre-publish checklist |

## Running the tests you can reproduce

```bash
export WAZUH_N8N_TOKEN=your_token
./test-webhook.sh sample-high-alert.json
./test-webhook.sh sample-medium-alert.json
./test-webhook.sh sample-critical-alert.json

# send the same file twice to verify dedup (T11)
./test-webhook.sh sample-high-alert.json
./test-webhook.sh sample-high-alert.json
```

Check the n8n Executions tab and the destination inbox after each run.
