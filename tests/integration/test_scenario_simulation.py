"""
Phase 4: Integration Testing - SUMO Simulation Validation Tests

Tests SUMO simulation execution with generated scenario files:
- Scenario simulation execution without errors
- Event injection verification (lane closure active)
- Control strategy activation verification
- Simulation output validation
"""

import os
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import pytest
import logging

logger = logging.getLogger(__name__)


class TestScenarioSimulation:
    """Task 4.2: SUMO Simulation Validation Tests"""

    @pytest.fixture
    def test_scenario_dir(self):
        """Get test scenario directory"""
        scenarios_dir = Path(__file__).parent.parent.parent / 'output' / 'scenarios'
        return scenarios_dir / '01_交通事故' / 'vss'

    @pytest.fixture
    def network_file(self):
        """Get SUMO network file path"""
        return Path(__file__).parent.parent.parent / 'templates' / 'network_files' / 'sichuan202508v7.net.xml'

    @pytest.fixture
    def sumo_binary(self):
        """Get SUMO binary path"""
        # Try common SUMO installation paths
        sumo_paths = [
            'sumo',  # Linux/Mac
            'sumo.exe',  # Windows (if in PATH)
            os.environ.get('SUMO_BIN'),  # Environment variable
        ]

        for sumo_path in sumo_paths:
            if sumo_path and subprocess.run(['where' if os.name == 'nt' else 'which', sumo_path],
                                           capture_output=True).returncode == 0:
                return sumo_path

        pytest.skip("SUMO binary not found in PATH or SUMO_BIN environment variable")

    def test_scenario_file_exists(self, test_scenario_dir):
        """Task 4.2.1: Verify scenario file exists"""
        # Find first scenario XML file
        if not test_scenario_dir.exists():
            pytest.skip(f"Scenario directory not found: {test_scenario_dir}")

        scenario_files = list(test_scenario_dir.glob('**/scenario_*.add.xml'))
        assert len(scenario_files) > 0, "No scenario XML files found"

        # Verify file is readable
        scenario_file = scenario_files[0]
        assert scenario_file.is_file()
        assert scenario_file.stat().st_size > 0

        logger.info(f"Found scenario file: {scenario_file}")

    def test_scenario_xml_structure(self, test_scenario_dir):
        """Task 4.2.1: Validate scenario XML structure"""
        scenario_files = list(test_scenario_dir.glob('**/scenario_*.add.xml'))

        if not scenario_files:
            pytest.skip("No scenario files to test")

        scenario_file = scenario_files[0]

        # Parse XML
        tree = ET.parse(scenario_file)
        root = tree.getroot()

        # Verify root element
        assert root.tag == 'additional', f"Expected 'additional' root element, got {root.tag}"

        # Verify schema reference
        assert root.attrib.get('{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation') is not None

        # Verify event injection element exists
        closed_lanes = root.findall('closedLane')
        assert len(closed_lanes) > 0, "No closedLane elements found (event injection missing)"

        # Verify control strategy element exists
        control_elements = (root.findall('variableSpeedSign') +
                           root.findall('rerouter') +
                           root.findall('calibrator'))
        assert len(control_elements) > 0, "No control strategy elements found"

        logger.info(f"XML validation passed for {scenario_file.name}")

    def test_scenario_metadata_completeness(self, test_scenario_dir):
        """Task 4.2.1: Verify all metadata files exist"""
        scenario_files = list(test_scenario_dir.glob('**/scenario_*.add.xml'))

        if not scenario_files:
            pytest.skip("No scenario files to test")

        scenario_file = scenario_files[0]
        scenario_dir = scenario_file.parent

        # Required metadata files
        required_files = [
            'event_description.json',
            'traffic_input_config.json',
            'control_strategy_config.json',
        ]

        for required_file in required_files:
            file_path = scenario_dir / required_file
            assert file_path.exists(), f"Missing required metadata file: {required_file}"

            # Verify JSON is valid
            with open(file_path) as f:
                data = json.load(f)
                assert data is not None, f"Invalid JSON in {required_file}"

        logger.info(f"Metadata validation passed for scenario: {scenario_dir.name}")

    def test_simulation_execution(self, test_scenario_dir, network_file, sumo_binary):
        """Task 4.2.1: Test scenario simulation execution"""
        scenario_files = list(test_scenario_dir.glob('**/scenario_*.add.xml'))

        if not scenario_files:
            pytest.skip("No scenario files to test")

        scenario_file = scenario_files[0]

        # Load traffic input config to get simulation duration
        scenario_dir = scenario_file.parent
        config_file = scenario_dir / 'traffic_input_config.json'

        with open(config_file) as f:
            traffic_config = json.load(f)
            sim_duration_hours = traffic_config.get('simulation_duration_hours', 2.0)
            sim_duration_seconds = int(sim_duration_hours * 3600)

        # Create temporary SUMO config
        with tempfile.TemporaryDirectory() as tmpdir:
            sumocfg_path = Path(tmpdir) / 'test_scenario.sumocfg'
            output_dir = Path(tmpdir) / 'output'
            output_dir.mkdir()

            # Create minimal SUMO config
            sumocfg_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/sumoConfiguration.xsd">
    <input>
        <net-file value="{network_file}"/>
        <additional-files value="{scenario_file}"/>
    </input>
    <time>
        <end value="{sim_duration_seconds}"/>
        <step-length value="1.0"/>
    </time>
    <output>
        <summary-file value="{output_dir}/summary.xml"/>
        <tripinfo-output value="{output_dir}/tripinfo.xml"/>
        <netstate-dump value="{output_dir}/netstate.xml"/>
    </output>
    <processing>
        <ignore-route-errors value="true"/>
    </processing>
    <report>
        <verbose value="false"/>
        <no-warnings value="true"/>
    </report>
