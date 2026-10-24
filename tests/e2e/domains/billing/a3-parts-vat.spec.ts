/**
 * A3–A4 E2E — parts + VAT (E-BILL-01..05).
 * Skeletons skip until pilot seed has billing-ready WO path; see #38.
 */
import { test, expect } from "@playwright/test";
import { login, DEMO_USERS } from "../../fixtures/auth";
import { preferEnglish } from "../../fixtures/helpers";

test.describe("A3–A4 — Parts & VAT billing", () => {
  test.beforeEach(async ({ page }) => {
    await preferEnglish(page);
  });

  test.skip("E-BILL-01 part → WO → invoice tax > 0", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/billing/parts");
    await expect(page.getByRole("heading", { name: /parts catalog/i })).toBeVisible();
  });

  test.skip("E-BILL-02 TaxProfile 15% visible on invoice", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/billing/tax");
    await expect(page.getByRole("heading", { name: /tax profile/i })).toBeVisible();
  });

  test.skip("E-BILL-03 snapshot immutable after rate change", async () => {
    // Needs issued invoice fixture + profile PATCH + reload assert
  });

  test.skip("E-BILL-04 pricing + contract create UI", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/billing/pricing");
    await expect(page.getByRole("heading", { name: /pricing/i })).toBeVisible();
  });

  test.skip("E-BILL-05 cross-tenant parts isolation", async () => {
    // Dual-tenant session harness
  });
});
