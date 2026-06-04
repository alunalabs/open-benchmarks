from __future__ import annotations

import csv
import math

from spatial_benchmarks.depmap_orr import (
    calculate_depmap_orr_baseline,
    write_depmap_orr_outputs,
)


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_depmap_baseline_rank_normalizes_lineage_sensitivity(tmp_path) -> None:
    drug_dir = tmp_path / "drug"
    drug_dir.mkdir()
    write_rows(
        drug_dir / "GDSC2Log2ViabilityCollapsedConditions.csv",
        [
            {
                "CompoundName": "Paclitaxel",
                "SampleID": "GDSC2:1",
                "CompoundID": "DPC-1",
                "Dose": "1",
                "DoseUnit": "uM",
                "index": "1",
            }
        ],
    )
    write_rows(
        drug_dir / "GDSC2AUCMatrix.csv",
        [
            {"ModelID": "ACH-1", "DPC-1": 0.1},
            {"ModelID": "ACH-2", "DPC-1": 0.2},
            {"ModelID": "ACH-3", "DPC-1": 0.8},
            {"ModelID": "ACH-4", "DPC-1": 0.9},
        ],
    )
    write_rows(
        tmp_path / "Model.csv",
        [
            {"ModelID": "ACH-1", "OncotreeLineage": "Breast"},
            {"ModelID": "ACH-2", "OncotreeLineage": "Breast"},
            {"ModelID": "ACH-3", "OncotreeLineage": "Lung"},
            {"ModelID": "ACH-4", "OncotreeLineage": "Lung"},
        ],
    )
    write_rows(
        tmp_path / "predictions.csv",
        [
            {
                "surface_pair_id": "breast::paclitaxel",
                "cohort": "breast",
                "disease": "breast",
                "drug": "Paclitaxel",
                "drug_norm_surface": "paclitaxel",
                "orr_pct": 30,
                "default_score": 0.2,
            },
            {
                "surface_pair_id": "nsclc::paclitaxel",
                "cohort": "nsclc",
                "disease": "nsclc",
                "drug": "Paclitaxel",
                "drug_norm_surface": "paclitaxel",
                "orr_pct": 5,
                "default_score": 0.1,
            },
        ],
    )

    result = calculate_depmap_orr_baseline(
        depmap_drug_dir=drug_dir,
        model_csv=tmp_path / "Model.csv",
        cohort_predictions_csv=tmp_path / "predictions.csv",
        min_rank_lines=1,
        min_global_lines=1,
    )

    breast = result["features"][0]
    nsclc = result["features"][1]
    assert breast["depmap_screen"] == "GDSC2"
    assert breast["depmap_compound_id"] == "DPC-1"
    assert math.isclose(breast["depmap_lineage_rank"], 0.375)
    assert math.isclose(breast["depmap_lineage_sensitivity_rank"], 0.625)
    assert math.isclose(nsclc["depmap_lineage_sensitivity_rank"], 0.125)
    assert result["summary"]["depmap_covered_rows"] == 2
    assert result["summary"]["primary_baseline"]["score_col"] == (
        "depmap_lineage_sensitivity_rank"
    )

    output = tmp_path / "out"
    write_depmap_orr_outputs(result, output)
    assert (output / "depmap_orr_features.csv").exists()
    assert (output / "depmap_orr_metrics.csv").exists()
    assert (output / "depmap_orr_methodology.md").exists()
