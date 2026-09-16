import { useEffect, useMemo, useState } from "react";
import {
  type DependencyResponse,
  type DerivedStateResponse,
  type DerivationRecord,
  type Provenance,
  displayValue,
  fetchJson,
} from "./api";

type InspectorState = "loading" | "ready" | "error";

function encodedResource(id: string): string {
  return id
    .split("/")
    .map((part) => encodeURIComponent(part))
    .join("/");
}

export default function DerivedInspector() {
  const [state, setState] = useState<InspectorState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [derived, setDerived] = useState<DerivedStateResponse | null>(null);
  const [selectedId, setSelectedId] = useState("");
  const [dependencies, setDependencies] = useState<DependencyResponse | null>(null);
  const [provenance, setProvenance] = useState<Provenance | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchJson<DerivedStateResponse>("/api/v1/derived")
      .then((value) => {
        if (cancelled) return;
        setDerived(value);
        setSelectedId(value.records[0]?.id ?? "");
        setState("ready");
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : "Unknown derived-state error");
        setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setDependencies(null);
      setProvenance(null);
      setDetailError(null);
      return;
    }
    let cancelled = false;
    const resource = encodedResource(selectedId);
    Promise.all([
      fetchJson<DependencyResponse>(`/api/v1/dependencies/${resource}`),
      fetchJson<Provenance>(`/api/v1/provenance/${resource}`),
    ])
      .then(([dependencyValue, provenanceValue]) => {
        if (cancelled) return;
        setDependencies(dependencyValue);
        setProvenance(provenanceValue);
        setDetailError(null);
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setDependencies(null);
        setProvenance(null);
        setDetailError(reason instanceof Error ? reason.message : "Unknown lineage error");
      });
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const selected = useMemo<DerivationRecord | null>(
    () => derived?.records.find((record) => record.id === selectedId) ?? null,
    [derived, selectedId],
  );
  const definition = useMemo(
    () => derived?.definitions.find((item) => item.id === selected?.definition_id) ?? null,
    [derived, selected],
  );

  return (
    <section className="research-grid derived-extension" aria-label="Derived information inspector">
      <article className="research-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Derived information</p>
            <h2>Persisted products</h2>
          </div>
          <span className="count-pill">{derived?.records.length ?? 0}</span>
        </div>
        {state === "loading" && <p className="empty-state">Loading derived state…</p>}
        {state === "error" && <p className="inline-error">{error}</p>}
        {state === "ready" && derived?.records.length === 0 && (
          <p className="empty-state">
            No persisted derived products are available. The dashboard does not invent substitute
            results when a derivation has not been produced.
          </p>
        )}
        {derived && derived.records.length > 0 && (
          <>
            <label className="field">
              <span>Derived product</span>
              <select value={selectedId} onChange={(event) => setSelectedId(event.target.value)}>
                {derived.records.map((record) => (
                  <option key={record.id} value={record.id}>
                    {record.phenomenon} · {record.entity_id}
                  </option>
                ))}
              </select>
            </label>
            {selected && (
              <div className="result-box">
                <strong>{displayValue(selected.value, selected.unit)}</strong>
                <span>Status: {selected.status}</span>
                <span>Freshness: {selected.freshness}</span>
                <span>Quality: {selected.quality}</span>
                <span>Context: {selected.context}</span>
                <span>Valid at: {selected.valid_at}</span>
                <span>Computed at: {selected.computed_at}</span>
              </div>
            )}
          </>
        )}
      </article>

      <article className="research-card provenance-card">
        <p className="eyebrow">Explainability</p>
        <h2>Definition, lineage & provenance</h2>
        {!selected && <p className="empty-state">Select a derived product to inspect its lineage.</p>}
        {detailError && <p className="inline-error">{detailError}</p>}
        {selected && definition && (
          <dl className="provenance-list">
            <dt>Definition</dt>
            <dd>{definition.name}</dd>
            <dt>Scientific interpretation</dt>
            <dd>{definition.description}</dd>
            <dt>Producer</dt>
            <dd>{definition.producer_agent_id} {definition.producer_version}</dd>
            <dt>Algorithm</dt>
            <dd>{definition.algorithm_version}</dd>
            <dt>Inputs</dt>
            <dd>{selected.inputs.map((item) => `${item.role}: ${item.id}`).join(", ")}</dd>
            <dt>Upstream</dt>
            <dd>{dependencies?.upstream.join(" → ") || "none"}</dd>
            <dt>Downstream</dt>
            <dd>{dependencies?.downstream.join(" → ") || "none"}</dd>
            <dt>Provider</dt>
            <dd>{provenance?.provider ?? selected.provenance.provider}</dd>
            <dt>Dataset</dt>
            <dd>{provenance?.dataset ?? selected.provenance.dataset}</dd>
            <dt>Agent</dt>
            <dd>{provenance?.agent ?? selected.provenance.agent}</dd>
            <dt>Source</dt>
            <dd>{provenance?.source_url ?? selected.provenance.source_url}</dd>
          </dl>
        )}
      </article>
    </section>
  );
}
