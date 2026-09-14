import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // MapLibre ships its own worker bundle. Vite's dependency optimizer can
    // otherwise cache a transient maplibre-gl-worker file that no longer
    // exists after re-optimization in dev mode, leaving the map blank.
    exclude: ["maplibre-gl"],
  },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/health": "http://127.0.0.1:8000",
      "/ready": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "node",
    include: ["src/**/*.test.ts"],
  },
});
