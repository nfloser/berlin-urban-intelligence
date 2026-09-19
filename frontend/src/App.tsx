import type { FeatureCollection } from "geojson";
import type {
  GeoJSONSource,
  Map as MapLibreMap,
  StyleSpecification,
} from "maplibre-gl";
import * as maplibregl from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import {
  type AssessmentResponse,
  type CriticalFacility,
  type CriticalRouteSnapshotResponse,
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
  networkDisruptionRequest,
  postJson,
  routeRequest,
  toFeatureCollection,
} from "./api";
import MapEntityInspector, { type MapSelection } from "./MapEntityInspector";
import {
  ReferenceMapRequestTracker,
  buildReferenceDetailPath,
  buildReferenceMapPath,
  featureCollectionForLayer,
  referenceHitTestBox,
  referenceLayerSummaries,
  referencePointHit,
  type ReferenceMapLayer,
  type ReferenceMapResponse,
} from "./mapReference";

const BASE_STYLE = "https://tiles.openfreemap.org/styles/liberty";
const FALLBACK_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [
    {
      id: "fallback-background",
      type: "background",
      paint: { "background-color": "#111821" },
    },
  ],
};
const WORKFLOWS: Array<{ value: WorkflowKind; label: string }> = [
  { value: "urban_snapshot", label: "Urban snapshot" },
  { value: "heat_energy", label: "Heat + energy" },
  { value: "mobility_exposure", label: "Mobility + exposure" },
  { value: "mobility_resilience", label: "Mobility + resilience" },
  { value: "heat_mobility_resilience", label: "Heat + mobility + resilience" },
];
const REFERENCE_LAYERS: ReferenceMapLayer[] = ["facilities", "stops", "climate"];
const EMPTY_FEATURE_COLLECTION: FeatureCollection = { type: "FeatureCollection", features: [] };
const CRITICAL_ROUTE_POLL_INTERVAL_MS = 15_000;

type LoadState = "loading" | "ready" | "error";
type ActionState = "idle" | "running" | "error";

function StatusBadge({ health }: { health?: Health }) {
  const status = health?.status ?? "unknown";
  return <span className={`status status-${status}`}>{status}</span>;
}

