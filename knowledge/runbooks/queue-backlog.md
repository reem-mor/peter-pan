# Runbook - Message queue backlog and consumer lag

**Symptoms:** Message age p99 climbing, consumer lag growing, downstream data increasingly stale.

**Steps**
1. Check consumer health: crashed, deadlocked, or throttled consumers.
2. Compare producer rate vs consumer throughput - find which side changed.
3. Scale consumers horizontally if throughput-bound; fix poison messages if stuck.
4. Verify dead-letter handling so one bad message cannot stall a partition.

**Note:** Backlog with healthy consumers means a producer-side surge - rate limit at ingress.

*Synthetic runbook - demo data, no real systems.*
