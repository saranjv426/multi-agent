"""
Validation report formatter/normalizer for consistent roof compliance output.
"""

from __future__ import annotations

import re
from typing import Dict, List


REQUIRED_BLOCKS = [
    "FRAMING",
    "SHEATHING",
    "CONNECTIONS_AND_WIND",
    "COVERING_AND_EDGE",
]

ALLOWED_REFERENCES: Dict[str, tuple[str, ...]] = {
    "FRAMING": ("R802",),
    "SHEATHING": ("R803",),
    "CONNECTIONS_AND_WIND": ("R802.11", "R301"),
    "COVERING_AND_EDGE": ("R905", "R903"),
}

STATUS_PATTERN = re.compile(
    r"Status:\s*(?:\[(COMPLIANT|NON-COMPLIANT|REQUIRES REVIEW|REQUIRES FURTHER REVIEW)\]|(COMPLIANT|NON-COMPLIANT|REQUIRES REVIEW|REQUIRES FURTHER REVIEW))",
    re.IGNORECASE,
)
OVERALL_PATTERN = re.compile(
    r"OVERALL_COMPLIANCE_STATUS:\s*(?:\[(COMPLIANT|NON-COMPLIANT|REQUIRES REVIEW|REQUIRES FURTHER REVIEW)\]|(COMPLIANT|NON-COMPLIANT|REQUIRES REVIEW|REQUIRES FURTHER REVIEW))",
    re.IGNORECASE,
)
SECTION_SUMMARY_PATTERN = re.compile(
    r"Overall:\s*(?:\[(COMPLIANT|NON-COMPLIANT|REQUIRES REVIEW|REQUIRES FURTHER REVIEW)\]|(COMPLIANT|NON-COMPLIANT|REQUIRES REVIEW|REQUIRES FURTHER REVIEW))",
    re.IGNORECASE,
)
CODE_REFERENCE_PATTERN = re.compile(r"Code_Reference:\s*(?:\[(.*?)\]|([^\n\r]+))", re.IGNORECASE)
EVIDENCE_PATTERN = re.compile(r"Evidence:\s*\[(.*?)\]", re.IGNORECASE | re.DOTALL)
ANALYSIS_PATTERN = re.compile(r"Analysis:\s*\[(.*?)\]", re.IGNORECASE | re.DOTALL)
REQUIRED_CORRECTIONS_PATTERN = re.compile(r"Required_Corrections:\s*\[(.*?)\]", re.IGNORECASE | re.DOTALL)
MISSING_INFO_PATTERN = re.compile(r"Missing_Info:\s*\[(.*?)\]", re.IGNORECASE | re.DOTALL)
REQUIRED_CORRECTIONS_LINE_PATTERN = re.compile(
    r"^(\s*Required_Corrections:\s*)(?:\[(.*?)\]|([^\n\r]+))\s*$",
    re.IGNORECASE | re.MULTILINE,
)
ANALYSIS_LINE_PATTERN = re.compile(
    r"^(\s*Analysis:\s*)(?:\[(.*?)\]|([^\n\r]+))\s*$",
    re.IGNORECASE | re.MULTILINE,
)

FRAMING_COMPLIANT_PATTERNS = (
    re.compile(r"\bNEW PRE ENGINEERED PRE FAB GABLE END W TRUSS WITH VERT 2X4 AT 24 OC\b"),
)

SHEATHING_ACCEPTED_TEXT_PATTERNS = (
    re.compile(r'\b7 8 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC (?:AT )?EDGES AND 6 OC FIELD\b'),
    re.compile(r'\b7 8 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC (?:AT )?EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b1 2 PLYWOOD NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC (?:AT )?EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b3 4 T G PLYWOOD (?:SHEATHING )?NAIL(?:ED)? WITH 10D(?: RING SHANK NAILS?)? AT 4 OC EDGES AND 8 OC FIELD\b'),
    re.compile(r'\b7 16 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b7 16 OSB NAIL(?:ED)? WITH 8D COMMON NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b15 32 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b15 32 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 4 OC EDGES AND 6 OC FIELD\b'),
    re.compile(r'\b19 32 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b23 32 OSB NAIL(?:ED)? WITH 10D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b7 8 OSB NAIL(?:ED)? WITH 10D RING SHANK NAILS? AT 4 OC EDGES AND 6 OC FIELD\b'),
    re.compile(r'\b1 1 8 OSB NAIL(?:ED)? WITH 10D RING SHANK NAILS? AT 4 OC EDGES AND 6 OC FIELD\b'),
    re.compile(r'\b3 8 PLYWOOD NAIL(?:ED)? WITH 8D COMMON NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b7 16 PLYWOOD NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b15 32 PLYWOOD NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b1 2 PLYWOOD NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 4 OC EDGES AND 8 OC FIELD\b'),
    re.compile(r'\b19 32 PLYWOOD NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b5 8 PLYWOOD NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b5 8 PLYWOOD NAIL(?:ED)? WITH 10D RING SHANK NAILS? AT 4 OC EDGES AND 6 OC FIELD\b'),
    re.compile(r'\b3 4 PLYWOOD NAIL(?:ED)? WITH 10D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b3 4 T G PLYWOOD NAIL(?:ED)? WITH 10D RING SHANK NAILS? AT 6 OC EDGES AND 12 OC FIELD\b'),
    re.compile(r'\b23 32 T G PLYWOOD NAIL(?:ED)? WITH 10D RING SHANK NAILS? AT 4 OC EDGES AND 6 OC FIELD\b'),
    re.compile(r'\b1 T G PLYWOOD NAIL(?:ED)? WITH 10D RING SHANK NAILS? AT 4 OC EDGES AND 6 OC FIELD\b'),
    re.compile(r'\b1 1 8 T G PLYWOOD NAIL(?:ED)? WITH 10D RING SHANK NAILS? AT 4 OC EDGES AND 6 OC FIELD\b'),
    re.compile(r'\b7 16 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 4 OC EDGES AND 4 OC FIELD\b'),
    re.compile(r'\b15 32 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 4 OC ALL\b'),
    re.compile(r'\b5 8 PLYWOOD NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 4 OC EDGES AND 4 OC FIELD\b'),
    re.compile(r'\b7 8 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 4 OC ALL\b'),
    re.compile(r'\b19 32 OSB NAIL(?:ED)? WITH 8D RING SHANK NAILS? AT 4 OC EDGES AND 4 OC FIELD\b'),
)


