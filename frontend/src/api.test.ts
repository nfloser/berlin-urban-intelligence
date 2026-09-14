import { describe, expect, it } from "vitest";
import { displayValue, toFeatureCollection } from "./api";

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
        spatial: { crs: "EPSG:25833", geometry: { type: "Point", coordinates: [391000, 5820000] } },
      },
      { id: "fixture:missing" },
    ]);
    expect(collection.features).toHaveLength(1);
    expect(collection.features[0].id).toBe("fixture:wgs84");
  });
});
