"""Small CSV/JSON helpers used by all benchmark modules."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any


Row = dict[str, Any]


def read_csv_rows(path: str | Path) -> list[Row]:
    """Read a CSV file as dictionaries."""

    with Path(path).open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv_rows(
    path: str | Path,
    rows: Sequence[Mapping[str, Any]],
    *,
    fieldnames: Sequence[str] | None = None,
) -> None:
    """Write dictionaries to CSV, preserving the caller's field order when supplied."""

    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = infer_fieldnames(rows)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def infer_fieldnames(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return stable fieldnames from a list of mapping rows."""

    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for field in row:
            if field not in seen:
                fields.append(field)
                seen.add(field)
    return fields


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, data: Any) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_columns(rows: Sequence[Mapping[str, Any]], columns: Iterable[str], *, table: str) -> None:
    """Validate that all required columns exist in a non-empty table."""

    if not rows:
        raise ValueError(f"{table} is empty")
    present = set(rows[0])
    missing = [column for column in columns if column not in present]
    if missing:
        raise ValueError(f"{table} is missing required columns: {missing}")


def parse_bool(value: Any, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y"}:
        return True
    if text in {"0", "false", "no", "n"}:
        return False
    return default


def relative_to_or_name(path: str | Path, root: str | Path) -> str:
    path_obj = Path(path)
    try:
        return str(path_obj.relative_to(root))
    except ValueError:
        return path_obj.name