def _normalize_status(raw: str) -> str:
    value = raw.strip().upper()
    value = value.replace("REQUISITES REVIEW", "REQUIRES REVIEW")
    value = value.replace("REQUISITE REVIEW", "REQUIRES REVIEW")
    if value == "REQUIRES FURTHER REVIEW":
        return "REQUIRES REVIEW"
    return value


def _status_from_match(match: re.Match[str]) -> str:
    return match.group(1) or match.group(2) or ""


def _set_status(block_text: str, status: str) -> str:
    replacement = f"Status: [{status}]"
    if STATUS_PATTERN.search(block_text):
        return STATUS_PATTERN.sub(replacement, block_text, count=1)
    return f"{block_text.rstrip()}\n  Status: [{status}]\n  Code_Reference: [Exact citation verification needed]"


def _set_required_corrections(block_text: str, value: str) -> str:
    replacement = f"\\1[{value}]"
    if REQUIRED_CORRECTIONS_LINE_PATTERN.search(block_text):
        return REQUIRED_CORRECTIONS_LINE_PATTERN.sub(replacement, block_text, count=1)
    return f"{block_text.rstrip()}\n  Required_Corrections: [{value}]"


def _set_analysis(block_text: str, value: str) -> str:
    replacement = f"\\1[{value}]"
    if ANALYSIS_LINE_PATTERN.search(block_text):
        return ANALYSIS_LINE_PATTERN.sub(replacement, block_text, count=1)
    return f"{block_text.rstrip()}\n  Analysis: [{value}]"


def _remove_field_line(block_text: str, field_name: str) -> str:
    return re.sub(
        rf"^\s*(?:[-*]\s*)?{field_name}:\s*(?:\[(.*?)\]|([^\n\r]+))\s*$\n?",
        "",
        block_text,
        count=0,
        flags=re.IGNORECASE | re.MULTILINE,
    ).rstrip()


def _extract_block(lines: List[str], block_name: str) -> tuple[int, int]:
    start = -1
    for idx, line in enumerate(lines):
        if line.strip() == f"{block_name}:":
            start = idx
            break
    if start == -1:
        return -1, -1

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.endswith(":") and stripped in [f"{b}:" for b in REQUIRED_BLOCKS + ["SECTION_SUMMARY"]]:
            end = idx
            break
    return start, end


