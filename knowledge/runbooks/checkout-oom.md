# Runbook — checkout service OOM

**Symptoms:** `OOMKilled` restarts on checkout pods; memory at limit before kill.

**Immediate mitigation**
1. Raise the memory limit one step (e.g. 512Mi → 768Mi) and roll the pods.
2. Confirm restart loop stops and p95 latency recovers.

**Root-cause hunt**
- Known leak class in checkout v2.3+: session cache grows unbounded when the
  eviction job is disabled. Check the eviction job's last run.
- Compare heap profiles before/after a 30-minute window under load.

**Escalate to:** residential/platform on-call if the leak reproduces after
eviction is confirmed running.

*Synthetic runbook — demo data, no real systems.*
