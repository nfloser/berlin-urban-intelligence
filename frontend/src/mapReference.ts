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
  totals: Partial<Record<ReferenceMapLayer, number>>;
  matched: Partial<Record<ReferenceMapLayer, number>>;
  returned: Partial<Record<ReferenceMapLayer, number>>;
  truncated: Partial<Record<ReferenceMapLayer, boolean>>;
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

export type ReferenceHitTestPoint = {
  x: number;
  y: number;
};

export type ReferenceHitTestBox = [[number, number], [number, number]];

export type ReferencePointHit = {
  layer: "facilities" | "stops";
  id: string;
};

export type ReferencePointProjector = (coordinates: [number, number]) => ReferenceHitTestPoint;

const LAYER_LABELS: Record<ReferenceMapLayer, string> = {
  facilities: "Critical facilities",
  stops: "VBB stops",
  climate: "Official climate features",
};
const POINT_LAYER_PRIORITY: Array<ReferencePointHit["layer"]> = ["facilities", "stops"];

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

export function buildReferenceDetailPath(layer: ReferenceMapLayer, resourceId: string): string {
  return `/api/v1/map/reference/${layer}/${encodeURIComponent(resourceId)}`;
}

export function featureCollectionForLayer(
  response: ReferenceMapResponse,
  layer: ReferenceMapLayer,
): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: response.features.filter((feature) => feature.properties?.layer === layer),
  };
}

export function referenceHitTestBox(
  point: ReferenceHitTestPoint,
  radius = 8,
): ReferenceHitTestBox {
  if (!Number.isFinite(radius) || radius <= 0) {
    throw new Error("reference hit-test radius must be positive");
  }
  return [
    [point.x - radius, point.y - radius],
    [point.x + radius, point.y + radius],
  ];
}

export function referencePointHit(
  response: ReferenceMapResponse,
  point: ReferenceHitTestPoint,
  project: ReferencePointProjector,
  radius = 8,
): ReferencePointHit | null {
  if (!Number.isFinite(radius) || radius <= 0) {
    throw new Error("reference point-hit radius must be positive");
  }

  for (const layer of POINT_LAYER_PRIORITY) {
    for (const feature of response.features) {
      if (feature.properties?.layer !== layer || feature.geometry?.type !== "Point") continue;
      const [longitude, latitude] = feature.geometry.coordinates;
      if (typeof longitude !== "number" || typeof latitude !== "number") continue;
      const projected = project([longitude, latitude]);
      if (
        Math.abs(projected.x - point.x) > radius ||
        Math.abs(projected.y - point.y) > radius
      ) {
        continue;
      }
      const rawId = feature.properties?.id ?? feature.id;
      if (rawId === null || rawId === undefined) continue;
      return { layer, id: String(rawId) };
    }
  }
  return null;
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
