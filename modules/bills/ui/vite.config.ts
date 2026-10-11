import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// This module's backend. `h4h dev` sets MODULE_URL from modules.toml.
const moduleUrl = process.env.MODULE_URL ?? "http://localhost:8001";

export default defineConfig(({ command }) => ({
  // The backend serves the built UI at /ui/.
  base: command === "build" ? "/ui/" : "/",
  plugins: [react(), tailwindcss()],
  server: { proxy: { "/api": moduleUrl } },
}));
