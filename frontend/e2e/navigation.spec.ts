import { expect, test } from "@playwright/test";

test("map-first navigation searches places, inspects a VIZ closure and reroutes automatically", async ({
  page,
}) => {
  await page.goto("/");

  const planner = page.getByRole("region", { name: "Route planner" });
  await expect(planner.getByRole("heading", { name: "Berlin Urban Intelligence" })).toBeVisible();

  const map = page.getByLabel("Berlin domain map");
  await expect(map).toHaveAttribute("data-reference-layers-ready", "true", { timeout: 15_000 });
  await expect(map).toHaveAttribute("data-traffic-disruptions-ready", "true");
  await expect(map).toHaveAttribute("data-traffic-disruptions-count", "1");

  await page.getByText("Inspect active disruptions", { exact: true }).click();
  await page.getByRole("button", { name: "Inspect disruption Acceptance Route" }).click();

  const disruption = page.getByRole("article", { name: "Road disruption detail" });
  await expect(disruption).toBeVisible();
  await expect(disruption.getByText("Acceptance Route", { exact: true })).toBeVisible();
  await expect(disruption.getByText("Vollsperrung", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Close road disruption detail" }).click();

  const origin = page.getByLabel("Origin search");
  await origin.fill("Acceptance Hospital");
  const originResult = planner
    .getByRole("listbox", { name: "Place suggestions" })
    .getByRole("option", { name: /Acceptance Hospital/ });
  await expect(originResult).toBeVisible();
  await originResult.click();

  const destination = page.getByLabel("Destination search");
  await destination.fill("Acceptance Fire Station");
  const destinationResult = planner
    .getByRole("listbox", { name: "Place suggestions" })
    .getByRole("option", { name: /Acceptance Fire Station/ });
  await expect(destinationResult).toBeVisible();
  await destinationResult.click();

  await expect(map).toHaveAttribute("data-user-route-state", "rerouted");
  await expect(planner.getByText("rerouted", { exact: true })).toBeVisible();
  await expect(planner.getByText("3 min", { exact: true })).toBeVisible();
  await expect(planner.getByText("2.2 km", { exact: true })).toBeVisible();
  await expect(
    planner.getByText(/Rerouted around an official VIZ full closure/),
  ).toBeVisible();

  await page.getByRole("button", { name: "Swap" }).click();
  await expect(origin).toHaveValue("Acceptance Fire Station");
  await expect(destination).toHaveValue("Acceptance Hospital");
  await expect(map).toHaveAttribute("data-user-route-state", "rerouted");

  await page.getByRole("button", { name: "Clear" }).click();
  await expect(origin).toHaveValue("");
  await expect(destination).toHaveValue("");
  await expect(map).toHaveAttribute("data-user-route-state", "none");
});
