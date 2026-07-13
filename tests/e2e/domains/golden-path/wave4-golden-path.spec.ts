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
import { login, DEMO_USERS } from "../../fixtures/auth";

test.describe.configure({ mode: "serial" });

test.describe("Wave 4 — Golden path (GP-03–GP-12)", () => {
  test("GP-01 company_admin login", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test.skip("setup API create company for GP-03", async () => {
    // POST /api/v1/clients after auth — seeds companyId with 0 sites (not yet implemented).
  });

  test.skip("GP-03 add site on company detail Sites tab", async () => {
    // Depends on API setup companyId + Sites tab add-site modal.
  });

  test.skip("GP-04 register asset on /assets", async () => {
    // Depends on GP-03 site existing for asset registration.
  });

  test.skip("GP-05 create work order on /work-orders", async () => {
    // Depends on GP-04 asset.
  });

  test.skip("GP-06 assign technician on WO detail", async () => {
    // Depends on GP-05 WO.
  });

  test.skip("GP-07 technician starts in_progress", async () => {
    // Depends on GP-06 assignment.
  });

  test.skip("GP-08 submit report with labor hours", async () => {
    // Depends on GP-07 in_progress.
  });

  test.skip("GP-09 complete and verify work order", async () => {
    // Depends on GP-08 submitted report.
  });

  test.skip("GP-10 invoice preview", async () => {
    // Depends on GP-09 verified WO.
  });

  test.skip("GP-11 generate invoice", async () => {
    // Depends on GP-10 preview.
  });

  test.skip("GP-12 download invoice PDF", async () => {
    // Depends on GP-11 generated invoice.
  });
});
