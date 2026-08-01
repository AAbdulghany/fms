/** Wave 4 Suite C — WO transition modals WO-03, WO-04. */
import { test } from "@playwright/test";

test.describe("Wave 4 — WO workflows", () => {
  test.skip("WO-03 hold reason modal on on_hold transition", async () => {
    // Needs WO in a status that allows on_hold + hold-reason modal assertions (AR/EN).
  });

  test.skip("WO-04 assignee required before assigned", async () => {
    // Needs WO without assignee + ASSIGNEE_REQUIRED modal/toast (AR/EN).
  });
});
