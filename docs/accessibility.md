# Dashboard accessibility baseline

Berlin Urban Intelligence treats accessibility as an engineering quality property of the research dashboard. This document records the current automated baseline, the non-pointer analytical path, manual review steps and explicit limits of the claim.

## Scope and claim boundary

The repository does **not** claim formal WCAG conformance or accessibility certification. The current baseline is intended to catch high-impact regressions in the principal dashboard workflow and to make core analytical actions operable without relying exclusively on a pointer.

A formal conformance statement would require a dedicated audit across supported browsers, assistive technologies, content states, responsive layouts and all applicable WCAG success criteria. Automated Axe results alone are not sufficient for that claim.

## Automated acceptance

The composed browser CI installs pinned `@playwright/test` and `@axe-core/playwright` versions in an isolated acceptance runner. `frontend/e2e/accessibility.spec.ts` runs against the same nginx → FastAPI → persisted acceptance-state → React/MapLibre stack as the rest of browser acceptance.

The automated contract currently verifies:

- principal initial and scenario-result states have no Axe violations classified as `critical` or `serious` for the configured WCAG A/AA tags;
- workflow selection and execution are keyboard operable;
- reference-layer checkboxes can be toggled with the keyboard;
- heat-scenario input and submission are keyboard operable;
- the derived-product selector is keyboard focusable;
- focused form controls expose a visible focus outline;
- scrollable source and agent diagnostic regions are keyboard focusable and have accessible region names; and
- resilience routing has a non-pointer alternative that resolves typed longitude/latitude coordinates through `/api/v1/network/nearest`, then uses the same baseline and disruption APIs as map-selected routing.

The map itself remains a visual spatial-analysis surface. Keyboard routing is therefore provided as an equivalent analytical route-selection path rather than attempting to emulate arbitrary map pointer gestures through hidden keyboard behavior.

## Keyboard routing alternative

The `Keyboard routing coordinates` fieldset accepts origin and destination longitude/latitude values. Each endpoint is resolved to the nearest persisted network node through the production nearest-node API. Once both nodes are resolved, the user can run the baseline route and select a route segment for disruption comparison with native form controls.

This path intentionally reuses the existing resilience API contracts. It does not create a parallel routing algorithm, synthetic network or test-only endpoint.

## Manual release checklist

Run this checklist when making substantial dashboard/layout changes or before a release candidate. Record any material failure as an issue rather than treating this document as proof that the check occurred.

### Keyboard navigation and focus

- [ ] Starting from the browser chrome, use `Tab`, `Shift+Tab`, arrow keys, `Space` and `Enter` only; confirm all principal form controls can be reached and operated.
- [ ] Confirm the focused element always has a clearly visible focus indicator against its surrounding surface.
- [ ] Confirm source and agent scroll regions can receive focus and scroll from the keyboard when their content overflows.
- [ ] Confirm workflow execution, layer toggles, heat-scenario assessment, derived inspection and keyboard routing can be completed without a mouse or touch input.
- [ ] Confirm focus does not become trapped in MapLibre controls or any inspector region.

### Zoom, reflow and low-vision use

- [ ] At 200% browser zoom, confirm text and controls remain readable and principal analytical actions do not require horizontal page scrolling to discover controls.
- [ ] At 400% browser zoom or an equivalently narrow viewport, confirm stacked layouts remain usable; where spatial map content necessarily clips or pans, confirm the non-map routing alternative remains reachable.
- [ ] Confirm text does not overlap controls, status messages or result values when zoomed.
- [ ] Confirm visible focus indicators remain distinguishable at high zoom.
- [ ] Check important text/status combinations for sufficient visual distinction; do not use color alone to communicate availability, freshness, errors or scenario state.

### Screen-reader naming and status semantics

- [ ] With a screen reader, confirm important inputs/selects/buttons announce a useful accessible name rather than only a visual position or icon.
- [ ] Confirm `Keyboard routing coordinates`, source-status and agent-capability regions have meaningful announced names.
- [ ] Confirm asynchronous routing endpoint resolution and result/error states are announced through their live-region or alert semantics without moving focus unexpectedly.
- [ ] Confirm scenario results and route-comparison values are understandable when read linearly without relying on map color or geometry.
- [ ] Confirm decorative map rendering does not hide the existence of the equivalent coordinate-based routing controls.

## Known limitations

- The MapLibre canvas is still primarily visual. Arbitrary feature exploration on the map is not claimed to be fully screen-reader equivalent.
- Automated Axe scans cover representative principal states, not every possible provider/error/scenario combination.
- Contrast and reflow still require human review because automated checks cannot establish usability for every display, zoom level or perceptual need.
- CI currently runs Chromium only; cross-browser assistive-technology behavior is not proven.
- The research dashboard is not yet the subject of an external accessibility audit.

## Regression policy

Accessibility failures are product defects, not test noise. Do not suppress an Axe rule or remove keyboard assertions solely to make CI pass. If an automated rule is demonstrably inapplicable, document the reason in the test or this file and preserve an equivalent verification path.
