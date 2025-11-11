"""
Unit tests for scenario_generator module.

Tests cover:
- XML combination logic
- Event description JSON generation
- Traffic input config JSON generation
- Control strategy config JSON generation
- Scenario file path generation
- Full scenario bundle generation

Author: AI Assistant
Created: 2025-01-10
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

import sys
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.control_tools.scenario_generator import ScenarioGenerator


class TestXMLCombination:
    """Test XML combination logic"""

    def test_combine_event_only(self):
        """Test combining event XML without control strategy"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_xml = '<closedLane id="accident_123" edge="-4688" lanes="-4688_0" disallow="all" begin="0" end="3600"/>'
            combined = generator._combine_event_and_control_xml(event_xml, "")

            assert '<?xml version="1.0"' in combined
            assert '<additional' in combined
            assert '<!-- Event Injection -->' in combined
            assert 'closedLane' in combined
            assert '</additional>' in combined

    def test_combine_event_and_control(self):
        """Test combining event and control strategy XML"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_xml = '<closedLane id="accident_123" edge="-4688" lanes="-4688_0" disallow="all" begin="0" end="3600"/>'
            control_xml = '<variableSpeedSign id="vss_001" lanes="-4688_1" begin="300" end="4200"><step time="300" speed="16.67"/></variableSpeedSign>'

            combined = generator._combine_event_and_control_xml(event_xml, control_xml)

            assert '<!-- Event Injection -->' in combined
            assert '<!-- Control Strategy -->' in combined
            assert 'closedLane' in combined
            assert 'variableSpeedSign' in combined
            assert combined.count('<additional') == 1
            assert combined.count('</additional>') == 1

    def test_xml_indentation(self):
        """Test proper XML indentation in combined output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_xml = '<closedLane id="test"/>'
            combined = generator._combine_event_and_control_xml(event_xml, "")

            lines = combined.split('\n')
            # Check event XML is indented
            assert any('    <closedLane' in line for line in lines)


class TestScenarioPathGeneration:
    """Test scenario file path generation"""

    def test_generate_scenario_path_accident_vss(self):
        """Test path generation for accident + VSS scenario (English naming)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            path = generator._generate_scenario_path("交通事故", "VSS", "12547")

            # Architecture Update (2025-11-11): Expect English directory names
            assert "01_accident" in str(path)
            assert "scenario_12547_vss" in str(path)
            assert path.parent == Path(tmpdir) / "01_accident"

    def test_generate_scenario_path_congestion_dhs(self):
        """Test path generation for congestion + DHS scenario (English naming)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            path = generator._generate_scenario_path("交通阻塞", "DHS", "20001")

            # Architecture Update (2025-11-11): Expect English directory names
            assert "02_congestion" in str(path)
            assert "scenario_20001_dhs" in str(path)
            assert path.parent == Path(tmpdir) / "02_congestion"

    def test_generate_scenario_path_road_control_tec(self):
        """Test path generation for road control + TEC scenario (English naming)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            path = generator._generate_scenario_path("交通管制", "TEC", "30001")

            # Architecture Update (2025-11-11): Expect English directory names
            assert "03_road_control" in str(path)
            assert "scenario_30001_tec" in str(path)
            assert path.parent == Path(tmpdir) / "03_road_control"

    def test_generate_scenario_path_geological_vss(self):
        """Test path generation for geological disaster + VSS scenario (English naming)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            path = generator._generate_scenario_path("地质灾害", "VSS", "40001")

            # Architecture Update (2025-11-11): Expect English directory names
            assert "04_geological" in str(path)
            assert "scenario_40001_vss" in str(path)
            assert path.parent == Path(tmpdir) / "04_geological"

    def test_generate_scenario_path_breakdown_dhs(self):
        """Test path generation for vehicle breakdown + DHS scenario (English naming)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            path = generator._generate_scenario_path("车辆故障", "DHS", "50001")

            # Architecture Update (2025-11-11): Expect English directory names
            assert "05_breakdown" in str(path)
            assert "scenario_50001_dhs" in str(path)
            assert path.parent == Path(tmpdir) / "05_breakdown"

    def test_generate_scenario_path_weather_vss(self):
        """Test path generation for severe weather + VSS scenario (English naming)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            path = generator._generate_scenario_path("恶劣天气", "VSS", "60001")

            # Architecture Update (2025-11-11): Expect English directory names
            assert "06_weather" in str(path)
            assert "scenario_60001_vss" in str(path)
            assert path.parent == Path(tmpdir) / "06_weather"


