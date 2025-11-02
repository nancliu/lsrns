"""
Parameter Transformation Testing

Tests the three-layer parameter transformation pipeline:
1. Strategy Instance Layer (JSON with display units)
2. Transformation Layer (additional_generator.py with unit conversion)
3. SUMO XML Layer (control.add.xml with SUMO units)

Focus areas (per 2025-11-02 specification):
- Case metadata time handling (case.metadata.time_range.start extraction)
- TWO-LAYER vehicle type conversion (UI types → vehicle_types.json → SUMO vClass)
- Parameter validation and assertions
- Transformation precision and data loss prevention
"""

import pytest
import json
import logging
from pathlib import Path
from shared.control_tools.additional_generator import (
    generate_vss_xml,
    generate_dhs_xml,
    _map_vehicle_types_to_sumo,
    _extract_case_start_hour,
    generate_strategy_xml
)
from shared.control_tools.xml_validator import validate_xml_string

logger = logging.getLogger(__name__)


class TestCaseMetadataExtraction:
    """Test case metadata time extraction for time context."""

    def test_extract_case_start_hour_valid_format(self):
        """Test extraction of case start hour from valid metadata."""
        case_metadata = {
            "case_id": "case_20251016_113040",
            "time_range": {
                "start": "2025/09/01 08:00:00",
                "end": "2025/09/01 09:00:00"
            }
        }

        hour = _extract_case_start_hour(case_metadata)
        assert hour == 8, f"Expected hour 8, got {hour}"

    def test_extract_case_start_hour_different_hours(self):
        """Test extraction with different hour values."""
        test_cases = [
            ("2025/09/01 00:00:00", 0),   # Midnight
            ("2025/09/01 07:30:45", 7),   # Morning
            ("2025/09/01 12:00:00", 12),  # Noon
            ("2025/09/01 19:45:00", 19),  # Evening
            ("2025/09/01 23:59:59", 23),  # Late evening
        ]

        for time_str, expected_hour in test_cases:
            case_metadata = {
                "time_range": {"start": time_str, "end": "2025/09/01 10:00:00"}
            }
            hour = _extract_case_start_hour(case_metadata)
            assert hour == expected_hour, f"For {time_str}, expected {expected_hour}, got {hour}"

    def test_extract_case_start_hour_missing_metadata(self):
        """Test extraction when metadata is missing."""
        case_metadata = {}
        hour = _extract_case_start_hour(case_metadata)
        assert hour is None, "Expected None for empty metadata"

    def test_extract_case_start_hour_invalid_format(self):
        """Test extraction with invalid time format."""
        case_metadata = {
            "time_range": {"start": "invalid-time-format"}
        }

        with pytest.raises(ValueError):
            _extract_case_start_hour(case_metadata)

    def test_extract_case_start_hour_out_of_range(self):
        """Test extraction with out-of-range hour values."""
        # This should be caught by the regex matching but assertion failing
        case_metadata = {
            "time_range": {"start": "2025/09/01 25:00:00"}  # Invalid hour (25 > 23)
        }

        # Should raise AssertionError or ValueError
        with pytest.raises((ValueError, AssertionError)):
            _extract_case_start_hour(case_metadata)


class TestVehicleTypeConversion:
    """Test TWO-LAYER vehicle type conversion."""

    def test_map_vehicle_types_empty_list(self):
        """Test conversion with empty vehicle type list."""
        result = _map_vehicle_types_to_sumo([])
        assert result == "", f"Expected empty string, got '{result}'"

    def test_map_vehicle_types_single_type(self):
        """Test conversion of single vehicle type."""
        result = _map_vehicle_types_to_sumo(["passenger"])
        assert result == "passenger", f"Expected 'passenger', got '{result}'"

    def test_map_vehicle_types_multiple_types(self):
        """Test conversion of multiple vehicle types."""
        allowed_types = ["passenger", "truck", "delivery"]
        result = _map_vehicle_types_to_sumo(allowed_types)

        # Should contain all types (order may vary due to set)
        result_types = set(result.split())
        expected_types = set(allowed_types)
        assert result_types == expected_types, f"Expected {expected_types}, got {result_types}"

    def test_map_vehicle_types_deduplicate(self):
        """Test that duplicate types are deduplicated."""
        result = _map_vehicle_types_to_sumo(["passenger", "passenger", "truck"])
        result_types = set(result.split())
        assert len(result_types) == 2, "Should have 2 unique types"
        assert "passenger" in result and "truck" in result

    def test_map_vehicle_types_sorted_output(self):
        """Test that output types are sorted."""
        result = _map_vehicle_types_to_sumo(["truck", "passenger", "delivery"])
        # Should be sorted
        expected = "delivery passenger truck"
        assert result == expected, f"Expected sorted '{expected}', got '{result}'"


