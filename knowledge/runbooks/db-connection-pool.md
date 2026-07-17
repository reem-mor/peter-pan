# Runbook - Database connection pool exhaustion

**Symptoms:** Timeouts on connection acquire, pool utilization at 100%, latency climbing downstream.

**Steps**
1. Check pool metrics: active vs idle vs waiting connections.
2. Compare pool size against recent deploy config diffs - halved pools are the classic regression.
3. Raise pool ceiling temporarily; roll back the config change that shrank it.
4. Verify no connection leak: connections acquired but never released in new code paths.

**Note:** Pool changes require canary + a dedicated dashboard panel (see INC-2231).

*Synthetic runbook - demo data, no real systems.*
