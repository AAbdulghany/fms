/**
 * A2 QR E2E — scan landing paths (auth vs anon).
 * Company/asset setup covered in a2-company-asset-qr.spec.ts (#34).
 */
import { test, expect } from "@playwright/test";
import { login, DEMO_USERS } from "../../fixtures/auth";
import { preferEnglish } from "../../fixtures/helpers";

test.describe("A2 — Asset QR landing (E-QR-02..03)", () => {
  test.beforeEach(async ({ page }) => {
    await preferEnglish(page);
  });

  test.skip("E-QR-02 /a/{token} logged in → asset page", async ({ page }) => {
    // Wire with a seed token once pilot backfill mints tags for demo assets.
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/a/PLACEHOLDER");
    await expect(page).toHaveURL(/\/assets\//);
  });

  test.skip("E-QR-03 /a/{token} logged out → report form only", async ({ page }) => {
    await page.goto("/a/PLACEHOLDER");
    await expect(page.getByText(/report a problem/i)).toBeVisible();
  });
});
