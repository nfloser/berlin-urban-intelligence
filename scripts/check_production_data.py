"""Guard against common accidental synthetic-data production paths."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_IMPORTS = ("import random", "from random import", "faker", "numpy.random")


def main() -> int:
    violations: list[str] = []
    for path in (ROOT / "src").rglob("*.py"):
        text = path.read_text(encoding="utf-8").lower()
        for marker in FORBIDDEN_IMPORTS:
            if marker in text:
                violations.append(f"{path.relative_to(ROOT)}: {marker}")
    if violations:
        raise SystemExit("potential production synthetic-data path:\n" + "\n".join(violations))
    print("production_synthetic_data_guard=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
