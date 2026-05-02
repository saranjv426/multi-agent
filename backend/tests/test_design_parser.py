from agents.design_parser import DesignParser


def test_parse_slope_specifications_reads_pitch_field_ratio():
    parser = DesignParser()

    specifications = parser.parse_agent1_output(
        """
SECTION_1:
  Roof_Pitch: 3/12
  Notes: roof edge shown
"""
    )

    slope_specs = [spec for spec in specifications if spec.element_type == "slope"]

    assert len(slope_specs) == 1
    assert slope_specs[0].value == "3.0:12.0"
    assert slope_specs[0].unit == "ratio"
