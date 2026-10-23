/**
 * A2 / A1 E2E — company → site → typed assets (inherit defaults) → QR tags.
 * Tracked on #34.
 *
 * Requires a running UI (pilot :9081 by default) with demo company_admin seed.
 */
import { test, expect, type Page } from "@playwright/test";
import { login, DEMO_USERS } from "../../fixtures/auth";
import {
  assertOpaqueAssetTagUrl,
  preferEnglish,
  selectOptionByLabel,
  uniqueSuffix,
} from "../../fixtures/helpers";

test.describe.configure({ mode: "serial", timeout: 60_000 });

const SUFFIX = uniqueSuffix();
const COMPANY_NAME = `E2E Co ${SUFFIX}`;
const FIRST_SITE = `HQ Site ${SUFFIX}`;
const SECOND_SITE = `Annex Site ${SUFFIX}`;
const TYPE_CODE = `e2e_pump_${SUFFIX}`;
const TYPE_NAME = `E2E Pump ${SUFFIX}`;
const ASSET_A = `Pump A ${SUFFIX}`;
const ASSET_B = `Pump B ${SUFFIX}`;
const TYPE_MAX_AGE = "17";
const TYPE_CRITICALITY = "high";

const qrLinks: string[] = [];

async function openRegisterModal(page: Page) {
  await page.goto("/assets");
  await page.getByTestId("register-asset-button").click();
  await expect(page.getByTestId("asset-register-modal")).toBeVisible();
}

async function fillRegisterShared(page: Page, assetName: string) {
  // Company picker mounts after /clients loads (clients.length > 1).
  const companySelect = page.getByTestId("asset-register-company");
  await expect(companySelect).toBeVisible({ timeout: 15_000 });
  await selectOptionByLabel(page, "asset-register-company", COMPANY_NAME);

  const siteSelect = page.getByTestId("asset-register-site");
  await expect(siteSelect).toBeEnabled({ timeout: 15_000 });
  // Wait until company-scoped sites finished loading before choosing.
  await expect(
    siteSelect.locator("option").filter({ hasText: new RegExp(SECOND_SITE, "i") })
  ).toHaveCount(1, { timeout: 15_000 });
  await selectOptionByLabel(page, "asset-register-site", SECOND_SITE);
  await expect(siteSelect).not.toHaveValue("");

  await page.getByTestId("asset-register-name").fill(assetName);
  await selectOptionByLabel(page, "asset-type-picker", TYPE_NAME);
  await expect(page.getByTestId("type-defaults-applied")).toBeVisible({ timeout: 10_000 });
  await expect(page.getByTestId("asset-register-criticality")).toHaveValue(TYPE_CRITICALITY);
  await expect(page.getByTestId("asset-register-max-age")).toHaveValue(TYPE_MAX_AGE);
}

async function captureQrForAsset(page: Page, assetName: string) {
  await page.goto("/assets");
  await page.getByRole("row", { name: new RegExp(assetName, "i") }).click();
  await expect(page).toHaveURL(/\/assets\/[0-9a-f-]+/i);
  await page.getByTestId("asset-qr-button").click();
  const modal = page.getByTestId("asset-qr-modal");
  await expect(modal).toBeVisible();
  const link = page.getByTestId("asset-qr-link");
  await expect(link).toBeVisible();
  const text = (await link.innerText()).trim();
  assertOpaqueAssetTagUrl(text);
  qrLinks.push(text);
  await page.getByTestId("asset-qr-close").click();
}

