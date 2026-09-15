"""Explicit registry for discoverable modular domain agents."""

from __future__ import annotations

import networkx as nx

from berlin_urban_intelligence.agents.base import BaseAgent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        agent_id = agent.descriptor.id
        if agent_id in self._agents:
            raise ValueError(f"agent already registered: {agent_id}")
        self._agents[agent_id] = agent

    def get(self, agent_id: str) -> BaseAgent:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"unknown agent: {agent_id}") from exc

    def all(self) -> tuple[BaseAgent, ...]:
        return tuple(self._agents.values())

    def validate(self) -> None:
        graph = self._dependency_graph()
        if not nx.is_directed_acyclic_graph(graph):
            cycle = nx.find_cycle(graph)
            rendered = " -> ".join(source for source, _ in cycle)
            raise ValueError(f"agent dependency cycle detected: {rendered}")

    def dependency_order(self) -> tuple[BaseAgent, ...]:
        self.validate()
        graph = self._dependency_graph()
        return tuple(self._agents[agent_id] for agent_id in nx.topological_sort(graph))

    def agents_with_capability(self, capability: str) -> tuple[BaseAgent, ...]:
        return tuple(
            agent for agent in self._agents.values() if capability in agent.descriptor.capabilities
        )

    def resolve_capability(self, capability: str) -> BaseAgent | None:
        """Resolve one capability while rejecting ambiguous provider selection."""
        candidates = self.agents_with_capability(capability)
        if not candidates:
            return None
        if len(candidates) > 1:
            candidate_ids = ", ".join(sorted(agent.descriptor.id for agent in candidates))
            raise ValueError(
                f"capability {capability!r} is provided by multiple agents: {candidate_ids}"
            )
        return candidates[0]

    def _dependency_graph(self) -> nx.DiGraph[str]:
        graph: nx.DiGraph[str] = nx.DiGraph()
        graph.add_nodes_from(self._agents)
        for agent_id, agent in self._agents.items():
            for dependency in agent.descriptor.agent_dependencies:
                if dependency not in self._agents:
                    raise ValueError(f"agent {agent_id} has missing dependency: {dependency}")
                graph.add_edge(dependency, agent_id)
            for dependency in agent.descriptor.optional_agent_dependencies:
                if dependency in self._agents:
                    graph.add_edge(dependency, agent_id)
        return graph
