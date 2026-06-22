/** Wave 4 Suite C — WO transition modals WO-03, WO-04. */
import { test } from "@playwright/test";
import { login, DEMO_USERS } from "./fixtures/auth";

test.describe("Wave 4 — WO workflows", () => {
  test.fixme("WO-03 hold reason modal on on_hold transition", async ({ page }) => {
    await login(page, DEMO_USERS.companyAdmin.email, DEMO_USERS.companyAdmin.password);
    void page;
  });

  test.fixme("WO-04 assignee required before assigned", async ({ page }) => {
    void page;
  });
});
