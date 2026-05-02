from agents.validation_report_formatter import normalize_validation_report


def test_normalize_validation_report_preserves_modern_section_blocks_without_legacy_padding():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [OUTDOOR BAR WALL SECTION DETAIL]

FRAMING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.5.1]
  Evidence: [2x6 @ 24" O.C.; span not shown]
  Analysis: [Span verification is not shown.]
  Required_Corrections: [Provide span table or engineered design.]

SHEATHING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R803.2.2]
  Evidence: [7/16" OSB]
  Analysis: [Edge support is not shown.]
  Required_Corrections: [Show edge support.]

CONNECTIONS_AND_WIND:
  Status: [NON-COMPLIANT]
  Code_Reference: [FBC-R §R802.11]
  Evidence: [3 16d toe nails]
  Analysis: [Toe nails alone do not document uplift connector capacity.]
  Required_Corrections: [Specify hurricane ties.]

COVERING_AND_EDGE:
  Status: [NON-COMPLIANT]
  Code_Reference: [FBC-R §R905.10.2]
  Evidence: [1/2:12 slope; galvalume mtl. roof]
  Analysis: [Roof system approval for low slope is not shown.]
  Required_Corrections: [Provide approved panel system.]
"""
    )

    assert "FRAMING:" in report
    assert "SHEATHING:" in report
    assert "CONNECTIONS_AND_WIND:" in report
    assert "COVERING_AND_EDGE:" in report
    assert "Roof_framing_compliance" not in report
    assert "Roof_sheathing_compliance" not in report
    assert "Exact citation verification needed" not in report


def test_normalize_validation_report_downgrades_compliant_connections_without_uplift_basis():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [OUTDOOR BAR WALL SECTION DETAIL]

CONNECTIONS_AND_WIND:
  Status: [COMPLIANT]
  Code_Reference: [FBC-R §R802.11]
  Evidence: [3 16d toe nails at each end, mtl. strap at each end]
  Analysis: [Connections appear robust.]
  Required_Corrections: [None]
"""
    )

    assert "CONNECTIONS_AND_WIND:" in report
    assert "Status: [REQUIRES REVIEW]" in report


def test_normalize_validation_report_downgrades_compliant_covering_with_old_code_and_low_slope():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [OUTDOOR BAR WALL SECTION DETAIL]

COVERING_AND_EDGE:
  Status: [COMPLIANT]
  Code_Reference: [FBC-R §R905.10.2]
  Evidence: [self-adhering synthetic underlayment per FBC 2020, galvalume roof, 1/2:12 slope]
  Analysis: [Roof covering appears compliant.]
  Required_Corrections: [None]
"""
    )

    assert "COVERING_AND_EDGE:" in report
    assert "Status: [REQUIRES REVIEW]" in report


def test_normalize_validation_report_downgrades_compliant_sheathing_without_support_context():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [OUTDOOR BAR WALL SECTION DETAIL]

SHEATHING:
  Status: [COMPLIANT]
  Code_Reference: [FBC-R §R803.2.2]
  Evidence: [7/16" OSB with 8d ring shank nails at 6" O.C.]
  Analysis: [Sheathing appears compliant.]
  Required_Corrections: [None]
"""
    )

    assert "SHEATHING:" in report
    assert "Status: [REQUIRES REVIEW]" in report


def test_normalize_validation_report_promotes_framing_when_accepted_truss_phrase_is_in_block():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

FRAMING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.10]
  Evidence: [PRE. ENG. FAB. WD.TRUSSES @ 24" O.C.]
  Analysis: [Member note is visible in the plan.]
  Required_Corrections: [Provide more framing information.]

COVERING_AND_EDGE:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R905.4]
  Evidence: [Metal roof]
  Analysis: [Pitch is not shown.]
  Required_Corrections: [Provide roof pitch.]
