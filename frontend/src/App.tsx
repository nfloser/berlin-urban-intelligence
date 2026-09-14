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
  type Observation,
  type OfficialModelFeature,
  type OrchestrationResponse,
  type SystemResponse,
  type UrbanEntity,
  type WorkflowKind,
  displayValue,
  fetchJson,
  heatAssessmentRequest,
  mapLayerCounts,
  postJson,
  toFeatureCollection,
} from "./api";

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
      setVisibility("facilities-circle", visibleLayers.facilities);
      setVisibility("stops-circle", visibleLayers.stops);
      setVisibility("climate-fill", visibleLayers.climate);
    };

    if (map.isStyleLoaded()) installLayers();
    else map.once("load", installLayers);
  }, [loadState, facilities, stops, climate, visibleLayers]);

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
