"""Network-dependent live source smoke test kept outside deterministic CI."""

from berlin_urban_intelligence.runtime.refresh import RefreshCoordinator
from berlin_urban_intelligence.shared.contracts import AvailabilityStatus


def main() -> int:
    state = RefreshCoordinator().refresh()
    failures = []
    for source_id, source in sorted(state.source_statuses.items()):
        print(
            f"{source_id}: availability={source.availability.value} "
            f"freshness={source.freshness.value} error={source.error_code or '-'}"
        )
        if source.availability != AvailabilityStatus.AVAILABLE:
            failures.append(source_id)
    if failures:
        raise SystemExit("live sources unavailable: " + ", ".join(failures))
    if not state.observations:
        raise SystemExit("live refresh returned no canonical observations")
    print(f"observations={len(state.observations)} live_smoke=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
