import { test, expect } from "@playwright/test";
import { login, DEMO_USERS } from "../../fixtures/auth";

test.describe("Wave 3 — Assets module (AST-01–AST-06)", () => {
  test("AST-01 company_admin sees quarterly maintenance calendar", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/assets");
    await expect(page.getByTestId("maintenance-calendar")).toBeVisible();
    await expect(page.getByTestId("calendar-grid-quarterly")).toBeVisible();
  });

  test("AST-02 switch to yearly calendar view", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/assets");
    await page.getByTestId("calendar-view-yearly").click();
    await expect(page.getByTestId("calendar-grid-yearly")).toBeVisible();
  });

  test("AST-03 select asset shows work order linkage panel", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/assets");
    const firstAsset = page.locator("[data-testid^='calendar-asset-']").first();
    if (await firstAsset.count()) {
      await firstAsset.click();
      await expect(page.getByTestId("asset-wo-panel")).toBeVisible();
    } else {
      await expect(page.getByTestId("asset-wo-panel-empty")).toBeVisible();
    }
  });

  test.skip("AST-04 tenant without assets feature hides nav", async () => {
    // Requires dedicated seed tenant without `assets` in package — verify via backend test_wave3_assets.
  });

  test("AST-05 client_admin assets page loads scoped calendar", async ({ page }) => {
    await login(page, DEMO_USERS.clientAdmin.email, DEMO_USERS.clientAdmin.password);
    await page.goto("/assets");
    await expect(page.getByTestId("maintenance-calendar")).toBeVisible();
    await expect(page.getByTestId("assets-client-filter")).toHaveCount(0);
  });

  test("AST-06 client_admin can open register asset modal", async ({ page }) => {
    await login(page, DEMO_USERS.clientAdmin.email, DEMO_USERS.clientAdmin.password);
    await page.goto("/assets");
    await page.getByRole("button", { name: /register asset|تسجيل أصل/i }).click();
    await expect(page.getByRole("heading", { name: /register asset|تسجيل أصل/i })).toBeVisible();
  });
});
