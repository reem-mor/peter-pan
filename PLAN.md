# P6 blocker remediation — DONE (2026-07-22)

## Verified closed
| Blocker | Proof |
|---|---|
| P0 DevIp | CFN `DevIp=46.210.191.192/32`; EC2 `:8001–8005/healthz` → 200 from this host |
| P0 local mesh | This worktree containers Up; open auth; `/predict` → `mode=floor` |
| P1 pytest auth | `391 passed, 8 skipped` with `tests/conftest.py` empty-token bootstrap |
| P1 ImageUri | Stack `…/peter-pan:6c97e47` (= worktree HEAD) |
| P1 EBS encrypt | `vol-0a74c2bd4bf07e912` Encrypted=true, gp3 30GB; instance `i-0412076b5c6494583` |

## Code/docs shipped this session
- `docker-compose.yml` → `PP_COMPOSE_API_TOKEN` (fixture-open default)
- `.env.example`, `docs/DEPLOYMENT.md` hygiene
- `scripts/deploy_ec2_rolling.py` InstanceId tag fallback
- `scripts/sync_demo_stack.py` change-set helper
- `@peterpan/product` typecheck + `next build` PASS

## Operator follow-up (not auto-done)
1. **Rotate secrets** that appeared as malformed `.env` “key” lines (spaces in names) — treat as exposed.
2. Rewrite `.env` as proper `KEY=value` (see `.env.example`) so `docker compose` can parse it again.
3. Live n8n re-import of triage v3 (manual).
