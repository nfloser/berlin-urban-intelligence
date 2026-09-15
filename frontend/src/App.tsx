import type { FeatureCollection } from "geojson";
import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";
import * as maplibregl from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import {
  type AssessmentResponse,
  type CriticalFacility,
  type EnergyResponse,
  type Health,
  type MobilityResponse,
  type NetworkNodePick,
  type Observation,
  type OfficialModelFeature,
  type OrchestrationResponse,
  type RouteComparisonResponse,
  type RouteResponse,
  type SystemResponse,
  type UrbanEntity,
  type WorkflowKind,
  displayValue,
  fetchJson,
  heatAssessmentRequest,
  mapLayerCounts,
  networkDisruptionRequest,
  postJson,
  routeRequest,
  toFeatureCollection,
} from "./api";
import MapEntityInspector, { type MapSelection } from "./MapEntityInspector";

const BASE_STYLE = "https://tiles.openfreemap.org/styles/liberty";
const WORKFLOWS: Array<{ value: WorkflowKind; label: string }> = [
  { value: "urban_snapshot", label: "Urban snapshot" },
  { value: "heat_energy", label: "Heat + energy" },
  { value: "mobility_exposure", label: "Mobility + exposure" },
  { value: "mobility_resilience", label: "Mobility + resilience" },
  { value: "heat_mobility_resilience", label: "Heat + mobility + resilience" },
];

type LoadState = "loading" | "ready" | "error";
type ActionState = "idle" | "running" | "error";

function StatusBadge({ health }: { health?: Health }) {
  const status = health?.status ?? "unknown";
  return <span className={`status status-${status}`}>{status}</span>;
}

