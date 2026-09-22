import { useEffect, useState } from "react";
import {
  type MapSearchResult,
  type NetworkNodePick,
  type RouteResponse,
  fetchJson,
  mapSearchPath,
} from "./api";

export type RouteEndpointKind = "origin" | "destination";

type Props = {
  origin: NetworkNodePick | null;
  originLabel: string;
  destination: NetworkNodePick | null;
  destinationLabel: string;
  route: RouteResponse | null;
  routeState: "idle" | "running" | "error";
  routeError: string | null;
  selectionMode: RouteEndpointKind | null;
  onResolve: (kind: RouteEndpointKind, node: NetworkNodePick, label: string) => void;
  onPickOnMap: (kind: RouteEndpointKind) => void;
  onSwap: () => void;
  onClear: () => void;
};

function minutes(seconds: number): string {
  if (seconds < 60) return "<1 min";
  return `${Math.max(1, Math.round(seconds / 60))} min`;
}

function distance(lengthM: number): string {
  if (lengthM < 1000) return `${Math.round(lengthM)} m`;
  return `${(lengthM / 1000).toFixed(lengthM >= 10_000 ? 0 : 1)} km`;
}

export default function MapRoutePlanner({
  origin,
  originLabel,
  destination,
  destinationLabel,
  route,
  routeState,
  routeError,
  selectionMode,
  onResolve,
  onPickOnMap,
  onSwap,
  onClear,
}: Props) {
  const [originQuery, setOriginQuery] = useState(originLabel);
  const [destinationQuery, setDestinationQuery] = useState(destinationLabel);
  const [activeField, setActiveField] = useState<RouteEndpointKind | null>(null);
  const [results, setResults] = useState<MapSearchResult[]>([]);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [resolving, setResolving] = useState(false);

  useEffect(() => setOriginQuery(originLabel), [originLabel]);
  useEffect(() => setDestinationQuery(destinationLabel), [destinationLabel]);

  useEffect(() => {
    const query = activeField === "origin" ? originQuery : destinationQuery;
    if (activeField === null || query.trim().length < 2) {
      setResults([]);
      setSearchError(null);
      return;
    }

    let cancelled = false;
    const timer = window.setTimeout(() => {
      void fetchJson<MapSearchResult[]>(mapSearchPath(query, 8))
        .then((items) => {
          if (cancelled) return;
          setResults(items);
          setSearchError(null);
        })
        .catch((reason: unknown) => {
          if (cancelled) return;
          setResults([]);
          setSearchError(reason instanceof Error ? reason.message : "Search unavailable.");
        });
    }, 180);

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [activeField, originQuery, destinationQuery]);

  const choose = async (item: MapSearchResult) => {
    if (activeField === null) return;
    const kind = activeField;
    setResolving(true);
    setSearchError(null);
    try {
      const params = new URLSearchParams({
        longitude: String(item.longitude),
        latitude: String(item.latitude),
      });
      const node = await fetchJson<NetworkNodePick>(`/api/v1/network/nearest?${params.toString()}`);
      onResolve(kind, node, item.name);
      if (kind === "origin") setOriginQuery(item.name);
      else setDestinationQuery(item.name);
      setResults([]);
      setActiveField(null);
    } catch (reason) {
      setSearchError(reason instanceof Error ? reason.message : "Could not resolve road network.");
    } finally {
      setResolving(false);
    }
  };

  const effectiveTime = route?.effective_travel_time_s ?? null;
  const effectiveLength = route?.effective_length_m ?? null;

  return (
    <section className="map-route-planner" aria-label="Route planner">
      <div className="route-planner-brand">
        <h1>Berlin Urban Intelligence</h1>
        <span>Live road disruptions · source-backed routing</span>
      </div>

      <div className="route-search-stack">
        <label className="route-search-field">
          <span className="route-dot route-dot-origin" aria-hidden="true" />
          <input
            aria-label="Origin search"
            autoComplete="off"
            placeholder="Choose starting point"
            value={originQuery}
            onChange={(event) => {
              setOriginQuery(event.target.value);
              setActiveField("origin");
            }}
            onFocus={() => setActiveField("origin")}
          />
          <button
            aria-label="Select origin on map"
            className={selectionMode === "origin" ? "map-pick active" : "map-pick"}
            onClick={() => onPickOnMap("origin")}
            type="button"
          >
            ⦿
          </button>
        </label>

        <div className="route-planner-connector" aria-hidden="true" />

        <label className="route-search-field">
          <span className="route-dot route-dot-destination" aria-hidden="true" />
          <input
            aria-label="Destination search"
            autoComplete="off"
            placeholder="Choose destination"
            value={destinationQuery}
            onChange={(event) => {
              setDestinationQuery(event.target.value);
              setActiveField("destination");
            }}
            onFocus={() => setActiveField("destination")}
          />
          <button
            aria-label="Select destination on map"
            className={selectionMode === "destination" ? "map-pick active" : "map-pick"}
            onClick={() => onPickOnMap("destination")}
            type="button"
          >
            ⦿
          </button>
        </label>
      </div>

      {activeField !== null && results.length > 0 && (
        <div className="route-search-results" role="listbox" aria-label="Place suggestions">
          {results.map((item) => (
            <button
              key={item.id}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => void choose(item)}
              role="option"
              type="button"
            >
              <span className="search-result-icon" aria-hidden="true">
                {item.layer === "stops" ? "T" : "●"}
              </span>
              <span>
                <strong>{item.name}</strong>
                <small>{item.subtitle}</small>
              </span>
            </button>
          ))}
        </div>
      )}

      {activeField !== null &&
        !resolving &&
        !searchError &&
        (activeField === "origin" ? originQuery : destinationQuery).trim().length >= 2 &&
        results.length === 0 && <p className="route-search-empty">No matching persisted place.</p>}

      {searchError && <p className="route-search-error">{searchError}</p>}

      <div className="route-planner-actions">
        <button
          disabled={!origin && !destination}
          onClick={onSwap}
          type="button"
        >
          Swap
        </button>
        <button
          disabled={!origin && !destination && !originQuery && !destinationQuery}
          onClick={onClear}
          type="button"
        >
          Clear
        </button>
      </div>

      {selectionMode && (
        <p className="route-map-prompt" role="status">
          Click the map to set the {selectionMode === "origin" ? "starting point" : "destination"}.
        </p>
      )}

      {routeState === "running" && (
        <div className="route-summary loading" role="status">
          Calculating route…
        </div>
      )}

      {route && routeState !== "running" && (
        <div className={`route-summary route-state-${route.route_state}`} aria-live="polite">
          <div>
            <strong>
              {route.route_state === "blocked"
                ? "Route blocked"
                : effectiveTime !== null
                  ? minutes(effectiveTime)
                  : "Unavailable"}
            </strong>
            <span className="route-state-label">{route.route_state}</span>
          </div>
          {route.route_state !== "blocked" && effectiveLength !== null && (
            <span>{distance(effectiveLength)}</span>
          )}
          {route.route_state === "rerouted" && route.travel_time_delta_s !== null && (
            <small>
              Rerouted around an official VIZ full closure · +
              {minutes(Math.max(0, route.travel_time_delta_s))}
            </small>
          )}
          {route.route_state === "disrupted" && (
            <small>
              Official disruption intersects the route; no unsupported speed penalty is inferred.
            </small>
          )}
          {route.route_state === "baseline" && route.disruption_data_available && (
            <small>
              No active VIZ disruption currently changes this route.
            </small>
          )}
          {!route.disruption_data_available && (
            <small>Road-disruption state unavailable; showing persisted baseline routing only.</small>
          )}
        </div>
      )}

      {routeError && (
        <p className="route-search-error" role="alert">
          {routeError}
        </p>
      )}
    </section>
  );
}
