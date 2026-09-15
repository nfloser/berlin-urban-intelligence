import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22aa"];

async function expectNoCriticalOrSeriousViolations(page: Page, state: string) {
  const result = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze();
  const blocking = result.violations.filter(
    (violation) => violation.impact === "critical" || violation.impact === "serious",
  );
  expect(blocking, `${state} contains critical/serious accessibility violations`).toEqual([]);
}

async function expectVisibleKeyboardFocus(page: Page, label: string) {
  const control = page.getByLabel(label);
  await control.focus();
  const focusStyle = await control.evaluate((element) => {
    const style = window.getComputedStyle(element);
    return {
      outlineStyle: style.outlineStyle,
      outlineWidth: style.outlineWidth,
    };
  });
  expect(focusStyle.outlineStyle).not.toBe("none");
  expect(Number.parseFloat(focusStyle.outlineWidth)).toBeGreaterThanOrEqual(2);
}

test("principal dashboard states have no critical or serious WCAG A/AA violations", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Berlin Urban Intelligence" })).toBeVisible();
  await expectNoCriticalOrSeriousViolations(page, "initial dashboard");

  const temperature = page.getByLabel("Temperature delta (Cel)");
  await temperature.fill("3");
  await page.getByRole("button", { name: "Assess hypothetical scenario" }).click();
  await expect(page.getByText("Hypothetical: yes", { exact: true })).toBeVisible();
  await expectNoCriticalOrSeriousViolations(page, "heat assessment result");
});

test("keyboard-only analytical controls expose visible focus and a non-map routing path", async ({
  page,
}) => {
  await page.goto("/");

  const workflow = page.getByLabel("Workflow");
  await workflow.focus();
  await page.keyboard.press("End");
  await page.keyboard.press("Tab");
  const runWorkflow = page.getByRole("button", { name: "Run deterministic workflow" });
  await expect(runWorkflow).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByText("LLM required: no", { exact: true })).toBeVisible();

  const facilitiesToggle = page.getByRole("checkbox", { name: /Critical facilities/ });
  await facilitiesToggle.focus();
  await page.keyboard.press("Space");
  await expect(facilitiesToggle).not.toBeChecked();
  await page.keyboard.press("Space");
  await expect(facilitiesToggle).toBeChecked();

  await expectVisibleKeyboardFocus(page, "Temperature delta (Cel)");
  const temperature = page.getByLabel("Temperature delta (Cel)");
  await temperature.pressSequentially("3");
  await page.keyboard.press("Tab");
  const assess = page.getByRole("button", { name: "Assess hypothetical scenario" });
  await expect(assess).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.getByText("Hypothetical: yes", { exact: true })).toBeVisible();

  const derivedProduct = page.getByLabel("Derived product");
  await derivedProduct.focus();
  await expect(derivedProduct).toBeFocused();

  const keyboardRouting = page.getByRole("group", { name: "Keyboard routing coordinates" });
  await expect(keyboardRouting).toBeVisible();

  const coordinateInputs = [
    ["Origin longitude", "13.4"],
    ["Origin latitude", "52.52"],
    ["Destination longitude", "13.42"],
    ["Destination latitude", "52.52"],
  ] as const;
  for (const [label, value] of coordinateInputs) {
    const input = page.getByLabel(label);
    await input.focus();
    await input.pressSequentially(value);
  }

  const resolveOrigin = page.getByRole("button", { name: "Resolve origin coordinates" });
  await resolveOrigin.focus();
  await page.keyboard.press("Enter");
  await expect(keyboardRouting.getByText("Origin node: acceptance-node-a", { exact: true })).toBeVisible();

  const resolveDestination = page.getByRole("button", { name: "Resolve destination coordinates" });
  await resolveDestination.focus();
  await page.keyboard.press("Enter");
  await expect(
    keyboardRouting.getByText("Destination node: acceptance-node-b", { exact: true }),
  ).toBeVisible();

  const baseline = page.getByRole("button", { name: "Show keyboard baseline route" });
  await baseline.focus();
  await page.keyboard.press("Enter");
  await expect(page.getByLabel("Keyboard disrupted route segment")).toBeVisible();

  await expectNoCriticalOrSeriousViolations(page, "keyboard routing result");
});
