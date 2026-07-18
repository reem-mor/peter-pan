import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// PETER PAN OS control plane (src/peterpan/services/ppos.py) — the dev
// server proxies the OS routes there so the console gets live data without
// CORS changes on the Python side (the proxy is a dev-only concern). If
// :8005 moves, set VITE_API_BASE instead of editing this.
const PPOS = "http://localhost:8005";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/os": PPOS,
      "/healthz": PPOS,
    },
  },
});
