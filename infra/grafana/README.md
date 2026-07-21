# Disposable Grafana for preview imports

Verifies that a `GrafanaDashboardPreview.dashboard_json` actually imports
into a real Grafana. Nothing here publishes anything — you boot a throwaway
instance, import the JSON yourself, and delete the container.

```bash
docker run --rm -d --name pp-grafana -p 127.0.0.1:3000:3000 \
  -e GF_SECURITY_ADMIN_PASSWORD=admin \
  -v "$(pwd)/infra/grafana/provisioning:/etc/grafana/provisioning" \
  grafana/grafana:11.4.0
```

PowerShell: replace `$(pwd)` with `${PWD}`.

1. Generate a preview: `POST /dashboard/grafana` (see docs/CONTRACTS.md),
   save the `dashboard_json` field to `preview.json`. Only import previews
   with `"validated": true`.
2. Import via API:

```bash
curl -fsS -u admin:admin -X POST http://localhost:3000/api/dashboards/db \
  -H 'Content-Type: application/json' \
  -d "{\"dashboard\": $(cat preview.json), \"overwrite\": false}"
```

3. Open http://localhost:3000 — panels render "no data" (the provisioned
   datasource URLs are deliberate placeholders); the import itself and the
   panel/template structure are what's being verified.
4. Tear down: `docker stop pp-grafana`.

The provisioned UIDs (`ds-prometheus`, `ds-loki`) mirror the exporter
defaults; point the exporter at an existing Grafana's datasources with
`PP_GRAFANA_PROMETHEUS_UID` / `PP_GRAFANA_LOKI_UID` instead of editing code.
