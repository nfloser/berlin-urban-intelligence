import { useState } from "react";
import {
  type NetworkNodePick,
  type RouteComparisonResponse,
  type RouteResponse,
  fetchJson,
  networkDisruptionRequest,
  postJson,
  routeRequest,
} from "./api";

type EndpointKind = "origin" | "destination";
type ActionState = "idle" | "running" | "error";

function parseCoordinate(value: string, kind: "longitude" | "latitude"): number {
  const parsed = Number(value);
  const limit = kind === "longitude" ? 180 : 90;
  if (value.trim() === "" || !Number.isFinite(parsed) || parsed < -limit || parsed > limit) {
    throw new Error(`Enter a valid ${kind} between ${-limit} and ${limit}.`);
  }
  return parsed;
}

function nearestNodePath(longitude: number, latitude: number): string {
  const query = new URLSearchParams({
    longitude: String(longitude),
    latitude: String(latitude),
  });
  return `/api/v1/network/nearest?${query.toString()}`;
}

export default function AccessibleRoutingPanel() {
  const [originLongitude, setOriginLongitude] = useState("");
  const [originLatitude, setOriginLatitude] = useState("");
  const [destinationLongitude, setDestinationLongitude] = useState("");
  const [destinationLatitude, setDestinationLatitude] = useState("");
  const [origin, setOrigin] = useState<NetworkNodePick | null>(null);
  const [destination, setDestination] = useState<NetworkNodePick | null>(null);
  const [baseline, setBaseline] = useState<RouteResponse | null>(null);
  const [comparison, setComparison] = useState<RouteComparisonResponse | null>(null);
  const [closedEdge, setClosedEdge] = useState("");
  const [state, setState] = useState<ActionState>("idle");
  const [error, setError] = useState<string | null>(null);

  const resetRoute = () => {
    setBaseline(null);
    setComparison(null);
    setClosedEdge("");
  };

  const resolveEndpoint = async (kind: EndpointKind) => {
    setState("running");
    setError(null);
    try {
      const longitude = parseCoordinate(
        kind === "origin" ? originLongitude : destinationLongitude,
        "longitude",
      );
      const latitude = parseCoordinate(
        kind === "origin" ? originLatitude : destinationLatitude,
        "latitude",
      );
      const node = await fetchJson<NetworkNodePick>(nearestNodePath(longitude, latitude));
      if (kind === "origin") setOrigin(node);
      else setDestination(node);
      resetRoute();
      setState("idle");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not resolve network coordinates.");
      setState("error");
    }
  };

  const showBaseline = async () => {
    setError(null);
    setComparison(null);
    if (!origin || !destination) {
      setError("Resolve both origin and destination coordinates first.");
      setState("error");
      return;
    }
    setState("running");
    try {
      const result = await postJson<RouteResponse>(
        "/api/v1/resilience/routes",
        routeRequest(origin.node_id, destination.node_id),
      );
      setBaseline(result);
      setClosedEdge(result.edge_ids[0] ?? "");
      setState("idle");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Baseline route failed.");
      setState("error");
    }
  };

  const compareDisruption = async () => {
    setError(null);
    if (!origin || !destination || !closedEdge) {
      setError("Resolve both endpoints and select a route segment first.");
      setState("error");
      return;
    }
    setState("running");
    try {
      const result = await postJson<RouteComparisonResponse>(
        "/api/v1/resilience/routes/compare",
        networkDisruptionRequest(origin.node_id, destination.node_id, closedEdge),
      );
      setComparison(result);
      setState("idle");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Route comparison failed.");
      setState("error");
    }
  };

  return (
    <section className="research-grid accessibility-extension" aria-label="Keyboard routing alternative">
      <fieldset className="research-card keyboard-routing-card">
        <legend>Keyboard routing coordinates</legend>
        <p className="method-note">
          The interactive map is optional for routing. Enter coordinates here to resolve the nearest
          persisted network nodes and run the same baseline and disruption analysis without a pointer.
        </p>

        <div className="keyboard-coordinate-grid">
          <label className="field">
            <span>Origin longitude</span>
            <input
              inputMode="decimal"
              value={originLongitude}
              onChange={(event) => setOriginLongitude(event.target.value)}
            />
          </label>
          <label className="field">
            <span>Origin latitude</span>
            <input
              inputMode="decimal"
              value={originLatitude}
              onChange={(event) => setOriginLatitude(event.target.value)}
            />
          </label>
          <button
            className="secondary-action"
            disabled={state === "running"}
            onClick={() => void resolveEndpoint("origin")}
            type="button"
          >
            Resolve origin coordinates
          </button>
          <span className="keyboard-node-status" aria-live="polite">
            {origin ? `Origin node: ${origin.node_id}` : "Origin node: unresolved"}
          </span>

          <label className="field">
            <span>Destination longitude</span>
            <input
              inputMode="decimal"
              value={destinationLongitude}
              onChange={(event) => setDestinationLongitude(event.target.value)}
            />
          </label>
          <label className="field">
            <span>Destination latitude</span>
            <input
              inputMode="decimal"
              value={destinationLatitude}
              onChange={(event) => setDestinationLatitude(event.target.value)}
            />
          </label>
          <button
            className="secondary-action"
            disabled={state === "running"}
            onClick={() => void resolveEndpoint("destination")}
            type="button"
          >
            Resolve destination coordinates
          </button>
          <span className="keyboard-node-status" aria-live="polite">
            {destination ? `Destination node: ${destination.node_id}` : "Destination node: unresolved"}
          </span>
        </div>

        <button
          className="primary-action"
          disabled={state === "running" || !origin || !destination}
          onClick={() => void showBaseline()}
          type="button"
        >
          {state === "running" ? "Working…" : "Show keyboard baseline route"}
        </button>

        {baseline && (
          <label className="field">
            <span>Keyboard disrupted route segment</span>
            <select value={closedEdge} onChange={(event) => setClosedEdge(event.target.value)}>
              {baseline.edge_ids.map((edgeId, index) => (
                <option key={edgeId} value={edgeId}>
                  Route segment {index + 1}
                </option>
              ))}
            </select>
          </label>
        )}

        <button
          className="primary-action"
          disabled={state === "running" || !baseline || !closedEdge}
          onClick={() => void compareDisruption()}
          type="button"
        >
          Simulate keyboard-selected disruption
        </button>

        {error && (
          <p className="inline-error" role="alert">
            {error}
          </p>
        )}
        {baseline && (
          <div className="result-box" aria-live="polite">
            <strong>Keyboard baseline route</strong>
            <span>Travel time: {Math.round(baseline.travel_time_s)} s</span>
            <span>Nodes: {baseline.node_path.join(" → ")}</span>
          </div>
        )}
        {comparison && (
          <div className="result-box" aria-live="polite">
            <strong>{comparison.scenario_name}</strong>
            <span>Baseline: {Math.round(comparison.baseline_travel_time_s)} s</span>
            <span>Scenario: {Math.round(comparison.scenario_travel_time_s)} s</span>
            <span>
              Change: {Math.round(comparison.absolute_delta_s)} s (
              {comparison.relative_delta_pct.toFixed(1)}%)
            </span>
          </div>
        )}
      </fieldset>
    </section>
  );
}
