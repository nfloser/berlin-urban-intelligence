import type { FeatureCollection } from "geojson";
import type { GeoJSONSource, Map as MapLibreMap } from "maplibre-gl";
import * as maplibregl from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import {
  CriticalFacility,
  EnergyResponse,
  Health,
  MobilityResponse,
  OfficialModelFeature,
  SystemResponse,
  UrbanEntity,
  displayValue,
  fetchJson,
  toFeatureCollection,
} from "./api";

const BASE_STYLE = "https://tiles.openfreemap.org/styles/liberty";

type LoadState = "loading" | "ready" | "error";

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
        ]) => {
          if (cancelled) return;
          setSystem(systemValue);
          setHealth(healthValue);
          setMobility(mobilityValue);
          setEnergy(energyValue);
          setFacilities(facilityValue);
          setStops(stopValue);
          setClimate(climateValue);
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
      attributionControl: true,
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
          paint: { "fill-opacity": 0.18 },
        });
      }
      if (!map.getLayer("stops-circle")) {
        map.addLayer({
          id: "stops-circle",
          type: "circle",
          source: "stops",
          paint: { "circle-radius": 2.5, "circle-opacity": 0.55 },
        });
      }
      if (!map.getLayer("facilities-circle")) {
        map.addLayer({
          id: "facilities-circle",
          type: "circle",
          source: "facilities",
          paint: { "circle-radius": 5, "circle-stroke-width": 1.5 },
        });
      }
    };

    if (map.isStyleLoaded()) installLayers();
    else map.once("load", installLayers);
  }, [loadState, facilities, stops, climate]);

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
            <strong>Layers</strong>
            <span>Critical facilities · {facilities.length}</span>
            <span>VBB stops · {stops.length}</span>
            <span>Official climate features · {climate.length}</span>
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
    </main>
  );
}

export default App;
