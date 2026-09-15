import { expect, test } from "@playwright/test";

test("dashboard renders explicit empty state and completes a hypothetical heat assessment", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Berlin Urban Intelligence" })).toBeVisible();
  await expect(page.getByText("No persisted derived products are available.")).toBeVisible();

  const temperature = page.getByPlaceholder("Enter delta, e.g. 3");
  await temperature.fill("3");
  await page.getByRole("button", { name: "Assess hypothetical scenario" }).click();

  await expect(page.getByText("Heat delta +3 Cel")).toBeVisible();
  await expect(page.getByText("Hypothetical: yes")).toBeVisible();
  await expect(page.getByText(/Unavailable dimensions: heat/)).toBeVisible();
});

test("deterministic workflow remains inspectable when source-backed agents are unavailable", async ({
  page,
}) => {
  await page.goto("/");

  await page.getByLabel("Workflow").selectOption("urban_snapshot");
  await page.getByRole("button", { name: "Run deterministic workflow" }).click();

  await expect(page.getByText("LLM required: no")).toBeVisible();
  await expect(page.getByText(/Missing:/)).toBeVisible();
});

test("reference map objects can be selected and inspected with canonical metadata", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByText("Critical facilities · 1")).toBeVisible();
  await expect(page.getByText("VBB stops · 1")).toBeVisible();
  await expect(page.getByText("Official climate features · 1")).toBeVisible();

  const map = page.getByLabel("Berlin domain map");
  await expect(map).toHaveAttribute("data-reference-layers-ready", "true", { timeout: 15_000 });
  const box = await map.boundingBox();
  expect(box).not.toBeNull();
  const center = { x: box!.width / 2, y: box!.height / 2 };

  await map.click({ position: center });
  await expect(page.getByText("Acceptance Hospital", { exact: true })).toBeVisible();
  await expect(page.getByText("Critical facility", { exact: true })).toBeVisible();
  await expect(page.getByText("acceptance facilities", { exact: true })).toBeVisible();
  await expect(page.getByText("deterministic CI acceptance fixture", { exact: true })).toBeVisible();
});

test("map-selected routing compares a baseline with an explicit closed-edge scenario", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByText("Critical facilities · 1")).toBeVisible();
  const map = page.getByLabel("Berlin domain map");
  await expect(map).toHaveAttribute("data-reference-layers-ready", "true", { timeout: 15_000 });
  const box = await map.boundingBox();
  expect(box).not.toBeNull();
  const center = { x: box!.width / 2, y: box!.height / 2 };

  await page.getByRole("button", { name: "Select origin on map" }).click();
  await map.click({ position: center });
  await expect(page.getByRole("button", { name: "Origin selected" })).toBeVisible();

  await page.getByRole("button", { name: "Select destination on map" }).click();
  await map.click({ position: { x: center.x + 35, y: center.y } });
  await expect(page.getByRole("button", { name: "Destination selected" })).toBeVisible();

  await page.getByRole("button", { name: "Show baseline route" }).click();
  await expect(page.getByLabel("Disrupted route segment")).toBeVisible();
  await page.getByRole("button", { name: "Simulate selected disruption" }).click();

  await expect(page.getByText("Baseline: 100 s", { exact: true })).toBeVisible();
  await expect(page.getByText("Scenario: 160 s", { exact: true })).toBeVisible();
  await expect(page.getByText("Change: 60 s (60.0%)", { exact: true })).toBeVisible();
});
