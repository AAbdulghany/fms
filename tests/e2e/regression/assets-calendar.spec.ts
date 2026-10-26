/**
 * REG — Assets + maintenance calendar (SC-AST-01/02). Actor: P-ADMIN
 */
import { test, expect } from "@playwright/test";
import { login, DEMO_USERS } from "../fixtures/auth";
import { preferEnglish } from "../fixtures/helpers";

test.describe("REG — Assets & calendar", () => {
  test.beforeEach(async ({ page }) => {
    await preferEnglish(page);
  });

  test("SC-AST-01 P-ADMIN assets page + register control", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/assets");
    // Desktop + mobile buttons both exist in DOM; assert the desktop control.
    await expect(page.getByTestId("register-asset-button")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("open-maintenance-calendar")).toBeVisible();
  });

  test("SC-AST-02 P-ADMIN maintenance calendar page loads", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/assets/maintenance-calendar");
    await expect(page.getByTestId("maintenance-calendar-page")).toBeVisible({ timeout: 20_000 });
  });
});
