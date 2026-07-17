# Runbook - Memory leak investigation

**Symptoms:** RSS grows steadily without corresponding load increase; eventual OOM kills.

**Steps**
1. Confirm leak vs legitimate growth: compare RSS slope against traffic.
2. Capture heap profiles at intervals; diff allocation sites.
3. Correlate leak onset with deploy history - leaks ship with releases.
4. Mitigate with scheduled rolling restarts while the fix is developed.

**Note:** A restart schedule is a mitigation, not a fix - keep the leak ticket open.

*Synthetic runbook - demo data, no real systems.*
