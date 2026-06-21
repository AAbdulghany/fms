import { Page } from "@playwright/test";

export async function login(page: Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /sign in|login|log in/i }).click();
  await page.waitForURL(/\/dashboard/);
}

export const DEMO_USERS = {
  companyAdmin: { email: "admin@demo.com", password: "admin123" },
  clientAdmin: { email: "client@demo.com", password: "client123" },
} as const;
