import { defineConfig, devices } from "@playwright/test";

/**
 * E2E base URL must match a running web UI:
 *   Demo Docker:      http://localhost:9081  (docker compose -f docker-compose-demo.yml up -d --build)
 *   Local full Docker: http://localhost:9080  (docker compose -f docker-compose-local.yml up -d --build)
 *   Hybrid (Vite):    http://localhost:5173  (hybrid compose + npm run dev + uvicorn)
 */
const baseURL = process.env.E2E_BASE_URL ?? "http://localhost:9081";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
