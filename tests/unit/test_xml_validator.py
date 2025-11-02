"""
SUMO XML Validator Tests

Tests for XML validation functionality covering:
- Well-formed XML validation
- SUMO constraint compliance (element types, attribute ranges)
- VSS (Variable Speed Sign) element validation
- DHS (Dynamic Hard Shoulder) element validation
- TEC (Toll Entrance Control) element validation
- Error reporting and diagnostics
"""

import pytest
from shared.control_tools.xml_validator import (
    validate_xml_string,
    XMLValidationResult,
    _validate_vss_step,
    _validate_dhs_interval,
    _validate_closing_lane_reroute,
    _validate_tec_flow
)
import xml.etree.ElementTree as ET


class TestXMLWellformedness:
    """Test XML parsing and well-formedness validation."""

    def test_valid_vss_xml(self):
        """Test validation of valid VSS XML."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1 edge2">
            <step time="0" speed="27.78"/>
            <step time="25200" speed="22.22"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid, f"Valid XML marked as invalid: {result.errors}"
        assert result.element_count >= 2

    def test_valid_dhs_xml(self):
        """Test validation of valid DHS XML."""
        xml_content = """<rerouter id="dhs_001" edges="edge1 edge2 edge3">
            <interval begin="25200" end="32400">
                <closingLaneReroute id="3" allow="passenger truck"/>
            </interval>
            <interval begin="32400" end="86400">
                <closingLaneReroute id="3" allow=""/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid, f"Valid XML marked as invalid: {result.errors}"

    def test_valid_tec_xml(self):
        """Test validation of valid TEC (calibrator) XML."""
        xml_content = """<calibrator id="tec_001" edge="entrance_edge" pos="0">
            <flow begin="0" end="25200" vehsPerHour="480" speed="15.0"/>
            <flow begin="25200" end="86400" vehsPerHour="300" speed="20.0"/>
        </calibrator>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid, f"Valid XML marked as invalid: {result.errors}"

    def test_malformed_xml(self):
        """Test that malformed XML is detected."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step time="0" speed="27.78">  <!-- Missing closing tag -->
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid, "Malformed XML should be invalid"
        assert len(result.errors) > 0

    def test_missing_closing_tag(self):
        """Test detection of missing closing tags."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step time="0" speed="27.78"/>
        """  # Missing </variableSpeedSign>

        result = validate_xml_string(xml_content)
        assert not result.is_valid

    def test_invalid_root_element(self):
        """Test detection of invalid root element."""
        xml_content = """<invalid_root id="test" edges="edge1">
            <step time="0" speed="27.78"/>
        </invalid_root>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid, "Invalid root element should be detected"
        assert any(e["type"] == "invalid_root_element" for e in result.errors)


class TestVSSValidation:
    """Test VSS element validation."""

    def test_vss_valid_step(self):
        """Test validation of valid VSS step."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step time="25200" speed="27.78"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid

    def test_vss_missing_required_id(self):
        """Test detection of missing id attribute."""
        xml_content = """<variableSpeedSign edges="edge1">
            <step time="0" speed="27.78"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid
        assert any(e["type"] == "missing_attribute" and e["attribute"] == "id"
                   for e in result.errors)

    def test_vss_missing_step_time(self):
        """Test detection of missing time attribute in step."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step speed="27.78"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid
        assert any(e["type"] == "missing_attribute" and "time" in e.get("message", "")
                   for e in result.errors)

    def test_vss_missing_step_speed(self):
        """Test detection of missing speed attribute in step."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step time="0"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid

    def test_vss_time_out_of_bounds(self):
        """Test detection of time out of SUMO bounds."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step time="90000" speed="27.78"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid
        assert any(e["type"] == "out_of_bounds" for e in result.errors)

    def test_vss_speed_out_of_bounds_high(self):
        """Test detection of speed exceeding upper bound."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step time="0" speed="55.5"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid
        assert any(e["type"] == "out_of_bounds" and e["attribute"] == "speed"
                   for e in result.errors)

    def test_vss_speed_precision_warning(self):
        """Test warning for speed precision > 2 decimals."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step time="0" speed="27.777777"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        # Should still be valid but with warning
        if result.is_valid:
            assert any(w["type"] == "precision_warning" for w in result.warnings)

    def test_vss_invalid_time_type(self):
        """Test detection of invalid time type."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step time="not_a_number" speed="27.78"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid
        assert any(e["type"] == "invalid_type" for e in result.errors)

    def test_vss_invalid_speed_type(self):
        """Test detection of invalid speed type."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1">
            <step time="0" speed="not_a_number"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid


