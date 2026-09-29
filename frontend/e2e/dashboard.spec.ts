import { type Page, expect, test } from "@playwright/test";
import { E2E_PASSWORD, E2E_USERNAME } from "../playwright.config";

async function signIn(page: Page, password = E2E_PASSWORD) {
  await page.goto("/");
  await page.getByLabel("Username").fill(E2E_USERNAME);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

test("shows the login form to anonymous visitors", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});

test("rejects a wrong password", async ({ page }) => {
  await signIn(page, "definitely wrong");
  await expect(page.getByRole("alert")).toHaveText("Invalid username or password");
  await expect(page.getByRole("button", { name: "Sign in" })).toBeEnabled();
});

test("shows live metrics after signing in", async ({ page }) => {
  await signIn(page);

  const system = page.getByRole("region", { name: "System" });
  await expect(system.getByText("Hostname")).toBeVisible();
  await expect(system.getByText("Kernel")).toBeVisible();

  await expect(page.getByRole("progressbar", { name: "CPU usage" })).toBeVisible();
  await expect(page.getByRole("progressbar", { name: "RAM usage" })).toBeVisible();
  await expect(page.getByRole("progressbar", { name: "/ usage" })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("keeps the session across reloads and ends it on sign out", async ({ page }) => {
  await signIn(page);
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();

  await page.reload();
  await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});

test("a failing endpoint only affects its own card", async ({ page }) => {
  await page.route("**/api/system/storage", (route) =>
    route.fulfill({ status: 503, json: { detail: "Storage data unavailable" } }),
  );
  await signIn(page);

  const storage = page.getByRole("region", { name: "Storage" });
  await expect(storage.getByRole("alert")).toHaveText("Storage data unavailable");
  await expect(page.getByRole("progressbar", { name: "CPU usage" })).toBeVisible();
});

test("returns to the login form when the session expires", async ({ page }) => {
  await signIn(page);
  await expect(page.getByRole("progressbar", { name: "CPU usage" })).toBeVisible();

  await page.route("**/api/system/**", (route) =>
    route.fulfill({ status: 401, json: { detail: "Not authenticated" } }),
  );
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible({ timeout: 10_000 });
});
