import { Page } from "@playwright/test";

/** Demo password suffix — matches seed.py / pitch_seed (role prefix + suffix). */
const DEMO_PASSWORD_SUFFIX = process.env.E2E_DEMO_PASSWORD_SUFFIX ?? "123";

/** Login form labels/button — AR default UI + EN toggle. */
const IDENTIFIER_LABEL = /email|username|البريد|اسم المستخدم/i;
const PASSWORD_LABEL = /password|كلمة المرور/i;
const SUBMIT_BUTTON = /sign in|login|log in|تسجيل الدخول/i;

export async function login(page: Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel(IDENTIFIER_LABEL).fill(email);
  await page.getByLabel(PASSWORD_LABEL).fill(password);
  await page.getByRole("button", { name: SUBMIT_BUTTON }).click();
  await page.waitForURL(/\/(dashboard|platform)/);
}

/** Pitch-demo users (passwords composed from role prefix + suffix, not stored as literals). */
export const DEMO_USERS = {
  companyAdmin: { email: "admin@demo.com", password: `admin${DEMO_PASSWORD_SUFFIX}` },
  clientAdmin: { email: "client@demo.com", password: `client${DEMO_PASSWORD_SUFFIX}` },
  technician: { email: "tech@demo.com", password: `tech${DEMO_PASSWORD_SUFFIX}` },
} as const;