</configuration>"""

            with open(sumocfg_path, 'w') as f:
                f.write(sumocfg_content)

            # Run SUMO simulation
            cmd = [sumo_binary, '--no-warnings', '-c', str(sumocfg_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            # Verify simulation completed without critical errors
            assert result.returncode == 0, f"SUMO simulation failed: {result.stderr}"

            # Verify output files created
            summary_file = output_dir / 'summary.xml'
            assert summary_file.exists(), "Summary file not created"

            logger.info(f"Simulation completed successfully for {scenario_file.name}")

    def test_control_strategy_activation(self, test_scenario_dir):
        """Task 4.2.2: Validate control strategy activation timing"""
        scenario_files = list(test_scenario_dir.glob('**/scenario_*.add.xml'))

        if not scenario_files:
            pytest.skip("No scenario files to test")

        scenario_file = scenario_files[0]
        scenario_dir = scenario_file.parent

        # Load event and control configurations
        with open(scenario_dir / 'event_description.json') as f:
            event_desc = json.load(f)
        with open(scenario_dir / 'control_strategy_config.json') as f:
            control_config = json.load(f)

        # Parse timestamps
        event_start = datetime.fromisoformat(event_desc['time']['start_time'])
        event_end = datetime.fromisoformat(event_desc['time']['end_time'])
        activation_time = datetime.fromisoformat(control_config['timing']['activation_time'])
        deactivation_time = datetime.fromisoformat(control_config['timing']['deactivation_time'])

        # Verify realistic timing: control activates AFTER event starts
        response_delay = control_config['parameters'].get('response_delay_seconds', 300)
        expected_activation = event_start.timestamp() + response_delay

        assert activation_time.timestamp() >= event_start.timestamp(), \
            f"Control activation ({activation_time}) before event start ({event_start})"

        assert deactivation_time.timestamp() > event_end.timestamp(), \
            f"Control deactivation ({deactivation_time}) before event end ({event_end})"

        logger.info(f"Control timing validation passed: "
                   f"Event {event_start} → {event_end}, "
                   f"Control {activation_time} → {deactivation_time}")

    def test_event_injection_timing_in_xml(self, test_scenario_dir):
        """Task 4.2.2: Verify event injection timing is valid in XML"""
        scenario_files = list(test_scenario_dir.glob('**/scenario_*.add.xml'))

        if not scenario_files:
            pytest.skip("No scenario files to test")

        scenario_file = scenario_files[0]

        # Parse XML
        tree = ET.parse(scenario_file)
        root = tree.getroot()

        # Find closedLane elements
        closed_lanes = root.findall('closedLane')
        assert len(closed_lanes) > 0, "No closedLane elements found"

        for closed_lane in closed_lanes:
            begin_time = int(closed_lane.get('begin', '0'))
            end_time = int(closed_lane.get('end', '0'))

            # Verify timing is reasonable
            assert begin_time >= 0, f"Invalid begin time: {begin_time}"
            assert end_time > begin_time, f"Event ends before it starts: begin={begin_time}, end={end_time}"

            # Verify event duration is reasonable (< 24 hours)
            duration_seconds = end_time - begin_time
            assert duration_seconds < 86400, f"Event duration too long: {duration_seconds}s"

        logger.info(f"Event injection timing validation passed for {scenario_file.name}")

    def test_control_strategy_timing_in_xml(self, test_scenario_dir):
        """Task 4.2.2: Verify control strategy timing is valid in XML"""
        scenario_files = list(test_scenario_dir.glob('**/scenario_*.add.xml'))

        if not scenario_files:
            pytest.skip("No scenario files to test")

        scenario_file = scenario_files[0]

        # Parse XML
        tree = ET.parse(scenario_file)
        root = tree.getroot()

        # Find control strategy elements
        control_elements = (root.findall('variableSpeedSign') +
                           root.findall('rerouter') +
                           root.findall('calibrator'))

        for control_elem in control_elements:
            begin_time = int(control_elem.get('begin', '0'))
            end_time = int(control_elem.get('end', '0'))

            # Verify timing is reasonable
            assert begin_time >= 0, f"Invalid control begin time: {begin_time}"
            assert end_time > begin_time, f"Control ends before it starts: begin={begin_time}, end={end_time}"

            # Verify control duration is reasonable
            duration_seconds = end_time - begin_time
            assert duration_seconds < 86400, f"Control duration too long: {duration_seconds}s"

        logger.info(f"Control strategy timing validation passed for {scenario_file.name}")

    def test_scenario_consistency_checks(self, test_scenario_dir):
        """Validate scenario consistency across files"""
        scenario_files = list(test_scenario_dir.glob('**/scenario_*.add.xml'))

        if not scenario_files:
            pytest.skip("No scenario files to test")

        for scenario_file in scenario_files[:3]:  # Test first 3 scenarios
            scenario_dir = scenario_file.parent

            # Parse XML
            tree = ET.parse(scenario_file)
            root = tree.getroot()

            # Load configs
            with open(scenario_dir / 'event_description.json') as f:
                event_desc = json.load(f)
            with open(scenario_dir / 'traffic_input_config.json') as f:
                traffic_config = json.load(f)
            with open(scenario_dir / 'control_strategy_config.json') as f:
                control_config = json.load(f)

            # Extract edge and lane info from XML
            closed_lanes = root.findall('closedLane')
            event_edge = closed_lanes[0].get('edge') if closed_lanes else None

            # Verify event edge matches between files
            if event_edge:
                assert event_edge == event_desc['location']['edge_id'], \
                    f"Event edge mismatch: XML={event_edge}, JSON={event_desc['location']['edge_id']}"

            logger.info(f"Consistency check passed for {scenario_dir.name}")
