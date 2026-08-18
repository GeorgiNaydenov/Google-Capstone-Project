import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { normalizeBuildId } from "./src/buildConfig";

const buildId = normalizeBuildId(process.env.FRONTEND_BUILD_ID);

export default defineConfig({
  plugins: [react()],
  build: {
    rolldownOptions: {
      output: {
        entryFileNames: `assets/[name]-${buildId}-[hash].js`,
        chunkFileNames: `assets/[name]-${buildId}-[hash].js`,
        assetFileNames: `assets/[name]-${buildId}-[hash][extname]`,
      },
    },
  },
  server: { proxy: { "/api": "http://localhost:8000" } },
  test: { environment: "jsdom", setupFiles: "./src/test/setup.ts" },
});
