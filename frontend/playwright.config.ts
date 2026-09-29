import { defineConfig, devices } from "@playwright/test";

export const E2E_USERNAME = "e2e-admin";
export const E2E_PASSWORD = "e2e password 1234";
const PORT = 8765;
const baseURL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: process.env.CI ? "github" : "list",
  use: {
    baseURL,
    trace: "retain-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        // Lets environments with a preinstalled browser skip `playwright install`.
        launchOptions: { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || undefined },
      },
    },
  ],
  webServer: {
    command: "bash e2e/server.sh",
    url: `${baseURL}/api/health`,
    reuseExistingServer: false,
    timeout: 60_000,
    env: { E2E_USERNAME, E2E_PASSWORD, E2E_PORT: String(PORT) },
  },
});
