import { describe, expect, it } from "vitest";
import {
  ReferenceMapRequestTracker,
  buildReferenceDetailPath,
  buildReferenceMapPath,
  featureCollectionForLayer,
  referenceHitTestBox,
  referenceLayerSummaries,
  referencePointHit,
  type ReferenceMapResponse,
} from "./mapReference";

function fixtureResponse(): ReferenceMapResponse {
  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        id: "facility:inside",
        geometry: { type: "Point", coordinates: [13.405, 52.52] },
        properties: { id: "facility:inside", layer: "facilities" },
      },
      {
        type: "Feature",
        id: "stop:inside",
        geometry: { type: "Point", coordinates: [13.41, 52.521] },
        properties: { id: "stop:inside", layer: "stops" },
      },
    ],
    metadata: {
      bounds: { west: 13.3, south: 52.4, east: 13.6, north: 52.7 },
      totals: { facilities: 213, stops: 42133, climate: 8963 },
      matched: { facilities: 12, stops: 4200, climate: 120 },
      returned: { facilities: 12, stops: 2500, climate: 120 },
      truncated: { facilities: false, stops: true, climate: false },
    },
  };
}

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
    expect(referenceLayerSummaries(fixtureResponse().metadata)).toEqual([
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

  it("models metadata from a request that selected only one layer", () => {
    const response: ReferenceMapResponse = {
      type: "FeatureCollection",
      features: [],
      metadata: {
        bounds: { west: 13.3, south: 52.4, east: 13.6, north: 52.7 },
        totals: { stops: 42133 },
        matched: { stops: 2 },
        returned: { stops: 2 },
        truncated: { stops: false },
      },
    };

    expect(referenceLayerSummaries(response.metadata)).toEqual([
      {
        key: "facilities",
        label: "Critical facilities",
        returned: 0,
        matched: 0,
        total: 0,
        truncated: false,
      },
      {
        key: "stops",
        label: "VBB stops",
        returned: 2,
        matched: 2,
        total: 42133,
        truncated: false,
      },
      {
        key: "climate",
        label: "Official climate features",
        returned: 0,
        matched: 0,
        total: 0,
        truncated: false,
      },
    ]);
  });

  it("projects a mixed viewport response into one map source per layer", () => {
    const facilities = featureCollectionForLayer(fixtureResponse(), "facilities");
    const stops = featureCollectionForLayer(fixtureResponse(), "stops");
    const climate = featureCollectionForLayer(fixtureResponse(), "climate");

    expect(facilities.features.map((feature) => feature.id)).toEqual(["facility:inside"]);
    expect(stops.features.map((feature) => feature.id)).toEqual(["stop:inside"]);
    expect(climate.features).toEqual([]);
  });

  it("builds an encoded canonical detail path from rendered layer identity", () => {
    expect(buildReferenceDetailPath("facilities", "facility:inside/ward a")).toBe(
      "/api/v1/map/reference/facilities/facility%3Ainside%2Fward%20a",
    );
  });

  it("expands a map click into a deterministic reference hit-test box", () => {
    expect(referenceHitTestBox({ x: 100, y: 200 })).toEqual([
      [92, 192],
      [108, 208],
    ]);
    expect(referenceHitTestBox({ x: 100, y: 200 }, 4)).toEqual([
      [96, 196],
      [104, 204],
    ]);
  });

  it("falls back to viewport point geometry when the rendered feature index lags", () => {
    const hit = referencePointHit(
      fixtureResponse(),
      { x: 400, y: 300 },
      ([longitude, latitude]) => ({
        x: 400 + (longitude - 13.405) * 1000,
        y: 300 - (latitude - 52.52) * 1000,
      }),
    );

    expect(hit).toEqual({ layer: "facilities", id: "facility:inside" });
  });

  it("prefers facilities over stops when point hit areas overlap", () => {
    const response = fixtureResponse();
    const hit = referencePointHit(response, { x: 10, y: 10 }, () => ({ x: 10, y: 10 }));

    expect(hit).toEqual({ layer: "facilities", id: "facility:inside" });
  });

  it("returns no point hit outside the tolerance", () => {
    const hit = referencePointHit(fixtureResponse(), { x: 0, y: 0 }, () => ({ x: 50, y: 50 }));
    expect(hit).toBeNull();
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