function App() {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [system, setSystem] = useState<SystemResponse | null>(null);
  const [health, setHealth] = useState<Record<string, Health>>({});
  const [mobility, setMobility] = useState<MobilityResponse | null>(null);
  const [energy, setEnergy] = useState<EnergyResponse | null>(null);
  const [facilities, setFacilities] = useState<CriticalFacility[]>([]);
  const [stops, setStops] = useState<UrbanEntity[]>([]);
  const [climate, setClimate] = useState<OfficialModelFeature[]>([]);
  const [mapSelection, setMapSelection] = useState<MapSelection | null>(null);
  const [observations, setObservations] = useState<Observation[]>([]);
  const [selectedObservationId, setSelectedObservationId] = useState<string | null>(null);
  const [workflow, setWorkflow] = useState<WorkflowKind>("urban_snapshot");
  const [workflowState, setWorkflowState] = useState<ActionState>("idle");
  const [workflowResult, setWorkflowResult] = useState<OrchestrationResponse | null>(null);
  const [workflowError, setWorkflowError] = useState<string | null>(null);
  const [temperatureDelta, setTemperatureDelta] = useState("");
  const [visibleLayers, setVisibleLayers] = useState({
    facilities: true,
    stops: true,
    climate: true,
  });
  const [assessmentState, setAssessmentState] = useState<ActionState>("idle");
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null);
  const [assessmentError, setAssessmentError] = useState<string | null>(null);
  const [routeOrigin, setRouteOrigin] = useState<NetworkNodePick | null>(null);
  const [routeDestination, setRouteDestination] = useState<NetworkNodePick | null>(null);
  const [routeSelectionMode, setRouteSelectionMode] = useState<"origin" | "destination" | null>(null);
  const [routeBaseline, setRouteBaseline] = useState<RouteResponse | null>(null);
  const [closedEdge, setClosedEdge] = useState("");
  const [routeState, setRouteState] = useState<ActionState>("idle");
  const [routeError, setRouteError] = useState<string | null>(null);
  const [routeComparison, setRouteComparison] = useState<RouteComparisonResponse | null>(null);

  const selectedObservation =
    observations.find((item) => item.id === selectedObservationId) ?? null;

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchJson<SystemResponse>("/api/v1/system"),
      fetchJson<Record<string, Health>>("/api/v1/agents/health"),
      fetchJson<MobilityResponse>("/api/v1/mobility"),
      fetchJson<EnergyResponse>("/api/v1/energy"),
      fetchJson<CriticalFacility[]>("/api/v1/facilities?limit=1000"),
      fetchJson<UrbanEntity[]>("/api/v1/transport-stops?limit=1000"),
      fetchJson<OfficialModelFeature[]>("/api/v1/climate-features?limit=1000"),
      fetchJson<Observation[]>("/api/v1/observations?limit=250"),
    ])
      .then(
        ([
          systemValue,
          healthValue,
          mobilityValue,
          energyValue,
          facilityValue,
          stopValue,
          climateValue,
          observationValue,
        ]) => {
          if (cancelled) return;
          setSystem(systemValue);
          setHealth(healthValue);
          setMobility(mobilityValue);
          setEnergy(energyValue);
          setFacilities(facilityValue);
          setStops(stopValue);
          setClimate(climateValue);
          setObservations(observationValue);
          setSelectedObservationId(observationValue[0]?.id ?? null);
          setLoadState("ready");
        },
      )
      .catch((reason: unknown) => {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : "Unknown API error");
        setLoadState("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: BASE_STYLE,
      center: [13.405, 52.52],
      zoom: 10,
    });
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || loadState !== "ready") return;
    const facilityData = toFeatureCollection(facilities);
    const stopData = toFeatureCollection(stops);
    const climateData = toFeatureCollection(climate);
    const inspectionData: FeatureCollection = mapSelection
      ? toFeatureCollection([mapSelection.item])
      : { type: "FeatureCollection", features: [] };
    const routeData = (geometry: RouteComparisonResponse["baseline_geometry"]): FeatureCollection => ({
      type: "FeatureCollection",
      features: geometry
        ? [{ type: "Feature", properties: {}, geometry }]
        : [],
    });
    const baselineRouteData = routeData(
      routeComparison?.baseline_geometry ?? routeBaseline?.geometry ?? null,
    );
    const selectionData: FeatureCollection = {
      type: "FeatureCollection",
      features: [routeOrigin, routeDestination]
        .filter((node): node is NetworkNodePick => node !== null)
        .map((node) => ({
          type: "Feature",
          properties: { node_id: node.node_id },
          geometry: { type: "Point", coordinates: [node.longitude, node.latitude] },
        })),
    };
    const scenarioRouteData = routeData(routeComparison?.scenario_geometry ?? null);
    const setVisibility = (layerId: string, visible: boolean) => {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, "visibility", visible ? "visible" : "none");
      }
    };

    const installLayers = () => {
      const upsert = (id: string, data: FeatureCollection) => {
        const source = map.getSource(id) as GeoJSONSource | undefined;
        if (source) source.setData(data);
        else map.addSource(id, { type: "geojson", data });
      };
      upsert("facilities", facilityData);
      upsert("stops", stopData);
      upsert("climate", climateData);
      upsert("map-inspection", inspectionData);
      upsert("route-baseline", baselineRouteData);
      upsert("route-scenario", scenarioRouteData);
      upsert("route-selection", selectionData);

      if (!map.getLayer("climate-fill")) {
        map.addLayer({
          id: "climate-fill",
          type: "fill",
          source: "climate",
          paint: { "fill-color": "#e0a458", "fill-outline-color": "#e0a458", "fill-opacity": 0.24 },
        });
      }
      if (!map.getLayer("stops-circle")) {
        map.addLayer({
          id: "stops-circle",
          type: "circle",
          source: "stops",
          paint: { "circle-radius": 3, "circle-color": "#65b3d1", "circle-opacity": 0.72 },
        });
      }
      if (!map.getLayer("facilities-circle")) {
        map.addLayer({
          id: "facilities-circle",
          type: "circle",
          source: "facilities",
          paint: {
            "circle-radius": 6,
            "circle-color": "#e36d6d",
            "circle-stroke-color": "#ffffff",
            "circle-stroke-width": 1.5,
          },
        });
      }
      if (!map.getLayer("map-inspection-fill")) {
        map.addLayer({
          id: "map-inspection-fill",
          type: "fill",
          source: "map-inspection",
          paint: { "fill-color": "#f0c75e", "fill-opacity": 0.16 },
        });
      }
      if (!map.getLayer("map-inspection-line")) {
        map.addLayer({
          id: "map-inspection-line",
          type: "line",
          source: "map-inspection",
          paint: { "line-color": "#f0c75e", "line-width": 4, "line-opacity": 0.95 },
        });
      }
      if (!map.getLayer("map-inspection-circle")) {
        map.addLayer({
          id: "map-inspection-circle",
          type: "circle",
          source: "map-inspection",
          paint: {
            "circle-radius": 10,
            "circle-color": "#f0c75e",
            "circle-opacity": 0.3,
            "circle-stroke-color": "#f0c75e",
            "circle-stroke-width": 3,
          },
        });
      }
      if (!map.getLayer("route-selection-circle")) {
        map.addLayer({
          id: "route-selection-circle",
          type: "circle",
          source: "route-selection",
          paint: {
            "circle-radius": 8,
            "circle-color": "#f0c75e",
            "circle-stroke-color": "#111821",
            "circle-stroke-width": 2,
          },
        });
      }
      if (!map.getLayer("route-baseline-line")) {
        map.addLayer({
          id: "route-baseline-line",
          type: "line",
          source: "route-baseline",
          paint: { "line-color": "#dfe8f0", "line-width": 4, "line-opacity": 0.72 },
        });
      }
      if (!map.getLayer("route-scenario-line")) {
        map.addLayer({
          id: "route-scenario-line",
          type: "line",
          source: "route-scenario",
          paint: { "line-color": "#d85f70", "line-width": 5, "line-opacity": 0.9 },
        });
      }
      setVisibility("facilities-circle", visibleLayers.facilities);
      setVisibility("stops-circle", visibleLayers.stops);
      setVisibility("climate-fill", visibleLayers.climate);
    };

    if (map.isStyleLoaded()) installLayers();
    else map.once("load", installLayers);
  }, [
    loadState,
    facilities,
    stops,
    climate,
    mapSelection,
    visibleLayers,
    routeComparison,
    routeBaseline,
    routeOrigin,
    routeDestination,
  ]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || routeSelectionMode === null) return;
    const selectNearestNode = async (event: maplibregl.MapMouseEvent) => {
      setRouteError(null);
      try {
        const point = event.lngLat;
        const node = await fetchJson<NetworkNodePick>(
          `/api/v1/network/nearest?longitude=${point.lng}&latitude=${point.lat}`,
        );
        if (routeSelectionMode === "origin") setRouteOrigin(node);
        else setRouteDestination(node);
        setRouteBaseline(null);
        setRouteComparison(null);
        setClosedEdge("");
        setRouteSelectionMode(null);
      } catch (reason) {
        setRouteError(reason instanceof Error ? reason.message : "Could not select a network node.");
        setRouteSelectionMode(null);
      }
    };
    map.on("click", selectNearestNode);
    return () => {
      map.off("click", selectNearestNode);
    };
  }, [routeSelectionMode]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || loadState !== "ready" || routeSelectionMode !== null) return;

    const inspectReferenceObject = (event: maplibregl.MapMouseEvent) => {
      const inspectableLayers = ["facilities-circle", "stops-circle", "climate-fill"].filter(
        (layerId) => map.getLayer(layerId) !== undefined,
      );
      if (inspectableLayers.length === 0) return;
      const hit = map.queryRenderedFeatures(event.point, { layers: inspectableLayers })[0];
      if (!hit) {
        setMapSelection(null);
        return;
      }
      const rawId = hit.properties?.id ?? hit.id;
      if (rawId === null || rawId === undefined) {
        setMapSelection(null);
        return;
      }
      const id = String(rawId);
      if (hit.layer.id === "facilities-circle") {
        const item = facilities.find((candidate) => candidate.id === id);
        setMapSelection(item ? { kind: "facility", item } : null);
        return;
      }
      if (hit.layer.id === "stops-circle") {
        const item = stops.find((candidate) => candidate.id === id);
        setMapSelection(item ? { kind: "stop", item } : null);
        return;
      }
      const item = climate.find((candidate) => candidate.id === id);
      setMapSelection(item ? { kind: "climate", item } : null);
    };

    map.on("click", inspectReferenceObject);
    return () => {
      map.off("click", inspectReferenceObject);
    };
  }, [loadState, routeSelectionMode, facilities, stops, climate]);

  const startRouteSelection = (mode: "origin" | "destination") => {
    setMapSelection(null);
    setRouteSelectionMode(mode);
  };

  const runWorkflow = async () => {
    setWorkflowState("running");
    setWorkflowError(null);
    try {
      const result = await postJson<OrchestrationResponse>("/api/v1/orchestrate", { workflow });
      setWorkflowResult(result);
      setWorkflowState("idle");
    } catch (reason) {
      setWorkflowError(reason instanceof Error ? reason.message : "Unknown orchestration error");
      setWorkflowState("error");
    }
  };

  const runRouteBaseline = async () => {
    setRouteError(null);
    setRouteComparison(null);
    if (!routeOrigin || !routeDestination) {
      setRouteError("Select an origin and a destination on the map first.");
      return;
    }
    setRouteState("running");
    try {
      const result = await postJson<RouteResponse>(
        "/api/v1/resilience/routes",
        routeRequest(routeOrigin.node_id, routeDestination.node_id),
      );
      setRouteBaseline(result);
      setClosedEdge(result.edge_ids[0] ?? "");
      setRouteState("idle");
    } catch (reason) {
      setRouteError(reason instanceof Error ? reason.message : "Baseline route failed.");
      setRouteState("error");
    }
  };

  const runRouteComparison = async () => {
    setRouteError(null);
    setRouteComparison(null);
    setRouteState("running");
    try {
      if (!routeOrigin || !routeDestination) {
        throw new Error("Select an origin and a destination on the map first.");
      }
      const request = networkDisruptionRequest(
        routeOrigin.node_id,
        routeDestination.node_id,
        closedEdge,
      );
      const result = await postJson<RouteComparisonResponse>(
        "/api/v1/resilience/routes/compare",
        request,
      );
      setRouteComparison(result);
      setRouteState("idle");
    } catch (reason) {
      setRouteError(reason instanceof Error ? reason.message : "Route comparison failed.");
      setRouteState("error");
    }
  };

  const runHeatAssessment = async () => {
    setAssessmentError(null);
    setAssessment(null);
    const parsed = Number(temperatureDelta);
    if (temperatureDelta.trim() === "" || !Number.isFinite(parsed)) {
      setAssessmentError("Enter an explicit temperature delta in Cel.");
      setAssessmentState("error");
      return;
    }
    setAssessmentState("running");
    try {
      const request = heatAssessmentRequest(parsed);
      const result = await postJson<AssessmentResponse>("/api/v1/assess", request);
      setAssessment(result);
      setAssessmentState("idle");
    } catch (reason) {
      setAssessmentError(reason instanceof Error ? reason.message : "Unknown assessment error");
      setAssessmentState("error");
    }
  };

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Research digital twin · Berlin</p>
          <h1>Berlin Urban Intelligence</h1>
        </div>
        <div className="snapshot-meta">
          <span>Platform {system?.version ?? "—"}</span>
          <span>Runtime {system?.runtime_generated_at ?? "unavailable"}</span>
          <span>Reference {system?.reference_generated_at ?? "unavailable"}</span>
          <span>Synthetic production fallback: {system?.synthetic_production_fallback ? "yes" : "no"}</span>
        </div>
      </header>

      {loadState === "error" && (
        <section className="notice error" role="alert">
          API state unavailable: {error}. No synthetic replacement values are shown.
        </section>
      )}

      <section className="status-grid" aria-label="Agent status">
        {Object.entries(health).map(([name, item]) => (
          <article className="status-card" key={name}>
            <div className="status-card-title">
              <strong>{name.replaceAll("_", " ")}</strong>
              <StatusBadge health={item} />
            </div>
            <p>{item.detail ?? "No detail supplied."}</p>
            <small>
              Freshness: {item.freshness} · Quality: {item.quality}
            </small>
          </article>
        ))}
        {Object.keys(health).length === 0 && (
          <article className="status-card">
            <strong>Agent state unavailable</strong>
            <p>No health response has been loaded.</p>
          </article>
        )}
      </section>

      <section className="workspace">
        <div className="map-panel">
          <div ref={mapContainer} className="map" aria-label="Berlin domain map" />
          <div className="legend">
            <strong>Reference layers</strong>
            <p>These layers are persisted reference data, not simulated changes.</p>
            {mapLayerCounts({
              facilities: facilities.length,
              stops: stops.length,
              climate: climate.length,
            }).map(([label, count]) => {
              const key: keyof typeof visibleLayers = label === "Critical facilities"
                ? "facilities"
                : label === "VBB stops"
                  ? "stops"
                  : "climate";
              return (
                <label className="layer-toggle" key={key}>
                  <input
                    checked={visibleLayers[key]}
                    onChange={(event) =>
                      setVisibleLayers((current) => ({ ...current, [key]: event.target.checked }))
                    }
                    type="checkbox"
                  />
                  <span className={`layer-swatch ${key}`} />
                  <span>{label} · {count}</span>
                </label>
              );
            })}
            {mapLayerCounts({ facilities: facilities.length, stops: stops.length, climate: climate.length }).length === 0 && (
              <span>No mappable reference data loaded.</span>
            )}
          </div>
        </div>

        <aside className="sidebar">
          <MapEntityInspector selection={mapSelection} onClear={() => setMapSelection(null)} />

          <section>
            <h2>Mobility</h2>
            <StatusBadge health={mobility?.health} />
            <dl>
              <dt>Realtime trip updates</dt>
              <dd>{displayValue(mobility?.snapshot?.trip_updates)}</dd>
              <dt>Delayed updates</dt>
              <dd>{displayValue(mobility?.snapshot?.delayed_trip_updates)}</dd>
              <dt>Observed</dt>
              <dd>{displayValue(mobility?.snapshot?.observed_at)}</dd>
            </dl>
            <p className="method-note">
              Missing realtime updates are not interpreted as normal operation.
            </p>
          </section>

          <section>
            <h2>Energy</h2>
            <StatusBadge health={energy?.health} />
            <dl>
              <dt>Evaluation</dt>
              <dd>{energy?.evaluation ? "Available" : "Unavailable"}</dd>
              <dt>Forecast artefacts</dt>
              <dd>{energy ? energy.forecasts.length : "Unavailable"}</dd>
            </dl>
            <p className="method-note">
              Forecasts appear only after model and dataset fingerprints match a Berlin evaluation.
            </p>
          </section>

          <section>
            <h2>Data semantics</h2>
            <p>
              Observed, official-modelled, forecast, derived and scenario values remain separate.
              This interface does not calculate a single city score.
            </p>
          </section>
        </aside>
      </section>

      <section className="research-grid" aria-label="Research controls and provenance">
        <article className="research-card observations-card">
          <div className="section-heading">
            <div>
              <p className="eyebrow">Canonical state</p>
              <h2>Latest observations</h2>
            </div>
            <span className="count-pill">{observations.length}</span>
          </div>
          {observations.length === 0 ? (
            <p className="empty-state">No persisted observations are available. No demo values are substituted.</p>
          ) : (
            <div className="observation-list">
              {observations.map((item) => (
                <button
                  className={`observation-row${item.id === selectedObservationId ? " selected" : ""}`}
                  key={item.id}
                  onClick={() => setSelectedObservationId(item.id)}
                  type="button"
                >
                  <span>
                    <strong>{item.phenomenon}</strong>
                    <small>{item.entity_id}</small>
                  </span>
                  <span>{displayValue(item.value, item.unit)}</span>
                  <span className="state-label">{item.state}</span>
                  <span className="quality-label">{item.quality}</span>
                </button>
              ))}
            </div>
          )}
        </article>

        <article className="research-card provenance-card">
          <p className="eyebrow">Audit trail</p>
          <h2>Provenance inspector</h2>
          {selectedObservation ? (
            <dl className="provenance-list">
              <dt>Observation</dt>
              <dd>{selectedObservation.id}</dd>
              <dt>Provider</dt>
              <dd>{selectedObservation.provenance.provider}</dd>
              <dt>Dataset</dt>
              <dd>{selectedObservation.provenance.dataset}</dd>
              <dt>Retrieved</dt>
              <dd>{selectedObservation.provenance.retrieved_at}</dd>
              <dt>Processed</dt>
              <dd>{selectedObservation.provenance.processed_at}</dd>
              <dt>Agent</dt>
              <dd>
                {selectedObservation.provenance.agent} · {selectedObservation.provenance.agent_version}
              </dd>
              <dt>Method</dt>
              <dd>{selectedObservation.provenance.processing_method}</dd>
              <dt>Licence</dt>
              <dd>{displayValue(selectedObservation.provenance.source_licence)}</dd>
              <dt>Quality note</dt>
              <dd>{displayValue(selectedObservation.provenance.quality_note)}</dd>
            </dl>
          ) : (
            <p className="empty-state">Select a real observation to inspect its provenance.</p>
          )}
        </article>

        <article className="research-card">
          <p className="eyebrow">Deterministic orchestration</p>
          <h2>Workflow planner</h2>
          <label className="field">
            <span>Workflow</span>
            <select value={workflow} onChange={(event) => setWorkflow(event.target.value as WorkflowKind)}>
              {WORKFLOWS.map((item) => (
                <option value={item.value} key={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <button className="primary-action" onClick={runWorkflow} disabled={workflowState === "running"} type="button">
            {workflowState === "running" ? "Running…" : "Run deterministic workflow"}
          </button>
          {workflowError && <p className="inline-error">{workflowError}</p>}
          {workflowResult && (
            <div className="result-box">
              <strong>{workflowResult.execution.status}</strong>
              <span>Agents: {workflowResult.plan.agents.join(", ")}</span>
              <span>LLM required: {workflowResult.plan.requires_llm ? "yes" : "no"}</span>
              <span>
                Missing: {workflowResult.execution.missing_agents.length > 0 ? workflowResult.execution.missing_agents.join(", ") : "none"}
              </span>
            </div>
          )}
        </article>

        <article className="research-card scenario-card">
          <p className="eyebrow">Spatial hypothetical scenario</p>
          <h2>Network disruption route</h2>
          <p className="method-note">
            Select origin and destination directly on the map. The white line is the baseline route;
            choose one displayed route segment to close, then compare it with the red disruption route.
          </p>
          <div className="route-selection-actions">
            <button
              className={`secondary-action${routeSelectionMode === "origin" ? " active" : ""}`}
              onClick={() => startRouteSelection("origin")}
              type="button"
            >
              {routeOrigin ? "Origin selected" : "Select origin on map"}
            </button>
            <button
              className={`secondary-action${routeSelectionMode === "destination" ? " active" : ""}`}
              onClick={() => startRouteSelection("destination")}
              type="button"
            >
              {routeDestination ? "Destination selected" : "Select destination on map"}
            </button>
          </div>
          {routeSelectionMode && <p className="method-note">Now click the map to set the {routeSelectionMode}.</p>}
          <button className="primary-action" onClick={runRouteBaseline} disabled={routeState === "running"} type="button">
            {routeState === "running" ? "Loading route…" : "Show baseline route"}
          </button>
          {routeBaseline && (
            <label className="field">
              <span>Disrupted route segment</span>
              <select value={closedEdge} onChange={(event) => setClosedEdge(event.target.value)}>
                {routeBaseline.edge_ids.map((edgeId, index) => (
                  <option key={edgeId} value={edgeId}>Route segment {index + 1}</option>
                ))}
              </select>
            </label>
          )}
          <button
            className="primary-action"
            onClick={runRouteComparison}
            disabled={routeState === "running" || !routeBaseline || !closedEdge}
            type="button"
          >
            {routeState === "running" ? "Comparing…" : "Simulate selected disruption"}
          </button>
          {routeError && <p className="inline-error">{routeError}</p>}
          {routeComparison && (
            <div className="result-box">
              <strong>{routeComparison.scenario_name}</strong>
              <span>Baseline: {Math.round(routeComparison.baseline_travel_time_s)} s</span>
              <span>Scenario: {Math.round(routeComparison.scenario_travel_time_s)} s</span>
              <span>Change: {Math.round(routeComparison.absolute_delta_s)} s ({routeComparison.relative_delta_pct.toFixed(1)}%)</span>
            </div>
          )}
        </article>

        <article className="research-card scenario-card">
          <p className="eyebrow">Hypothetical scenario</p>
          <h2>Heat assessment</h2>
          <p className="method-note">
            This control never changes the observed baseline. The result is a counterfactual derived from an explicit delta.
          </p>
          <label className="field">
            <span>Temperature delta (Cel)</span>
            <input
              inputMode="decimal"
              placeholder="Enter delta, e.g. 3"
              value={temperatureDelta}
              onChange={(event) => setTemperatureDelta(event.target.value)}
            />
          </label>
          <button className="primary-action" onClick={runHeatAssessment} disabled={assessmentState === "running"} type="button">
            {assessmentState === "running" ? "Assessing…" : "Assess hypothetical scenario"}
          </button>
          {assessmentError && <p className="inline-error">{assessmentError}</p>}
          {assessment && (
            <div className="result-box">
              <strong>{assessment.scenario_name}</strong>
              <span>Hypothetical: yes</span>
              <span>Composite score: none by design</span>
              <span>
                Unavailable dimensions: {assessment.unavailable_dimensions.length > 0 ? assessment.unavailable_dimensions.join(", ") : "none"}
              </span>
              {Object.entries(assessment.dimension_errors).map(([dimension, detail]) => (
                <span key={dimension}>
                  {dimension}: {detail}
                </span>
              ))}
            </div>
          )}
        </article>
      </section>
    </main>
  );
}

export default App;
