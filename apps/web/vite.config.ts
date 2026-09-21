import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  build: {
    // Split large vendors so app code stays small and cacheable. three.js stays
    // isolated in the lazy StlViewer chunk. Build assets go to /static so the
    // SPA route /assets/:assetId is not shadowed by static files in nginx.
    assetsDir: "static",
    chunkSizeWarningLimit: 1100,
    rolldownOptions: {
      output: {
        advancedChunks: {
          groups: [
            {
              name: "vendor-react",
              test: /[\\/]node_modules[\\/](react|react-dom|react-router|scheduler)[\\/]/,
            },
            {
              name: "vendor-antd",
              test: /[\\/]node_modules[\\/](antd|@ant-design|rc-|@rc-component)[\\/]/,
            },
          ],
        },
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    exclude: ["e2e/**", "node_modules/**"],
  },
  server: {
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
