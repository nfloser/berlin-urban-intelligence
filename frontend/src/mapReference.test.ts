import { describe, expect, it } from "vitest";
import {
  ReferenceMapRequestTracker,
  buildReferenceMapPath,
  referenceLayerSummaries,
  type ReferenceMapResponse,
} from "./mapReference";

describe("viewport reference map semantics", () => {
  it("builds a deterministic bbox request for the active viewport", () => {
    expect(
      buildReferenceMapPath(
        { west: 13.3, south: 52.4, east: 13.6, north: 52.7 },
        ["facilities", "stops", "climate"],
        2500,
      ),
    ).toBe(
      "/api/v1/map/reference?west=13.3&south=52.4&east=13.6&north=52.7&layers=facilities%2Cstops%2Cclimate&limit_per_layer=2500",
    );
  });

  it("rejects invalid bounds before issuing a request", () => {
    expect(() =>
      buildReferenceMapPath(
        { west: 13.6, south: 52.4, east: 13.3, north: 52.7 },
        ["facilities"],
      ),
    ).toThrow(/west must be smaller than east/);
  });

  it("reports matched, returned and truncation per visible layer", () => {
    const response: ReferenceMapResponse = {
      type: "FeatureCollection",
      features: [],
      metadata: {
        bounds: { west: 13.3, south: 52.4, east: 13.6, north: 52.7 },
        totals: { facilities: 213, stops: 42133, climate: 8963 },
        matched: { facilities: 12, stops: 4200, climate: 120 },
        returned: { facilities: 12, stops: 2500, climate: 120 },
        truncated: { facilities: false, stops: true, climate: false },
      },
    };

    expect(referenceLayerSummaries(response.metadata)).toEqual([
      {
        key: "facilities",
        label: "Critical facilities",
        returned: 12,
        matched: 12,
        total: 213,
        truncated: false,
      },
      {
        key: "stops",
        label: "VBB stops",
        returned: 2500,
        matched: 4200,
        total: 42133,
        truncated: true,
      },
      {
        key: "climate",
        label: "Official climate features",
        returned: 120,
        matched: 120,
        total: 8963,
        truncated: false,
      },
    ]);
  });

  it("marks an older viewport request stale as soon as a newer request starts", () => {
    const tracker = new ReferenceMapRequestTracker();
    const first = tracker.begin();
    expect(tracker.isCurrent(first)).toBe(true);

    const second = tracker.begin();
    expect(tracker.isCurrent(first)).toBe(false);
    expect(tracker.isCurrent(second)).toBe(true);

    tracker.invalidate();
    expect(tracker.isCurrent(second)).toBe(false);
  });
});
