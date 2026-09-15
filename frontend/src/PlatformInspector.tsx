import { useEffect, useState } from "react";
import { fetchJson, type SystemResponse } from "./api";

type SourceDefinition = {
  id: string;
  provider: string;
  dataset: string;
  domain: string;
  reference_url: string;
  authoritative: boolean;
  expected_update_frequency: string;
  spatial_coverage: string;
  status: string;
  limitations: string[];
};

type SourceRuntimeStatus = {
  source_id: string;
  availability: string;
  freshness: string;
  last_retrieval_attempt?: string | null;
  last_successful_retrieval?: string | null;
  latest_observation_time?: string | null;
  error_code?: string | null;
};

type AgentDescriptor = {
  id: string;
  name?: string | null;
  version: string;
  domain?: string | null;
  description: string;
  capabilities: string[];
  input_contracts: string[];
  output_contracts: string[];
  source_dependencies: string[];
  agent_dependencies: string[];
  optional_agent_dependencies: string[];
};

type InspectorState = "loading" | "ready" | "error";

export default function PlatformInspector() {
  const [state, setState] = useState<InspectorState>("loading");
  const [error, setError] = useState<string | null>(null);
  const [sources, setSources] = useState<SourceDefinition[]>([]);
  const [statuses, setStatuses] = useState<Record<string, SourceRuntimeStatus>>({});
  const [agents, setAgents] = useState<AgentDescriptor[]>([]);
  const [system, setSystem] = useState<SystemResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchJson<SourceDefinition[]>("/api/v1/sources"),
      fetchJson<Record<string, SourceRuntimeStatus>>("/api/v1/source-status"),
      fetchJson<AgentDescriptor[]>("/api/v1/agents"),
      fetchJson<SystemResponse>("/api/v1/system"),
    ])
      .then(([sourceValue, statusValue, agentValue, systemValue]) => {
        if (cancelled) return;
        setSources(sourceValue);
        setStatuses(statusValue);
        setAgents(agentValue);
        setSystem(systemValue);
        setState("ready");
      })
      .catch((reason: unknown) => {
        if (cancelled) return;
        setError(reason instanceof Error ? reason.message : "Unknown platform inspector error");
        setState("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="research-grid" aria-label="Platform registry and source inspector">
      <article className="research-card">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Source registry</p>
            <h2>Configured and runtime sources</h2>
          </div>
          <span className="count-pill">{sources.length}</span>
        </div>
        {state === "loading" && <p className="empty-state">Loading source registry…</p>}
        {state === "error" && <p className="inline-error">{error}</p>}
        {state === "ready" && (
          <div className="observation-list">
            {sources.map((source) => {
              const runtime = statuses[source.id];
              return (
                <div className="observation-row" key={source.id}>
                  <span>
                    <strong>{source.dataset}</strong>
                    <small>{source.provider} · {source.domain}</small>
                  </span>
                  <span>{runtime?.availability ?? "not loaded"}</span>
                  <span className="state-label">{runtime?.freshness ?? source.status}</span>
                  <span className="quality-label">{runtime?.error_code ?? "no error"}</span>
                </div>
              );
            })}
          </div>
        )}
      </article>

      <article className="research-card provenance-card">
        <p className="eyebrow">Agent registry</p>
        <h2>Capabilities & dependencies</h2>
        {agents.length === 0 ? (
          <p className="empty-state">No registered agent descriptors are available.</p>
        ) : (
          <div className="observation-list">
            {agents.map((agent) => (
              <div className="observation-row" key={agent.id}>
                <span>
                  <strong>{agent.name ?? agent.id}</strong>
                  <small>{agent.domain ?? "cross-domain"} · v{agent.version}</small>
                </span>
                <span>{agent.capabilities.length} capabilities</span>
                <span className="state-label">
                  deps {agent.agent_dependencies.length}
                </span>
                <span className="quality-label">
                  sources {agent.source_dependencies.length}
                </span>
              </div>
            ))}
          </div>
        )}
      </article>

      <article className="research-card">
        <p className="eyebrow">Snapshot lifecycle</p>
        <h2>Reload diagnostics</h2>
        <dl className="provenance-list">
          {Object.entries(system?.snapshot_reload ?? {}).map(([snapshot, diagnostic]) => (
            <FragmentRow
              key={snapshot}
              name={snapshot}
              value={`${diagnostic.status}${diagnostic.last_error ? ` · ${diagnostic.last_error}` : ""}`}
            />
          ))}
        </dl>
        {Object.keys(system?.snapshot_reload ?? {}).length === 0 && (
          <p className="empty-state">Snapshot diagnostics are unavailable.</p>
        )}
      </article>

      <article className="research-card">
        <p className="eyebrow">Runtime policy</p>
        <h2>Failure semantics</h2>
        <p className="method-note">
          Source transport availability, data freshness and agent health are reported separately.
          Invalid replacement snapshots retain the last known valid state; unavailable domains are
          not filled with synthetic production values.
        </p>
      </article>
    </section>
  );
}

function FragmentRow({ name, value }: { name: string; value: string }) {
  return (
    <>
      <dt>{name}</dt>
      <dd>{value}</dd>
    </>
  );
}
