# Runbook - DNS resolution and network connectivity failures

**Symptoms:** Connection refused or host-not-found between internal services, intermittent timeouts.

**Steps**
1. Distinguish refused (service down/port closed) from timeout (network path/policy).
2. Check network policy and security group changes in the last deploy window.
3. Verify DNS: resolve the service name from inside the failing namespace.
4. Test upstream health directly by IP to bypass DNS.

**Note:** Refused almost always means the target; timeout almost always means the path.

*Synthetic runbook - demo data, no real systems.*