"""
    )

    framing_start = report.index("FRAMING:")
    sheathing_start = report.index("SHEATHING:")
    framing_block = report[framing_start:sheathing_start]

    assert "Status: [COMPLIANT]" in framing_block
    assert "Required_Corrections: [None]" in framing_block


def test_normalize_validation_report_promotes_framing_when_accepted_truss_phrase_is_only_in_extraction():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

FRAMING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.10]
  Evidence: [Roof framing note partially captured.]
  Analysis: [Framing note is abbreviated in the detail.]
  Required_Corrections: [Clarify truss spacing.]
""",
        extraction_text="""
STEP 1: ROOF DESIGN EXTRACTION
SECTION_1:
  Framing: [PRE-ENGINEERED/PRE-FAB. WOOD TRUSS AT 2' O.C.]
""",
    )

    framing_start = report.index("FRAMING:")
    sheathing_start = report.index("SHEATHING:")
    framing_block = report[framing_start:sheathing_start]

    assert "Status: [COMPLIANT]" in framing_block
    assert "Required_Corrections: [None]" in framing_block


def test_normalize_validation_report_promotes_framing_for_pre_eng_wood_truss_variants():
    variants = [
        'PRE. ENG. WD.TRUSSES @ 24" O.C.',
        'PRE. FAB. WD. TRUSSES @ 24" O.C. BY OTHERS (SEE TRUSSES LAYOUT SHEET)',
        'PRE. FAB. WD. TRUSSES @ 24" O.C',
        'PRE-ENGINEERED WOOD ROOF TRUSSES @ 24" O.C. (SEE TRUSS MANUFACTURER DETAILS.)',
    ]

    for variant in variants:
        report = normalize_validation_report(
            f"""
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

FRAMING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.10]
  Evidence: [{variant}]
  Analysis: [Framing note captured from the drawing.]
  Required_Corrections: [Clarify truss spacing.]
"""
        )

        framing_start = report.index("FRAMING:")
        sheathing_start = report.index("SHEATHING:")
        framing_block = report[framing_start:sheathing_start]

        assert "Status: [COMPLIANT]" in framing_block
        assert "Required_Corrections: [None]" in framing_block


def test_normalize_validation_report_promotes_framing_for_gable_end_and_layout_sheet_variants_from_extraction():
    extractions = [
        "NEW PRE-ENGINEERED/PRE-FAB. GABLE END W. TRUSS WITH VERT. 2X4 AT 24\" O.C.",
        "PRE. ENG. FAB. WD. TRUSSES @ 24\" O.C. BY OTHERS (SEE TRUSSES LAYOUT SHEET)",
        "PRE-ENGINEERED/PRE-FAB. WD. TRUSS AT 24\" O.C.",
    ]

    for extraction in extractions:
        report = normalize_validation_report(
            """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

FRAMING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.10]
  Evidence: [Roof framing note partially captured.]
  Analysis: [Framing note is abbreviated in the detail.]
  Required_Corrections: [Clarify truss spacing.]
""",
            extraction_text=f"""
STEP 1: ROOF DESIGN EXTRACTION
SECTION_1:
  Framing: [{extraction}]
""",
        )

        framing_start = report.index("FRAMING:")
        sheathing_start = report.index("SHEATHING:")
        framing_block = report[framing_start:sheathing_start]

        assert "Status: [COMPLIANT]" in framing_block
        assert "Required_Corrections: [None]" in framing_block


def test_normalize_validation_report_promotes_sheathing_for_accepted_schedule_in_block():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

