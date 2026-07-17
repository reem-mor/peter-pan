# Runbook — certificate expiry / rotation

**Symptoms:** TLS handshake failures, `certificate has expired` in gateway
logs, synthetic checks failing on HTTPS endpoints.

**Fix**
1. Rotate via cert-manager: `kubectl cert-manager renew <cert>` (or trigger
   the issuing pipeline).
2. Verify: `openssl s_client -connect host:443 -servername host | openssl
   x509 -noout -dates`.
3. Confirm the renewal automation (expiry alert at T-14d) is armed — an
   expired cert means the alert path failed too; fix both.

*Synthetic runbook — demo data, no real systems.*
