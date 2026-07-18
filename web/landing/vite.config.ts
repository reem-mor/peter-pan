import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Dev-only: forward lead submissions to the ppos service (:8005).
    // Production fronts both behind one origin (reverse proxy).
    proxy: {
      "/leads": "http://localhost:8005",
    },
  },
});
