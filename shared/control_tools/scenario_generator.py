"""
Event Scenario Configuration Generator

Orchestrates generation of complete scenario configuration bundles including:
- SUMO .add.xml files (event + control strategy combined)
- event_description.json (event metadata)
- traffic_input_config.json (OD data time range configuration)
- control_strategy_config.json (control strategy parameters)

This module combines event injection XML (from event_injector.py) with control
strategy XML (from additional_generator.py) into unified scenario configurations.

Author: AI Assistant
Created: 2025-01-10
Version: 1.0.0
"""

import logging
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring

from .event_injector import create_event_injector
from .additional_generator import generate_strategy_xml

logger = logging.getLogger(__name__)


# ============================================================================
# Event Type Mapping Layer (Architecture Update 2025-11-11)
# ============================================================================

# Event type Chinese to English mapping
EVENT_TYPE_MAPPING = {
    "交通事故": "accident",
    "交通阻塞": "congestion",
    "交通管制": "road_control",
    "地质灾害": "geological",
    "车辆故障": "breakdown",
    "恶劣天气": "weather",
    "流量激增工况": "flowsurge"  # Flow surge workload (high traffic volume periods)
}

# Directory name mapping with numeric prefixes
EVENT_TYPE_DIRECTORIES = {
    "accident": "01_accident",
    "congestion": "02_congestion",
    "road_control": "03_road_control",
    "geological": "04_geological",
    "breakdown": "05_breakdown",
    "weather": "06_weather",
    "flowsurge": "07_flowsurge"  # Flow surge workload scenarios
}


def get_event_type_english(chinese_name: str) -> str:
    """
    Convert Chinese event type to English identifier.

    Args:
        chinese_name: Chinese event type name (e.g., "交通事故")

    Returns:
        English event type identifier (e.g., "accident")
        Falls back to input if not found in mapping
    """
    return EVENT_TYPE_MAPPING.get(chinese_name, chinese_name)


def get_event_directory_name(event_type: str) -> str:
    """
    Get directory name for event type (with numeric prefix).

    Args:
        event_type: Event type in English (e.g., "accident")

    Returns:
        Directory name (e.g., "01_accident")
        Falls back to "99_{event_type}" if not found
    """
    return EVENT_TYPE_DIRECTORIES.get(event_type, f"99_{event_type}")


# ============================================================================


