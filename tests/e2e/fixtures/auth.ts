import { Page } from "@playwright/test";

/** Demo password suffix — matches seed.py / pitch_seed (role prefix + suffix). */
const DEMO_PASSWORD_SUFFIX = process.env.E2E_DEMO_PASSWORD_SUFFIX ?? "123";

export async function login(page: Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /sign in|login|log in/i }).click();
  await page.waitForURL(/\/dashboard/);
}

/** Pitch-demo users (passwords composed from role prefix + suffix, not stored as literals). */
export const DEMO_USERS = {
  companyAdmin: { email: "admin@demo.com", password: `admin${DEMO_PASSWORD_SUFFIX}` },
  clientAdmin: { email: "client@demo.com", password: `client${DEMO_PASSWORD_SUFFIX}` },
  technician: { email: "tech@demo.com", password: `tech${DEMO_PASSWORD_SUFFIX}` },
} as const;