function App() {
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const mapRequestTracker = useRef(new ReferenceMapRequestTracker());
  const detailRequestTracker = useRef(new ReferenceMapRequestTracker());
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [system, setSystem] = useState<SystemResponse | null>(null);
  const [health, setHealth] = useState<Record<string, Health>>({});
  const [mobility, setMobility] = useState<MobilityResponse | null>(null);
  const [energy, setEnergy] = useState<EnergyResponse | null>(null);
  const [referenceMap, setReferenceMap] = useState<ReferenceMapResponse | null>(null);
  const [mapDataError, setMapDataError] = useState<string | null>(null);
  const [mapSelection, setMapSelection] = useState<MapSelection | null>(null);
  const [mapSelectionError, setMapSelectionError] = useState<string | null>(null);
  const [mapLayersReady, setMapLayersReady] = useState(false);
  const [criticalRouteLayerReady, setCriticalRouteLayerReady] = useState(false);
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
  const [criticalRoutes, setCriticalRoutes] = useState<CriticalRouteSnapshotResponse | null>(null);
  const [criticalRoutesError, setCriticalRoutesError] = useState<string | null>(null);
  const [criticalRoutesVisible, setCriticalRoutesVisible] = useState(true);
  const [selectedCriticalRouteId, setSelectedCriticalRouteId] = useState<string | null>(null);

  const selectedCriticalRoute =
    criticalRoutes?.routes.find((item) => item.id === selectedCriticalRouteId) ?? null;
  const selectedObservation =
    observations.find((item) => item.id === selectedObservationId) ?? null;
  const layerSummaries = referenceMap ? referenceLayerSummaries(referenceMap.metadata) : [];
  const referenceMapTruncated = layerSummaries.some((layer) => layer.truncated);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchJson<SystemResponse>("/api/v1/system"),
      fetchJson<Record<string, Health>>("/api/v1/agents/health"),
      fetchJson<MobilityResponse>("/api/v1/mobility"),
      fetchJson<EnergyResponse>("/api/v1/energy"),
      fetchJson<Observation[]>("/api/v1/observations?limit=250"),
    ])
      .then(([systemValue, healthValue, mobilityValue, energyValue, observationValue]) => {
        if (cancelled) return;
        setSystem(systemValue);
        setHealth(healthValue);
        setMobility(mobilityValue);
        setEnergy(energyValue);
        setObservations(observationValue);
        setSelectedObservationId(observationValue[0]?.id ?? null);
        setLoadState("ready");
      })
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
    let cancelled = false;

    const loadCriticalRoutes = async () => {
      try {
        const result = await fetchJson<CriticalRouteSnapshotResponse>(
          "/api/v1/resilience/critical-routes?limit=250",
        );
        if (cancelled) return;
        setCriticalRoutes(result);
        setCriticalRoutesError(null);
        setSelectedCriticalRouteId((current) => {
          if (current && result.routes.some((route) => route.id === current)) return current;
          return result.routes[0]?.id ?? null;
        });
      } catch (reason) {
        if (cancelled) return;
        setCriticalRoutesError(
          reason instanceof Error ? reason.message : "Critical route monitor unavailable.",
        );
      }
    };

    void loadCriticalRoutes();
    const interval = window.setInterval(() => {
      void loadCriticalRoutes();
    }, CRITICAL_ROUTE_POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
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

    const fallbackTimer = window.setTimeout(() => {
      if (!map.isStyleLoaded()) {
        map.setStyle(FALLBACK_STYLE);
      }
    }, 5000);
    const clearFallbackTimer = () => window.clearTimeout(fallbackTimer);
    map.once("load", clearFallbackTimer);

    return () => {
      window.clearTimeout(fallbackTimer);
      map.off("load", clearFallbackTimer);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || loadState !== "ready") return;
    let disposed = false;
    const tracker = mapRequestTracker.current;

    const clearReferenceSources = () => {
      for (const sourceId of REFERENCE_LAYERS) {
        const source = map.getSource(sourceId) as GeoJSONSource | undefined;
        source?.setData(EMPTY_FEATURE_COLLECTION);
      }
    };

    const loadViewport = async () => {
      const token = tracker.begin();
      const bounds = map.getBounds();
      setMapLayersReady(false);
      try {
        const response = await fetchJson<ReferenceMapResponse>(
          buildReferenceMapPath(
            {
              west: bounds.getWest(),
              south: bounds.getSouth(),
              east: bounds.getEast(),
              north: bounds.getNorth(),
            },
            REFERENCE_LAYERS,
          ),
        );
        if (disposed || !tracker.isCurrent(token)) return;
        setReferenceMap(response);
        setMapDataError(null);
      } catch (reason) {
        if (disposed || !tracker.isCurrent(token)) return;
        clearReferenceSources();
        setReferenceMap(null);
        setMapLayersReady(false);
        setMapDataError(
          reason instanceof Error ? reason.message : "Could not load reference map data.",
        );
      }
    };

    const onMoveEnd = () => {
      void loadViewport();
    };
    map.on("moveend", onMoveEnd);
    void loadViewport();

    return () => {
      disposed = true;
      tracker.invalidate();
      map.off("moveend", onMoveEnd);
    };
  }, [loadState]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || loadState !== "ready") return;
    setMapLayersReady(false);
    const facilityData = referenceMap
      ? featureCollectionForLayer(referenceMap, "facilities")
      : EMPTY_FEATURE_COLLECTION;
    const stopData = referenceMap
      ? featureCollectionForLayer(referenceMap, "stops")
      : EMPTY_FEATURE_COLLECTION;
    const climateData = referenceMap
      ? featureCollectionForLayer(referenceMap, "climate")
      : EMPTY_FEATURE_COLLECTION;
    const inspectionData: FeatureCollection = mapSelection
      ? toFeatureCollection([mapSelection.item])
      : EMPTY_FEATURE_COLLECTION;
    const routeData = (geometry: RouteComparisonResponse["baseline_geometry"]): FeatureCollection => ({
      type: "FeatureCollection",
      features: geometry ? [{ type: "Feature", properties: {}, geometry }] : [],
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
    const criticalRouteData: FeatureCollection = {
      type: "FeatureCollection",
      features: (criticalRoutes?.routes ?? []).map((route) => ({
        type: "Feature",
        id: route.id,
        properties: { route_id: route.id },
        geometry: route.geometry,
      })),
    };
    const selectedCriticalRouteData: FeatureCollection = {
      type: "FeatureCollection",
      features: selectedCriticalRoute
        ? [
            {
              type: "Feature",
              id: selectedCriticalRoute.id,
              properties: { route_id: selectedCriticalRoute.id },
              geometry: selectedCriticalRoute.geometry,
            },
          ]
        : [],
    };
    const criticalRouteColor = criticalRoutes?.status === "degraded" ? "#e3bd71" : "#4ea5d9";
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
      upsert("critical-routes", criticalRouteData);
      upsert("critical-route-selected", selectedCriticalRouteData);

      if (!map.getLayer("climate-fill")) {
        map.addLayer({
          id: "climate-fill",
          type: "fill",
          source: "climate",
          paint: {
            "fill-color": "#e0a458",
            "fill-outline-color": "#e0a458",
            "fill-opacity": 0.24,
          },
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
      if (!map.getLayer("critical-routes-line")) {
        map.addLayer({
          id: "critical-routes-line",
          type: "line",
          source: "critical-routes",
          paint: {
            "line-color": criticalRouteColor,
            "line-width": 5,
            "line-opacity": 0.78,
          },
        });
      } else {
        map.setPaintProperty("critical-routes-line", "line-color", criticalRouteColor);
      }
      if (!map.getLayer("critical-route-selected-line")) {
        map.addLayer({
          id: "critical-route-selected-line",
          type: "line",
          source: "critical-route-selected",
          paint: {
            "line-color": "#f0c75e",
            "line-width": 8,
            "line-opacity": 0.96,
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
      setVisibility("critical-routes-line", criticalRoutesVisible);
      setVisibility("critical-route-selected-line", criticalRoutesVisible);
      setCriticalRouteLayerReady(map.getLayer("critical-routes-line") !== undefined);
      setMapLayersReady(referenceMap !== null);
    };

    const maybeInstallLayers = () => {
      if (!map.isStyleLoaded()) return;
      installLayers();
      map.off("styledata", maybeInstallLayers);
      map.off("load", maybeInstallLayers);
    };

    if (map.getSource("facilities")) {
      installLayers();
      return;
    }

    maybeInstallLayers();
    if (!map.isStyleLoaded()) {
      map.on("styledata", maybeInstallLayers);
      map.on("load", maybeInstallLayers);
    }
    return () => {
      map.off("styledata", maybeInstallLayers);
      map.off("load", maybeInstallLayers);
    };
  }, [
    loadState,
    referenceMap,
    mapSelection,
    visibleLayers,
    routeComparison,
    routeBaseline,
    routeOrigin,
    routeDestination,
    criticalRoutes,
    selectedCriticalRoute,
    criticalRoutesVisible,
  ]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || loadState !== "ready" || routeSelectionMode !== null) return;

    const inspectCriticalRoute = (event: maplibregl.MapMouseEvent) => {
      if (!criticalRoutesVisible || !map.getLayer("critical-routes-line")) return;
      const hitBox = referenceHitTestBox(event.point);
      const hit = map.queryRenderedFeatures(hitBox, { layers: ["critical-routes-line"] })[0];
      const routeId = hit?.properties?.route_id;
      if (routeId !== null && routeId !== undefined) {
        setSelectedCriticalRouteId(String(routeId));
      }
    };

    map.on("click", inspectCriticalRoute);
    return () => {
      map.off("click", inspectCriticalRoute);
    };
  }, [criticalRoutesVisible, loadState, routeSelectionMode]);

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
    const tracker = detailRequestTracker.current;
    const visiblePointLayers: Array<"facilities" | "stops"> = [];
    if (visibleLayers.facilities) visiblePointLayers.push("facilities");
    if (visibleLayers.stops) visiblePointLayers.push("stops");

    const inspectReferenceObject = async (event: maplibregl.MapMouseEvent) => {
      const inspectableLayers = ["facilities-circle", "stops-circle", "climate-fill"].filter(
        (layerId) => map.getLayer(layerId) !== undefined,
      );
      if (inspectableLayers.length === 0) return;
      const hitBox = referenceHitTestBox(event.point);
      const renderedHit = inspectableLayers
        .map((layerId) => map.queryRenderedFeatures(hitBox, { layers: [layerId] })[0])
        .find((feature) => feature !== undefined);

      let layer: ReferenceMapLayer | null = null;
      let id: string | null = null;
      if (renderedHit) {
        const rawId = renderedHit.properties?.id ?? renderedHit.id;
        if (rawId !== null && rawId !== undefined) {
          id = String(rawId);
          layer =
            renderedHit.layer.id === "facilities-circle"
              ? "facilities"
              : renderedHit.layer.id === "stops-circle"
                ? "stops"
                : "climate";
        }
      } else if (referenceMap) {
        const pointHit = referencePointHit(
          referenceMap,
          event.point,
          ([longitude, latitude]) => {
            const projected = map.project([longitude, latitude]);
            return { x: projected.x, y: projected.y };
          },
          8,
          visiblePointLayers,
        );
        if (pointHit) {
          layer = pointHit.layer;
          id = pointHit.id;
        }
      }

      if (!layer || !id) {
        tracker.invalidate();
        setMapSelection(null);
        setMapSelectionError(null);
        return;
      }

      const token = tracker.begin();
      setMapSelectionError(null);
      try {
        if (layer === "facilities") {
          const item = await fetchJson<CriticalFacility>(buildReferenceDetailPath(layer, id));
          if (tracker.isCurrent(token)) setMapSelection({ kind: "facility", item });
          return;
        }
        if (layer === "stops") {
          const item = await fetchJson<UrbanEntity>(buildReferenceDetailPath(layer, id));
          if (tracker.isCurrent(token)) setMapSelection({ kind: "stop", item });
          return;
        }
        const item = await fetchJson<OfficialModelFeature>(buildReferenceDetailPath(layer, id));
        if (tracker.isCurrent(token)) setMapSelection({ kind: "climate", item });
      } catch (reason) {
        if (!tracker.isCurrent(token)) return;
        setMapSelection(null);
        setMapSelectionError(
          reason instanceof Error ? reason.message : "Could not load canonical reference detail.",
        );
      }
    };

    map.on("click", inspectReferenceObject);
    return () => {
      tracker.invalidate();
      map.off("click", inspectReferenceObject);
    };
  }, [loadState, referenceMap, routeSelectionMode, visibleLayers]);

  const startRouteSelection = (mode: "origin" | "destination") => {
    detailRequestTracker.current.invalidate();
    setMapSelection(null);
    setMapSelectionError(null);
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
          <span>
            Synthetic production fallback: {system?.synthetic_production_fallback ? "yes" : "no"}
          </span>
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
          <div
            ref={mapContainer}
            className="map"
            aria-label="Berlin domain map"
            data-reference-layers-ready={mapLayersReady ? "true" : "false"}
            data-reference-map-truncated={referenceMapTruncated ? "true" : "false"}
            data-critical-routes-ready={criticalRouteLayerReady ? "true" : "false"}
            data-critical-routes-count={criticalRoutes?.returned ?? 0}
          />
          <div className="legend">
            <strong>Reference layers</strong>
            <p>Viewport projection of persisted reference data; simulated changes stay separate.</p>
            {layerSummaries.map((summary) => (
              <label className="layer-toggle" key={summary.key}>
                <input
                  checked={visibleLayers[summary.key]}
                  onChange={(event) =>
                    setVisibleLayers((current) => ({
                      ...current,
                      [summary.key]: event.target.checked,
                    }))
                  }
                  type="checkbox"
                />
                <span className={`layer-swatch ${summary.key}`} />
                <span>
                  {summary.label} · {summary.returned} visible / {summary.matched} in viewport ·{" "}
                  {summary.total} total
                  {summary.truncated ? " · truncated, zoom in" : ""}
                </span>
              </label>
            ))}
            <label className="layer-toggle">
              <input
                checked={criticalRoutesVisible}
                onChange={(event) => setCriticalRoutesVisible(event.target.checked)}
                type="checkbox"
              />
              <span className="layer-swatch critical-routes" />
              <span>
                Critical routes · {criticalRoutes?.returned ?? 0} shown /{" "}
                {criticalRoutes?.route_count_total ?? 0} monitored · refresh 15 s
              </span>
            </label>
            <p className="critical-route-traffic-note">
              Baseline road weights only · live road traffic telemetry: not integrated
            </p>
            {referenceMap === null && <span>No reference viewport has been loaded yet.</span>}
            {mapDataError && (
              <p className="inline-error">Reference map data unavailable: {mapDataError}</p>
            )}
          </div>
        </div>

        <aside className="sidebar">
          <MapEntityInspector selection={mapSelection} onClear={() => setMapSelection(null)} />
          {mapSelectionError && (
            <p className="inline-error">Reference detail unavailable: {mapSelectionError}</p>
          )}

          <section aria-label="Critical route monitor">
            <div className="section-heading compact-heading">
              <h2>Critical route monitor</h2>
              <span className={`status status-${criticalRoutes?.status ?? "unknown"}`}>
                {criticalRoutes?.status ?? "unknown"}
              </span>
            </div>
            <dl>
              <dt>Monitored routes</dt>
              <dd>{criticalRoutes?.route_count_total ?? "Unavailable"}</dd>
              <dt>Reference snapshot</dt>
              <dd>{criticalRoutes?.reference_generated_at ?? "Unavailable"}</dd>
              <dt>Road traffic telemetry</dt>
              <dd>{criticalRoutes?.traffic_data_available ? "Available" : "Not integrated"}</dd>
            </dl>
            {criticalRoutes && criticalRoutes.routes.length > 0 && (
              <label className="field">
                <span>Critical route</span>
                <select
                  aria-label="Critical route"
                  value={selectedCriticalRouteId ?? ""}
                  onChange={(event) => setSelectedCriticalRouteId(event.target.value)}
                >
                  {criticalRoutes.routes.map((route) => (
                    <option key={route.id} value={route.id}>
                      {route.origin_name} → {route.destination_name}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {selectedCriticalRoute && (
              <div className="result-box critical-route-detail" aria-live="polite">
                <strong>
                  {selectedCriticalRoute.origin_name} → {selectedCriticalRoute.destination_name}
                </strong>
                <span>
                  {selectedCriticalRoute.origin_category} → {selectedCriticalRoute.destination_category}
                </span>
                <span>Baseline travel time: {(selectedCriticalRoute.travel_time_s / 60).toFixed(1)} min</span>
                <span>Road distance: {(selectedCriticalRoute.length_m / 1000).toFixed(2)} km</span>
                <span>Edges: {selectedCriticalRoute.edge_ids.length}</span>
                <span>
                  Providers:{" "}
                  {selectedCriticalRoute.provenance.source_providers.length > 0
                    ? selectedCriticalRoute.provenance.source_providers.join(", ")
                    : "Unavailable"}
                </span>
                <span>
                  Licences:{" "}
                  {selectedCriticalRoute.provenance.source_licences.length > 0
                    ? selectedCriticalRoute.provenance.source_licences.join(", ")
                    : "Unavailable"}
                </span>
              </div>
            )}
            {criticalRoutes?.note && <p className="method-note">{criticalRoutes.note}</p>}
            {criticalRoutesError && (
              <p className="inline-error" role="alert">
                Critical routes unavailable: {criticalRoutesError}
              </p>
            )}
          </section>

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
            <p className="method-note">Missing realtime updates are not interpreted as normal operation.</p>
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
            <p className="empty-state">
              No persisted observations are available. No demo values are substituted.
            </p>
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
            <select
              value={workflow}
              onChange={(event) => setWorkflow(event.target.value as WorkflowKind)}
            >
              {WORKFLOWS.map((item) => (
                <option value={item.value} key={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <button
            className="primary-action"
            onClick={runWorkflow}
            disabled={workflowState === "running"}
            type="button"
          >
            {workflowState === "running" ? "Running…" : "Run deterministic workflow"}
          </button>
          {workflowError && <p className="inline-error">{workflowError}</p>}
          {workflowResult && (
            <div className="result-box">
              <strong>{workflowResult.execution.status}</strong>
              <span>Agents: {workflowResult.plan.agents.join(", ")}</span>
              <span>LLM required: {workflowResult.plan.requires_llm ? "yes" : "no"}</span>
              <span>
                Missing:{" "}
                {workflowResult.execution.missing_agents.length > 0
                  ? workflowResult.execution.missing_agents.join(", ")
                  : "none"}
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
          {routeSelectionMode && (
            <p className="method-note">Now click the map to set the {routeSelectionMode}.</p>
          )}
          <button
            className="primary-action"
            onClick={runRouteBaseline}
            disabled={routeState === "running"}
            type="button"
          >
            {routeState === "running" ? "Loading route…" : "Show baseline route"}
          </button>
          {routeBaseline && (
            <label className="field">
              <span>Disrupted route segment</span>
              <select value={closedEdge} onChange={(event) => setClosedEdge(event.target.value)}>
                {routeBaseline.edge_ids.map((edgeId, index) => (
                  <option key={edgeId} value={edgeId}>
                    Route segment {index + 1}
                  </option>
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
              <span>
                Change: {Math.round(routeComparison.absolute_delta_s)} s (
                {routeComparison.relative_delta_pct.toFixed(1)}%)
              </span>
            </div>
          )}
        </article>

        <article className="research-card scenario-card">
          <p className="eyebrow">Hypothetical scenario</p>
          <h2>Heat assessment</h2>
          <p className="method-note">
            This control never changes the observed baseline. The result is a counterfactual derived
            from an explicit delta.
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
          <button
            className="primary-action"
            onClick={runHeatAssessment}
            disabled={assessmentState === "running"}
            type="button"
          >
            {assessmentState === "running" ? "Assessing…" : "Assess hypothetical scenario"}
          </button>
          {assessmentError && <p className="inline-error">{assessmentError}</p>}
          {assessment && (
            <div className="result-box">
              <strong>{assessment.scenario_name}</strong>
              <span>Hypothetical: yes</span>
              <span>Composite score: none by design</span>
              <span>
                Unavailable dimensions:{" "}
                {assessment.unavailable_dimensions.length > 0
                  ? assessment.unavailable_dimensions.join(", ")
                  : "none"}
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
