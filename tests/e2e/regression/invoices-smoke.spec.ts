/**
 * REG — Invoices page smoke (SC-INV-01). Actor: P-ADMIN
 */
import { test, expect } from "@playwright/test";
import { login, DEMO_USERS, INVOICES_HEADING } from "../fixtures/auth";
import { preferEnglish } from "../fixtures/helpers";

test.describe("REG — Invoices", () => {
  test.beforeEach(async ({ page }) => {
    await preferEnglish(page);
  });

  test("SC-INV-01 P-ADMIN invoices page loads", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/invoices");
    await expect(page.getByRole("heading", { name: INVOICES_HEADING })).toBeVisible({
      timeout: 20_000,
    });
  });
});
