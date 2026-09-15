import pytest

from berlin_urban_intelligence.shared.contracts import DerivationStatus
from berlin_urban_intelligence.shared.dependencies import DependencyGraph


def build_graph() -> DependencyGraph:
    graph = DependencyGraph()
    graph.add_derivation("heat:condition", ("weather:temperature",))
    graph.add_derivation("exposure:population", ("heat:condition", "population:grid"))
    graph.add_derivation("resilience:impact", ("exposure:population", "facilities:critical"))
    return graph


def test_affected_products_are_returned_in_dependency_order() -> None:
    graph = build_graph()
    assert graph.affected_order(("weather:temperature",)) == (
        "heat:condition",
        "exposure:population",
        "resilience:impact",
    )


def test_upstream_change_marks_all_downstream_products_stale() -> None:
    graph = build_graph()
    affected = graph.mark_upstream_changed("weather:temperature")
    assert affected == {"heat:condition", "exposure:population", "resilience:impact"}
    assert graph.status("heat:condition") is DerivationStatus.STALE
    assert graph.status("resilience:impact") is DerivationStatus.STALE


def test_duplicate_dependencies_are_rejected() -> None:
    graph = DependencyGraph()
    with pytest.raises(ValueError, match="duplicate"):
        graph.add_derivation("heat:condition", ("weather:temperature", "weather:temperature"))


def test_cycle_rejection_does_not_damage_existing_graph() -> None:
    graph = build_graph()
    before = graph.affected_order(("weather:temperature",))

    with pytest.raises(ValueError, match="acyclic"):
        graph.add_derivation("weather:temperature", ("resilience:impact",))

    assert graph.affected_order(("weather:temperature",)) == before
    assert graph.dependencies("heat:condition") == ("weather:temperature",)


def test_registered_product_cannot_be_silently_redefined() -> None:
    graph = DependencyGraph()
    graph.add_derivation("heat:condition", ("weather:temperature",))
    with pytest.raises(ValueError, match="already registered"):
        graph.add_derivation("heat:condition", ("weather:humidity",))


def test_lineage_exposes_direct_and_transitive_relationships() -> None:
    graph = build_graph()
    assert graph.upstream("resilience:impact") == (
        "weather:temperature",
        "heat:condition",
        "population:grid",
        "exposure:population",
        "facilities:critical",
    )
    assert graph.downstream("weather:temperature") == (
        "heat:condition",
        "exposure:population",
        "resilience:impact",
    )
    assert graph.direct_downstream("heat:condition") == ("exposure:population",)