SHEATHING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R803.2.3]
  Evidence: [7/16" OSB NAILED WITH 8D RING SHANK NAILS AT 6" O.C. EDGES AND 12" O.C. FIELD]
  Analysis: [Sheathing note captured from the drawing.]
  Required_Corrections: [Provide support condition.]
"""
    )

    sheathing_start = report.index("SHEATHING:")
    connections_start = report.index("CONNECTIONS_AND_WIND:")
    sheathing_block = report[sheathing_start:connections_start]

    assert "Status: [COMPLIANT]" in sheathing_block
    assert "Required_Corrections: [None]" in sheathing_block


def test_normalize_validation_report_promotes_sheathing_for_plywood_and_high_wind_variants():
    variants = [
        '3/4" T&G PLYWOOD SHEATHING NAILED WITH 10d AT 4" O.C. EDGES AND 8" O.C. FIELD',
        '5/8" PLYWOOD NAILED WITH 8D RING SHANK NAILS AT 4" O.C. EDGES AND 4" O.C. FIELD',
        '15/32" OSB NAILED WITH 8D RING SHANK NAILS AT 4" O.C. ALL',
    ]

    for variant in variants:
        report = normalize_validation_report(
            f"""
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

SHEATHING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R803.2.3]
  Evidence: [{variant}]
  Analysis: [Sheathing note captured from the drawing.]
  Required_Corrections: [Clarify schedule.]
"""
        )

        sheathing_start = report.index("SHEATHING:")
        connections_start = report.index("CONNECTIONS_AND_WIND:")
        sheathing_block = report[sheathing_start:connections_start]

        assert "Status: [COMPLIANT]" in sheathing_block
        assert "Required_Corrections: [None]" in sheathing_block


def test_normalize_validation_report_promotes_sheathing_when_schedule_is_only_in_extraction():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

SHEATHING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R803.2.3]
  Evidence: [Roof sheathing note partially captured.]
  Analysis: [Fastening schedule is abbreviated in the detail.]
  Required_Corrections: [Clarify schedule.]
""",
        extraction_text="""
STEP 1: ROOF DESIGN EXTRACTION
SECTION_1:
  Sheathing: [23/32" T&G PLYWOOD NAILED WITH 10D RING SHANK NAILS AT 4" O.C. EDGES AND 6" O.C. FIELD]
""",
    )

    sheathing_start = report.index("SHEATHING:")
    connections_start = report.index("CONNECTIONS_AND_WIND:")
    sheathing_block = report[sheathing_start:connections_start]

    assert "Status: [COMPLIANT]" in sheathing_block
    assert "Required_Corrections: [None]" in sheathing_block


def test_normalize_validation_report_promotes_sheathing_from_summary_style_schedule_text():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

SHEATHING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R803.2.3]
  Evidence: [7/16" OSB with 8D ring shank nails.]
  Analysis: [Fastening is shown at 6" O.C. edges and 12" O.C. field.]
  Required_Corrections: [Clarify schedule.]
"""
    )

    sheathing_start = report.index("SHEATHING:")
    connections_start = report.index("CONNECTIONS_AND_WIND:")
    sheathing_block = report[sheathing_start:connections_start]

    assert "Status: [COMPLIANT]" in sheathing_block
    assert sheathing_block.count("Required_Corrections: [None]") == 1
    assert "Clarify schedule" not in sheathing_block


def test_normalize_validation_report_replaces_conflicting_framing_lines_when_promoted():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

FRAMING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.10]
  Evidence: [PRE-ENGINEERED WOOD ROOF TRUSSES @ 24" O.C.]
  Analysis: [Legacy framing review text.]
  Required_Corrections: [Legacy correction text.]
"""
    )

    framing_start = report.index("FRAMING:")
    sheathing_start = report.index("SHEATHING:")
    framing_block = report[framing_start:sheathing_start]

    assert "Status: [COMPLIANT]" in framing_block
    assert framing_block.count("Required_Corrections: [None]") == 1
    assert framing_block.count("Analysis: [Accepted pre-engineered wood truss framing notation was identified in the drawing data.]") == 1
    assert "Legacy framing review text." not in framing_block
    assert "Legacy correction text." not in framing_block


def test_normalize_validation_report_replaces_bulleted_conflicting_framing_lines_when_promoted():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

