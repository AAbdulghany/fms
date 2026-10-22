import { Page, expect } from "@playwright/test";

/** Force EN UI before first navigation (survives via localStorage `app_lang`). */
export async function preferEnglish(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem("app_lang", "en");
  });
}

export function uniqueSuffix(): string {
  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

/** Select option whose visible text matches (partial, case-insensitive). */
export async function selectOptionByLabel(page: Page, testId: string, labelPart: string) {
  const select = page.getByTestId(testId);
  await expect(select).toBeVisible();
  const option = select.locator("option").filter({ hasText: new RegExp(labelPart, "i") }).first();
  const value = await option.getAttribute("value");
  expect(value, `option matching "${labelPart}"`).toBeTruthy();
  await select.selectOption(value!);
}

/** Opaque A2 tag path: /a/{crockford} — not a UUID deep link. */
export function assertOpaqueAssetTagUrl(url: string) {
  expect(url).toMatch(/\/a\/[0-9A-HJKMNP-TV-Z]{8,16}$/i);
  expect(url).not.toMatch(
    /\/assets\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i
  );
}
