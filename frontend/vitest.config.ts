import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

// Vitest config — Phase 5 Plan 05 (P5-B.2 infra).
// JSDOM env so @testing-library/react can render. Resolves @/* the same
// way Next.js does (tsconfig.json baseUrl = src, paths "@/*" -> "src/*").
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: [
      "src/**/*.test.ts",
      "src/**/*.test.tsx",
    ],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "src"),
    },
  },
});