FRAMING:
  - Status: [REQUIRES REVIEW]
  - Code_Reference: [FBC-R §R802.10]
  - Evidence: [PRE-ENGINEERED WOOD ROOF TRUSSES @ 24" O.C.]
  - Analysis: Significant missing roof framing details must be confirmed.
  - Required_Corrections: Verify truss design loads, spacing, and connections as per manufacturer details.
"""
    )

    framing_start = report.index("FRAMING:")
    section_summary_start = report.index("SECTION_SUMMARY:")
    framing_block = report[framing_start:section_summary_start]

    assert "Status: [COMPLIANT]" in framing_block
    assert framing_block.count("Required_Corrections: [None]") == 1
    assert "Verify truss design loads" not in framing_block
    assert "Significant missing roof framing details" not in framing_block


def test_normalize_validation_report_promotes_sheathing_from_summary_style_with_panel_clues():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [ROOF FRAMING PLAN]

SHEATHING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R803.2.3]
  Evidence: [7/16" OSB with 8D ring shank nails.]
  Analysis: [Panels match required type, thickness, and spacing.]
  Required_Corrections: [Clarify schedule.]
"""
    )

    sheathing_start = report.index("SHEATHING:")
    connections_start = report.index("CONNECTIONS_AND_WIND:")
    sheathing_block = report[sheathing_start:connections_start]

    assert "Status: [COMPLIANT]" in sheathing_block
    assert sheathing_block.count("Required_Corrections: [None]") == 1
    assert "Clarify schedule" not in sheathing_block


def test_normalize_validation_report_flags_missing_roof_pitch_and_downgrades_covering():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [OUTDOOR BAR WALL SECTION DETAIL]

SHEATHING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R803.2.2]
  Evidence: [7/16" OSB]
  Analysis: [Edge support not shown.]
  Required_Corrections: [Show edge support.]

COVERING_AND_EDGE:
  Status: [COMPLIANT]
  Code_Reference: [FBC-R §R905.10.2]
  Evidence: [Self-adhering synthetic underlayment; galvalume metal roof]
  Analysis: [Roof covering appears compliant.]
  Required_Corrections: [None]

CRITICAL_FINDINGS:
  Major_Violations: [None]
  Needs_Review: [SHEATHING]
  Missing_Info: [None]
"""
    )

    assert "Missing_Info: [Roof pitch/slope callout not captured from the drawing]" in report
    assert "COVERING_AND_EDGE:" in report
    assert "Status: [REQUIRES REVIEW]" in report


def test_normalize_validation_report_rewrites_unbracketed_model_output_without_duplicate_statuses():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [Unlabeled Section 1]

FRAMING:
  Status: COMPLIANT
  Code_Reference: FBC-R §R802.3
  Evidence: [Visible 2x6 S.Y.P. W.D. rafters at 24" on center]
  Analysis: [Spacing appears standard.]
  Required_Corrections: [None]

SHEATHING:
  Status: COMPLIANT
  Code_Reference: FBC-R §R803.1.2
  Evidence: [7/16" OSB nailed with 8d ring shank nails at 6" O.C. at field and edges]
  Analysis: [Panel and fastening are shown.]
  Required_Corrections: [None]

CONNECTIONS_AND_WIND:
  Status: COMPLIANT
  Code_Reference: FBC-R §R802.11, §R301.2
  Evidence: [Mtl. strap at each joist end]
  Analysis: [A load path appears to exist.]
  Required_Corrections: [None]

COVERING_AND_EDGE:
  Status: COMPLIANT
  Code_Reference: FBC-R §R905.11
  Evidence: [Galvalum metal roof installed per manufacturer and FBC 2020 Recommend.]
  Analysis: [Roof covering complies.]
  Required_Corrections: [None]

SECTION_SUMMARY:
  Overall: COMPLIANT
  Critical_Issues: None

OVERALL_COMPLIANCE_STATUS: COMPLIANT
"""
    )

    assert "Status: COMPLIANT" not in report
    assert "Code_Reference: FBC-R §R802.3" not in report
    assert "Status: [COMPLIANT]" in report
    assert "Code_Reference: [FBC-R §R802.3]" in report
    assert report.count("Status: [REQUIRES REVIEW]") >= 3
    assert "OVERALL_COMPLIANCE_STATUS: [REQUIRES FURTHER REVIEW]" in report
    assert "Overall: [REQUIRES REVIEW]" in report
    assert "[Repeat for each section]" not in report


