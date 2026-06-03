from __future__ import annotations

from spatial_benchmarks.biobench_v3 import build_row_index


def test_build_biobench_row_index() -> None:
    modules = [
        {
            "module_id": "egfr_ligands",
            "ligands": "AREG;EGF",
            "receptors": "EGFR",
            "receptor_complexes": "",
            "complex_partners": "",
            "pathway": "EGFR",
            "expected_direction": "decrease",
        }
    ]
    manifest = [
        {
            "tissue": "colon",
            "dataset_name": "example_crc",
            "expected_sender_cell_types": "tumor",
            "expected_receiver_cell_types": "tumor",
            "module_id": "egfr_ligands",
            "pathway": "EGFR",
        }
    ]
    rows = build_row_index(manifest, modules)
    assert rows[0]["row_layer"] == "ligand_receptor"
    assert rows[0]["expected_ko_readout_change"] == "decrease"
    assert rows[0]["expected_oe_readout_change"] == "increase"
    assert rows[0]["sender_genes"] == "AREG;EGF"

