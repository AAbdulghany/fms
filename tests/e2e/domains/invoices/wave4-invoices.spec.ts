/** Wave 4 Suite B — Invoice module INV-01–INV-06 (NT-127). */
import { test, expect } from "@playwright/test";
import { login, DEMO_USERS, INVOICES_HEADING } from "../../fixtures/auth";

test.describe("Wave 4 — Invoices (INV-01–INV-06)", () => {
  test("INV-smoke company_admin invoices page loads", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/invoices");
    await expect(page.getByRole("heading", { name: INVOICES_HEADING })).toBeVisible();
  });

  test.skip("INV-01 generate invoice from verified WO", async () => {
    // Needs verified WO + generate CTA flow (NT-127); UI not fully wired for E2E yet.
  });

  test.skip("INV-02 edit draft invoice fields", async () => {
    // Needs draft invoice fixture from verified WO.
  });

  test.skip("INV-03 download invoice PDF", async () => {
    // Needs existing invoice with PDF endpoint.
  });

  test.skip("INV-04 tenant without invoices feature", async () => {
    // Backend: test_wave4_invoices.py
  });

  test.skip("INV-05 invoice preview before generate", async () => {
    // Needs preview panel on verified WO detail.
  });

  test.skip("INV-06 approve and send invoice", async () => {
    // Needs approve/send actions on invoice detail.
  });
});
