# Runbook - Feature flag related incident response

**Symptoms:** Error spike correlates exactly with a flag flip; blast radius matches the flag cohort.

**Steps**
1. Correlate error onset timestamp with the flag change audit log.
2. Flip the flag off - flags exist precisely for instant rollback.
3. Verify recovery, then diagnose offline with the flag cohort traces.
4. Flag flips on write paths need the same canary discipline as deploys.

**Note:** The audit-log correlation IS the diagnosis in most flag incidents.

*Synthetic runbook - demo data, no real systems.*
