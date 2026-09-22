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

export type Provenance = {
  provider: string;
  dataset: string;
  source_url: string;
  original_identifier?: string | null;
  observation_time?: string | null;
  retrieved_at: string;
  processed_at: string;
  processing_method?: string | null;
  agent: string;
  agent_version: string;
  model_version?: string | null;
  source_licence?: string | null;
  quality_note?: string | null;
  upstream_ids: string[];
};

export type Observation = {
  id: string;
  entity_id: string;
  phenomenon: string;
  value: unknown;
  unit?: string | null;
  observed_at: string;
  state: string;
  quality: string;
  provenance: Provenance;
  spatial?: Spatial | null;
};

export type UrbanEntity = {
  id: string;
  name?: string | null;
  entity_type: string;
  spatial?: Spatial | null;
  source_identifier?: string | null;
};

export type CriticalFacility = UrbanEntity & {
  category: string;
  confidence?: string | null;
  quality: string;
  provenance?: Provenance | null;
};

export type OfficialModelFeature = {
  id: string;
  entity_id: string;
  model_name: string;
  feature_type: string;
  state: "official_modelled";
  quality: string;
  properties: Record<string, unknown>;
  provenance: Provenance;
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

export type SnapshotReloadDiagnostic = {
  status: "current" | "missing" | "invalid";
  last_error: string | null;
};

export type SystemResponse = {
  name: string;
  version: string;
  contract_version: string;
  runtime_generated_at: string | null;
  reference_generated_at: string | null;
  energy_generated_at: string | null;
  derived_generated_at: string | null;
  traffic_disruption_generated_at: string | null;
  snapshot_reload: Record<string, SnapshotReloadDiagnostic>;
  synthetic_production_fallback: boolean;
};

export type DerivationDefinition = {
  id: string;
  name: string;
  description: string;
  producer_agent_id: string;
  producer_version: string;
  algorithm_version: string;
  output_kind: string;
};

export type DerivationInput = {
  id: string;
  role: string;
  required: boolean;
};

export type DerivationRecord = {
  id: string;
  definition_id: string;
  entity_id: string;
  phenomenon: string;
  value: unknown;
  unit?: string | null;
  valid_at: string;
  computed_at: string;
  quality: string;
  freshness: string;
  status: string;
  inputs: DerivationInput[];
  provenance: Provenance;
  context: "baseline" | "scenario";
  scenario_id?: string | null;
};

export type DerivedStateResponse = {
  generated_at: string | null;
  definitions: DerivationDefinition[];
  records: DerivationRecord[];
};

export type DependencyResponse = {
  resource_id: string;
  upstream: string[];
  downstream: string[];
  status: string | null;
};

export type WorkflowKind =
  | "urban_snapshot"
  | "heat_energy"
  | "mobility_exposure"
  | "mobility_resilience"
  | "heat_mobility_resilience";

export type OrchestrationResponse = {
  plan: {
    workflow: WorkflowKind;
    agents: string[];
    required_capabilities: string[];
    missing_capabilities: string[];
    requires_llm: false;
    note: string;
  };
  execution: {
    workflow: WorkflowKind;
    generated_at: string;
    status: string;
    agent_health: Record<string, Health>;
    missing_agents: string[];
    missing_capabilities: string[];
    requires_llm: false;
    note: string;
  };
};

export type MapSearchResult = {
  id: string;
  layer: "facilities" | "stops";
  name: string;
  subtitle: string;
  longitude: number;
  latitude: number;
};

export type TrafficDisruption = {
  id: string;
  subtype: string;
  severity?: string | null;
  street?: string | null;
  section?: string | null;
  description: string;
  direction?: string | null;
  valid_from: string;
  valid_to: string;
  source_updated_at: string;
  is_future?: boolean | null;
  network_reference_ids: string[];
  is_full_closure: boolean;
  speed_penalty_factor?: number | null;
  spatial: Spatial;
  provenance: Provenance;
};

export type TrafficDisruptionResponse = {
  generated_at: string | null;
  source_id: string;
  last_success_at: string | null;
  latest_source_update_at: string | null;
  source_error: string | null;
  freshness: string;
  routing_eligible: boolean;
  evaluated_at: string | null;
  disruption_count_total: number;
  active_count_total: number;
  returned: number;
  truncated: boolean;
  disruptions: TrafficDisruption[];
};

export type RouteState = "baseline" | "disrupted" | "rerouted" | "blocked";

export type NetworkNodePick = {
  node_id: string;
  longitude: number;
  latitude: number;
  distance_m: number;
  metric_crs: string;
};

export type RouteResponse = {
  node_path: string[];
  edge_ids: string[];
  travel_time_s: number;
  scenario_name: string | null;
  geometry: Geometry | null;
  length_m: number;
  route_state: RouteState;
  active_disruption_ids: string[];
  closed_edge_ids: string[];
  effective_node_path: string[];
  effective_edge_ids: string[];
  effective_travel_time_s: number | null;
  effective_length_m: number | null;
  effective_geometry: Geometry | null;
  travel_time_delta_s: number | null;
  disruption_data_available: boolean;
  disruption_freshness: string;
  disruption_source_error: string | null;
};

export type RouteComparisonResponse = {
  origin: string;
  destination: string;
  scenario_name: string;
  baseline_travel_time_s: number;
  scenario_travel_time_s: number;
  absolute_delta_s: number;
  relative_delta_pct: number;
  baseline_node_path: string[];
  baseline_edge_ids: string[];
  scenario_node_path: string[];
  scenario_edge_ids: string[];
  baseline_geometry: Geometry | null;
  scenario_geometry: Geometry | null;
};

export type CriticalRouteProvenance = {
  reference_generated_at: string;
  computed_at: string;
  source_providers: string[];
  source_datasets: string[];
  source_licences: string[];
  processing_method: string;
  traffic_data_available: false;
  disruption_source_providers: string[];
  disruption_source_licences: string[];
};

export type CriticalRoute = {
  id: string;
  origin_facility_id: string;
  origin_name: string;
  origin_category: string;
  destination_facility_id: string;
  destination_name: string;
  destination_category: string;
  travel_time_s: number;
  length_m: number;
  node_path: string[];
  edge_ids: string[];
  geometry: Geometry;
  quality: string;
  freshness: string;
  route_state: RouteState;
  active_disruption_ids: string[];
  closed_edge_ids: string[];
  disruption_aware_travel_time_s: number | null;
  disruption_aware_length_m: number | null;
  disruption_aware_node_path: string[];
  disruption_aware_edge_ids: string[];
  disruption_aware_geometry: Geometry | null;
  travel_time_delta_s: number | null;
  provenance: CriticalRouteProvenance;
};

export type CriticalRouteSnapshotResponse = {
  computed_at: string;
  reference_generated_at: string | null;
  status: "available" | "degraded" | "unavailable" | "unknown";
  freshness: string;
  quality: string;
  unsnapped_facility_ids: string[];
  unreachable_facility_ids: string[];
  source_errors: Record<string, string>;
  traffic_data_available: false;
  disruption_data_available: boolean;
  disruption_generated_at: string | null;
  disruption_freshness: string;
  disruption_source_error: string | null;
  note: string;
  route_count_total: number;
  returned: number;
  truncated: boolean;
  routes: CriticalRoute[];
};

export type AssessmentResponse = {
  generated_at: string;
  scenario_name: string;
  heat: Record<string, unknown> | null;
  energy: Record<string, unknown> | null;
  resilience: Record<string, unknown> | null;
  unavailable_dimensions: string[];
  dimension_errors: Record<string, string>;
  composite_score: null;
  note: string;
};

export function mapSearchPath(query: string, limit = 8): string {
  const normalized = query.trim();
  if (normalized.length < 2) {
    throw new Error("Search query must contain at least two characters.");
  }
  if (!Number.isInteger(limit) || limit < 1 || limit > 50) {
    throw new Error("Search result limit must be between 1 and 50.");
  }
  const params = new URLSearchParams({ q: normalized, limit: String(limit) });
  return `/api/v1/map/search?${params.toString()}`;
}

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}${detail ? ` · ${detail}` : ""}`);
  }
  return (await response.json()) as T;
}

export function routeRequest(origin: string, destination: string): Record<string, string> {
  const start = origin.trim();
  const end = destination.trim();
  if (!start || !end) {
    throw new Error("Origin and destination are required.");
  }
  if (start === end) {
    throw new Error("Origin and destination must be different.");
  }
  return { origin: start, destination: end };
}

export function networkDisruptionRequest(
  origin: string,
  destination: string,
  closedEdge: string,
): Record<string, unknown> {
  const values = [origin, destination, closedEdge].map((value) => value.trim());
  if (values.some((value) => value.length === 0)) {
    throw new Error("Origin, destination and closed edge are required.");
  }
  return {
    origin: values[0],
    destination: values[1],
    scenario: {
      name: `Network disruption: ${values[2]}`,
      kinds: ["network_disruption"],
      closed_network_edges: [values[2]],
      is_hypothetical: true,
    },
  };
}

export function heatAssessmentRequest(deltaC: number): Record<string, unknown> {
  if (!Number.isFinite(deltaC) || deltaC < -20 || deltaC > 20) {
    throw new Error("Temperature delta must be between -20 and 20 Cel.");
  }
  return {
    scenario: {
      name: `Heat delta ${deltaC >= 0 ? "+" : ""}${deltaC} Cel`,
      kinds: ["extreme_heat"],
      temperature_delta_c: deltaC,
      is_hypothetical: true,
    },
  };
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

export function mapLayerCounts(counts: {
  facilities: number;
  stops: number;
  climate: number;
}): Array<[string, number]> {
  const layers: Array<[string, number]> = [
    ["Critical facilities", counts.facilities],
    ["VBB stops", counts.stops],
    ["Official climate features", counts.climate],
  ];
  return layers.filter(([, count]) => count > 0);
}

export function systemSnapshotToken(system: SystemResponse): string {
  return [
    system.runtime_generated_at ?? "missing",
    system.reference_generated_at ?? "missing",
    system.energy_generated_at ?? "missing",
    system.derived_generated_at ?? "missing",
    system.traffic_disruption_generated_at ?? "missing",
  ].join("|");
}
