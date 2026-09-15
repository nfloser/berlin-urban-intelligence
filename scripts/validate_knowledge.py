"""Deterministic syntax and vocabulary validation for repository ontology artefacts."""

from pathlib import Path

from rdflib import RDF, RDFS, Graph, Namespace

BUI = Namespace("https://w3id.org/berlin-urban-intelligence/ontology#")
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    ontology = Graph().parse(ROOT / "knowledge/ontology/bui.ttl", format="turtle")
    Graph().parse(ROOT / "knowledge/ontology/shapes.ttl", format="turtle")
    required = (
        BUI.UrbanEntity,
        BUI.Observation,
        BUI.DerivedValue,
        BUI.DerivedInformation,
        BUI.DerivationDefinition,
        BUI.Forecast,
        BUI.ScenarioValue,
    )
    missing = [term for term in required if (term, RDF.type, RDFS.Class) not in ontology]
    if missing:
        raise SystemExit(f"missing ontology classes: {', '.join(map(str, missing))}")
    print(f"ontology_triples={len(ontology)} status=valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
