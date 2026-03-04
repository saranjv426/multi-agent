from agents.validation_report_formatter import (
    normalize_validation_report,
    apply_section_label_from_extraction,
)


def test_normalize_validation_report_adds_required_sections():
    raw = "STEP 2: FBC-R 2023 COMPLIANCE VALIDATION\nSECTION: [A]\n"
    normalized = normalize_validation_report(raw)

    assert "ROOF_FRAMING_COMPLIANCE:" in normalized
    assert "ROOF_SHEATHING_COMPLIANCE:" in normalized
    assert "ROOF_TO_WALL_CONNECTION_COMPLIANCE:" in normalized
    assert "ROOF_COVERING_COMPLIANCE:" in normalized
    assert "WIND_RESISTANCE_COMPLIANCE:" in normalized
    assert "OVERALL_COMPLIANCE_STATUS:" in normalized
    assert "CRITICAL_FINDINGS:" in normalized
    assert "REQUIRED_CORRECTIONS:" in normalized
    assert "PROFESSIONAL_RECOMMENDATION:" in normalized
    assert "VALIDATION_METADATA:" in normalized


def test_normalize_validation_report_rewrites_wrong_roof_code_reference():
    raw = """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [A]
ROOF_SHEATHING_COMPLIANCE:
  Status: [COMPLIANT]
  Code_Reference: [FBC-R R502.3.2]
  Analysis: |
    Sheathing: [7/16 OSB]
  Required_Corrections: [None]
"""
    normalized = normalize_validation_report(raw)

    assert "Code_Reference: [Exact citation verification needed (roof scope: R802/R803/R905/R301/R806)]" in normalized
    assert "ROOF_SHEATHING_COMPLIANCE:\n  Status: [REQUIRES REVIEW]" in normalized


def test_normalize_validation_report_sets_overall_from_statuses():
    raw = """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [A]
ROOF_FRAMING_COMPLIANCE:
  Status: [NON-COMPLIANT]
  Code_Reference: [FBC-R R802.4]
  Analysis: |
    bad
  Required_Corrections: [fix]
"""
    normalized = normalize_validation_report(raw)
    assert "OVERALL_COMPLIANCE_STATUS: [NON-COMPLIANT]" in normalized


def test_apply_section_label_from_extraction_replaces_unlabeled():
    validation = "SECTION: [Unlabeled Section 1]\nROOF_FRAMING_COMPLIANCE:\n  Status: [REQUIRES REVIEW]\n"
    extraction = "SECTION_1:\n  Label: [New Women Restrooms Wall Section Detail]\n"
    updated = apply_section_label_from_extraction(validation, extraction)
    assert "[Unlabeled Section 1]" not in updated
    assert "SECTION: [New Women Restrooms Wall Section Detail]" in updated