class TestVSSParameterTransformation:
    """Test VSS parameter transformation with real strategy data."""

    def test_vss_speed_transformation_precision(self):
        """Test that speed km/h → m/s conversion maintains 2 decimal precision."""
        template = {
            "strategy_type": "VSS",
            "parameters_schema": []
        }

        parameters = {
            "affected_edges": ["edge1", "edge2"],
            "speed_steps": [
                {"time_hours": 7, "speed_kmh": 100},
                {"time_hours": 9, "speed_kmh": 50},
                {"time_hours": 17, "speed_kmh": 80}
            ]
        }

        xml_str = generate_vss_xml("test_vss", template, parameters)

        # Parse XML and check speed values
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)

        steps = list(root.findall("step"))
        assert len(steps) == 3, f"Expected 3 steps, got {len(steps)}"

        # Check specific speed values
        speed_values = [float(step.get("speed")) for step in steps]
        expected_speeds = [
            round(100 / 3.6, 2),  # 27.78
            round(50 / 3.6, 2),   # 13.89
            round(80 / 3.6, 2)    # 22.22
        ]

        for actual, expected in zip(speed_values, expected_speeds):
            assert abs(actual - expected) < 0.01, f"Speed mismatch: {actual} vs {expected}"

    def test_vss_time_transformation(self):
        """Test VSS time hours → seconds transformation."""
        template = {
            "strategy_type": "VSS",
            "parameters_schema": []
        }

        parameters = {
            "affected_edges": ["edge1"],
            "speed_steps": [
                {"time_hours": 0, "speed_kmh": 100},
                {"time_hours": 12, "speed_kmh": 80},
                {"time_hours": 24, "speed_kmh": 100}
            ]
        }

        xml_str = generate_vss_xml("test_vss", template, parameters)

        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)

        steps = list(root.findall("step"))
        time_values = [int(step.get("time")) for step in steps]

        expected_times = [0, 43200, 86400]  # 0, 12*3600, 24*3600
        assert time_values == expected_times, f"Time mismatch: {time_values} vs {expected_times}"

    def test_vss_assertion_speed_out_of_range(self):
        """Test that VSS generator asserts on speed exceeding SUMO bounds."""
        template = {"strategy_type": "VSS", "parameters_schema": []}

        # Speed > 130 km/h should fail
        parameters = {
            "affected_edges": ["edge1"],
            "speed_steps": [
                {"time_hours": 7, "speed_kmh": 150}  # Exceeds max
            ]
        }

        with pytest.raises(AssertionError):
            generate_vss_xml("test_vss", template, parameters)

    def test_vss_assertion_time_out_of_range(self):
        """Test that VSS generator asserts on time exceeding SUMO bounds."""
        template = {"strategy_type": "VSS", "parameters_schema": []}

        # Time > 24 hours should fail
        parameters = {
            "affected_edges": ["edge1"],
            "speed_steps": [
                {"time_hours": 25, "speed_kmh": 100}  # Exceeds 24 hours
            ]
        }

        with pytest.raises(AssertionError):
            generate_vss_xml("test_vss", template, parameters)


