import path from "node:path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { tanstackRouter } from "@tanstack/router-plugin/vite";
import tailwindcss from "@tailwindcss/vite";

// Phase 4 Task 1 — Vite SPA + TanStack Router; /api proxied to FastAPI in dev.
// TanStack Router plugin runs before React; proxy is development-only (Phase 6
// serves frontend/dist same-origin from FastAPI). Vitest settings live in
// vitest.config.ts (keeps vite-8 plugin types clean of vitest's bundled vite).
export default defineConfig({
  plugins: [
    tanstackRouter({ target: "react", autoCodeSplitting: true }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      "@": path.resolve(import.meta.dirname, "./src"),
    },
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});
