# Runbook - Disk pressure and volume exhaustion

**Symptoms:** Disk usage above 90 percent and rising, log rotation failing, writes at risk of stalling.

**Steps**
1. Identify the growth driver: logs, tmp files, database segments, or core dumps.
2. Free safe space first: rotate/compress logs, clear tmp, prune old artifacts.
3. Expand the volume if growth is legitimate; add a usage alert at 80 percent.
4. Check the rotation policy actually ran - a stuck rotation job is the usual cause.

**Note:** Never delete database segments by hand; escalate to the DB owner.

*Synthetic runbook - demo data, no real systems.*