def _sanitize_code_reference(block_name: str, block_text: str) -> str:
    code_ref_match = CODE_REFERENCE_PATTERN.search(block_text)
    if not code_ref_match:
        return _set_status(block_text, "REQUIRES REVIEW")

    code_ref = (code_ref_match.group(1) or code_ref_match.group(2) or "").strip()
    upper_ref = code_ref.upper()
    allowed = ALLOWED_REFERENCES.get(block_name, ())
    is_allowed = any(token in upper_ref for token in allowed)

    # Guardrail: R502 (floor framing) should not be used for roof validation sections.
    has_known_wrong_ref = "R502" in upper_ref

    if is_allowed and not has_known_wrong_ref:
        return block_text

    block_text = _set_status(block_text, "REQUIRES REVIEW")
    return re.sub(
        r"Code_Reference:\s*(?:\[(.*?)\]|([^\n\r]+))",
        "Code_Reference: [Exact citation verification needed (roof scope: R802/R803/R905/R301/R806)]",
        block_text,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _canonicalize_model_output(text: str) -> str:
    """Normalize common unbracketed model fields into the bracketed report format."""
    text = re.sub(r"^\[Repeat for each section\]\s*$", "", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"\bREQUISITES REVIEW\b", "REQUIRES REVIEW", text, flags=re.IGNORECASE)
    text = re.sub(r"\bREQUISITE REVIEW\b", "REQUIRES REVIEW", text, flags=re.IGNORECASE)

    def canonicalize_status(label_pattern: str, source: str) -> str:
        regex = re.compile(
            rf"^(\s*{label_pattern}\s*:\s*)(?:\[(COMPLIANT|NON-COMPLIANT|REQUIRES REVIEW|REQUIRES FURTHER REVIEW)\]|(COMPLIANT|NON-COMPLIANT|REQUIRES REVIEW|REQUIRES FURTHER REVIEW))\s*$",
            re.IGNORECASE | re.MULTILINE,
        )
        return regex.sub(lambda m: f"{m.group(1)}[{(m.group(2) or m.group(3)).upper()}]", source)

    text = canonicalize_status("Status", text)
    text = canonicalize_status("Overall", text)
    text = canonicalize_status("OVERALL_COMPLIANCE_STATUS", text)
    text = re.sub(
        r"^(\s*Code_Reference:\s*)(?!\[)([^\n\r]+)$",
        lambda m: f"{m.group(1)}[{m.group(2).strip()}]",
        text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    text = re.sub(
        r"(Code_Reference:\s*)\[\[(.*?)\]\]",
        r"\1[\2]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(r"Code_Reference:\[", "Code_Reference: [", text, flags=re.IGNORECASE)
    return text


def _rewrite_section_summary(report_text: str) -> str:
    statuses = [_normalize_status(_status_from_match(m)) for m in STATUS_PATTERN.finditer(report_text)]
    section_overall = "COMPLIANT"
    if "NON-COMPLIANT" in statuses:
        section_overall = "NON-COMPLIANT"
    elif "REQUIRES REVIEW" in statuses:
        section_overall = "REQUIRES REVIEW"

    if "SECTION_SUMMARY:" not in report_text:
        return report_text

    if SECTION_SUMMARY_PATTERN.search(report_text):
        report_text = SECTION_SUMMARY_PATTERN.sub(f"Overall: [{section_overall}]", report_text, count=1)
    return report_text


def _strip_generated_summary_sections(report_text: str) -> str:
    markers = [
        "CRITICAL_FINDINGS:",
        "REQUIRED_CORRECTIONS:",
        "RECOMMENDED CORRECTIONS:",
        "PROFESSIONAL_RECOMMENDATION:",
        "VALIDATION_METADATA:",
    ]
    cut_points = [report_text.find(marker) for marker in markers if marker in report_text]
    if not cut_points:
        return report_text
    return report_text[:min(cut_points)].rstrip()


def _rewrite_section_summary_block(report_text: str, overall: str, critical_issues: str) -> str:
    replacement_lines = [
        "SECTION_SUMMARY:",
        f"  Overall: [{overall}]",
        f"  Critical_Issues: [{critical_issues}]",
    ]
    lines = report_text.splitlines()
    start = next((idx for idx, line in enumerate(lines) if line.strip() == "SECTION_SUMMARY:"), -1)
    if start == -1:
        return report_text.rstrip() + "\n" + "\n".join(replacement_lines)

    end = len(lines)
    for idx in range(start + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("OVERALL_COMPLIANCE_STATUS:") or stripped in {
            "CRITICAL_FINDINGS:",
            "REQUIRED_CORRECTIONS:",
            "RECOMMENDED CORRECTIONS:",
            "PROFESSIONAL_RECOMMENDATION:",
            "VALIDATION_METADATA:",
        }:
            end = idx
            break

    lines[start:end] = replacement_lines
    return "\n".join(lines)


def _default_block(block_name: str) -> str:
    labels = {
        "FRAMING": "roof framing",
        "SHEATHING": "roof sheathing",
        "CONNECTIONS_AND_WIND": "roof connections and wind load path",
        "COVERING_AND_EDGE": "roof covering and edge details",
    }
    label = labels.get(block_name, block_name.lower().replace("_", " "))
    return "\n".join(
        [
            f"{block_name}:",
            "  Status: [REQUIRES REVIEW]",
            "  Code_Reference: [Exact citation verification needed (roof scope: R802/R803/R905/R301/R806)]",
            f"  Evidence: [{label} information was not captured in the validation response.]",
            f"  Analysis: [The {label} item must be verified from the drawing set.]",
            f"  Required_Corrections: [Provide code-citable {label} information.]",
        ]
    )


def _ensure_required_blocks(report_text: str) -> str:
    lines = report_text.splitlines()
    for block_name in REQUIRED_BLOCKS:
        start, _end = _extract_block(lines, block_name)
        if start != -1:
            continue

        insert_at = len(lines)
        later_blocks = REQUIRED_BLOCKS[REQUIRED_BLOCKS.index(block_name) + 1 :] + [
            "SECTION_SUMMARY",
        ]
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("OVERALL_COMPLIANCE_STATUS:") or stripped in {
                f"{name}:" for name in later_blocks
            } or stripped in {
                "CRITICAL_FINDINGS:",
                "REQUIRED_CORRECTIONS:",
                "RECOMMENDED CORRECTIONS:",
                "PROFESSIONAL_RECOMMENDATION:",
                "VALIDATION_METADATA:",
            }:
                insert_at = idx
                break

        block_lines = [""] + _default_block(block_name).splitlines()
        lines[insert_at:insert_at] = block_lines

    return "\n".join(lines).strip()


def _block_status(block_text: str) -> str:
    match = STATUS_PATTERN.search(block_text)
    return _normalize_status(_status_from_match(match)) if match else "REQUIRES REVIEW"


def _block_code_reference(block_text: str) -> str:
    match = CODE_REFERENCE_PATTERN.search(block_text)
    value = (match.group(1) or match.group(2) or "").strip() if match else ""
    return value or "Exact citation verification needed (roof scope: R802/R803/R905/R301/R806)"


def _block_field(pattern: re.Pattern[str], block_text: str) -> str:
    value = _extract_bracketed_value(pattern, block_text)
    if value:
        return value
    fallback = re.search(pattern.pattern.replace(r"\[(.*?)\]", r"(.*)"), block_text, re.IGNORECASE | re.DOTALL)
    return fallback.group(1).strip() if fallback else ""


def _collect_block_data(lines: List[str]) -> List[Dict[str, str]]:
    blocks: List[Dict[str, str]] = []
    for block_name in REQUIRED_BLOCKS:
        start, end = _extract_block(lines, block_name)
        if start == -1:
            continue
        block_text = "\n".join(lines[start:end]).strip()
        blocks.append(
            {
                "name": block_name,
                "text": block_text,
                "status": _block_status(block_text),
                "code_reference": _block_code_reference(block_text),
                "evidence": _block_field(EVIDENCE_PATTERN, block_text) or "not shown",
                "analysis": _block_field(ANALYSIS_PATTERN, block_text) or "not shown",
                "required_corrections": _block_field(REQUIRED_CORRECTIONS_PATTERN, block_text) or "None",
            }
        )
    return blocks


def _section_summary_status(blocks: List[Dict[str, str]]) -> str:
    statuses = [block["status"] for block in blocks]
    if "NON-COMPLIANT" in statuses:
        return "NON-COMPLIANT"
    if "REQUIRES REVIEW" in statuses:
        return "REQUIRES REVIEW"
    return "COMPLIANT"


def _section_summary_issues(blocks: List[Dict[str, str]]) -> str:
    issues = [block["name"] for block in blocks if block["status"] != "COMPLIANT"]
    return ", ".join(issues) if issues else "None"


def _normalize_issue_name(name: str) -> str:
    return name.replace("_", " ").title()


def _derive_missing_info(blocks: List[Dict[str, str]], report_text: str) -> str:
    items: List[str] = []
    if not _report_mentions_roof_pitch(report_text):
        items.append("Roof pitch/slope callout not captured from the drawing")

    deduped: List[str] = []
    seen = set()
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    return "; ".join(deduped) if deduped else "None"


def _derive_critical_findings(blocks: List[Dict[str, str]], report_text: str) -> str:
    major = [_normalize_issue_name(block["name"]) for block in blocks if block["status"] == "NON-COMPLIANT"]
    review = [_normalize_issue_name(block["name"]) for block in blocks if block["status"] == "REQUIRES REVIEW"]
    missing = _derive_missing_info(blocks, report_text)
    return (
        "\nCRITICAL_FINDINGS:\n"
        f"  Major_Violations: [{'; '.join(major) if major else 'None'}]\n"
        f"  Needs_Review: [{'; '.join(review) if review else 'None'}]\n"
        f"  Missing_Info: [{missing}]\n"
    )


def _derive_required_corrections(blocks: List[Dict[str, str]]) -> str:
    high_priority: List[str] = []
    recommended: List[str] = []
    for block in blocks:
        correction = block["required_corrections"].strip()
        if not correction or correction.lower() == "none":
            continue
        bucket = high_priority if block["status"] == "NON-COMPLIANT" else recommended
        bucket.append(correction)

    if not high_priority:
        high_priority = ["Resolve all NON-COMPLIANT items with code-citable roof details."]
    if not recommended:
        recommended = ["Add explicit design loads, spans, wind inputs, and connector ratings."]

    return (
        "\nREQUIRED_CORRECTIONS:\n"
        f"  High_Priority: [{'; '.join(high_priority)}]\n"
        f"  Recommended: [{'; '.join(recommended)}]\n"
    )


def _derive_professional_recommendation(blocks: List[Dict[str, str]], overall: str, report_text: str) -> str:
    if overall == "NON-COMPLIANT":
        lead = "The detail is not permit-ready because at least one roof-safety item is non-compliant."
    elif overall == "REQUIRES FURTHER REVIEW":
        lead = "The detail needs additional roof documentation before permit readiness can be determined."
    else:
        lead = "The visible roof detail appears generally consistent with the reviewed code scope."

    focus_items = [_normalize_issue_name(block["name"]) for block in blocks if block["status"] != "COMPLIANT"]
    focus_text = ", ".join(focus_items[:3]) if focus_items else "roof framing, sheathing, and covering coordination"
    pitch_note = (
        " Roof pitch is captured in the drawing."
        if _report_mentions_roof_pitch(report_text)
        else " Roof pitch still needs to be shown explicitly in the permit set."
    )
    recommendation = (
        f"{lead} Focus the next revision on {focus_text}. "
        "Use code-citable product, fastening, and connector information rather than narrative assumptions."
        f"{pitch_note}"
    )
    return f"\nPROFESSIONAL_RECOMMENDATION:\n  {recommendation}\n"


def _derive_validation_metadata(existing_report: str) -> str:
    confidence = "MEDIUM"
    if "NON-COMPLIANT" in existing_report and "REQUIRES REVIEW" not in existing_report:
        confidence = "MEDIUM"
    elif "REQUIRES REVIEW" in existing_report:
        confidence = "MEDIUM"
    return (
        "\nVALIDATION_METADATA:\n"
        "  Code_Edition: Florida Building Code - Residential 2023\n"
        "  Chapters: 8 (Roof-Ceiling), 9 (Roof Assemblies)\n"
        "  Sections_Analyzed: [1]\n"
        f"  Confidence: [{confidence}]\n"
        "  Analyzer: [AI roof compliance review system]\n"
    )


def _extract_bracketed_value(pattern: re.Pattern[str], block_text: str) -> str:
    match = pattern.search(block_text)
    return match.group(1).strip() if match else ""


def _mentions_any(text: str, needles: tuple[str, ...]) -> bool:
    upper_text = text.upper()
    return any(needle in upper_text for needle in needles)


def _canonicalize_for_phrase_match(text: str) -> str:
    upper = text.upper()
    upper = upper.replace("O.C.", "OC")
    upper = upper.replace("O.C", "OC")
    upper = upper.replace("ON CENTER", "OC")
    upper = upper.replace('24"', "24")
    upper = upper.replace("24 INCH", "24")
    upper = upper.replace("24-INCH", "24")
    upper = upper.replace("24 IN", "24")
    upper = upper.replace("12 INCH", "12")
    upper = upper.replace("12-INCH", "12")
    upper = upper.replace("12 IN", "12")
    upper = upper.replace("8 INCH", "8")
    upper = upper.replace("8-INCH", "8")
    upper = upper.replace("8 IN", "8")
    upper = upper.replace("6 INCH", "6")
    upper = upper.replace("6-INCH", "6")
    upper = upper.replace("6 IN", "6")
    upper = upper.replace("4 INCH", "4")
    upper = upper.replace("4-INCH", "4")
    upper = upper.replace("4 IN", "4")
    upper = upper.replace("2'", "2")
    upper = upper.replace("1-1/8", "1 1 8")
    upper = upper.replace("1 1/8", "1 1 8")
    upper = upper.replace("1-1-8", "1 1 8")
    upper = upper.replace("1-1/8\"", "1 1 8")
    upper = upper.replace("7/8", "7 8")
    upper = upper.replace("7/16", "7 16")
    upper = upper.replace("15/32", "15 32")
    upper = upper.replace("19/32", "19 32")
    upper = upper.replace("23/32", "23 32")
    upper = upper.replace("3/8", "3 8")
    upper = upper.replace("1/2", "1 2")
    upper = upper.replace("5/8", "5 8")
    upper = upper.replace("3/4", "3 4")
    upper = upper.replace("PRE-ENGINEERED", "PRE ENGINEERED")
    upper = upper.replace("PREENGINEERED", "PRE ENGINEERED")
    upper = upper.replace("PRE-ENG.", "PRE ENG")
    upper = upper.replace("PRE. ENG.", "PRE ENG")
    upper = upper.replace("PRE ENG.", "PRE ENG")
    upper = upper.replace("PRE-ENG", "PRE ENG")
    upper = upper.replace("PRE-FAB.", "PRE FAB")
    upper = upper.replace("PRE/FAB.", "PRE FAB")
    upper = upper.replace("PRE-FAB", "PRE FAB")
    upper = upper.replace("PREFAB", "PRE FAB")
    upper = upper.replace("FAB.", "FAB")
    upper = upper.replace("ENGR", "ENGINEER")
    upper = upper.replace("ENGINEERED", "ENGINEER")
    upper = upper.replace("ENGINEERING", "ENGINEER")
    upper = upper.replace("WD.", "WD")
    upper = upper.replace("WD/TRUSS", "WD TRUSS")
    upper = upper.replace("WD TRUSS", "WD TRUSS")
    upper = upper.replace("WOOD", "WD")
    upper = upper.replace("TIMBER", "WD")
    upper = upper.replace("PLYWD", "PLYWOOD")
    upper = upper.replace("PLY WD", "PLYWOOD")
    upper = upper.replace("W.", "W")
    upper = upper.replace("ORIENTED STRAND BOARD", "OSB")
    upper = upper.replace("STRAND BOARD", "OSB")
    upper = upper.replace("TRUSSES", "TRUSS")
    upper = upper.replace("RING-SHANK", "RING SHANK")
    upper = upper.replace("SCREW-SHANK", "SCREW SHANK")
    upper = upper.replace("SPIRAL/SCREW SHANK", "SCREW SHANK")
    upper = upper.replace("TONGUE AND GROOVE", "T G")
    upper = upper.replace("T&G", "T G")
    upper = re.sub(r"[^A-Z0-9]+", " ", upper)
    upper = upper.replace("WDTRUSS", "WD TRUSS")
    upper = upper.replace("WTRUSS", "W TRUSS")
    return re.sub(r"\s+", " ", upper).strip()


def _has_wood_truss_spacing(tokens: set[str]) -> bool:
    has_truss = "TRUSS" in tokens
    has_wood_reference = any(token in tokens for token in ("WD", "W"))
    has_spacing = ("24" in tokens and "OC" in tokens) or ("2" in tokens and "OC" in tokens)
    return has_truss and has_wood_reference and has_spacing


def _has_pre_engineered_or_prefab_marker(tokens: set[str]) -> bool:
    has_pre = "PRE" in tokens
    has_engineered = "ENGINEER" in tokens or "ENG" in tokens
    has_prefab = "FAB" in tokens
    return (has_pre and has_engineered) or (has_pre and has_prefab)


def _has_accepted_framing_phrase(*texts: str) -> bool:
    combined = " ".join(text for text in texts if text)
    normalized = _canonicalize_for_phrase_match(combined)
    tokens = set(normalized.split())

    if any(pattern.search(normalized) for pattern in FRAMING_COMPLIANT_PATTERNS):
        return True

    if _has_wood_truss_spacing(tokens) and _has_pre_engineered_or_prefab_marker(tokens):
        return True

    by_others_layout_variant = (
        _has_wood_truss_spacing(tokens)
        and "PRE" in tokens
        and "FAB" in tokens
        and "BY" in tokens
        and "OTHERS" in tokens
        and "SEE" in tokens
        and "LAYOUT" in tokens
    )
    if by_others_layout_variant:
        return True

    return False


def _promote_framing_block_if_accepted(block_text: str, extraction_text: str) -> str:
    if not _has_accepted_framing_phrase(extraction_text, block_text):
        return block_text

    block_text = _set_status(block_text, "COMPLIANT")
    block_text = _remove_field_line(block_text, "Required_Corrections")
    block_text = _set_required_corrections(block_text, "None")
    block_text = _remove_field_line(block_text, "Analysis")
    block_text = _set_analysis(
        block_text,
        "Accepted pre-engineered wood truss framing notation was identified in the drawing data.",
    )

    return block_text


def _has_accepted_sheathing_phrase(*texts: str) -> bool:
    combined = " ".join(text for text in texts if text)
    normalized = _canonicalize_for_phrase_match(combined)
    tokens = normalized.split()
    token_set = set(tokens)

    if any(pattern.search(normalized) for pattern in SHEATHING_ACCEPTED_TEXT_PATTERNS):
        return True

    panel_tokens = (
        ("7", "16"),
        ("15", "32"),
        ("19", "32"),
        ("23", "32"),
        ("3", "8"),
        ("1", "2"),
        ("5", "8"),
        ("3", "4"),
        ("7", "8"),
        ("1", "1", "8"),
    )
    panel_type_present = "OSB" in token_set or "PLYWOOD" in token_set
    thickness_present = any(all(part in token_set for part in parts) for parts in panel_tokens)
    nail_size_present = "8D" in token_set or "10D" in token_set
    nail_type_present = any(
        marker in normalized
        for marker in (
            "COMMON NAIL",
            "RING SHANK",
            "SCREW SHANK",
            "SPIRAL",
            "SINKER",
        )
    )
    spacing_present = (
        "ALL" in token_set
        or {"4", "EDGES", "4", "FIELD"} <= token_set
        or {"4", "EDGES", "6", "FIELD"} <= token_set
        or {"4", "EDGES", "8", "FIELD"} <= token_set
        or {"6", "EDGES", "12", "FIELD"} <= token_set
    )
    summary_schedule_present = any(
        phrase in normalized
        for phrase in (
            "MATCH REQUIRED TYPE THICKNESS AND SPACING",
            "TYPE THICKNESS AND SPACING ARE SHOWN",
            "FASTENING DETAILS IS COMPLIANT",
            "FASTENING DETAILS ARE COMPLIANT",
            "PANELS MATCH REQUIRED TYPE THICKNESS AND SPACING",
            "PANEL TYPE THICKNESS AND SPACING",
        )
    )

    return (
        panel_type_present
        and thickness_present
        and nail_size_present
        and nail_type_present
        and (spacing_present or summary_schedule_present)
    )


def _promote_sheathing_block_if_accepted(block_text: str, extraction_text: str) -> str:
    if not _has_accepted_sheathing_phrase(extraction_text, block_text):
        return block_text

    block_text = _set_status(block_text, "COMPLIANT")
    block_text = _remove_field_line(block_text, "Required_Corrections")
    block_text = _set_required_corrections(block_text, "None")
    block_text = _remove_field_line(block_text, "Analysis")
    block_text = _set_analysis(
        block_text,
        "Accepted roof sheathing fastening schedule was identified in the drawing data.",
    )

    return block_text


def _guard_compliant_block(block_name: str, block_text: str, extraction_text: str = "") -> str:
    status_match = STATUS_PATTERN.search(block_text)
    if not status_match or _normalize_status(_status_from_match(status_match)) != "COMPLIANT":
        return block_text

    evidence = _extract_bracketed_value(EVIDENCE_PATTERN, block_text)
    analysis = _extract_bracketed_value(ANALYSIS_PATTERN, block_text)
    corrections = _extract_bracketed_value(REQUIRED_CORRECTIONS_PATTERN, block_text)
    combined = " ".join(part for part in (evidence, analysis, corrections, extraction_text) if part).upper()

    if block_name == "CONNECTIONS_AND_WIND":
        has_positive_connector = _mentions_any(
            combined,
            ("HURRICANE TIE", "HURRICANE TIES", "STRAP", "STRAPS", "SIMPSON", "CONNECTOR"),
        )
        has_capacity_or_wind_basis = _mentions_any(
            combined,
            ("UPLIFT", "CAPACITY", "RATED", "DESIGN WIND", "WIND SPEED", "EXPOSURE"),
        )
        toe_nails_only = "TOE NAIL" in combined and not has_capacity_or_wind_basis
        if toe_nails_only or not (has_positive_connector and has_capacity_or_wind_basis):
            return _set_status(block_text, "REQUIRES REVIEW")

    if block_name == "COVERING_AND_EDGE":
        references_old_code = _mentions_any(combined, ("FBC 2020", "FBC-R 2020"))
        missing_approval = _mentions_any(
            combined,
            ("NOT SHOWN", "NOT PROVIDED", "UNSPECIFIED", "APPROVAL NOT SHOWN", "PRODUCT APPROVAL"),
        )
        low_slope = _mentions_any(combined, ("1/2:12", "0.5:12", "LOW SLOPE", "LOW-SLOPE"))
        if references_old_code or missing_approval or low_slope:
            return _set_status(block_text, "REQUIRES REVIEW")

    if block_name == "SHEATHING":
        if (
            "ACCEPTED ROOF SHEATHING FASTENING SCHEDULE WAS IDENTIFIED IN THE DRAWING DATA" in combined
            or _has_accepted_sheathing_phrase(combined)
        ):
            return block_text
        has_panel_thickness = _mentions_any(
            combined,
            ("OSB", "PLYWOOD", '7/16"', '15/32"', '19/32"', '5/8"', '23/32"'),
        )
        has_fastener_schedule = _mentions_any(
            combined,
            ("NAIL", "NAILS", "8D", "RING SHANK", '6" O.C.', '6 INCHES O.C.', '4" O.C.', '12" O.C.'),
        )
        has_support_context = _mentions_any(
            combined,
            ("SPAN", "EDGE SUPPORT", "H-CLIP", "RAFTERS", "TRUSSES", "24\" O.C.", "16\" O.C.", "ON CENTER"),
        )
        if not (has_panel_thickness and has_fastener_schedule and has_support_context):
            return _set_status(block_text, "REQUIRES REVIEW")

    return block_text


def _report_mentions_roof_pitch(report_text: str) -> bool:
    return bool(
        re.search(r"Roof_Pitch:\s*\[(?!not shown\])[^]]+\]", report_text, re.IGNORECASE)
        or re.search(r"\b\d+\s*[:/]\s*12\b", report_text, re.IGNORECASE)
    )


def _ensure_missing_info_item(report_text: str, item: str) -> str:
    missing_info_match = MISSING_INFO_PATTERN.search(report_text)
    if missing_info_match:
        current = missing_info_match.group(1).strip()
        if item.lower() in current.lower():
            return report_text
        if current.lower() == "none":
            replacement = item
        else:
            replacement = f"{current}; {item}"
        return MISSING_INFO_PATTERN.sub(f"Missing_Info: [{replacement}]", report_text, count=1)

    insertion = f"\nCRITICAL_FINDINGS:\n  Major_Violations: [None or see section findings]\n  Needs_Review: [See REQUIRES REVIEW items]\n  Missing_Info: [{item}]\n"
    if "CRITICAL_FINDINGS:" in report_text:
        return report_text.replace("CRITICAL_FINDINGS:\n", insertion, 1)
    return report_text + insertion


def _clean_missing_info(report_text: str) -> str:
    match = MISSING_INFO_PATTERN.search(report_text)
    if not match:
        return report_text

    current = match.group(1).strip()
    upper = current.upper()
    if any(
        phrase in upper
        for phrase in (
            "ROOF PITCH VISIBILITY WAS RELIABLE",
            "PITCH VISIBILITY WAS RELIABLE",
            "RISE-OVER-RUN INFO NOTED",
        )
    ):
        replacement = "None"
        return MISSING_INFO_PATTERN.sub(f"Missing_Info: [{replacement}]", report_text, count=1)
    return report_text


def _clean_professional_recommendation(report_text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        body = match.group(1).strip()
        cleaned = body
        cleaned = re.sub(r"\bconverted hurricanes clips\b", "hurricane clips", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bcomplaints with FBC-R 2023\b", "compliance with FBC-R 2023", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\bsnow load conditions\b", "applicable design loads", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"LINKED.*$", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
        if not cleaned:
            cleaned = "Provide a coordinated, code-citable roof package and resolve the identified review items before permit submission."
        return f"PROFESSIONAL_RECOMMENDATION:\n  {cleaned}.\n"

    return re.sub(
        r"PROFESSIONAL_RECOMMENDATION:\s*\n(.*?)(?=\n[A-Z_][A-Z_ ]*:|\Z)",
        repl,
        report_text,
        count=1,
        flags=re.DOTALL,
    )


def _sanitize_metadata(report_text: str) -> str:
    report_text = re.sub(
        r"^\s*Analyzer:.*$",
        "  Analyzer: [AI roof compliance review system]",
        report_text,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    report_text = re.sub(
        r"\blicensed structural engineer\b",
        "AI roof compliance review system",
        report_text,
        flags=re.IGNORECASE,
    )
    return report_text


def _derive_overall_status(text: str) -> str:
    statuses = [_normalize_status(_status_from_match(m)) for m in STATUS_PATTERN.finditer(text)]
    if not statuses:
        return "REQUIRES FURTHER REVIEW"
    if "NON-COMPLIANT" in statuses:
        return "NON-COMPLIANT"
    if "REQUIRES REVIEW" in statuses:
        return "REQUIRES FURTHER REVIEW"
    return "COMPLIANT"


def normalize_validation_report(validation_text: str, extraction_text: str = "") -> str:
    """
    Normalize report into a stable structure and apply roof-code guardrails.
    """
    if not validation_text or not validation_text.strip():
        validation_text = "STEP 2: FBC-R 2023 COMPLIANCE VALIDATION\n"

    validation_text = _canonicalize_model_output(validation_text)

    if "STEP 2: FBC-R 2023 COMPLIANCE VALIDATION" not in validation_text:
        validation_text = f"STEP 2: FBC-R 2023 COMPLIANCE VALIDATION\n{validation_text.strip()}"

    lines = validation_text.splitlines()

    # Ensure at least one section header exists.
    if not any(line.strip().startswith("SECTION:") for line in lines):
        lines.insert(1, "---")
        lines.insert(2, "SECTION: [Unlabeled Section 1]")

    # Sanitize code references on blocks the model actually returned.
    for block_name in REQUIRED_BLOCKS:
        start, end = _extract_block(lines, block_name)
        if start == -1:
            continue

        block_text = "\n".join(lines[start:end])
        sanitized = _sanitize_code_reference(block_name, block_text)
        if block_name == "FRAMING":
            sanitized = _promote_framing_block_if_accepted(sanitized, extraction_text)
        if block_name == "SHEATHING":
            sanitized = _promote_sheathing_block_if_accepted(sanitized, extraction_text)
        sanitized = _guard_compliant_block(block_name, sanitized, extraction_text)
        lines[start:end] = sanitized.splitlines()

    report = "\n".join(lines).strip()
    report = _ensure_required_blocks(report)
    blocks = _collect_block_data(report.splitlines())

    if not _report_mentions_roof_pitch(report):
        report = _ensure_missing_info_item(report, "Roof pitch/slope callout not captured from the drawing")
        covering_start, covering_end = _extract_block(report.splitlines(), "COVERING_AND_EDGE")
        if covering_start != -1:
            report_lines = report.splitlines()
            block_text = "\n".join(report_lines[covering_start:covering_end])
            report_lines[covering_start:covering_end] = _set_status(block_text, "REQUIRES REVIEW").splitlines()
            report = "\n".join(report_lines).strip()
            blocks = _collect_block_data(report.splitlines())

    report = _clean_missing_info(report)
    report = _rewrite_section_summary(report)
    overall = _derive_overall_status(report)
    if "OVERALL_COMPLIANCE_STATUS:" in report:
        report = OVERALL_PATTERN.sub(
            f"OVERALL_COMPLIANCE_STATUS: [{overall}]",
            report,
            count=1,
        )
    else:
        report += (
            "\n\n================================================================================\n"
            f"OVERALL_COMPLIANCE_STATUS: [{overall}]\n"
            "================================================================================\n"
        )
    report = _strip_generated_summary_sections(report)
    blocks = _collect_block_data(report.splitlines())
    summary_status = _section_summary_status(blocks)
    critical_issues = _section_summary_issues(blocks)
    report = _rewrite_section_summary_block(report, summary_status, critical_issues)

    report += _derive_critical_findings(blocks, report)
    report += _derive_required_corrections(blocks)
    report += _derive_professional_recommendation(blocks, overall, report)
    report += _derive_validation_metadata(report)
    report = _clean_professional_recommendation(report)
    report = _sanitize_metadata(report)

    return report.strip() + "\n"


def apply_section_label_from_extraction(validation_text: str, extraction_text: str) -> str:
    """
    Replace fallback section labels with extracted labels from STEP 1 when available.
    """
    if not validation_text:
        return validation_text

    if "[Unlabeled Section 1]" not in validation_text:
        return validation_text

    # Typical extraction line format: Label: [New Women Restrooms Wall Section Detail]
    bracketed = re.search(r"Label:\s*\[([^\]]+)\]", extraction_text or "", re.IGNORECASE)
    if bracketed and bracketed.group(1).strip():
        label = bracketed.group(1).strip()
        return validation_text.replace("[Unlabeled Section 1]", label)

    # Secondary fallback: "SECTION_1:" followed by "Label: value" (without brackets)
    plain = re.search(r"Label:\s*([^\n\r]+)", extraction_text or "", re.IGNORECASE)
    if plain and plain.group(1).strip():
        label = plain.group(1).strip().strip("[]")
        if label and "Unlabeled" not in label:
            return validation_text.replace("[Unlabeled Section 1]", label)

    return validation_text