class TestDHSValidation:
    """Test DHS element validation."""

    def test_dhs_valid_interval(self):
        """Test validation of valid DHS interval."""
        xml_content = """<rerouter id="dhs_001" edges="edge1 edge2">
            <interval begin="25200" end="32400">
                <closingLaneReroute id="3" allow="passenger truck"/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid

    def test_dhs_missing_interval_begin(self):
        """Test detection of missing begin attribute."""
        xml_content = """<rerouter id="dhs_001" edges="edge1">
            <interval end="32400">
                <closingLaneReroute id="3" allow="passenger"/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid

    def test_dhs_missing_interval_end(self):
        """Test detection of missing end attribute."""
        xml_content = """<rerouter id="dhs_001" edges="edge1">
            <interval begin="25200">
                <closingLaneReroute id="3" allow="passenger"/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid

    def test_dhs_begin_greater_than_end(self):
        """Test detection of invalid interval (begin >= end)."""
        xml_content = """<rerouter id="dhs_001" edges="edge1">
            <interval begin="40000" end="25200">
                <closingLaneReroute id="3" allow="passenger"/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid
        assert any(e["type"] == "invalid_interval" for e in result.errors)

    def test_dhs_time_out_of_bounds(self):
        """Test detection of time out of SUMO bounds."""
        xml_content = """<rerouter id="dhs_001" edges="edge1">
            <interval begin="0" end="90000">
                <closingLaneReroute id="3" allow="passenger"/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid

    def test_dhs_missing_closing_lane_reroute_id(self):
        """Test detection of missing lane id in closingLaneReroute."""
        xml_content = """<rerouter id="dhs_001" edges="edge1">
            <interval begin="0" end="25200">
                <closingLaneReroute allow="passenger"/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid

    def test_dhs_valid_empty_allow(self):
        """Test validation of closed lane (empty allow)."""
        xml_content = """<rerouter id="dhs_001" edges="edge1">
            <interval begin="0" end="25200">
                <closingLaneReroute id="3" allow=""/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid

    def test_dhs_multiple_intervals(self):
        """Test validation of multiple intervals."""
        xml_content = """<rerouter id="dhs_001" edges="edge1 edge2 edge3">
            <interval begin="0" end="25200">
                <closingLaneReroute id="3" allow="passenger truck"/>
            </interval>
            <interval begin="25200" end="50400">
                <closingLaneReroute id="3" allow="passenger"/>
            </interval>
            <interval begin="50400" end="86400">
                <closingLaneReroute id="3" allow=""/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid


class TestTECValidation:
    """Test TEC (Toll Entrance Control) element validation."""

    def test_tec_valid_flow(self):
        """Test validation of valid TEC flow element."""
        xml_content = """<calibrator id="tec_001" edge="entrance" pos="0">
            <flow begin="0" end="25200" vehsPerHour="480" speed="15.0"/>
        </calibrator>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid

    def test_tec_missing_vehs_per_hour(self):
        """Test detection of missing vehsPerHour."""
        xml_content = """<calibrator id="tec_001" edge="entrance" pos="0">
            <flow begin="0" end="25200" speed="15.0"/>
        </calibrator>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid

    def test_tec_vehs_per_hour_out_of_bounds(self):
        """Test detection of flow rate exceeding bounds."""
        xml_content = """<calibrator id="tec_001" edge="entrance" pos="0">
            <flow begin="0" end="25200" vehsPerHour="5000" speed="15.0"/>
        </calibrator>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid
        assert any(e["type"] == "out_of_bounds" for e in result.errors)

    def test_tec_speed_out_of_bounds(self):
        """Test detection of speed exceeding bounds."""
        xml_content = """<calibrator id="tec_001" edge="entrance" pos="0">
            <flow begin="0" end="25200" vehsPerHour="480" speed="55.0"/>
        </calibrator>"""

        result = validate_xml_string(xml_content)
        assert not result.is_valid


class TestEdgeHandling:
    """Test edges attribute handling."""

    def test_empty_edges_warning(self):
        """Test warning for empty edges attribute."""
        xml_content = """<variableSpeedSign id="vss_001" edges="">
            <step time="0" speed="27.78"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        # Should still be valid but with warning
        assert any(w["type"] == "empty_edges" for w in result.warnings)

    def test_duplicate_edges_warning(self):
        """Test warning for duplicate edges."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1 edge2 edge1">
            <step time="0" speed="27.78"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        # Should still be valid but with warning
        assert any(w["type"] == "duplicate_edges" for w in result.warnings)

    def test_valid_multiple_edges(self):
        """Test validation with multiple unique edges."""
        xml_content = """<variableSpeedSign id="vss_001" edges="edge1 edge2 edge3 edge4">
            <step time="0" speed="27.78"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid


class TestRealWorldScenarios:
    """Test with realistic/real strategy XML output."""

    def test_realistic_vss_with_multiple_steps(self):
        """Test realistic VSS with multiple control steps."""
        xml_content = """<variableSpeedSign id="strategy_real_vss_g4202_001" edges="-8712 -15452.627 -9350 -6906">
            <step time="25200" speed="27.78"/>
            <step time="32400" speed="22.22"/>
            <step time="61200" speed="27.78"/>
            <step time="68400" speed="22.22"/>
        </variableSpeedSign>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid, f"Realistic VSS XML invalid: {result.errors}"

    def test_realistic_dhs_multiple_intervals_with_closures(self):
        """Test realistic DHS with mixed open/closed intervals."""
        xml_content = """<rerouter id="strategy_real_dhs_g4202_002" edges="-8712 -15452.627 -9350">
            <interval begin="25200" end="32400">
                <closingLaneReroute id="3" allow="passenger truck delivery"/>
            </interval>
            <interval begin="32400" end="61200">
                <closingLaneReroute id="3" allow=""/>
            </interval>
            <interval begin="61200" end="68400">
                <closingLaneReroute id="3" allow="passenger truck"/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid, f"Realistic DHS XML invalid: {result.errors}"

    def test_mixed_vehicle_types(self):
        """Test DHS with various vehicle type combinations."""
        xml_content = """<rerouter id="dhs_test" edges="edge1">
            <interval begin="0" end="10000">
                <closingLaneReroute id="3" allow="passenger"/>
            </interval>
            <interval begin="10000" end="20000">
                <closingLaneReroute id="3" allow="truck"/>
            </interval>
            <interval begin="20000" end="30000">
                <closingLaneReroute id="3" allow="delivery"/>
            </interval>
            <interval begin="30000" end="86400">
                <closingLaneReroute id="3" allow="passenger truck delivery"/>
            </interval>
        </rerouter>"""

        result = validate_xml_string(xml_content)
        assert result.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
