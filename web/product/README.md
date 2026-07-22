# `@peterpan/product` — canonical Next.js UI

App Router surface that consolidates the three Vite shells:

| Route | Role | Migration source |
| --- | --- | --- |
| `/` | Marketing / lead landing | `web/landing` |
| `/app` | Incident workspace (story via BFF) | `web/demo` |
| `/os` | PETER PAN OS control plane | `web/agent-os` |

Server-only mesh access lives in `src/lib/backend.ts` and `/api/*` BFF
routes. `PP_API_TOKEN` never reaches the browser.

```sh
# from repo root
npm ci
npm run dev -w web/product
```

Shared wire shapes come from `@peterpan/types` (mirror of
`src/peterpan/schemas.py`). Vite apps under `web/landing`, `web/demo`, and
`web/agent-os` remain migration sources until their UX is fully ported here.
