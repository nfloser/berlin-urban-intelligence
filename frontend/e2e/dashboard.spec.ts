import { expect, test } from "@playwright/test";

function isReferenceViewportResponse(url: string): boolean {
  const parsed = new URL(url);
  return parsed.pathname === "/api/v1/map/reference";
}

test("dashboard completes a hypothetical heat assessment with persisted acceptance state", async ({
  page,
}) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Berlin Urban Intelligence" })).toBeVisible();

  const temperature = page.getByPlaceholder("Enter delta, e.g. 3");
  await temperature.fill("3");
  await page.getByRole("button", { name: "Assess hypothetical scenario" }).click();

  await expect(page.getByText("Heat delta +3 Cel")).toBeVisible();
  await expect(page.getByText("Hypothetical: yes")).toBeVisible();
  await expect(page.getByText(/Unavailable dimensions: heat/)).toBeVisible();
});

test("populated derived and platform inspectors expose persisted lineage and runtime semantics", async ({
  page,
}) => {
  await page.goto("/");

  const derived = page.getByLabel("Derived information inspector");
  await expect(derived.getByText("Acceptance mobility delay share", { exact: true })).toBeVisible();
  await expect(derived.getByText("Freshness: stale", { exact: true })).toBeVisible();
  await expect(derived.getByText("mobility 0.1.0", { exact: true })).toBeVisible();
  await expect(
    derived.getByText("observation:acceptance:mobility-input", { exact: true }),
  ).toBeVisible();
  await expect(
    derived.getByText("Berlin Urban Intelligence acceptance fixture", { exact: true }),
  ).toBeVisible();
  await expect(derived.getByText("acceptance derived lineage", { exact: true })).toBeVisible();

  const product = derived.getByLabel("Derived product");
  await product.selectOption("derived:context:heat-air-quality:current");
  await expect(
    derived.getByText("Latest measured heat and air-quality context", { exact: true }),
  ).toBeVisible();
  await expect(
    derived.getByText(/Values remain separate; no combined risk score or causal claim is produced/),
  ).toBeVisible();
  await expect(
    derived.getByText(/measured_air_temperature_2m: observation:acceptance:temperature/),
  ).toBeVisible();
  await expect(derived.getByText(/measured_berlin_lqi_grade: observation:acceptance:lqi/)).toBeVisible();

  await product.selectOption("derived:context:mobility-air-quality:current");
  await expect(
    derived.getByText("Latest mobility and air-quality context", { exact: true }),
  ).toBeVisible();
  await expect(
    derived.getByText(/no causal relationship, exposure attribution or combined score is inferred/),
  ).toBeVisible();
  await expect(derived.getByText(/vbb_gtfs_realtime_snapshot: vbb-gtfs-rt:/)).toBeVisible();
  await expect(derived.getByText(/measured_berlin_lqi_grade: observation:acceptance:lqi/)).toBeVisible();

  const platform = page.getByLabel("Platform registry and source inspector");
  const sourceRow = platform.locator('[data-source-id="berlin_air_quality"]');
  await expect(sourceRow).toBeVisible();
  await expect(sourceRow).toContainText("Luftgütemessdaten / REST API");
  await expect(sourceRow).toContainText("Berliner Luftgütemessnetz");
  await expect(sourceRow).toContainText("exposure");
  await expect(sourceRow.getByText("unavailable", { exact: true })).toBeVisible();
  await expect(sourceRow.getByText("stale", { exact: true })).toBeVisible();
  await expect(sourceRow.getByText("Failure: SOURCE_UNAVAILABLE", { exact: true })).toBeVisible();

  const liveStateRow = platform.locator('[data-agent-id="live_state"]');
  await expect(liveStateRow).toBeVisible();
  await expect(liveStateRow.getByText("Live State Agent", { exact: true })).toBeVisible();
  await expect(liveStateRow.getByText("degraded", { exact: true })).toBeVisible();
  await expect(liveStateRow.getByText("agent_health_snapshot", { exact: true })).toBeVisible();
  await expect(
    liveStateRow.getByText(/Depends on: mobility, exposure, heat, energy, resilience/),
  ).toBeVisible();

  const reloadCard = platform.locator("article").filter({ hasText: "Reload diagnostics" });
  await expect(reloadCard.getByText("runtime", { exact: true })).toBeVisible();
  await expect(reloadCard.getByText("reference", { exact: true })).toBeVisible();
  await expect(reloadCard.getByText("derived", { exact: true })).toBeVisible();
  await expect(reloadCard.getByText("energy", { exact: true })).toBeVisible();
  await expect(reloadCard.getByText("current", { exact: true })).toHaveCount(3);
  await expect(reloadCard.getByText("missing", { exact: true })).toHaveCount(1);
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

test("reference map loads the viewport, reloads after navigation and inspects canonical detail", async ({
  page,
}) => {
  const requests: string[] = [];
  page.on("request", (request) => requests.push(request.url()));
  const initialViewport = page.waitForResponse(
    (response) => isReferenceViewportResponse(response.url()) && response.ok(),
  );

  await page.goto("/");
  await initialViewport;

  const map = page.getByLabel("Berlin domain map");
  await expect(map).toHaveAttribute("data-reference-layers-ready", "true", { timeout: 15_000 });
  await expect(page.getByText(/Critical facilities · 2 visible \/ 2 in viewport · 2 total/)).toBeVisible();
  await expect(page.getByText(/VBB stops · 1 visible \/ 1 in viewport · 1 total/)).toBeVisible();
  await expect(
    page.getByText(/Official climate features · 1 visible \/ 1 in viewport · 1 total/),
  ).toBeVisible();

  expect(requests.some((url) => url.includes("/api/v1/facilities?limit=1000"))).toBe(false);
  expect(requests.some((url) => url.includes("/api/v1/transport-stops?limit=1000"))).toBe(false);
  expect(requests.some((url) => url.includes("/api/v1/climate-features?limit=1000"))).toBe(false);

  const nextViewport = page.waitForResponse(
    (response) => isReferenceViewportResponse(response.url()) && response.ok(),
  );
  await page.locator(".maplibregl-ctrl-zoom-in").click();
  await nextViewport;
  await expect(map).toHaveAttribute("data-reference-layers-ready", "true");

  const box = await map.boundingBox();
  expect(box).not.toBeNull();
  const center = { x: box!.width / 2, y: box!.height / 2 };
  const detailResponse = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/map/reference/facilities/") && response.ok(),
  );
  await map.click({ position: center });
  await detailResponse;

  await expect(page.getByText("Acceptance Hospital", { exact: true })).toBeVisible();
  await expect(page.getByText("Critical facility", { exact: true })).toBeVisible();
  await expect(page.getByText("acceptance facilities", { exact: true })).toBeVisible();
  await expect(page.getByText("deterministic CI acceptance fixture", { exact: true })).toBeVisible();
});

test("a failed current viewport request clears the previous rendering projection", async ({ page }) => {
  let viewportRequests = 0;
  await page.route(/\/api\/v1\/map\/reference\?/, async (route) => {
    viewportRequests += 1;
    if (viewportRequests === 1) {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ detail: "viewport fixture failure" }),
    });
  });

  await page.goto("/");
  const map = page.getByLabel("Berlin domain map");
  await expect(map).toHaveAttribute("data-reference-layers-ready", "true", { timeout: 15_000 });
  await expect(page.getByText(/Critical facilities · 2 visible/)).toBeVisible();

  await page.locator(".maplibregl-ctrl-zoom-in").click();

  await expect(page.getByText(/Reference map data unavailable:/)).toBeVisible();
  await expect(map).toHaveAttribute("data-reference-layers-ready", "false");
  await expect(page.getByText(/Critical facilities · 1 visible/)).toHaveCount(0);
});

test("map-selected routing compares a baseline with an explicit closed-edge scenario", async ({
  page,
}) => {
  const initialViewport = page.waitForResponse(
    (response) => isReferenceViewportResponse(response.url()) && response.ok(),
  );
  await page.goto("/");
  await initialViewport;

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
