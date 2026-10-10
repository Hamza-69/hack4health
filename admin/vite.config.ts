import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The core API. `h4h dev` sets CORE_URL; /api/* is forwarded there without the /api prefix.
const coreUrl = process.env.CORE_URL ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: { "/api": { target: coreUrl, rewrite: (path) => path.replace(/^\/api/, "") } },
  },
});
