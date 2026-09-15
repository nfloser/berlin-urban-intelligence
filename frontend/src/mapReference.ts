import type { FeatureCollection } from "geojson";

export type ReferenceMapLayer = "facilities" | "stops" | "climate";

export type ReferenceMapBounds = {
  west: number;
  south: number;
  east: number;
  north: number;
};

export type ReferenceMapMetadata = {
  bounds: ReferenceMapBounds;
  totals: Record<ReferenceMapLayer, number>;
  matched: Record<ReferenceMapLayer, number>;
  returned: Record<ReferenceMapLayer, number>;
  truncated: Record<ReferenceMapLayer, boolean>;
};

export type ReferenceMapResponse = FeatureCollection & {
  metadata: ReferenceMapMetadata;
};

export type ReferenceLayerSummary = {
  key: ReferenceMapLayer;
  label: string;
  returned: number;
  matched: number;
  total: number;
  truncated: boolean;
};

const LAYER_LABELS: Record<ReferenceMapLayer, string> = {
  facilities: "Critical facilities",
  stops: "VBB stops",
  climate: "Official climate features",
};

export class ReferenceMapRequestTracker {
  private generation = 0;

  begin(): number {
    this.generation += 1;
    return this.generation;
  }

  isCurrent(token: number): boolean {
    return token === this.generation;
  }

  invalidate(): void {
    this.generation += 1;
  }
}

export function buildReferenceMapPath(
  bounds: ReferenceMapBounds,
  layers: ReferenceMapLayer[],
  limitPerLayer = 2500,
): string {
  if (bounds.west >= bounds.east) {
    throw new Error("west must be smaller than east");
  }
  if (bounds.south >= bounds.north) {
    throw new Error("south must be smaller than north");
  }
  if (layers.length === 0) {
    throw new Error("at least one map layer is required");
  }
  if (!Number.isInteger(limitPerLayer) || limitPerLayer <= 0 || limitPerLayer > 5000) {
    throw new Error("limit per layer must be an integer between 1 and 5000");
  }

  const params = new URLSearchParams({
    west: String(bounds.west),
    south: String(bounds.south),
    east: String(bounds.east),
    north: String(bounds.north),
    layers: layers.join(","),
    limit_per_layer: String(limitPerLayer),
  });
  return `/api/v1/map/reference?${params.toString()}`;
}

export function referenceLayerSummaries(metadata: ReferenceMapMetadata): ReferenceLayerSummary[] {
  const keys: ReferenceMapLayer[] = ["facilities", "stops", "climate"];
  return keys.map((key) => ({
    key,
    label: LAYER_LABELS[key],
    returned: metadata.returned[key] ?? 0,
    matched: metadata.matched[key] ?? 0,
    total: metadata.totals[key] ?? 0,
    truncated: metadata.truncated[key] ?? false,
  }));
}
