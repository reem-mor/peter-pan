# Runbook - Canary rollback procedure

**Symptoms:** Error rate or latency regression isolated to the canary cohort after a progressive rollout.

**Steps**
1. Confirm regression correlates with the canary cohort, not global traffic.
2. Shift traffic off the canary (set canary weight to 0).
3. Roll back the canary deployment; keep the artifact for diagnosis.
4. Write-path canaries need explicit write-checks before re-promotion.

**Note:** Rollback is fast and auditable when it goes through the approval gate.

*Synthetic runbook - demo data, no real systems.*
