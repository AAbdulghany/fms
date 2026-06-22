/**
 * Wave 4 Suite A — Golden path (NT-132).
 *
 * GP-02 skipped — company pre-created via API fixture (not a UI step).
 * First UI step: GP-03 add site on company detail.
 *
 * Flow:
 *   setup  POST /clients (API) — company with 0 sites
 *   GP-01  login
 *   GP-03  /companies/:id → Sites → + Add site (add-only)
 *   GP-04  /assets → Register asset
 *   GP-05  /work-orders → Create WO
 *   GP-06  /work-orders/:id → Assign technician
 */
import { test, expect } from "@playwright/test";
import { login, DEMO_USERS } from "./fixtures/auth";

const runId = Date.now();
const siteName = `E2E Site ${runId}`;

/** Set by API setup before GP-03 (implement in fixture). */
let companyId: string | undefined;

test.describe.configure({ mode: "serial" });

test.describe("Wave 4 — Golden path (GP-03–GP-12)", () => {
  test.fixme("GP-01 company_admin login", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test.fixme("setup API create company for GP-03", async ({ request }) => {
    // POST /api/v1/clients after auth — not GP-02 UI; seeds companyId with 0 sites
    void request;
    void companyId;
  });

  test.fixme("GP-03 add site on company detail Sites tab", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto(`/companies/${companyId}`);
    await page.getByTestId("company-add-site-button").click();
    await expect(page.getByTestId("site-add-modal")).toBeVisible();
    void siteName;
  });

  test.fixme("GP-04 register asset on /assets", async ({ page }) => {
    await page.goto("/assets");
  });

  test.fixme("GP-05 create work order on /work-orders", async ({ page }) => {
    await page.goto("/work-orders");
  });

  test.fixme("GP-06 assign technician on WO detail", async ({ page }) => {
    void page;
  });

  test.fixme("GP-07 technician starts in_progress", async ({ page }) => {
    await login(page, DEMO_USERS.technician.email, DEMO_USERS.technician.password);
  });

  test.fixme("GP-08 submit report with labor hours", async ({ page }) => {
    void page;
  });

  test.fixme("GP-09 complete and verify work order", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    void page;
  });

  test.fixme("GP-10 invoice preview", async ({ page }) => {
    void page;
  });

  test.fixme("GP-11 generate invoice", async ({ page }) => {
    void page;
  });

  test.fixme("GP-12 download invoice PDF", async ({ page }) => {
    void page;
  });
});