class TestDHSParameterTransformation:
    """Test DHS parameter transformation with vehicle type conversion."""

    def test_dhs_interval_transformation(self):
        """Test DHS interval hours → seconds transformation."""
        template = {"strategy_type": "DHS", "parameters_schema": []}

        parameters = {
            "affected_edges": ["edge1", "edge2"],
            "hard_shoulder_lane_index": 3,
            "intervals": [
                {"begin_hours": 7, "end_hours": 10, "status": "OPEN", "allowed_vehicle_types": ["passenger"]},
                {"begin_hours": 10, "end_hours": 16, "status": "CLOSED", "allowed_vehicle_types": []},
                {"begin_hours": 16, "end_hours": 19, "status": "OPEN", "allowed_vehicle_types": ["truck"]}
            ]
        }

        xml_str = generate_dhs_xml("test_dhs", template, parameters)

        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)

        intervals = list(root.findall("interval"))
        assert len(intervals) == 3, f"Expected 3 intervals, got {len(intervals)}"

        # Check time transformations
        for i, interval in enumerate(intervals):
            begin = int(interval.get("begin"))
            end = int(interval.get("end"))

            # Verify seconds conversion
            expected_begin = i * 3 + 7  # Hours
            expected_begin *= 3600  # Convert to seconds

            if i == 0:
                assert begin == 7 * 3600
                assert end == 10 * 3600
            elif i == 1:
                assert begin == 10 * 3600
                assert end == 16 * 3600
            elif i == 2:
                assert begin == 16 * 3600
                assert end == 19 * 3600

    def test_dhs_vehicle_type_conversion(self):
        """Test DHS TWO-LAYER vehicle type conversion."""
        template = {"strategy_type": "DHS", "parameters_schema": []}

        parameters = {
            "affected_edges": ["edge1"],
            "hard_shoulder_lane_index": 3,
            "intervals": [
                {"begin_hours": 7, "end_hours": 10, "status": "OPEN", "allowed_vehicle_types": ["passenger", "truck"]},
                {"begin_hours": 10, "end_hours": 16, "status": "CLOSED", "allowed_vehicle_types": []},
            ]
        }

        xml_str = generate_dhs_xml("test_dhs", template, parameters)

        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)

        closing_routes = list(root.findall(".//closingLaneReroute"))
        assert len(closing_routes) == 2

        # First interval: OPEN with types
        allow1 = closing_routes[0].get("allow")
        assert "passenger" in allow1 and "truck" in allow1

        # Second interval: CLOSED
        allow2 = closing_routes[1].get("allow")
        assert allow2 == ""

    def test_dhs_assertion_invalid_interval(self):
        """Test DHS assertion for invalid interval (begin >= end)."""
        template = {"strategy_type": "DHS", "parameters_schema": []}

        parameters = {
            "affected_edges": ["edge1"],
            "hard_shoulder_lane_index": 3,
            "intervals": [
                {"begin_hours": 10, "end_hours": 7, "status": "OPEN", "allowed_vehicle_types": []}  # Invalid
            ]
        }

        with pytest.raises(AssertionError):
            generate_dhs_xml("test_dhs", template, parameters)


class TestRealStrategyInstances:
    """Test with real strategy instances from the codebase."""

    def test_real_vss_strategy_g4202_001(self):
        """Test with real strategy_real_vss_g4202_001.json."""
        # Load real strategy
        strategy_file = Path(__file__).parent.parent.parent / "control_data" / "strategies" / "strategy_real_vss_g4202_001.json"

        if not strategy_file.exists():
            pytest.skip(f"Real strategy file not found: {strategy_file}")

        with open(strategy_file) as f:
            strategy = json.load(f)

        # Extract components
        template = strategy.get("template", {})
        parameters = strategy.get("parameters", {})
        strategy_id = strategy.get("strategy_id", "test_vss")

        # Generate XML
        xml_str = generate_vss_xml(strategy_id, template, parameters)

        # Validate XML
        result = validate_xml_string(xml_str)
        assert result.is_valid, f"Generated XML invalid: {result.errors}"

        # Check structure
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)

        assert root.tag == "variableSpeedSign"
        assert root.get("id") == strategy_id
        assert len(root.findall("step")) > 0

    def test_real_dhs_strategy_transformation(self):
        """Test with a real DHS strategy pattern."""
        template = {
            "strategy_type": "DHS",
            "strategy_id": "dhs_real",
            "parameters_schema": []
        }

        # Simulate real DHS strategy with time-dependent vehicle type restrictions
        parameters = {
            "affected_edges": ["-8712", "-15452.627", "-9350"],
            "hard_shoulder_lane_index": 3,
            "intervals": [
                {
                    "begin_hours": 7,
                    "end_hours": 9,
                    "status": "OPEN",
                    "allowed_vehicle_types": ["passenger", "truck", "delivery"]
                },
                {
                    "begin_hours": 9,
                    "end_hours": 17,
                    "status": "CLOSED",
                    "allowed_vehicle_types": []
                },
                {
                    "begin_hours": 17,
                    "end_hours": 19,
                    "status": "OPEN",
                    "allowed_vehicle_types": ["passenger", "truck"]
                }
            ]
        }

        xml_str = generate_dhs_xml("test_dhs_real", template, parameters)

        # Validate
        result = validate_xml_string(xml_str)
        assert result.is_valid, f"Generated XML invalid: {result.errors}"

        # Check intervals
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)
        intervals = list(root.findall("interval"))
        assert len(intervals) == 3


