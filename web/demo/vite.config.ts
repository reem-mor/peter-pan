import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Dev convenience: same-origin /agent/* forwards to the agent service
    // (uvicorn peterpan.services.agent:app --port 8004). Production builds
    // point elsewhere via VITE_API_BASE instead.
    proxy: {
      "/agent": "http://localhost:8004",
    },
  },
});
