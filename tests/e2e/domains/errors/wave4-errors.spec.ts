/** Wave 4 Suite D — Friendly error UX (NT-131). */
import { test, expect } from "@playwright/test";
import {
  IDENTIFIER_LABEL,
  PASSWORD_LABEL,
  SUBMIT_BUTTON,
} from "../../fixtures/auth";

const SCREAMING_SNAKE = /\b[A-Z]{2,}_[A-Z0-9_]+\b/;

/** Exact bilingual catalog copy for INVALID_CREDENTIALS (backend ERROR_CATALOG). */
const LOGIN_INVALID_CREDENTIALS = [
  "Invalid email or password.",
  "البريد أو كلمة المرور غير صحيحة.",
];

test.describe("Wave 4 — Error messages (ERR)", () => {
  test("ERR-LOGIN login shows friendly text on bad password", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(IDENTIFIER_LABEL).fill("admin@demo.com");
    await page.getByLabel(PASSWORD_LABEL).fill("wrong-password");
    await page.getByRole("button", { name: SUBMIT_BUTTON }).click();
    const alert = page.getByRole("alert");
    await expect(alert).toBeVisible();
    const text = (await alert.textContent())?.trim() ?? "";
    expect(text).not.toMatch(SCREAMING_SNAKE);
    expect(LOGIN_INVALID_CREDENTIALS).toContain(text);
  });

  test.skip("ERR-01 feature gate shows subscription message", async () => {
    // Needs a dedicated tenant without the gated feature in seed — covered by
    // backend/tests/domains/core/test_api_errors.py::test_error_handler_expands_feature_gate
  });
});
