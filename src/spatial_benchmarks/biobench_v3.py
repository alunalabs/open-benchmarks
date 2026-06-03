"""BioBench v3 manifest loading and validation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .io import read_csv_rows, read_json, require_columns


MODULE_COLUMNS = (
    "module_id",
    "ligands",
    "receptors",
    "receptor_complexes",
    "pathway",
    "expected_direction",
)
MANIFEST_COLUMNS = (
    "tissue",
    "dataset_name",
    "platform",
    "expected_sender_cell_types",
    "module_id",
    "pathway",
    "expected_receiver_cell_types",
)
ROW_INDEX_COLUMNS = (
    "row_layer",
    "row_id",
    "row_type",
    "tissue",
    "module_or_candidate_id",
    "readout",
    "expected_ko_readout_change",
    "expected_oe_readout_change",
)

SURFACE_FILES = {
    "raw": {
        "manifest": "biobench_v3_manifest.csv",
        "modules": "biobench_v3_ligand_modules.csv",
        "row_index": "biobench_all_rows_index.csv",
        "summary": "biobench_v3_summary.json",
    },
    "headline": {
        "manifest": "biobench_v3_headline_manifest.csv",
        "modules": "biobench_v3_headline_ligand_modules.csv",
        "row_index": None,
        "summary": None,
    },
    "added_directional": {
        "manifest": "biobench_v3_added_directional_candidates_manifest.csv",
        "modules": "biobench_v3_added_directional_candidates_ligand_modules.csv",
        "row_index": None,
        "summary": None,
    },
    "curated": {
        "manifest": "biobench_v3_curated_manifest.csv",
        "modules": "biobench_v3_curated_ligand_modules.csv",
        "row_index": "biobench_v3_curated_all_rows_index.csv",
        "summary": "biobench_v3_curated_summary.json",
    },
}


@dataclass(frozen=True)
class BiobenchV3Surface:
    root: Path
    surface: str
    modules: list[dict[str, Any]]
    manifest: list[dict[str, Any]]
    row_index: list[dict[str, Any]]
    summary: dict[str, Any]

    @classmethod
    def from_directory(cls, root: str | Path, *, surface: str = "curated") -> "BiobenchV3Surface":
        root_path = Path(root)
        try:
            files = SURFACE_FILES[surface]
        except KeyError as exc:
            raise ValueError(f"unknown BioBench v3 surface {surface!r}; expected one of {sorted(SURFACE_FILES)}") from exc

        manifest = read_csv_rows(root_path / files["manifest"])
        modules = read_csv_rows(root_path / files["modules"])
        row_index_file = files["row_index"]
        row_index = read_csv_rows(root_path / row_index_file) if row_index_file else build_row_index(manifest, modules)
        summary_file = files["summary"]
        summary = read_json(root_path / summary_file) if summary_file and (root_path / summary_file).exists() else {}
        surface_obj = cls(root=root_path, surface=surface, modules=modules, manifest=manifest, row_index=row_index, summary=summary)
        surface_obj.validate()
        return surface_obj

    def validate(self) -> None:
        require_columns(self.modules, MODULE_COLUMNS, table="BioBench v3 modules")
        require_columns(self.manifest, MANIFEST_COLUMNS, table="BioBench v3 manifest")
        require_columns(self.row_index, ROW_INDEX_COLUMNS, table="BioBench v3 row index")

        module_ids = {row["module_id"] for row in self.modules}
        manifest_module_ids = {row["module_id"] for row in self.manifest}
        missing = sorted(manifest_module_ids - module_ids)
        if missing:
            raise ValueError(f"manifest references undefined modules: {missing[:20]}")

        bad_direction = [
            row["module_id"]
            for row in self.modules
            if str(row.get("expected_direction", "")).strip() not in {"increase", "decrease"}
        ]
        if bad_direction:
            raise ValueError(f"modules have unsupported expected_direction: {bad_direction[:20]}")

    def counts(self) -> dict[str, Any]:
        tissues = {row.get("tissue", "") for row in self.manifest}
        modules = {row.get("module_id", "") for row in self.manifest}
        row_layers: dict[str, int] = {}
        for row in self.row_index:
            layer = str(row.get("row_layer", ""))
            row_layers[layer] = row_layers.get(layer, 0) + 1
        return {
            "surface": self.surface,
            "module_count": len(self.modules),
            "manifest_rows": len(self.manifest),
            "row_index_rows": len(self.row_index),
            "tissues": len(tissues),
            "manifest_modules": len(modules),
            "row_layers": row_layers,
            "summary": self.summary,
        }


def build_row_index(
    manifest_rows: list[dict[str, Any]],
    module_rows: list[dict[str, Any]],
    *,
    regional_rows: list[dict[str, Any]] | None = None,
    source_file: str = "biobench_v3_manifest.csv",
    regional_source_file: str = "biobench_v3_regional_biology_rows.csv",
) -> list[dict[str, Any]]:
    """Build an audit row index from ligand/receptor rows and optional regional rows."""

    modules_by_id = {row["module_id"]: row for row in module_rows}
    rows: list[dict[str, Any]] = []
    for manifest in manifest_rows:
        module_id = str(manifest["module_id"])
        module = modules_by_id[module_id]
        expected_ko = str(module.get("expected_direction", "decrease") or "decrease").strip()
        if expected_ko not in {"increase", "decrease"}:
            expected_ko = "decrease"
        expected_oe = "increase" if expected_ko == "decrease" else "decrease"
        tissue = str(manifest.get("tissue", ""))
        pathway = str(manifest.get("pathway", module.get("pathway", "")))
        sender_genes = join_nonempty(module.get("ligands", ""), module.get("complex_partners", ""))
        receiver_genes = join_nonempty(module.get("receptors", ""), module.get("receptor_complexes", ""))
        rows.append(
            {
                "row_layer": "ligand_receptor",
                "row_id": f"biobench_v3::{tissue}::{module_id}::{pathway}",
                "row_type": "ligand_receptor_progeny",
                "tissue": tissue,
                "dataset_name": manifest.get("dataset_name", ""),
                "patient_id": "",
                "module_or_candidate_id": module_id,
                "label": module_id,
                "sender_cell_types": manifest.get("expected_sender_cell_types", ""),
                "sender_genes": sender_genes,
                "receiver_cell_types_or_mode": manifest.get("expected_receiver_cell_types", ""),
                "receiver_genes": receiver_genes,
                "readout": pathway,
                "expected_ko_readout_change": expected_ko,
                "expected_oe_readout_change": expected_oe,
                "source_file": source_file,
            }
        )

    for regional in regional_rows or []:
        rows.append(
            {
                "row_layer": "regional_biology",
                "row_id": regional.get("row_id", ""),
                "row_type": "regional_sender_program",
                "tissue": regional.get("tissue_type", regional.get("tissue", "")),
                "dataset_name": regional.get("dataset_name", ""),
                "patient_id": regional.get("patient_id", ""),
                "module_or_candidate_id": regional.get("candidate", ""),
                "label": regional.get("label", ""),
                "sender_cell_types": regional.get("sender_cell_types", ""),
                "sender_genes": regional.get("sender_genes", ""),
                "receiver_cell_types_or_mode": regional.get("receiver_mode_label") or regional.get("receiver_mode", ""),
                "receiver_genes": regional.get("receiver_genes", ""),
                "readout": regional.get("readout", ""),
                "expected_ko_readout_change": regional.get("expected_ko_readout_change", ""),
                "expected_oe_readout_change": regional.get("expected_oe_readout_change", ""),
                "source_file": regional_source_file,
            }
        )
    return rows


def join_nonempty(*parts: Any) -> str:
    return ";".join(str(part).strip() for part in parts if str(part or "").strip())


def direction_accuracy(rows: list[dict[str, Any]], *, expected_col: str, observed_col: str) -> float:
    """Compute simple direction-pass accuracy for BioBench result rows."""

    total = 0
    passed = 0
    for row in rows:
        expected = str(row.get(expected_col, "")).strip().lower()
        observed = str(row.get(observed_col, "")).strip().lower()
        if expected not in {"increase", "decrease"} or observed not in {"increase", "decrease"}:
            continue
        total += 1
        passed += int(expected == observed)
    return passed / total if total else math.nan

