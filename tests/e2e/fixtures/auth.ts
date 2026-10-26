import { Page } from "@playwright/test";

/** Seed password suffix — must match the stack's SEED_PASSWORD_SUFFIX (role prefix + suffix). */
const DEMO_PASSWORD_SUFFIX = process.env.E2E_DEMO_PASSWORD_SUFFIX ?? "123";

/** Login form labels/button — AR default UI + EN toggle. */
export const IDENTIFIER_LABEL = /email|username|البريد|اسم المستخدم/i;
export const PASSWORD_LABEL = /password|كلمة المرور/i;
export const SUBMIT_BUTTON = /sign in|login|log in|تسجيل الدخول/i;

/** Invoices page heading — AR default + EN. */
export const INVOICES_HEADING = /invoices|الفواتير/i;

/** After login: office → dashboard; field → work-orders; platform → platform. */
const POST_LOGIN_URL = /\/(dashboard|work-orders|platform)/;

export async function login(page: Page, email: string, password: string) {
  await page.goto("/login");
  // Mobile splash: open sign-in if fields are hidden
  const idField = page.getByLabel(IDENTIFIER_LABEL);
  if (!(await idField.isVisible().catch(() => false))) {
    const open = page.getByRole("button", { name: /sign in|تسجيل|continue/i }).first();
    if (await open.isVisible().catch(() => false)) await open.click();
  }
  await page.getByLabel(IDENTIFIER_LABEL).fill(email);
  await page.getByLabel(PASSWORD_LABEL).fill(password);
  await page.getByRole("button", { name: SUBMIT_BUTTON }).click();
  await page.waitForURL(POST_LOGIN_URL, { timeout: 30_000 });
}

/** Seed users (passwords = local-part + suffix). See docs/testing/FULL_SCENARIO_CATALOG.md. */
export const DEMO_USERS = {
  companyAdmin: { email: "admin@demo.com", password: `admin${DEMO_PASSWORD_SUFFIX}` },
  clientAdmin: { email: "client@demo.com", password: `client${DEMO_PASSWORD_SUFFIX}` },
  technician: { email: "tech@demo.com", password: `tech${DEMO_PASSWORD_SUFFIX}` },
  siteManager: { email: "site@demo.com", password: `site${DEMO_PASSWORD_SUFFIX}` },
  superUser: { email: "super@demo.com", password: `super${DEMO_PASSWORD_SUFFIX}` },
} as const;
