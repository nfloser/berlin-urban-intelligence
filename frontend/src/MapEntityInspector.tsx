import {
  displayValue,
  type CriticalFacility,
  type OfficialModelFeature,
  type UrbanEntity,
} from "./api";

export type MapSelection =
  | { kind: "facility"; item: CriticalFacility }
  | { kind: "stop"; item: UrbanEntity }
  | { kind: "climate"; item: OfficialModelFeature };

type Props = {
  selection: MapSelection | null;
  onClear: () => void;
};

function provenanceRows(selection: MapSelection): Array<[string, string]> {
  if (selection.kind === "stop") return [];
  const provenance = selection.item.provenance;
  if (!provenance) return [];
  return [
    ["Provider", provenance.provider],
    ["Dataset", provenance.dataset],
    ["Retrieved", provenance.retrieved_at],
    ["Method", displayValue(provenance.processing_method)],
    ["Licence", displayValue(provenance.source_licence)],
    ["Quality note", displayValue(provenance.quality_note)],
  ];
}

function selectionRows(selection: MapSelection): Array<[string, string]> {
  if (selection.kind === "facility") {
    return [
      ["Type", "Critical facility"],
      ["ID", selection.item.id],
      ["Category", selection.item.category],
      ["Quality", selection.item.quality],
      ["Confidence", displayValue(selection.item.confidence)],
      ["Source ID", displayValue(selection.item.source_identifier)],
      ["CRS", displayValue(selection.item.spatial?.crs)],
      ...provenanceRows(selection),
    ];
  }
  if (selection.kind === "stop") {
    return [
      ["Type", "Transport stop"],
      ["ID", selection.item.id],
      ["Entity type", selection.item.entity_type],
      ["Source ID", displayValue(selection.item.source_identifier)],
      ["CRS", displayValue(selection.item.spatial?.crs)],
    ];
  }
  return [
    ["Type", "Official climate model feature"],
    ["ID", selection.item.id],
    ["Entity", selection.item.entity_id],
    ["Model", selection.item.model_name],
    ["Feature type", selection.item.feature_type],
    ["State", selection.item.state],
    ["Quality", selection.item.quality],
    ["Properties", JSON.stringify(selection.item.properties)],
    ["CRS", selection.item.spatial.crs],
    ...provenanceRows(selection),
  ];
}

function title(selection: MapSelection): string {
  if (selection.kind === "facility" || selection.kind === "stop") {
    return selection.item.name ?? selection.item.id;
  }
  return selection.item.model_name;
}

export default function MapEntityInspector({ selection, onClear }: Props) {
  return (
    <section aria-label="Map selection inspector">
      <p className="eyebrow">Map inspection</p>
      <h2>Selected reference object</h2>
      {selection ? (
        <>
          <div className="section-heading compact-heading">
            <strong>{title(selection)}</strong>
            <button className="inspector-clear" onClick={onClear} type="button">
              Clear
            </button>
          </div>
          <dl className="provenance-list map-inspector-list">
            {selectionRows(selection).map(([name, value]) => (
              <FragmentRow key={name} name={name} value={value} />
            ))}
          </dl>
        </>
      ) : (
        <p className="empty-state">
          Click a visible facility, transport stop or climate feature to inspect its canonical
          metadata. Route-selection mode remains separate from reference-object inspection.
        </p>
      )}
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
