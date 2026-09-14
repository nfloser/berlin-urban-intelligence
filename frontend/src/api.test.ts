import { describe, expect, it } from "vitest";
import {
  displayValue,
  heatAssessmentRequest,
  mapLayerCounts,
  networkDisruptionRequest,
  toFeatureCollection,
} from "./api";

describe("dashboard data semantics", () => {
  it("does not turn missing values into plausible numbers", () => {
    expect(displayValue(null, "Cel")).toBe("Unavailable");
    expect(displayValue(undefined)).toBe("Unavailable");
    expect(displayValue(0, "s")).toBe("0 s");
  });

  it("only maps explicitly WGS84 geometries", () => {
    const collection = toFeatureCollection([
      {
        id: "fixture:wgs84",
        spatial: { crs: "EPSG:4326", geometry: { type: "Point", coordinates: [13.4, 52.5] } },
      },
      {
        id: "fixture:projected",
        spatial: {
          crs: "EPSG:25833",
          geometry: { type: "Point", coordinates: [391000, 5820000] },
        },
      },
      { id: "fixture:missing" },
    ]);
    expect(collection.features).toHaveLength(1);
    expect(collection.features[0].id).toBe("fixture:wgs84");
  });

  it("reports map layer counts only for mappable features", () => {
    expect(mapLayerCounts({ facilities: 2, stops: 5, climate: 1 })).toEqual([
      ["Critical facilities", 2],
      ["VBB stops", 5],
      ["Official climate features", 1],
    ]);
    expect(mapLayerCounts({ facilities: 0, stops: 0, climate: 0 })).toEqual([]);
  });

  it("builds a route-comparison request with an explicit closed edge", () => {
    expect(networkDisruptionRequest("node:a", "node:c", "edge:bc")).toEqual({
      origin: "node:a",
      destination: "node:c",
      scenario: {
        name: "Network disruption: edge:bc",
        kinds: ["network_disruption"],
        closed_network_edges: ["edge:bc"],
        is_hypothetical: true,
      },
    });
    expect(() => networkDisruptionRequest("", "node:c", "edge:bc")).toThrow(/required/);
  });

  it("builds an explicitly hypothetical heat scenario without observed-state fields", () => {
    expect(heatAssessmentRequest(3)).toEqual({
      scenario: {
        name: "Heat delta +3 Cel",
        kinds: ["extreme_heat"],
        temperature_delta_c: 3,
        is_hypothetical: true,
      },
    });
  });

  it("rejects implausible dashboard heat deltas before calling the API", () => {
    expect(() => heatAssessmentRequest(21)).toThrow(/between -20 and 20/);
    expect(() => heatAssessmentRequest(Number.NaN)).toThrow(/between -20 and 20/);
  });
});
