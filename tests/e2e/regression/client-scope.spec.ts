/**
 * REG — Client admin scoped access (SC-CLIENT-VIEW partial). Actor: P-CLIENT
 */
import { test, expect } from "@playwright/test";
import { login, DEMO_USERS } from "../fixtures/auth";
import { preferEnglish } from "../fixtures/helpers";

test.describe("REG — Client scope", () => {
  test.beforeEach(async ({ page }) => {
    await preferEnglish(page);
  });

  test("SC-CLIENT P-CLIENT assets page loads", async ({ page }) => {
    await login(page, DEMO_USERS.clientAdmin.email, DEMO_USERS.clientAdmin.password);
    await page.goto("/assets");
    await expect(page.getByTestId("open-maintenance-calendar").or(page.getByTestId("register-asset-button"))).toBeVisible({
      timeout: 20_000,
    });
  });

  test("SC-CLIENT P-CLIENT cannot use Companies admin", async ({ page }) => {
    await login(page, DEMO_USERS.clientAdmin.email, DEMO_USERS.clientAdmin.password);
    await page.goto("/companies");
    await expect(page.getByText(/access denied|ليس لديك صلاحية|permission/i)).toBeVisible({
      timeout: 15_000,
    });
  });
});
