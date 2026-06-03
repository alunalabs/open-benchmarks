from __future__ import annotations

import math

from spatial_benchmarks.atlas_ctgov_audit import audit_support_row


def test_audit_support_row_matches_ctgov_group_and_orr_value() -> None:
    support_row = {
        "nct_id": "NCT00000000",
        "ctgov_result_group_ids": "OG000",
        "ctgov_result_group_titles": "DOCOX",
        "arm_title": "DOCOX",
        "orr_endpoint_title": "Objective Response Rate (ORR)",
        "model_orr_pct": "26.5",
        "model_orr_pct_source": "ctgov",
    }
    study = {
        "resultsSection": {
            "outcomeMeasuresModule": {
                "outcomeMeasures": [
                    {
                        "title": "Objective Response Rate (ORR)",
                        "type": "SECONDARY",
                        "timeFrame": "Until progression",
                        "groups": [
                            {"id": "OG000", "title": "DOCOX"},
                            {"id": "OG001", "title": "DOCOX + Cetuximab"},
                        ],
                        "classes": [
                            {
                                "categories": [
                                    {
                                        "measurements": [
                                            {"groupId": "OG000", "value": "26.5"},
                                            {"groupId": "OG001", "value": "38.0"},
                                        ]
                                    }
                                ]
                            }
                        ],
                    }
                ]
            }
        }
    }

    audited = audit_support_row(support_row, study, retrieved_date="2026-06-03")

    assert audited["ctgov_audit_status"] == "ctgov_verified_match"
    assert math.isclose(audited["ctgov_verified_orr_pct"], 26.5)
    assert audited["ctgov_group_id"] == "OG000"
    assert audited["ctgov_citation"] == "https://clinicaltrials.gov/study/NCT00000000"


def test_audit_support_row_matches_blank_endpoint_recist_response() -> None:
    support_row = {
        "nct_id": "NCT00000001",
        "ctgov_result_group_ids": "OG001",
        "ctgov_result_group_titles": "Arm B",
        "arm_title": "Arm B",
        "orr_endpoint_title": "",
        "model_orr_pct": "0",
        "model_orr_pct_source": "pubmed",
    }
    study = {
        "resultsSection": {
            "outcomeMeasuresModule": {
                "outcomeMeasures": [
                    {
                        "title": "RECIST Response",
                        "type": "SECONDARY",
                        "timeFrame": "On treatment",
                        "paramType": "COUNT_OF_PARTICIPANTS",
                        "unitOfMeasure": "Participants",
                        "groups": [
                            {"id": "OG000", "title": "Arm A"},
                            {"id": "OG001", "title": "Arm B"},
                        ],
                        "denoms": [
                            {
                                "counts": [
                                    {"groupId": "OG000", "value": "15"},
                                    {"groupId": "OG001", "value": "8"},
                                ],
                                "units": "Participants",
                            }
                        ],
                        "classes": [
                            {
                                "title": "PR",
                                "categories": [
                                    {
                                        "measurements": [
                                            {"groupId": "OG000", "value": "3"},
                                            {"groupId": "OG001", "value": "0"},
                                        ]
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        }
    }

    audited = audit_support_row(support_row, study, retrieved_date="2026-06-03")

    assert audited["ctgov_audit_status"] == "ctgov_verified_match"
    assert audited["ctgov_verified_orr_pct"] == 0.0
    assert audited["ctgov_measurement_denominator"] == 8.0
