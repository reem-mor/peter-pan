# PETER PAN — web surfaces

Three Vite + React + TypeScript + Tailwind v4 apps, managed as npm workspaces
from the repo root, sharing typed contracts via `packages/types`
(a TypeScript mirror of `src/peterpan/schemas.py` — schemas.py is the source
of truth; regenerate the mirror, never diverge).

| App | Path | What it is |
| --- | --- | --- |
| Landing | `web/landing` | Marketing site shell: hero ("Get a demo" CTA stub), feature grid, footer. No form logic yet. |
| Demo | `web/demo` | Demo app shell: incident timeline panel, agent-reasoning stream panel (empty — SSE lands later), incident story panel. |
| Agent OS | `web/agent-os` | Operator console shell: sidebar nav (Incidents, Deployments, On-call, Token Usage, System Map, Post-mortems) with empty routed pages (react-router). |

All content is synthetic placeholder — no real incidents, no network calls.
Real design language and product features land in later workstreams; the
per-app `@theme` blocks in `src/index.css` are placeholder tokens only.

## Run

From the repo root:

```sh
npm ci                      # installs all workspaces
npm run dev -w web/landing  # or -w web/demo / -w web/agent-os
```

Per-app scripts (run with `-w web/<app>` from the root, or inside the app dir):

```sh
npm run build      # vite production build
npm run typecheck  # tsc --noEmit
npm run lint       # eslint src
```

CI: `.github/workflows/web.yml` runs typecheck + lint + build for each app on
changes under `web/**` or `packages/**`.