class ScenarioGenerator:
    """Generates complete event scenario configuration bundles"""

    def __init__(self, network_file: str, output_base_dir: str = "output/scenarios"):
        """
        Initialize scenario generator.

        Args:
            network_file: Path to SUMO network file
            output_base_dir: Base directory for scenario output
        """
        self.network_file = network_file
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)

    def _validate_vss_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Validate VSS (Variable Speed Sign) parameters.

        Args:
            parameters: VSS control parameters

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Check required fields
        if 'affected_edges' not in parameters or not parameters['affected_edges']:
            raise ValueError("VSS strategy requires non-empty 'affected_edges' parameter")

        # Check that either simplified or complete format is provided
        has_simplified = 'speed_limit_kmh' in parameters
        has_complete = 'speed_steps' in parameters and len(parameters['speed_steps']) > 0

        if not has_simplified and not has_complete:
            logger.warning(
                "VSS parameters missing both 'speed_limit_kmh' and 'speed_steps'. "
                "Using default speed_limit_kmh=60."
            )

        # Validate speed values if provided
        if has_simplified:
            speed = parameters['speed_limit_kmh']
            if not (30 <= speed <= 130):
                raise ValueError(
                    f"VSS speed_limit_kmh={speed} must be between 30 and 130 km/h"
                )

        if has_complete:
            for i, step in enumerate(parameters['speed_steps']):
                if 'speed_kmh' in step:
                    speed = step['speed_kmh']
                    if not (30 <= speed <= 130):
                        raise ValueError(
                            f"VSS speed_steps[{i}] speed_kmh={speed} must be between 30 and 130 km/h"
                        )

    def _validate_tec_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Validate TEC (Toll Entrance Control) parameters.

        Args:
            parameters: TEC control parameters

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Check required fields
        if 'entrance_edges' not in parameters or not parameters['entrance_edges']:
            raise ValueError("TEC strategy requires non-empty 'entrance_edges' parameter")

        # Check that either simplified or complete format is provided
        has_simplified = 'flow_reduction' in parameters
        has_complete = 'flow_intervals' in parameters and len(parameters['flow_intervals']) > 0

        if not has_simplified and not has_complete:
            logger.warning(
                "TEC parameters missing both 'flow_reduction' and 'flow_intervals'. "
                "Using default flow_reduction=0.2."
            )

        # Validate flow values if provided
        if has_simplified:
            reduction = parameters['flow_reduction']
            if not (0 < reduction < 1):
                raise ValueError(
                    f"TEC flow_reduction={reduction} must be between 0 and 1"
                )

        if has_complete:
            for i, interval in enumerate(parameters['flow_intervals']):
                if 'flow_coefficient' in interval:
                    coef = interval['flow_coefficient']
                    if not (0.1 <= coef <= 1.0):
                        raise ValueError(
                            f"TEC flow_intervals[{i}] flow_coefficient={coef} must be between 0.1 and 1.0"
                        )
                if 'vehsPerHour' in interval:
                    flow = interval['vehsPerHour']
                    if flow <= 0:
                        raise ValueError(
                            f"TEC flow_intervals[{i}] vehsPerHour={flow} must be > 0"
                        )

    def _validate_dhs_parameters(self, parameters: Dict[str, Any]) -> None:
        """
        Validate DHS (Dynamic Hard Shoulder) parameters.

        Args:
            parameters: DHS control parameters

        Raises:
            ValueError: If required parameters are missing or invalid
        """
        # Check required fields
        if 'shoulder_segments' not in parameters or not parameters['shoulder_segments']:
            raise ValueError("DHS strategy requires non-empty 'shoulder_segments' parameter")

        if 'activation_schedule' not in parameters or not parameters['activation_schedule']:
            raise ValueError("DHS strategy requires non-empty 'activation_schedule' parameter")

        # Validate activation schedule
        for i, schedule in enumerate(parameters['activation_schedule']):
            if 'begin' not in schedule or 'end' not in schedule:
                raise ValueError(
                    f"DHS activation_schedule[{i}] missing 'begin' or 'end' field"
                )

            begin = schedule['begin']
            end = schedule['end']

            if begin >= end:
                raise ValueError(
                    f"DHS activation_schedule[{i}] begin={begin} must be < end={end}"
                )

            if begin < 0 or end > 86400:
                logger.warning(
                    f"DHS activation_schedule[{i}] times outside typical range [0, 86400] seconds"
                )

    def generate_scenario(self, event_data: Dict[str, Any], strategy_type: str,
                         control_params: Dict[str, Any]) -> Dict[str, Path]:
        """
        Generate complete scenario configuration bundle.

        Args:
            event_data: Event information dictionary
            strategy_type: Control strategy type (VSS, DHS, TEC)
            control_params: Control strategy parameters

        Returns:
            Dictionary mapping file types to generated file paths
            {
                "add_xml": Path,
                "event_description": Path,
                "traffic_input_config": Path,
                "control_strategy_config": Path
            }
        """
        # Generate scenario directory path
        scenario_dir = self._generate_scenario_path(
            event_data['event_type'],
            strategy_type,
            event_data['report_id']
        )
        scenario_dir.mkdir(parents=True, exist_ok=True)

        # Validate control parameters based on strategy type
        if strategy_type and control_params:
            strategy_upper = strategy_type.upper()
            if strategy_upper == 'VSS':
                self._validate_vss_parameters(control_params)
            elif strategy_upper == 'TEC':
                self._validate_tec_parameters(control_params)
            elif strategy_upper == 'DHS':
                self._validate_dhs_parameters(control_params)

        generated_files = {}

        # 1. Generate SUMO .add.xml (event + control)
        add_xml_path = self._generate_add_xml(
            scenario_dir, event_data, strategy_type, control_params
        )
        generated_files["add_xml"] = add_xml_path

        # 2. Generate event_description.json
        event_desc_path = self._generate_event_description_json(
            scenario_dir, event_data
        )
        generated_files["event_description"] = event_desc_path

        # 3. Generate traffic_input_config.json
        traffic_config_path = self._generate_traffic_input_config(
            scenario_dir, event_data
        )
        generated_files["traffic_input_config"] = traffic_config_path

        # 4. Generate control_strategy_config.json
        control_config_path = self._generate_control_strategy_config(
            scenario_dir, strategy_type, control_params, event_data
        )
        generated_files["control_strategy_config"] = control_config_path

        logger.info(f"Generated scenario bundle at: {scenario_dir}")
        return generated_files

    def _generate_scenario_path(self, event_type: str, strategy: str,
                                event_id: str) -> Path:
        """
        Generate scenario directory path using English naming convention.

        Each scenario instance (event + strategy) gets its own directory.

        Architecture Update (2025-11-11): Now uses English directory names
        for SUMO compatibility (e.g., "01_accident" instead of "01_交通事故").

        Args:
            event_type: Event type (Chinese, e.g., "交通事故")
            strategy: Strategy type (VSS, DHS, TEC)
            event_id: Event report ID

        Returns:
            Path to scenario directory (e.g., output/scenarios/01_accident/scenario_12547_vss/)
        """
        # Convert Chinese event type to English
        event_type_en = get_event_type_english(event_type)

        # Get directory name with numeric prefix (e.g., "01_accident")
        event_dir = get_event_directory_name(event_type_en)

        # Create unique scenario directory
        # NO_CONTROL strategy uses "no_control" as directory name
        if strategy.upper() == "NO_CONTROL":
            scenario_instance_dir = f"scenario_{event_id}_no_control"
        else:
            scenario_instance_dir = f"scenario_{event_id}_{strategy.lower()}"

        return self.output_base_dir / event_dir / scenario_instance_dir

    def _enrich_control_params_with_timing(self, control_params: Dict, strategy_type: str,
                                             event_data: Dict, sim_start_time_str: str) -> Dict:
        """
        Enrich control parameters with timing fields for XML generation.

        Args:
            control_params: Original control parameters
            strategy_type: Strategy type (VSS, TEC, DHS)
            event_data: Event data with start/end times
            sim_start_time_str: Simulation start time string

        Returns:
            Enriched parameters with time_seconds, begin_seconds, end_seconds fields
        """
        # Calculate simulation timing
        event_start = datetime.strptime(event_data['start_time'], "%Y-%m-%d %H:%M:%S")
        event_end = datetime.strptime(event_data['end_time'], "%Y-%m-%d %H:%M:%S")
        sim_start = datetime.strptime(sim_start_time_str, "%Y-%m-%d %H:%M:%S")

        buffer_minutes = 30  # Must match _generate_traffic_input_config
        buffer = timedelta(minutes=buffer_minutes)
        sim_end = event_end + buffer

        # Calculate control activation times
        response_delay_seconds = control_params.get('response_delay_seconds', 300)
        recovery_period_seconds = control_params.get('recovery_period_seconds', 600)

        control_start_time = event_start + timedelta(seconds=response_delay_seconds)
        control_end_time = event_end + timedelta(seconds=recovery_period_seconds)

        # Convert to simulation seconds (relative to sim_start)
        begin_seconds = max(0, int((control_start_time - sim_start).total_seconds()))
        end_seconds_raw = int((control_end_time - sim_start).total_seconds())
        sim_duration_seconds = int((sim_end - sim_start).total_seconds())
        end_seconds = min(end_seconds_raw, sim_duration_seconds)

        # Add timing fields based on strategy type
        if strategy_type.upper() == 'VSS' and 'speed_steps' in control_params:
            for step in control_params['speed_steps']:
                if 'time_seconds' not in step:
                    step['time_seconds'] = begin_seconds
                step['begin'] = begin_seconds
                step['end'] = end_seconds

        elif strategy_type.upper() == 'TEC' and 'flow_intervals' in control_params:
            for interval in control_params['flow_intervals']:
                if 'begin_seconds' not in interval:
                    interval['begin_seconds'] = begin_seconds
                if 'end_seconds' not in interval:
                    interval['end_seconds'] = end_seconds
                interval['begin'] = begin_seconds
                interval['end'] = end_seconds

        return control_params

    def _generate_add_xml(self, scenario_dir: Path, event_data: Dict,
                         strategy_type: str, control_params: Dict) -> Path:
        """
        Generate combined SUMO .add.xml file (event + control).

        Combines event injection XML and control strategy XML into a single
        SUMO additional file.

        Architecture Update (2025-11-11): Filenames now use English event types
        for SUMO compatibility (e.g., "scenario_accident_vss_12547.add.xml").

        Args:
            scenario_dir: Directory to save the file
            event_data: Event data dictionary
            strategy_type: Control strategy type (VSS, DHS, TEC)
            control_params: Control strategy parameters

        Returns:
            Path to generated .add.xml file
        """
        # Convert event type to English for filename
        event_type_en = get_event_type_english(event_data['event_type'])

        # Handle NO_CONTROL strategy (event-only baseline)
        if strategy_type.upper() == "NO_CONTROL":
            filename = f"scenario_{event_type_en}_event_{event_data['report_id']}.add.xml"
        else:
            filename = f"scenario_{event_type_en}_{strategy_type.lower()}_{event_data['report_id']}.add.xml"

        xml_path = scenario_dir / filename

        # Calculate simulation start time for event injection timing
        # CRITICAL FIX (2025-11-14): Event loading must use correct simulation start time
        # Previously, event_data lacked sim_start_time, causing events to load at t=0
        # instead of at actual event time relative to simulation start.
        buffer_minutes = 30  # Must match _generate_traffic_input_config
        event_start = datetime.strptime(event_data['start_time'], "%Y-%m-%d %H:%M:%S")
        buffer = timedelta(minutes=buffer_minutes)
        sim_start_time = (event_start - buffer).strftime("%Y-%m-%d %H:%M:%S")

        # Add sim_start_time to event_data for correct timing calculation
        event_data_with_sim_time = event_data.copy()
        event_data_with_sim_time['sim_start_time'] = sim_start_time

        logger.debug(f"Event timing: event_start={event_data['start_time']}, "
                    f"sim_start={sim_start_time}, buffer={buffer_minutes}min")

        # 1. Generate event injection XML with correct simulation timing
        event_injector = create_event_injector(
            event_data['event_type'],
            network_file=self.network_file
        )
        event_xml = event_injector.generate_xml(event_data_with_sim_time)

        # 2. Generate control strategy XML (if control_params provided and not NO_CONTROL)
        control_xml = ""
        if control_params and strategy_type.upper() != "NO_CONTROL":
            # Enrich control_params with timing fields for XML generation
            enriched_params = self._enrich_control_params_with_timing(
                control_params.copy(),  # Copy to avoid modifying original
                strategy_type,
                event_data,
                sim_start_time
            )

            # Create minimal template structure for additional_generator
            template = {
                "strategy_type": strategy_type,
                "schema": {}  # additional_generator uses parameters directly
            }
            template_id = f"{strategy_type.lower()}_{event_data['report_id']}"

            try:
                control_xml = generate_strategy_xml(
                    template_id=template_id,
                    template=template,
                    parameters=enriched_params,
                    strategy_type=strategy_type
                )
            except Exception as e:
                logger.warning(f"Could not generate control strategy XML: {e}")
                logger.warning("Proceeding with event-only scenario")

        # 3. Combine XMLs
        combined_xml = self._combine_event_and_control_xml(event_xml, control_xml)

        # 4. Write to file
        xml_path.write_text(combined_xml, encoding='utf-8')
        logger.info(f"Generated .add.xml with event + control: {xml_path}")
        return xml_path

    def _remove_xml_declaration(self, xml_str: str) -> str:
        """
        Remove XML declaration from XML string if present.

        This ensures that when combining event and control XML fragments,
        we don't end up with duplicate XML declarations.

        Args:
            xml_str: XML string that may contain an XML declaration

        Returns:
            XML string without the declaration
        """
        if not xml_str:
            return xml_str

        # Remove XML declaration (<?xml ... ?>)
        import re
        cleaned = re.sub(r'<\?xml[^?]*\?>', '', xml_str, count=1)
        return cleaned.lstrip()

    def _combine_event_and_control_xml(self, event_xml: str, control_xml: str = "") -> str:
        """
        Combine event and control XML into single SUMO additional file.

        Args:
            event_xml: Event injection XML (closedLane, rerouter, etc.)
            control_xml: Control strategy XML (variableSpeedSign, calibrator, etc.)

        Returns:
            Combined XML string with <additional> root element
        """
        # Remove any XML declarations from fragments to prevent duplication
        event_xml_clean = self._remove_xml_declaration(event_xml)
        control_xml_clean = self._remove_xml_declaration(control_xml)

        # XML header and root element
        xml_parts = []
        xml_parts.append('<?xml version="1.0" encoding="UTF-8"?>')
        xml_parts.append('<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                        'xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">')

        # Add comment header
        xml_parts.append('    <!-- Generated by Event Scenario Generator -->')
        xml_parts.append('')

        # Add event injection XML
        if event_xml_clean:
            xml_parts.append('    <!-- Event Injection -->')
            # Indent event XML
            for line in event_xml_clean.strip().split('\n'):
                xml_parts.append('    ' + line)
            xml_parts.append('')

        # Add control strategy XML
        if control_xml_clean:
            xml_parts.append('    <!-- Control Strategy -->')
            # Indent control XML (already may have some indentation)
            for line in control_xml_clean.strip().split('\n'):
                if line.strip():  # Skip empty lines
                    xml_parts.append('    ' + line)
            xml_parts.append('')

        # Close root element
        xml_parts.append('</additional>')

        return '\n'.join(xml_parts)

    def _generate_event_description_json(self, scenario_dir: Path,
                                         event_data: Dict) -> Path:
        """
        Generate event_description.json with complete event metadata.

        Args:
            scenario_dir: Directory to save the file
            event_data: Event data dictionary

        Returns:
            Path to generated event_description.json file
        """
        json_path = scenario_dir / "event_description.json"

        # Calculate duration
        event_start = datetime.strptime(event_data['start_time'], "%Y-%m-%d %H:%M:%S")
        event_end = datetime.strptime(event_data['end_time'], "%Y-%m-%d %H:%M:%S")
        duration_hours = (event_end - event_start).total_seconds() / 3600

        # Resolve lane IDs from descriptions
        lane_ids = []
        if 'affected_lanes' in event_data and event_data['affected_lanes']:
            event_injector = create_event_injector(
                event_data['event_type'],
                network_file=self.network_file
            )
            lane_ids = event_injector._resolve_lane_ids(
                event_data['edge_id'],
                event_data['affected_lanes']
            )

        event_desc = {
            "event_id": event_data.get('report_id'),
            "event_type": event_data.get('event_type'),
            "event_description": event_data.get('event_description', ''),
            "location": {
                "road": event_data.get('road', ''),
                "direction": event_data.get('direction', ''),
                "mileage": event_data.get('mileage', ''),
                "junction_id": event_data.get('junction_id', ''),
                "edge_id": event_data.get('edge_id', '')
            },
            "time": {
                "start_time": event_data['start_time'],
                "end_time": event_data['end_time'],
                "duration_hours": round(duration_hours, 2)
            },
            "impact": {
                "affected_lanes": event_data.get('affected_lanes', []),
                "lane_ids": lane_ids
            }
        }

        json_path.write_text(json.dumps(event_desc, indent=2, ensure_ascii=False), encoding='utf-8')
        logger.info(f"Generated event_description.json: {json_path}")
        return json_path

    def _generate_traffic_input_config(self, scenario_dir: Path,
                                        event_data: Dict, buffer_minutes: int = 30) -> Path:
        """
        Generate traffic_input_config.json with OD time range and simulation duration.

        Structure:
        {
          "od_time_range": {
            "start": "...",  # event start - buffer
            "end": "...",    # event end + buffer
            "event_start": "...",
            "event_end": "...",
            "buffer_before_minutes": 30,
            "buffer_after_minutes": 30
          },
          "simulation_duration_hours": 2.48
        }

        Note: Does NOT include od_table or vehicle_types fields.
        - od_table is determined by case metadata
        - vehicle_types are from template configuration

        Args:
            scenario_dir: Scenario directory
            event_data: Event data
            buffer_minutes: Buffer time before/after event (default: 30)

        Returns:
            Path to generated traffic_input_config.json file
        """
        json_path = scenario_dir / "traffic_input_config.json"

        # Calculate time range with buffer
        event_start = datetime.strptime(event_data['start_time'], "%Y-%m-%d %H:%M:%S")
        event_end = datetime.strptime(event_data['end_time'], "%Y-%m-%d %H:%M:%S")
        buffer = timedelta(minutes=buffer_minutes)

        # Calculate simulation duration
        total_duration_seconds = (event_end - event_start).total_seconds() + 2 * buffer_minutes * 60
        simulation_duration_hours = total_duration_seconds / 3600

        traffic_config = {
            "od_time_range": {
                "start": (event_start - buffer).strftime("%Y-%m-%d %H:%M:%S"),
                "end": (event_end + buffer).strftime("%Y-%m-%d %H:%M:%S"),
                "event_start": event_data['start_time'],
                "event_end": event_data['end_time'],
                "buffer_before_minutes": buffer_minutes,
                "buffer_after_minutes": buffer_minutes
            },
            "simulation_duration_hours": round(simulation_duration_hours, 2)
        }

        json_path.write_text(json.dumps(traffic_config, indent=2, ensure_ascii=False), encoding='utf-8')
        logger.info(f"Generated traffic_input_config.json: {json_path}")
        return json_path

    def _generate_control_strategy_config(self, scenario_dir: Path, strategy_type: str,
                                         control_params: Dict, event_data: Dict) -> Path:
        """
        Generate control_strategy_config.json with realistic timing logic.

        IMPORTANT: Control strategies activate AFTER events occur (realistic response).
        This reflects real-world scenarios where control measures are deployed
        in response to detected events, not predictively.

        Special handling:
        - DHS: Uses pre-scheduled fixed timing (7:30-9:30) if provided
        - VSS/TEC: Automatically calculates begin/end times relative to simulation start

        Args:
            scenario_dir: Directory to save the file
            strategy_type: Strategy type (VSS, DHS, TEC)
            control_params: Control strategy parameters
            event_data: Event data dictionary

        Returns:
            Path to generated control_strategy_config.json file
        """
        json_path = scenario_dir / "control_strategy_config.json"

        # Calculate realistic control timing (activates AFTER event)
        event_start = datetime.strptime(event_data['start_time'], "%Y-%m-%d %H:%M:%S")
        event_end = datetime.strptime(event_data['end_time'], "%Y-%m-%d %H:%M:%S")

        # Realistic response delays
        response_delay_seconds = control_params.get('response_delay_seconds', 300)  # Default: 5 min
        recovery_period_seconds = control_params.get('recovery_period_seconds', 600)  # Default: 10 min

        response_delay = timedelta(seconds=response_delay_seconds)
        recovery_period = timedelta(seconds=recovery_period_seconds)

        # Resolve affected edges and lanes
        affected_edges = control_params.get('affected_edges', [event_data.get('edge_id', '')])
        affected_lanes = control_params.get('affected_lanes', [])

        # If no lanes specified, resolve from event data
        if not affected_lanes and 'affected_lanes' in event_data:
            event_injector = create_event_injector(
                event_data['event_type'],
                network_file=self.network_file
            )
            affected_lanes = event_injector._resolve_lane_ids(
                event_data['edge_id'],
                event_data['affected_lanes']
            )

        # Build comprehensive parameters (remove internal timing fields)
        parameters = {
            k: v for k, v in control_params.items()
            if not k.startswith('_')  # Exclude internal fields like _actual_control_start
        }
        parameters.update({
            "affected_edges": affected_edges if isinstance(affected_edges, list) else [affected_edges],
            "affected_lanes": affected_lanes if isinstance(affected_lanes, list) else [affected_lanes],
            "response_delay_seconds": response_delay_seconds,
            "recovery_period_seconds": recovery_period_seconds
        })

        # Calculate timing (use actual control times for DHS if provided)
        if '_actual_control_start' in control_params and '_actual_control_end' in control_params:
            # DHS with pre-scheduled timing
            activation_time = control_params['_actual_control_start']
            deactivation_time = control_params['_actual_control_end']
        else:
            # Default: event-based timing with response delay
            activation_time = (event_start + response_delay).strftime("%Y-%m-%d %H:%M:%S")
            deactivation_time = (event_end + recovery_period).strftime("%Y-%m-%d %H:%M:%S")

        # Auto-calculate begin/end times for VSS and TEC strategies
        # This ensures consistency across all scenarios
        if strategy_type.upper() in ['VSS', 'TEC']:
            # Read traffic_input_config to get simulation time range
            traffic_config_path = scenario_dir / "traffic_input_config.json"
            if traffic_config_path.exists():
                try:
                    with open(traffic_config_path, 'r', encoding='utf-8') as f:
                        traffic_config = json.load(f)

                    # Extract simulation time range
                    sim_start_str = traffic_config['od_time_range']['start']
                    sim_end_str = traffic_config['od_time_range']['end']
                    sim_start = datetime.strptime(sim_start_str, "%Y-%m-%d %H:%M:%S")
                    sim_end = datetime.strptime(sim_end_str, "%Y-%m-%d %H:%M:%S")
                    sim_duration_seconds = int((sim_end - sim_start).total_seconds())

                    # Calculate control activation and deactivation times
                    control_start_time = datetime.strptime(activation_time, "%Y-%m-%d %H:%M:%S")
                    control_end_time = datetime.strptime(deactivation_time, "%Y-%m-%d %H:%M:%S")

                    # Convert to simulation seconds (relative to sim_start)
                    begin_seconds = max(0, int((control_start_time - sim_start).total_seconds()))
                    end_seconds_raw = int((control_end_time - sim_start).total_seconds())
                    end_seconds = min(end_seconds_raw, sim_duration_seconds)

                    # Update VSS speed_steps
                    if strategy_type.upper() == 'VSS' and 'speed_steps' in parameters:
                        for step in parameters['speed_steps']:
                            # XML generator expects 'time_seconds' field
                            step['time_seconds'] = begin_seconds
                            # Keep original fields for reference/display
                            step['begin'] = begin_seconds
                            step['end'] = end_seconds
                        logger.debug(f"Auto-calculated VSS timing: time_seconds={begin_seconds}s, begin={begin_seconds}s, end={end_seconds}s")

                    # Update TEC flow_intervals
                    elif strategy_type.upper() == 'TEC' and 'flow_intervals' in parameters:
                        for interval in parameters['flow_intervals']:
                            # XML generator expects 'begin_seconds' and 'end_seconds' fields
                            interval['begin_seconds'] = begin_seconds
                            interval['end_seconds'] = end_seconds
                            # Keep original fields for reference/display
                            interval['begin'] = begin_seconds
                            interval['end'] = end_seconds
                        logger.debug(f"Auto-calculated TEC timing: begin_seconds={begin_seconds}s, end_seconds={end_seconds}s")

                except Exception as e:
                    logger.warning(f"Failed to auto-calculate begin/end times: {e}")
                    # Continue with original parameters

        control_config = {
            "strategy_type": strategy_type,
            "strategy_name": self._get_strategy_name(strategy_type),
            "parameters": parameters,
            "timing": {
                "activation_time": activation_time,
                "deactivation_time": deactivation_time,
                "response_delay_minutes": response_delay_seconds / 60,
                "recovery_period_minutes": recovery_period_seconds / 60
            }
        }

        json_path.write_text(json.dumps(control_config, indent=2, ensure_ascii=False), encoding='utf-8')
        logger.info(f"Generated control_strategy_config.json: {json_path}")
        return json_path

    def _get_strategy_name(self, strategy_type: str) -> str:
        """Get Chinese display name for strategy type"""
        names = {
            "VSS": "可变限速标志",
            "DHS": "动态硬路肩",
            "TEC": "收费站管控",
        }
        return names.get(strategy_type, strategy_type)
