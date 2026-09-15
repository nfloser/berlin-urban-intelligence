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
