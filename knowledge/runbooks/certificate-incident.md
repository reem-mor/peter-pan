# Runbook - Certificate expiry incident response

**Symptoms:** TLS handshake failures, certificate expired errors in gateway or client logs.

**Steps**
1. Identify which cert expired: edge, internal mTLS, or partner-facing.
2. Rotate via cert-manager or the issuing pipeline; verify with openssl s_client.
3. Check why the expiry alert did not fire at T-14d; fix the alert path too.
4. Audit sibling certs issued in the same batch - they expire together.

**Note:** An expired cert is two incidents: the outage, and the dead alert that allowed it.

*Synthetic runbook - demo data, no real systems.*
