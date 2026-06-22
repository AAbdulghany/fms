/** Wave 4 Suite D — Friendly error UX (NT-131). */
import { test, expect } from "@playwright/test";
import { login, DEMO_USERS } from "../../fixtures/auth";

const SCREAMING_SNAKE = /\b[A-Z]{2,}_[A-Z0-9_]+\b/;

test.describe("Wave 4 — Error messages (ERR)", () => {
  test("ERR-07 login shows friendly text on bad password", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/email|username|البريد|اسم المستخدم/i).fill("admin@demo.com");
    await page.getByLabel(/password|كلمة المرور/i).fill("wrong-password");
    await page.getByRole("button", { name: /sign in|login|log in|تسجيل الدخول/i }).click();
    const alert = page.getByRole("alert");
    await expect(alert).toBeVisible();
    const text = await alert.textContent();
    expect(text).not.toMatch(SCREAMING_SNAKE);
    expect(text?.toLowerCase()).toMatch(/invalid|password|credentials/i);
  });

  test.fixme("ERR-01 feature gate shows subscription message", async ({ page }) => {
    void page;
    void DEMO_USERS;
  });
});