test.describe("A2 — company / site / asset inherit / QR", () => {
  test.beforeEach(async ({ page }) => {
    await preferEnglish(page);
  });

  test("1 create company (client) with first site", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/companies");
    await page.getByTestId("add-company-button").click();
    const modal = page.getByTestId("company-create-modal");
    await expect(modal).toBeVisible();

    await page.getByTestId("company-legal-name").fill(COMPANY_NAME);
    await page.getByTestId("company-manager-name").fill(`Mgr ${SUFFIX}`);
    await modal.getByRole("button", { name: /hospital|مستشفى/i }).click();
    await page.getByTestId("company-first-site-name").fill(FIRST_SITE);
    await page.getByTestId("company-first-site-city").fill("Riyadh");
    await page.getByTestId("company-first-site-country").fill("Saudi Arabia");
    await page.getByTestId("company-create-submit").click();

    await expect(page.getByTestId("credentials-confirm")).toBeVisible({ timeout: 20_000 });
    await page.getByTestId("credentials-confirm").click();
    await expect(page).toHaveURL(/\/companies\/[0-9a-f-]+/i, { timeout: 15_000 });
    await expect(page.getByRole("heading", { name: COMPANY_NAME })).toBeVisible();
    await expect(page.getByText(FIRST_SITE)).toBeVisible();
  });

  test("2 add a second site on the company", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/companies");
    await page.getByRole("row", { name: new RegExp(COMPANY_NAME, "i") }).click();
    await expect(page).toHaveURL(/\/companies\/[0-9a-f-]+/i);

    await page.getByTestId("company-add-site-button").click();
    const siteModal = page.getByTestId("site-add-modal");
    await expect(siteModal).toBeVisible();
    await page.getByTestId("site-name-input").fill(SECOND_SITE);
    await page.getByTestId("site-city-input").fill("Jeddah");
    await page.getByTestId("site-country-input").fill("Saudi Arabia");
    await page.getByTestId("site-add-submit").click();
    await expect(siteModal).toBeHidden({ timeout: 15_000 });
    await expect(page.getByText(SECOND_SITE)).toBeVisible();
  });

  test("3 create asset type with known defaults", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await page.goto("/asset-types");
    await page.getByTestId("asset-type-create-button").click();
    await expect(page.getByTestId("asset-type-form-modal")).toBeVisible();

    await page.getByTestId("asset-type-code").fill(TYPE_CODE);
    await page.getByTestId("asset-type-name-en").fill(TYPE_NAME);
    await page.getByTestId("asset-type-name-ar").fill(`مضخة ${SUFFIX}`);
    await page.getByTestId("asset-type-max-age").fill(TYPE_MAX_AGE);
    await page.getByTestId("asset-type-criticality").selectOption(TYPE_CRITICALITY);
    await page.getByTestId("asset-type-form-submit").click();

    await expect(page.getByTestId("asset-type-form-modal")).toBeHidden({ timeout: 15_000 });
    await expect(page.getByText(TYPE_NAME)).toBeVisible();
  });

  test("4 register first asset — inherits type defaults", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await openRegisterModal(page);
    await fillRegisterShared(page, ASSET_A);
    await page.getByTestId("asset-register-submit").click();
    await expect(page.getByTestId("asset-register-modal")).toBeHidden({ timeout: 20_000 });
    await expect(page.getByText(ASSET_A)).toBeVisible();
  });

  test("5 register second asset same type — same inherited defaults", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await openRegisterModal(page);
    await fillRegisterShared(page, ASSET_B);
    // Explicit inheritance check again before submit (untouched fields).
    await expect(page.getByTestId("asset-register-criticality")).toHaveValue(TYPE_CRITICALITY);
    await expect(page.getByTestId("asset-register-max-age")).toHaveValue(TYPE_MAX_AGE);
    await page.getByTestId("asset-register-submit").click();
    await expect(page.getByTestId("asset-register-modal")).toBeHidden({ timeout: 20_000 });
    await expect(page.getByText(ASSET_B)).toBeVisible();
  });

  test("6 each asset has a unique opaque QR tag", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    await captureQrForAsset(page, ASSET_A);
    await captureQrForAsset(page, ASSET_B);
    expect(qrLinks).toHaveLength(2);
    expect(qrLinks[0]).not.toEqual(qrLinks[1]);
  });
});
