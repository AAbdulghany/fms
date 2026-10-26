/**
 * REG — Persona auth + RBAC smoke (SC-AUTH-*, SC-TEN-*).
 * Actors: P-ADMIN, P-TECH
 */
import { test, expect } from "@playwright/test";
import {
  login,
  DEMO_USERS,
  IDENTIFIER_LABEL,
  PASSWORD_LABEL,
  SUBMIT_BUTTON,
} from "../fixtures/auth";
import { preferEnglish } from "../fixtures/helpers";

const SCREAMING_SNAKE = /\b[A-Z]{2,}_[A-Z0-9_]+\b/;
const LOGIN_INVALID = [
  "Invalid email or password.",
  "البريد أو كلمة المرور غير صحيحة.",
];

test.describe("REG — Personas (multi-user)", () => {
  test.beforeEach(async ({ page }) => {
    await preferEnglish(page);
  });

  test("SC-AUTH-01 P-ADMIN login lands on dashboard", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("SC-AUTH-02 P-TECH login lands on work-orders", async ({ page }) => {
    await login(page, DEMO_USERS.technician.email, DEMO_USERS.technician.password);
    await expect(page).toHaveURL(/\/work-orders/);
  });

  test("SC-AUTH-03 bad password shows friendly message", async ({ page }) => {
    await page.goto("/login");
    const idField = page.getByLabel(IDENTIFIER_LABEL);
    if (!(await idField.isVisible().catch(() => false))) {
      const open = page.getByRole("button", { name: /sign in|تسجيل|continue/i }).first();
      if (await open.isVisible().catch(() => false)) await open.click();
    }
    await page.getByLabel(IDENTIFIER_LABEL).fill("admin@demo.com");
    await page.getByLabel(PASSWORD_LABEL).fill("wrong-password");
    await page.getByRole("button", { name: SUBMIT_BUTTON }).click();
    const alert = page.getByRole("alert");
    await expect(alert).toBeVisible();
    const text = (await alert.textContent())?.trim() ?? "";
    expect(text).not.toMatch(SCREAMING_SNAKE);
    expect(LOGIN_INVALID).toContain(text);
  });

  test("SC-TEN-01 P-TECH blocked from companies", async ({ page }) => {
    await login(page, DEMO_USERS.technician.email, DEMO_USERS.technician.password);
    await page.goto("/companies");
    await expect(page.getByRole("heading", { name: /access denied/i })).toBeVisible({
      timeout: 15_000,
    });
  });

  test("SC-TEN-02 P-TECH nav has no Invoices link", async ({ page }) => {
    await login(page, DEMO_USERS.technician.email, DEMO_USERS.technician.password);
    await expect(page.locator('a[href="/invoices"]')).toHaveCount(0);
    await expect(page.locator('a[href="/companies"]')).toHaveCount(0);
  });
});
