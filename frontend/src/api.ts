import type { Feature, FeatureCollection, Geometry } from "geojson";

export type Health = {
  agent_id: string;
  status: "available" | "degraded" | "unavailable" | "unknown";
  checked_at: string;
  freshness: string;
  quality: string;
  detail?: string | null;
};

export type Spatial = {
  crs: string;
  geometry?: Geometry | null;
};

export type UrbanEntity = {
  id: string;
  name?: string | null;
  entity_type: string;
  spatial?: Spatial | null;
};

export type CriticalFacility = UrbanEntity & {
  category: string;
  confidence: string;
};

export type OfficialModelFeature = {
  id: string;
  entity_id: string;
  model_name: string;
  feature_type: string;
  state: "official_modelled";
  properties: Record<string, unknown>;
  spatial: Spatial;
};

export type MobilityResponse = {
  health: Health;
  snapshot: {
    observed_at: string;
    retrieved_at: string;
    trip_updates: number;
    delayed_trip_updates: number;
    max_abs_delay_s: number | null;
    quality: string;
    note: string;
    source: string;
  } | null;
};

export type EnergyResponse = {
  health: Health;
  evaluation: Record<string, unknown> | null;
  forecasts: Array<Record<string, unknown>>;
};

export type SystemResponse = {
  name: string;
  version: string;
  contract_version: string;
  runtime_generated_at: string | null;
  reference_generated_at: string | null;
  synthetic_production_fallback: boolean;
};

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export function displayValue(value: unknown, unit?: string | null): string {
  if (value === null || value === undefined || value === "") {
    return "Unavailable";
  }
  return unit ? `${String(value)} ${unit}` : String(value);
}

export function toFeatureCollection(
  entities: Array<{ id: string; spatial?: Spatial | null }>,
): FeatureCollection {
  const features: Feature[] = [];
  for (const entity of entities) {
    const geometry = entity.spatial?.geometry;
    if (!geometry || entity.spatial?.crs !== "EPSG:4326") continue;
    features.push({
      type: "Feature",
      id: entity.id,
      geometry,
      properties: { id: entity.id },
    });
  }
  return { type: "FeatureCollection", features };
}
