# Domains plan

Three public surfaces, three (sub)domains. Buying domains is a human step —
registrar checkout requires payment. Until purchased, every surface works on
free platform subdomains, so nothing here blocks development.

| Surface | Purpose | Free interim | Target domain (example) |
|---|---|---|---|
| Product landing page | Marketing page for users/clients | `peter-pan.vercel.app` | `peterpan.io` / `getpeterpan.com` (check availability) |
| Main demo | The live WebUI (mirage env) for demos/recordings | `demo-peter-pan.vercel.app` or EC2 public DNS | `demo.<domain>` |
| PETER PAN OS | Token/agent monitoring console | `os-peter-pan.vercel.app` or EC2 | `os.<domain>` |

## Recommended setup once a domain is purchased

1. Buy one apex domain at a registrar (Cloudflare Registrar is at-cost;
   Namecheap/Porkbun also fine). One domain, three subdomains — don't buy three.
2. DNS on Cloudflare (free tier): `@` → landing (Vercel), `demo` → demo host,
   `os` → OS console host.
3. TLS is automatic on both Vercel and Cloudflare-proxied EC2.
4. The OS console (`os.`) should sit behind auth (at minimum Cloudflare
   Access / basic auth) — it exposes cost and operational data.

## Action for Reem

Pick and purchase the apex domain at the registrar (payment step — yours),
then tell Claude the domain and where each surface is hosted; wiring DNS +
deploy config from there is automatable.
