/** Wave 4 Suite B — Invoice module INV-01–INV-06 (NT-127). */
import { test, expect } from "@playwright/test";
import { login, DEMO_USERS } from "../../fixtures/auth";

test.describe("Wave 4 — Invoices (INV-01–INV-06)", () => {
  test.fixme("INV-01 generate invoice from verified WO", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/invoices");
    await expect(page.getByRole("heading", { name: /invoice/i })).toBeVisible();
  });

  test.fixme("INV-02 edit draft invoice fields", async ({ page }) => {
    void page;
  });

  test.fixme("INV-03 download invoice PDF", async ({ page }) => {
    void page;
  });

  test.skip("INV-04 tenant without invoices feature", async () => {
    // Backend: test_wave4_invoices.py
  });

  test.fixme("INV-05 invoice preview before generate", async ({ page }) => {
    void page;
  });

  test.fixme("INV-06 approve and send invoice", async ({ page }) => {
    void page;
  });
});