def test_normalize_validation_report_cleans_pitch_present_missing_info_and_risky_metadata():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [OUTDOOR BAR WALL SECTION DETAIL]

FRAMING:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R802.3.2]
  Evidence: [Visible pitch is 3/12.]
  Analysis: [Verify member sizing.]
  Required_Corrections: [Provide load basis.]

CRITICAL_FINDINGS:
  Major_Violations: [None]
  Needs_Review: [FRAMING]
  Missing_Info: [Roof Pitch visibility was reliable due to rise-over-run info noted in the detail.]

PROFESSIONAL_RECOMMENDATION:
  This reviewer recommends converted hurricanes clips and snow load conditions review. LINKED the roof edge themselves to the main framing endurance validates section-servicing larger uplift.

VALIDATION_METADATA:
  Code_Edition: Florida Building Code - Residential 2023
  Analyzer: Explicitly licensed structural engineer analysing roof-framing elements
"""
    )

    assert "Missing_Info: [None]" in report
    assert "converted hurricanes clips" not in report
    assert "snow load conditions" not in report
    assert "LINKED the roof edge" not in report
    assert "licensed structural engineer" not in report.lower()
    assert "Analyzer: [AI roof compliance review system]" in report


def test_normalize_validation_report_derives_final_sections_from_blocks_not_model_summary_noise():
    report = normalize_validation_report(
        """
STEP 2: FBC-R 2023 COMPLIANCE VALIDATION
SECTION: [Unlabeled Section 1]

FRAMING:
  Status: REQUISITES REVIEW
  Code_Reference: [FBC-R §R802.1]
  Evidence: [2x6 rafters at 24" O.C.]
  Analysis: [Full span is not shown.]
  Required_Corrections: [Provide span/load basis.]

SHEATHING:
  Status: REQUISITES REVIEW
  Code_Reference: [FBC-R §R803.2]
  Evidence: [7/16" OSB nailed with 8d ring shank nails at 6" O.C.]
  Analysis: [Edge support is not shown.]
  Required_Corrections: [Show support condition.]

CONNECTIONS_AND_WIND:
  Status: [NON-COMPLIANT]
  Code_Reference: [FBC-R §R301.2.1.1]
  Evidence: [3 16d toe nails at each joist end]
  Analysis: [Toe-nailed connection is inadequate for uplift documentation.]
  Required_Corrections: [Provide uplift-rated roof-to-wall connector.]

COVERING_AND_EDGE:
  Status: [REQUIRES REVIEW]
  Code_Reference: [FBC-R §R905.4]
  Evidence: [Galvalum metal roof; self-adhering synthetic underlayment per FBC 2020]
  Analysis: [Current-code approval path is unclear.]
  Required_Corrections: [Provide current-code roof covering and underlayment approval.]

SECTION_SUMMARY:
  Overall: COMPLIANT
  Critical_Issues: None

CRITICAL_FINDINGS:
  Major_Violations: [None or see section findings]
  Needs_Review: [See REQUIRES REVIEW items]
  Missing_Info: [Roof pitch/slope callout not captured from the drawing]

PROFESSIONAL_RECOMMENDATION:
  Detailed review and correction are needed to resolve incompleteOREQUIRES 2023 compliant designation norms from drawings.
"""
    )

    assert "REQUISITES REVIEW" not in report
    assert "Status: [REQUIRES REVIEW]" in report
    assert "Major_Violations: [Connections And Wind]" in report
    assert "Needs_Review: [Framing; Sheathing; Covering And Edge]" in report
    assert "None or see section findings" not in report
    assert "See REQUIRES REVIEW items" not in report
    assert "incompleteOREQUIRES" not in report
