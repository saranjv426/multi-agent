from utils.pdf_generator import ComplianceReportGenerator


def test_generate_report_handles_special_characters_in_validation_text():
    generator = ComplianceReportGenerator()

    validation_data = {
        "success": True,
        "validation_report": """
### Technical Specifications
- Existing wall remains & must be reviewed <carefully>
**VALIDATION CHECKLIST:**
Sheathing: COMPLIANT
Rafter Spacing/Spans: NON-COMPLIANT
Fastening/Connections: REQUIRES FURTHER REVIEW
Underlayment: MISSING
""",
    }

    pdf_bytes = generator.generate_report(validation_data)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b"%PDF")
