# Runbook - Cache stampede and cold cache recovery

**Symptoms:** Latency spike and database overload right after cache flush, restart, or TTL expiry wave.

**Steps**
1. Confirm the cache hit rate collapsed at incident start.
2. Enable request coalescing / stale-while-revalidate if available.
3. Warm the cache progressively; do not restart all replicas at once.
4. Stagger TTLs to prevent synchronized expiry waves.

**Note:** A cache restart during peak traffic is a self-inflicted incident.

*Synthetic runbook - demo data, no real systems.*