class TestEventDescriptionJSON:
    """Test event description JSON generation"""

    def test_generate_event_description_complete(self):
        """Test generation with complete event data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "report_id": "12547",
                "event_type": "交通事故",
                "event_description": "货车追尾事故",
                "road": "G5京昆高速（绵广段）",
                "direction": "下行",
                "mileage": "K1576+000",
                "junction_id": "-35882",
                "edge_id": "-4688",
                "affected_lanes": ["应急车道"],
                "start_time": "2025-07-14 01:53:49",
                "end_time": "2025-07-14 03:22:39"
            }

            scenario_dir = Path(tmpdir) / "test_scenario"
            scenario_dir.mkdir()

            json_path = generator._generate_event_description_json(scenario_dir, event_data)

            assert json_path.exists()
            data = json.loads(json_path.read_text(encoding='utf-8'))

            assert data["event_id"] == "12547"
            assert data["event_type"] == "交通事故"
            assert data["event_description"] == "货车追尾事故"
            assert data["location"]["edge_id"] == "-4688"
            assert data["location"]["road"] == "G5京昆高速（绵广段）"
            assert data["time"]["start_time"] == "2025-07-14 01:53:49"
            assert data["time"]["duration_hours"] == 1.48
            assert "affected_lanes" in data["impact"]

    def test_generate_event_description_minimal(self):
        """Test generation with minimal event data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "report_id": "12548",
                "event_type": "交通事故",
                "edge_id": "-4688",
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 03:00:00"
            }

            scenario_dir = Path(tmpdir) / "test_scenario"
            scenario_dir.mkdir()

            json_path = generator._generate_event_description_json(scenario_dir, event_data)

            assert json_path.exists()
            data = json.loads(json_path.read_text(encoding='utf-8'))

            assert data["event_id"] == "12548"
            assert data["time"]["duration_hours"] == 1.0
            assert data["location"]["edge_id"] == "-4688"


class TestTrafficInputConfigJSON:
    """Test traffic input config JSON generation"""

    def test_generate_traffic_config_with_buffer(self):
        """Test traffic config generation with time buffers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 03:00:00"
            }

            scenario_dir = Path(tmpdir) / "test_scenario"
            scenario_dir.mkdir()

            json_path = generator._generate_traffic_input_config(
                scenario_dir, event_data, buffer_minutes=30
            )

            assert json_path.exists()
            data = json.loads(json_path.read_text(encoding='utf-8'))

            # Check buffer applied correctly
            assert data["od_time_range"]["start"] == "2025-07-14 01:30:00"  # 30 min before
            assert data["od_time_range"]["end"] == "2025-07-14 03:30:00"    # 30 min after
            assert data["od_time_range"]["event_start"] == "2025-07-14 02:00:00"
            assert data["od_time_range"]["event_end"] == "2025-07-14 03:00:00"
            assert data["od_time_range"]["buffer_before_minutes"] == 30
            assert data["od_time_range"]["buffer_after_minutes"] == 30

    def test_od_table_resolution(self):
        """Test OD table name resolution from event date"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 03:00:00"
            }

            scenario_dir = Path(tmpdir) / "test_scenario"
            scenario_dir.mkdir()

            json_path = generator._generate_traffic_input_config(scenario_dir, event_data)

            data = json.loads(json_path.read_text(encoding='utf-8'))

            # Should resolve to July 2025 table
            assert data["od_table"] == "baseline.od_data_sichuan_202507"

    def test_simulation_duration_calculation(self):
        """Test simulation duration calculation including buffers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 04:00:00"  # 2 hour event
            }

            scenario_dir = Path(tmpdir) / "test_scenario"
            scenario_dir.mkdir()

            json_path = generator._generate_traffic_input_config(
                scenario_dir, event_data, buffer_minutes=30
            )

            data = json.loads(json_path.read_text(encoding='utf-8'))

            # 2 hours + 30 min before + 30 min after = 3 hours
            assert data["simulation_duration_hours"] == 3.0

    def test_vehicle_types_included(self):
        """Test vehicle types are included in config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 03:00:00"
            }

            scenario_dir = Path(tmpdir) / "test_scenario"
            scenario_dir.mkdir()

            json_path = generator._generate_traffic_input_config(scenario_dir, event_data)

            data = json.loads(json_path.read_text(encoding='utf-8'))

            assert "vehicle_types" in data
            assert "passenger" in data["vehicle_types"]
            assert "truck" in data["vehicle_types"]
            assert "bus" in data["vehicle_types"]


