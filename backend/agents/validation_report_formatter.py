"""
Validation report formatter/normalizer for consistent roof compliance output.
"""

from __future__ import annotations

import re
from typing import Dict, List


REQUIRED_BLOCKS = [
    "ROOF_FRAMING_COMPLIANCE",
    "ROOF_SHEATHING_COMPLIANCE",
    "ROOF_TO_WALL_CONNECTION_COMPLIANCE",
    "ROOF_COVERING_COMPLIANCE",
    "WIND_RESISTANCE_COMPLIANCE",
]

ALLOWED_REFERENCES: Dict[str, tuple[str, ...]] = {
    "ROOF_FRAMING_COMPLIANCE": ("R802",),
    "ROOF_SHEATHING_COMPLIANCE": ("R803",),
    "ROOF_TO_WALL_CONNECTION_COMPLIANCE": ("R802.11", "R301"),
    "ROOF_COVERING_COMPLIANCE": ("R905", "R903"),
    "WIND_RESISTANCE_COMPLIANCE": ("R301", "R802.11", "R905"),
}

STATUS_PATTERN = re.compile(
    r"Status:\s*\[(COMPLIANT|NON-COMPLIANT|REQUIRES REVIEW|REQUIRES FURTHER REVIEW)\]",
    re.IGNORECASE,
)


def _normalize_status(raw: str) -> str:
    value = raw.strip().upper()
    if value == "REQUIRES FURTHER REVIEW":
        return "REQUIRES REVIEW"
    return value


def _set_status(block_text: str, status: str) -> str:
    replacement = f"Status: [{status}]"
    if STATUS_PATTERN.search(block_text):
        return STATUS_PATTERN.sub(replacement, block_text, count=1)
    return f"{replacement}\n  Code_Reference: [Exact citation verification needed]\n{block_text}"


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
    code_ref_match = re.search(r"Code_Reference:\s*\[(.*?)\]", block_text, re.IGNORECASE | re.DOTALL)
    if not code_ref_match:
        return _set_status(block_text, "REQUIRES REVIEW")

    code_ref = code_ref_match.group(1)
    upper_ref = code_ref.upper()
    allowed = ALLOWED_REFERENCES.get(block_name, ())
    is_allowed = any(token in upper_ref for token in allowed)

    # Guardrail: R502 (floor framing) should not be used for roof validation sections.
    has_known_wrong_ref = "R502" in upper_ref

    if is_allowed and not has_known_wrong_ref:
        return block_text

    block_text = _set_status(block_text, "REQUIRES REVIEW")
    return re.sub(
        r"Code_Reference:\s*\[(.*?)\]",
        "Code_Reference: [Exact citation verification needed (roof scope: R802/R803/R905/R301/R806)]",
        block_text,
        count=1,
        flags=re.IGNORECASE | re.DOTALL,
    )


def _default_block(block_name: str) -> str:
    return (
        f"{block_name}:\n"
        "  Status: [REQUIRES REVIEW]\n"
        "  Code_Reference: [Exact citation verification needed (roof scope: R802/R803/R905/R301/R806)]\n"
        "  Analysis: |\n"
        "    Insufficient or ambiguous data for deterministic validation.\n"
        "  Required_Corrections: [Provide complete roof details and exact code-citable specs]\n"
    )


def _derive_overall_status(text: str) -> str:
    statuses = [_normalize_status(m.group(1)) for m in STATUS_PATTERN.finditer(text)]
    if not statuses:
        return "REQUIRES FURTHER REVIEW"
    if "NON-COMPLIANT" in statuses:
        return "NON-COMPLIANT"
    if "REQUIRES REVIEW" in statuses:
        return "REQUIRES FURTHER REVIEW"
    return "COMPLIANT"


def normalize_validation_report(validation_text: str) -> str:
    """
    Normalize report into a stable structure and apply roof-code guardrails.
    """
    if not validation_text or not validation_text.strip():
        validation_text = "STEP 2: FBC-R 2023 COMPLIANCE VALIDATION\n"

    if "STEP 2: FBC-R 2023 COMPLIANCE VALIDATION" not in validation_text:
        validation_text = f"STEP 2: FBC-R 2023 COMPLIANCE VALIDATION\n{validation_text.strip()}"

    lines = validation_text.splitlines()

    # Ensure at least one section header exists.
    if not any(line.strip().startswith("SECTION:") for line in lines):
        lines.insert(1, "---")
        lines.insert(2, "SECTION: [Unlabeled Section 1]")

    # Ensure required section blocks exist and sanitize their code references.
    for block_name in REQUIRED_BLOCKS:
        start, end = _extract_block(lines, block_name)
        if start == -1:
            lines.append(_default_block(block_name).rstrip("\n"))
            continue

        block_text = "\n".join(lines[start:end])
        sanitized = _sanitize_code_reference(block_name, block_text)
        lines[start:end] = sanitized.splitlines()

    report = "\n".join(lines).strip()

    overall = _derive_overall_status(report)
    if "OVERALL_COMPLIANCE_STATUS:" in report:
        report = re.sub(
            r"OVERALL_COMPLIANCE_STATUS:\s*\[(.*?)\]",
            f"OVERALL_COMPLIANCE_STATUS: [{overall}]",
            report,
            count=1,
            flags=re.IGNORECASE,
        )
    else:
        report += (
            "\n\n================================================================================\n"
            f"OVERALL_COMPLIANCE_STATUS: [{overall}]\n"
            "================================================================================\n"
        )

    if "CRITICAL_FINDINGS:" not in report:
        report += (
            "\nCRITICAL_FINDINGS:\n"
            "  Major_Violations: [None or see section findings]\n"
            "  Needs_Review: [See REQUIRES REVIEW items]\n"
            "  Missing_Info: [Complete roof details required for full determination]\n"
        )

    if "REQUIRED_CORRECTIONS:" not in report:
        report += (
            "\nREQUIRED_CORRECTIONS:\n"
            "  High_Priority:\n"
            "    - Resolve all REQUIRES REVIEW and NON-COMPLIANT items with code-citable details.\n"
            "  Recommended:\n"
            "    - Add explicit design loads, spans, wind inputs, and connector ratings.\n"
        )

    if "PROFESSIONAL_RECOMMENDATION:" not in report:
        report += (
            "\nPROFESSIONAL_RECOMMENDATION:\n"
            "  Provide a coordinated, code-citable roof package (framing/sheathing/covering/wind) before permit submission.\n"
        )

    if "VALIDATION_METADATA:" not in report:
        report += (
            "\nVALIDATION_METADATA:\n"
            "  Code_Edition: Florida Building Code - Residential 2023\n"
            "  Chapters: 8 (Roof-Ceiling), 9 (Roof Assemblies)\n"
            "  Confidence: [MEDIUM]\n"
        )

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
