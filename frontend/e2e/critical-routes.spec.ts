import { expect, test } from "@playwright/test";

test("critical facility routes appear automatically and remain keyboard inspectable", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Berlin Urban Intelligence" })).toBeVisible();

  const map = page.getByLabel("Berlin domain map");
  await expect(map).toHaveAttribute("data-critical-routes-ready", "true");
  await expect(map).toHaveAttribute("data-critical-routes-count", "2");

  const monitor = page.getByRole("region", { name: "Critical route monitor" });
  await expect(monitor).toBeVisible();
  await expect(monitor.getByText("available", { exact: true })).toBeVisible();
  await expect(monitor.getByText("2", { exact: true }).first()).toBeVisible();
  await expect(monitor.getByText("Available · valid", { exact: true })).toBeVisible();
  await expect(monitor.getByText("Not integrated", { exact: true })).toBeVisible();
  await expect(
    monitor.getByText(/No live traffic congestion-speed telemetry is integrated/, { exact: false }),
  ).toBeVisible();

  const routeSelect = page.getByLabel("Critical route", { exact: true });
  await expect(routeSelect).toBeVisible();
  await routeSelect.focus();
  await expect(routeSelect).toBeFocused();

  const options = routeSelect.locator("option");
  await expect(options).toHaveCount(2);
  await expect(monitor.getByText("State: rerouted", { exact: true })).toBeVisible();
  await expect(monitor.getByText(/Baseline: 1.7 min · 1.40 km/)).toBeVisible();
  await expect(monitor.getByText(/Effective: 2.7 min · 2.20 km/)).toBeVisible();
  await expect(monitor.getByText("Added travel time: 1.0 min", { exact: true })).toBeVisible();
  await expect(monitor.getByText("Active disruptions: 1", { exact: true })).toBeVisible();

  await routeSelect.selectOption({ label: "Acceptance Hospital → Acceptance Fire Station" });
  await expect(
    monitor.locator("strong").filter({ hasText: "Acceptance Hospital → Acceptance Fire Station" }),
  ).toBeVisible();

  const toggle = page.getByRole("checkbox", { name: /Critical routes/ });
  await expect(toggle).toBeChecked();
  await toggle.uncheck();
  await expect(toggle).not.toBeChecked();
  await toggle.check();
  await expect(toggle).toBeChecked();

  await expect(
    page.getByText(/Critical routes · 2 shown \/ 2 monitored · refresh 15 s/),
  ).toBeVisible();
});
