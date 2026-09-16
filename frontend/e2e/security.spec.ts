import { expect, test } from "@playwright/test";

test("frontend proxy emits the safe baseline security headers", async ({ page }) => {
  const response = await page.goto("/");

  expect(response).not.toBeNull();
  const headers = response!.headers();
  expect(headers["x-content-type-options"]).toBe("nosniff");
  expect(headers["x-frame-options"]).toBe("DENY");
  expect(headers["referrer-policy"]).toBe("no-referrer");
  expect(headers["permissions-policy"]).toBe("camera=(), microphone=(), geolocation=()");
});