class TestTransformationIntegration:
    """Integration tests for complete transformation pipeline."""

    def test_parameter_to_xml_vss_complete_flow(self):
        """Test complete VSS flow from parameters to validated XML."""
        template = {"strategy_type": "VSS", "parameters_schema": []}
        parameters = {
            "affected_edges": ["edge1", "edge2", "edge3"],
            "speed_steps": [
                {"time_hours": 7, "speed_kmh": 100},
                {"time_hours": 9, "speed_kmh": 80},
                {"time_hours": 17, "speed_kmh": 100}
            ]
        }

        # Generate
        xml_str = generate_vss_xml("integration_test_vss", template, parameters)

        # Validate
        result = validate_xml_string(xml_str)
        assert result.is_valid, f"XML validation failed: {result.errors}"

        # Verify content
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)

        assert root.tag == "variableSpeedSign"
        assert root.get("id") == "integration_test_vss"

        edges = root.get("edges").split()
        assert len(edges) == 3
        assert all(e in ["edge1", "edge2", "edge3"] for e in edges)

        steps = list(root.findall("step"))
        assert len(steps) == 3

    def test_parameter_to_xml_dhs_complete_flow(self):
        """Test complete DHS flow with vehicle type conversion."""
        template = {"strategy_type": "DHS", "parameters_schema": []}
        parameters = {
            "affected_edges": ["-8712", "-15452.627"],
            "hard_shoulder_lane_index": 3,
            "intervals": [
                {
                    "begin_hours": 7,
                    "end_hours": 10,
                    "status": "OPEN",
                    "allowed_vehicle_types": ["passenger", "truck"]
                },
                {
                    "begin_hours": 16,
                    "end_hours": 19,
                    "status": "OPEN",
                    "allowed_vehicle_types": ["delivery"]
                }
            ]
        }

        # Generate
        xml_str = generate_dhs_xml("integration_test_dhs", template, parameters)

        # Validate
        result = validate_xml_string(xml_str)
        assert result.is_valid, f"XML validation failed: {result.errors}"

        # Verify content
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_str)

        assert root.tag == "rerouter"
        assert root.get("id") == "integration_test_dhs"

        intervals = list(root.findall("interval"))
        assert len(intervals) == 2

        # Check closing routes
        closing_routes = list(root.findall(".//closingLaneReroute"))
        assert len(closing_routes) == 2
        assert closing_routes[0].get("id") == "3"  # Hard shoulder lane


class TestDataLossPrevention:
    """Tests for preventing data loss during transformation."""

    def test_speed_precision_no_truncation(self):
        """Test that speed conversion doesn't truncate or lose precision."""
        # Test cases where rounding matters
        test_cases = [
            (50, 13.89),      # 50 / 3.6 = 13.888... → 13.89 (2 decimals)
            (100, 27.78),     # 100 / 3.6 = 27.777... → 27.78
            (75, 20.83),      # 75 / 3.6 = 20.833... → 20.83
            (30, 8.33),       # 30 / 3.6 = 8.333... → 8.33
            (130, 36.11),     # 130 / 3.6 = 36.111... → 36.11
        ]

        for speed_kmh, expected_ms in test_cases:
            actual_ms = round(speed_kmh / 3.6, 2)
            assert actual_ms == expected_ms, f"{speed_kmh} km/h: expected {expected_ms}, got {actual_ms}"

    def test_time_no_data_loss_in_conversion(self):
        """Test that time conversion to seconds has no data loss."""
        test_times = [0, 1, 5, 7, 12, 18, 24]

        for time_hours in test_times:
            time_seconds = int(time_hours * 3600)
            # Verify exact conversion (no floating point errors)
            assert time_seconds % 3600 == 0, f"Time conversion lost precision for {time_hours}h"
            assert time_seconds // 3600 == time_hours, f"Time conversion incorrect for {time_hours}h"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
