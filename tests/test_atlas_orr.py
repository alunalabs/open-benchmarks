from __future__ import annotations

import csv
import math

from spatial_benchmarks.atlas_orr import (
    calculate_atlas_orr_baseline,
    write_atlas_orr_outputs,
)


def write_rows(path, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def atlas_row(
    *,
    nct_id: str,
    arm_title: str,
    orr: float,
    denom: int = 10,
    tissue: str = "breast",
    therapy_class: str = "chemotherapy",
) -> dict[str, object]:
    return {
        "nct_id": nct_id,
        "brief_title": "",
        "conditions": "",
        "tissue_type": tissue,
        "line_of_therapy": "2L+",
        "biomarker": "no",
        "arm_title": arm_title,
        "arm_description": "",
        "interventions": arm_title,
        "regimen": arm_title,
        "treatment_regimen": arm_title,
        "therapy_class": therapy_class,
        "is_combination": "false",
        "orr_denom": denom,
        "model_orr_pct": orr,
        "model_orr_pct_source": "ctgov",
    }


def test_atlas_baseline_excludes_exact_drug_and_selects_disease_therapy(tmp_path) -> None:
    atlas_rows = [
        atlas_row(nct_id="NCT999", arm_title="docetaxel", orr=90, denom=10),
        *[
            atlas_row(
                nct_id=f"NCT{i}",
                arm_title=f"paclitaxel comparator {i}",
                orr=20 + i,
                denom=10,
            )
            for i in range(8)
        ],
    ]
    target_rows = [
        {
            "surface_pair_id": "breast::docetaxel",
            "cohort": "breast",
            "disease": "breast",
            "drug": "Docetaxel",
            "drug_norm": "docetaxel",
            "moa_component": "taxane",
            "orr_pct": 25,
            "default_score": 0.2,
        }
    ]
    atlas_path = tmp_path / "atlas.csv"
    target_path = tmp_path / "predictions.csv"
    write_rows(atlas_path, atlas_rows)
    write_rows(target_path, target_rows)

    result = calculate_atlas_orr_baseline(
        atlas_csv=atlas_path,
        cohort_predictions_csv=target_path,
    )

    prediction = result["predictions"][0]
    assert prediction["excluded_exact_drug_atlas_arms"] == 1
    assert (
        prediction["atlas_mono_allcomer_hierarchical_prior_therapy_first_source"]
        == "disease_therapy"
    )
    assert prediction["atlas_mono_allcomer_hierarchical_prior_therapy_first_n_arms"] == 8
    assert math.isclose(
        prediction["atlas_mono_allcomer_hierarchical_prior_therapy_first_orr"],
        23.5,
    )
    assert math.isclose(prediction["atlas_mono_disease_therapy_shrink_k8"], 23.5)
    assert result["summary"]["primary_baseline"]["score_col"] == (
        "atlas_mono_disease_therapy_shrink_k8"
    )


def test_atlas_prior_score_does_not_use_target_label_or_surface_score(tmp_path) -> None:
    atlas_rows = [
        atlas_row(nct_id="NCT999", arm_title="docetaxel", orr=90, denom=10),
        *[
            atlas_row(
                nct_id=f"NCTB{i}",
                arm_title=f"paclitaxel comparator {i}",
                orr=20 + i,
                denom=10,
            )
            for i in range(8)
        ],
        *[
            atlas_row(
                nct_id=f"NCTL{i}",
                arm_title=f"gemcitabine comparator {i}",
                orr=40 + i,
                denom=10,
                tissue="nsclc",
            )
            for i in range(8)
        ],
    ]
    target_base = {
        "surface_pair_id": "breast::docetaxel",
        "cohort": "breast",
        "disease": "breast",
        "drug": "Docetaxel",
        "drug_norm": "docetaxel",
        "moa_component": "taxane",
    }
    atlas_path = tmp_path / "atlas.csv"
    low_label_path = tmp_path / "predictions_low.csv"
    high_label_path = tmp_path / "predictions_high.csv"
    write_rows(atlas_path, atlas_rows)
    write_rows(
        low_label_path,
        [{**target_base, "orr_pct": 0, "default_score": 0.1}],
    )
    write_rows(
        high_label_path,
        [{**target_base, "orr_pct": 100, "default_score": 0.9}],
    )

    low = calculate_atlas_orr_baseline(
        atlas_csv=atlas_path,
        cohort_predictions_csv=low_label_path,
    )["predictions"][0]
    high = calculate_atlas_orr_baseline(
        atlas_csv=atlas_path,
        cohort_predictions_csv=high_label_path,
    )["predictions"][0]

    assert low["observed_orr_pct"] == 0
    assert high["observed_orr_pct"] == 100
    assert math.isclose(
        low["atlas_mono_disease_therapy_shrink_k8"],
        high["atlas_mono_disease_therapy_shrink_k8"],
    )
    assert math.isclose(low["atlas_mono_disease_therapy_shrink_k8"], 28.5)


def test_atlas_baseline_can_exclude_raw_atlas_row_indices(tmp_path) -> None:
    atlas_rows = [
        *[
            atlas_row(
                nct_id=f"NCT{i}",
                arm_title=f"paclitaxel comparator {i}",
                orr=20,
                denom=10,
            )
            for i in range(8)
        ],
        atlas_row(nct_id="NCT_BAD", arm_title="endpoint caveat", orr=100, denom=10),
    ]
    target_rows = [
        {
            "surface_pair_id": "breast::doxorubicin",
            "cohort": "breast",
            "disease": "breast",
            "drug": "Doxorubicin",
            "drug_norm": "doxorubicin",
            "moa_component": "topo2_anthracycline",
            "orr_pct": 25,
            "default_score": 0.2,
        }
    ]
    atlas_path = tmp_path / "atlas.csv"
    target_path = tmp_path / "predictions.csv"
    write_rows(atlas_path, atlas_rows)
    write_rows(target_path, target_rows)

    unfiltered = calculate_atlas_orr_baseline(
        atlas_csv=atlas_path,
        cohort_predictions_csv=target_path,
    )["predictions"][0]
    filtered = calculate_atlas_orr_baseline(
        atlas_csv=atlas_path,
        cohort_predictions_csv=target_path,
        excluded_raw_atlas_row_indices={8},
    )["predictions"][0]

    assert unfiltered["atlas_mono_allcomer_prior_disease_therapy_n_arms"] == 9
    assert filtered["atlas_mono_allcomer_prior_disease_therapy_n_arms"] == 8
    assert math.isclose(unfiltered["atlas_mono_disease_therapy_shrink_k8"], 28.88888888888889)
    assert math.isclose(filtered["atlas_mono_disease_therapy_shrink_k8"], 20.0)


def test_write_atlas_outputs(tmp_path) -> None:
    atlas_rows = [
        atlas_row(nct_id=f"NCT{i}", arm_title=f"paclitaxel comparator {i}", orr=20 + i)
        for i in range(8)
    ]
    target_rows = [
        {
            "surface_pair_id": "breast::paclitaxel",
            "cohort": "breast",
            "drug": "Paclitaxel",
            "drug_norm": "paclitaxel",
            "moa_component": "taxane",
            "orr_pct": 25,
            "default_score": 0.2,
        }
    ]
    atlas_path = tmp_path / "atlas.csv"
    target_path = tmp_path / "predictions.csv"
    output = tmp_path / "out"
    write_rows(atlas_path, atlas_rows)
    write_rows(target_path, target_rows)

    result = calculate_atlas_orr_baseline(
        atlas_csv=atlas_path,
        cohort_predictions_csv=target_path,
    )
    write_atlas_orr_outputs(result, output)

    assert (output / "atlas_orr_predictions.csv").exists()
    assert (output / "atlas_orr_metrics.csv").exists()
    assert (output / "atlas_orr_methodology.md").exists()