class TestControlStrategyConfigJSON:
    """Test control strategy config JSON generation"""

    def test_generate_control_config_realistic_timing(self):
        """Test control activation AFTER event (realistic timing)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "event_type": "交通事故",
                "edge_id": "-4688",
                "affected_lanes": ["应急车道"],
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 03:00:00"
            }

            control_params = {
                "speed_limit_kmh": 60,
                "response_delay_seconds": 300,      # 5 min
                "recovery_period_seconds": 600      # 10 min
            }

            scenario_dir = Path(tmpdir) / "test_scenario"
            scenario_dir.mkdir()

            json_path = generator._generate_control_strategy_config(
                scenario_dir, "VSS", control_params, event_data
            )

            assert json_path.exists()
            data = json.loads(json_path.read_text(encoding='utf-8'))

            # Control activates AFTER event starts
            assert data["timing"]["activation_time"] == "2025-07-14 02:05:00"  # +5 min
            # Control deactivates AFTER event ends
            assert data["timing"]["deactivation_time"] == "2025-07-14 03:10:00"  # +10 min
            assert data["timing"]["response_delay_minutes"] == 5
            assert data["timing"]["recovery_period_minutes"] == 10

    def test_control_config_strategy_metadata(self):
        """Test strategy type and name are included"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "event_type": "交通事故",
                "edge_id": "-4688",
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 03:00:00"
            }

            control_params = {"speed_limit_kmh": 60}

            scenario_dir = Path(tmpdir) / "test_scenario"
            scenario_dir.mkdir()

            json_path = generator._generate_control_strategy_config(
                scenario_dir, "VSS", control_params, event_data
            )

            data = json.loads(json_path.read_text(encoding='utf-8'))

            assert data["strategy_type"] == "VSS"
            assert data["strategy_name"] == "可变限速标志"

    def test_control_config_parameters_merged(self):
        """Test user parameters are merged with defaults"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "event_type": "交通事故",
                "edge_id": "-4688",
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 03:00:00"
            }

            control_params = {
                "speed_limit_kmh": 60,
                "custom_param": "test_value"
            }

            scenario_dir = Path(tmpdir) / "test_scenario"
            scenario_dir.mkdir()

            json_path = generator._generate_control_strategy_config(
                scenario_dir, "VSS", control_params, event_data
            )

            data = json.loads(json_path.read_text(encoding='utf-8'))

            # User params preserved
            assert data["parameters"]["speed_limit_kmh"] == 60
            assert data["parameters"]["custom_param"] == "test_value"
            # Defaults added
            assert "affected_edges" in data["parameters"]
            assert "response_delay_seconds" in data["parameters"]


class TestFullScenarioGeneration:
    """Test full scenario bundle generation"""

    @patch('shared.control_tools.scenario_generator.create_event_injector')
    @patch('shared.control_tools.scenario_generator.generate_strategy_xml')
    def test_generate_complete_scenario_bundle(self, mock_generate_xml, mock_create_injector):
        """Test generation of complete 4-file bundle"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Mock event injector
            mock_injector = Mock()
            mock_injector.generate_xml.return_value = '<closedLane id="test"/>'
            mock_injector._resolve_lane_ids.return_value = ["-4688_0"]
            mock_create_injector.return_value = mock_injector

            # Mock control strategy XML generation
            mock_generate_xml.return_value = '<variableSpeedSign id="vss_test"/>'

            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "report_id": "12547",
                "event_type": "交通事故",
                "edge_id": "-4688",
                "affected_lanes": ["应急车道"],
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 03:00:00"
            }

            control_params = {"speed_limit_kmh": 60}

            files = generator.generate_scenario(event_data, "VSS", control_params)

            # Check all 4 files generated
            assert "add_xml" in files
            assert "event_description" in files
            assert "traffic_input_config" in files
            assert "control_strategy_config" in files

            # Check files exist
            assert files["add_xml"].exists()
            assert files["event_description"].exists()
            assert files["traffic_input_config"].exists()
            assert files["control_strategy_config"].exists()

            # Verify XML file content
            xml_content = files["add_xml"].read_text(encoding='utf-8')
            assert '<additional' in xml_content
            assert 'closedLane' in xml_content
            assert 'variableSpeedSign' in xml_content

    def test_scenario_directory_creation(self):
        """Test scenario directory is created correctly (English naming)"""
        with tempfile.TemporaryDirectory() as tmpdir:
            generator = ScenarioGenerator(
                network_file=None,
                output_base_dir=tmpdir
            )

            event_data = {
                "report_id": "12547",
                "event_type": "交通事故",
                "edge_id": "-4688",
                "affected_lanes": ["应急车道"],
                "start_time": "2025-07-14 02:00:00",
                "end_time": "2025-07-14 03:00:00"
            }

            files = generator.generate_scenario(event_data, "VSS", {})

            scenario_dir = files["add_xml"].parent
            assert scenario_dir.exists()
            # Architecture Update (2025-11-11): Expect English directory names
            assert "01_accident" in str(scenario_dir)
            assert "vss" in str(scenario_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
