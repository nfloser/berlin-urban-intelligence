"""Small dependency graph for freshness propagation of derived products."""

from __future__ import annotations

import networkx as nx

from berlin_urban_intelligence.shared.contracts import DerivationStatus


class DependencyGraph:
    def __init__(self) -> None:
        self._graph: nx.DiGraph[str] = nx.DiGraph()
        self._statuses: dict[str, DerivationStatus] = {}

    def add_derivation(self, product_id: str, upstream_ids: list[str] | tuple[str, ...]) -> None:
        if not product_id:
            raise ValueError("product_id must not be empty")
        if not upstream_ids:
            raise ValueError("a derivation requires at least one upstream dependency")
        candidate = self._graph.copy()
        candidate.add_node(product_id)
        for upstream_id in upstream_ids:
            if not upstream_id:
                raise ValueError("upstream dependency id must not be empty")
            candidate.add_edge(upstream_id, product_id)
        if not nx.is_directed_acyclic_graph(candidate):
            raise ValueError("derivation dependencies must remain acyclic")
        self._graph = candidate
        self._statuses[product_id] = DerivationStatus.VALID

    def mark_upstream_changed(self, upstream_id: str) -> set[str]:
        if upstream_id not in self._graph:
            return set()
        affected = {
            node for node in nx.descendants(self._graph, upstream_id) if node in self._statuses
        }
        for product_id in affected:
            self._statuses[product_id] = DerivationStatus.STALE
        return affected

    def status(self, product_id: str) -> DerivationStatus:
        try:
            return self._statuses[product_id]
        except KeyError as exc:
            raise KeyError(f"unknown derived product: {product_id}") from exc

    def set_status(self, product_id: str, status: DerivationStatus) -> None:
        if product_id not in self._statuses:
            raise KeyError(f"unknown derived product: {product_id}")
        self._statuses[product_id] = status
