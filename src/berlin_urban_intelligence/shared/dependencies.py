"""Deterministic dependency graph for derived products and freshness propagation."""

from __future__ import annotations

from collections.abc import Iterable

import networkx as nx

from berlin_urban_intelligence.shared.contracts import DerivationStatus


class DependencyGraph:
    def __init__(self) -> None:
        self._graph: nx.DiGraph[str] = nx.DiGraph()
        self._statuses: dict[str, DerivationStatus] = {}

    def add_derivation(self, product_id: str, upstream_ids: list[str] | tuple[str, ...]) -> None:
        if not product_id:
            raise ValueError("product_id must not be empty")
        if product_id in self._statuses:
            raise ValueError(f"derived product already registered: {product_id}")
        if not upstream_ids:
            raise ValueError("a derivation requires at least one upstream dependency")
        if len(set(upstream_ids)) != len(upstream_ids):
            raise ValueError("duplicate upstream dependencies are not allowed")
        if any(not upstream_id for upstream_id in upstream_ids):
            raise ValueError("upstream dependency id must not be empty")

        candidate = self._graph.copy()
        candidate.add_node(product_id)
        for upstream_id in upstream_ids:
            candidate.add_edge(upstream_id, product_id)
        if not nx.is_directed_acyclic_graph(candidate):
            raise ValueError("derivation dependencies must remain acyclic")

        self._graph = candidate
        self._statuses[product_id] = DerivationStatus.VALID

    def dependencies(self, product_id: str) -> tuple[str, ...]:
        if product_id not in self._statuses:
            raise KeyError(f"unknown derived product: {product_id}")
        return tuple(self._graph.predecessors(product_id))

    def direct_downstream(self, input_id: str) -> tuple[str, ...]:
        if input_id not in self._graph:
            return ()
        return tuple(node for node in self._graph.successors(input_id) if node in self._statuses)

    def upstream(self, product_id: str) -> tuple[str, ...]:
        """Return lineage depth-first so every dependency appears before its consumer."""

        if product_id not in self._statuses:
            raise KeyError(f"unknown derived product: {product_id}")
        ordered: list[str] = []
        seen: set[str] = set()

        def visit(node_id: str) -> None:
            for dependency in self._graph.predecessors(node_id):
                if dependency in seen:
                    continue
                visit(dependency)
                seen.add(dependency)
                ordered.append(dependency)

        visit(product_id)
        return tuple(ordered)

    def downstream(self, input_id: str) -> tuple[str, ...]:
        return self.affected_order((input_id,))

    def affected_order(self, upstream_ids: Iterable[str]) -> tuple[str, ...]:
        affected: set[str] = set()
        for upstream_id in upstream_ids:
            if upstream_id in self._graph:
                affected.update(nx.descendants(self._graph, upstream_id))
        ordered = nx.topological_sort(self._graph)
        return tuple(node for node in ordered if node in affected and node in self._statuses)

    def mark_upstream_changed(self, upstream_id: str) -> set[str]:
        affected = set(self.affected_order((upstream_id,)))
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

    def products(self) -> tuple[str, ...]:
        return tuple(node for node in nx.topological_sort(self._graph) if node in self._statuses)
