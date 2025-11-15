"""
Event Injection XML Generator for SUMO Scenarios

Generates SUMO-compatible event injection XML elements for traffic event scenarios.
Supports traffic accidents, congestion, and other event types.

Key Features:
- Lane closure XML generation (rerouter with closingLaneReroute elements)
- Event time conversion from absolute timestamps to simulation time
- Lane ID resolution from Chinese descriptions to SUMO lane IDs
- Support for multiple event types (accidents, congestion, weather, etc.)

Functions:
- create_event_injector: Factory function to create appropriate injector
- AccidentInjector: Generates rerouter XML for traffic accidents
- CongestionInjector: Generates rerouter XML for congestion (placeholder)
- RoadControlInjector: Generates rerouter XML for road control events
- GeologicalInjector: Generates rerouter XML for geological disasters
- BreakdownInjector: Generates rerouter XML for vehicle breakdowns
- WeatherInjector: Generates rerouter XML for severe weather events

Author: AI Assistant
Created: 2025-01-10
Version: 1.0.0
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
import sumolib

logger = logging.getLogger(__name__)


class EventInjector(ABC):
    """Base class for event injection XML generators"""

    def __init__(self, network_file: Optional[str] = None):
        """
        Initialize event injector with optional network file.

        Args:
            network_file: Path to SUMO network file for lane resolution
        """
        self.network_file = network_file
        self.network = None
        if network_file and Path(network_file).exists():
            try:
                self.network = sumolib.net.readNet(network_file, withInternal=False)
                logger.info(f"Loaded network file: {network_file}")
            except Exception as e:
                logger.warning(f"Failed to load network file: {e}")

    @abstractmethod
    def generate_xml(self, event_data: Dict[str, Any]) -> str:
        """
        Generate event injection XML from event data.

        Args:
            event_data: Dictionary containing event information

        Returns:
            XML string for event injection element
        """
        pass

    def _resolve_lane_ids(self, edge_id: str, lane_descriptions: List[str]) -> List[str]:
        """
        Map Chinese lane descriptions to SUMO lane IDs.

        Lane naming convention in SUMO: {edge_id}_{lane_index}
        Lane indices start from 0 (rightmost lane = 0, leftmost = n-1)

        Chinese lane mappings:
        - 应急车道 (Emergency lane) → index 0 (rightmost)
        - 第一车道 (Lane 1) → index 1
        - 第二车道 (Lane 2) → index 2
        - 第三车道 (Lane 3) → index 3
        - 匝道 (Ramp) → index 0 (rightmost)

        Args:
            edge_id: SUMO edge ID (e.g., "-4688")
            lane_descriptions: List of Chinese lane descriptions (may contain comma-separated values)

        Returns:
            List of SUMO lane IDs (e.g., ["-4688_0", "-4688_1"])
        """
        lane_mapping = {
            "应急车道": 0,
            "紧急停车带": 0,
            "匝道": 0,  # Ramp lane
            "第一车道": 1,
            "第二车道": 2,
            "第三车道": 3,
            "第四车道": 4,
        }

        # Validate edge exists in network if available
        if self.network:
            try:
                edge = self.network.getEdge(edge_id)
                max_lane_index = edge.getLaneNumber() - 1
            except Exception as e:
                logger.warning(f"Edge {edge_id} not found in network: {e}")
                max_lane_index = 4  # Assume max 5 lanes if network unavailable
        else:
            max_lane_index = 4  # Default assumption

        lane_ids = []
        processed_indices = set()  # Track already added indices to avoid duplicates

        for desc in lane_descriptions:
            # Handle comma or Chinese comma separated lane descriptions
            sub_descs = desc.replace("、", ",").split(",")

            for sub_desc in sub_descs:
                sub_desc = sub_desc.strip()  # Remove whitespace

                if sub_desc in lane_mapping:
                    lane_index = lane_mapping[sub_desc]

                    # Validate lane index is within edge's lane count
                    if lane_index > max_lane_index:
                        logger.debug(f"Lane index {lane_index} exceeds max {max_lane_index} "
                                     f"for edge {edge_id}, skipping lane '{sub_desc}'")
                        continue

                    # Skip if already added this lane index
                    if lane_index in processed_indices:
                        logger.debug(f"Lane index {lane_index} already added, skipping duplicate")
                        continue

                    lane_id = f"{edge_id}_{lane_index}"
                    lane_ids.append(lane_id)
                    processed_indices.add(lane_index)
                    logger.debug(f"Mapped '{sub_desc}' → {lane_id}")
                elif sub_desc:  # Only warn if not empty
                    logger.warning(f"Unknown lane description: {sub_desc}, skipping")

        if not lane_ids:
            logger.warning(f"No valid lane IDs resolved from descriptions: {lane_descriptions}")

        return lane_ids

    def _convert_event_time(self, start_time: str, end_time: str,
                           sim_start_time: Optional[str] = None) -> Tuple[int, int]:
        """
        Convert absolute event times to simulation time (seconds from sim start).

        Args:
            start_time: Event start time (YYYY-MM-DD HH:MM:SS)
            end_time: Event end time (YYYY-MM-DD HH:MM:SS)
            sim_start_time: Simulation start time (YYYY-MM-DD HH:MM:SS)
                           If None, uses event start time as reference

        Returns:
            Tuple of (begin_seconds, end_seconds) for SUMO XML

        Raises:
            ValueError: If time parsing fails or time range is invalid
        """
        time_format = "%Y-%m-%d %H:%M:%S"

        try:
            event_start = datetime.strptime(start_time, time_format)
            event_end = datetime.strptime(end_time, time_format)

            # Determine simulation start reference point
            if sim_start_time:
                try:
                    sim_start = datetime.strptime(sim_start_time, time_format)
                except ValueError as e:
                    logger.error(f"Invalid sim_start_time format: {sim_start_time}")
                    raise ValueError(
                        f"Invalid sim_start_time format: {sim_start_time}. "
                        f"Expected: {time_format}"
                    ) from e
            else:
                # Default: simulation starts at event start time
                sim_start = event_start
                logger.debug("No sim_start_time provided, using event start as simulation start")

            # Calculate seconds from simulation start
            begin_seconds = int((event_start - sim_start).total_seconds())
            end_seconds = int((event_end - sim_start).total_seconds())

            # Validation and adjustments
            if begin_seconds < 0:
                logger.warning(
                    f"Event starts before simulation start: {begin_seconds}s. "
                    f"Event: {start_time}, Sim: {sim_start_time}. Setting begin to 0."
                )
                begin_seconds = 0

            if end_seconds <= begin_seconds:
                raise ValueError(
                    f"Invalid time range after conversion: end ({end_seconds}s) <= begin ({begin_seconds}s). "
                    f"Event times: {start_time} to {end_time}, Sim start: {sim_start_time or 'event start'}"
                )

            # Warn about very long events
            duration_hours = (end_seconds - begin_seconds) / 3600
            if duration_hours > 24:
                logger.warning(f"Event duration exceeds 24 hours: {duration_hours:.2f}h")

            logger.debug(f"Time conversion: {start_time} → {begin_seconds}s, {end_time} → {end_seconds}s")
            return begin_seconds, end_seconds

        except ValueError as e:
            if "does not match format" in str(e):
                logger.error(f"Time format error: {e}")
                raise ValueError(
                    f"Invalid time format. Expected '{time_format}'. "
                    f"start_time='{start_time}', end_time='{end_time}'"
                ) from e
            else:
                raise


class AccidentInjector(EventInjector):
    """Generate rerouter with closingLaneReroute XML for traffic accident events"""

    def generate_xml(self, event_data: Dict[str, Any]) -> str:
        """
        Generate rerouter XML with closingLaneReroute elements for accident.

        Args:
            event_data: Dictionary with keys:
                - report_id: Unique event identifier
                - edge_id: SUMO edge ID where accident occurred
                - affected_lanes: List of Chinese lane descriptions
                - start_time: Accident start time (YYYY-MM-DD HH:MM:SS)
                - end_time: Accident end time (YYYY-MM-DD HH:MM:SS)
                - sim_start_time (optional): Simulation start time

        Returns:
            XML string for rerouter with closingLaneReroute elements

        Raises:
            ValueError: If required fields missing or validation fails

        Example:
            <rerouter id="accident_12547" edges="-4688">
                <interval begin="6749" end="12069">
                    <closingLaneReroute id="-4688_0" disallow="all"/>
                </interval>
            </rerouter>
        """
        # Comprehensive validation
        self._validate_accident_event(event_data)

        # Resolve lane IDs
        lane_ids = self._resolve_lane_ids(
            event_data['edge_id'],
            event_data['affected_lanes']
        )

        if not lane_ids:
            raise ValueError(
                f"No valid lanes resolved for accident {event_data['report_id']}. "
                f"Provided lanes: {event_data['affected_lanes']}, edge: {event_data['edge_id']}"
            )

        # Convert times
        begin, end = self._convert_event_time(
            event_data['start_time'],
            event_data['end_time'],
            event_data.get('sim_start_time')
        )

        # Generate XML using SUMO's rerouter with closingLaneReroute elements
        xml_parts = []
        xml_parts.append(f'<rerouter id="accident_{event_data["report_id"]}" edges="{event_data["edge_id"]}">')
        xml_parts.append(f'    <interval begin="{begin}" end="{end}">')

        # Add closingLaneReroute for each lane
        for lane_id in lane_ids:
            xml_parts.append(f'        <closingLaneReroute id="{lane_id}" disallow="all"/>')

        xml_parts.append('    </interval>')
        xml_parts.append('</rerouter>')

        xml = '\n'.join(xml_parts)

        logger.info(f"Generated rerouter XML for accident {event_data['report_id']}: "
                   f"{len(lane_ids)} lanes closed from {begin}s to {end}s")
        return xml

    def _validate_accident_event(self, event_data: Dict[str, Any]) -> None:
        """
        Validate accident event data completeness and consistency.

        Args:
            event_data: Event data dictionary

        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        required_fields = ['report_id', 'edge_id', 'affected_lanes', 'start_time', 'end_time']
        missing_fields = [field for field in required_fields if field not in event_data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

        # Validate data types
        if not isinstance(event_data['report_id'], (str, int)):
            raise ValueError(f"Invalid report_id type: {type(event_data['report_id'])}")

        if not isinstance(event_data['edge_id'], str):
            raise ValueError(f"Invalid edge_id type: {type(event_data['edge_id'])}")

        if not isinstance(event_data['affected_lanes'], list):
            raise ValueError(f"Invalid affected_lanes type: {type(event_data['affected_lanes'])}")

        if not event_data['affected_lanes']:
            raise ValueError("affected_lanes list is empty")

        # Validate time format (basic check)
        time_format = "%Y-%m-%d %H:%M:%S"
        for time_field in ['start_time', 'end_time']:
            try:
                datetime.strptime(event_data[time_field], time_format)
            except ValueError as e:
                raise ValueError(f"Invalid {time_field} format: {event_data[time_field]}. "
                               f"Expected format: {time_format}") from e

        # Validate time order
        start = datetime.strptime(event_data['start_time'], time_format)
        end = datetime.strptime(event_data['end_time'], time_format)
        if end <= start:
            raise ValueError(
                f"end_time ({event_data['end_time']}) must be after start_time "
                f"({event_data['start_time']})"
            )

        # Validate event duration (warn if unrealistic)
        duration = (end - start).total_seconds() / 3600  # hours
        if duration > 24:
            logger.warning(f"Accident {event_data['report_id']} has unusually long duration: "
                         f"{duration:.2f} hours")
        elif duration < 0.05:  # < 3 minutes
            logger.warning(f"Accident {event_data['report_id']} has very short duration: "
                         f"{duration*60:.1f} minutes")

        logger.debug(f"Validation passed for accident {event_data['report_id']}")


class CongestionInjector(EventInjector):
    """
    Generate event description for congestion events (NO lane closure).

    Congestion events do NOT require physical lane closures in SUMO.
    Traffic management is handled solely through control strategies (VSS/TEC).
    Event details are preserved in event_description.json for reference.
    """

    def generate_xml(self, event_data: Dict[str, Any]) -> str:
        """
        Generate NO XML for congestion events (control strategy only).

        Args:
            event_data: Dictionary with keys:
                - report_id: Unique event identifier
                - edge_id: SUMO edge ID where congestion occurred
                - start_time: Congestion start time
                - end_time: Congestion end time

        Returns:
            Empty string (no lane closure, event description only)

        Note:
            Phase 3.5: Congestion events use control strategies without lane closures.
            The event is documented in event_description.json but does not inject
            any SUMO XML elements. Traffic management is handled by VSS/TEC strategies.
        """
        logger.info(
            f"Congestion event {event_data['report_id']} on edge {event_data['edge_id']}: "
            f"No lane closure injection (control strategy only)"
        )

        # Return empty string - no SUMO XML injection for congestion
        # Event details will be preserved in event_description.json
        return ""


class RoadControlInjector(EventInjector):
    """Generate rerouter with closingLaneReroute XML for road control events"""

    def generate_xml(self, event_data: Dict[str, Any]) -> str:
        """
        Generate rerouter XML with closingLaneReroute elements for road control events.

        Road control events (交通管制) are typically planned closures for maintenance,
        special events, or safety reasons. If no specific lanes are provided, ALL lanes
        on the edge are closed (common for toll station closures or weather-related controls).

        Args:
            event_data: Dictionary with keys:
                - report_id: Unique event identifier
                - edge_id: SUMO edge ID where control is applied
                - affected_lanes: List of Chinese lane descriptions (optional, if empty closes ALL lanes)
                - start_time: Control start time (YYYY-MM-DD HH:MM:SS)
                - end_time: Control end time (YYYY-MM-DD HH:MM:SS)
                - sim_start_time (optional): Simulation start time

        Returns:
            XML string for rerouter with closingLaneReroute elements

        Example (all lanes):
            <rerouter id="road_control_98765" edges="-4688">
                <interval begin="0" end="7200">
                    <closingLaneReroute id="-4688_0" disallow="all"/>
                    <closingLaneReroute id="-4688_1" disallow="all"/>
                </interval>
            </rerouter>
        """
        # Validate required fields (affected_lanes now optional)
        required_fields = ['report_id', 'edge_id', 'start_time', 'end_time']
        for field in required_fields:
            if field not in event_data:
                raise ValueError(f"Missing required field: {field}")

        # Check if affected_lanes provided
        affected_lanes = event_data.get('affected_lanes', [])

        # If no specific lanes, close ALL lanes on edge
        if not affected_lanes or (isinstance(affected_lanes, list) and len(affected_lanes) == 0):
            logger.info(f"No specific lanes for road control {event_data['report_id']}, closing ALL lanes on edge {event_data['edge_id']}")
            lane_ids = self._get_all_lanes_on_edge(event_data['edge_id'])
        else:
            # Resolve specific lane IDs
            lane_ids = self._resolve_lane_ids(
                event_data['edge_id'],
                affected_lanes
            )

        if not lane_ids:
            raise ValueError(
                f"No valid lanes resolved for road control {event_data['report_id']}. "
                f"Edge: {event_data['edge_id']}"
            )

        # Convert times
        begin, end = self._convert_event_time(
            event_data['start_time'],
            event_data['end_time'],
            event_data.get('sim_start_time')
        )

        # Generate XML using SUMO's rerouter with closingLaneReroute elements
        xml_parts = []
        xml_parts.append(f'<rerouter id="road_control_{event_data["report_id"]}" edges="{event_data["edge_id"]}">')
        xml_parts.append(f'    <interval begin="{begin}" end="{end}">')

        # Add closingLaneReroute for each lane
        for lane_id in lane_ids:
            xml_parts.append(f'        <closingLaneReroute id="{lane_id}" disallow="all"/>')

        xml_parts.append('    </interval>')
        xml_parts.append('</rerouter>')

        xml = '\n'.join(xml_parts)

        logger.info(f"Generated rerouter XML for road control {event_data['report_id']}: "
                   f"{len(lane_ids)} lanes closed from {begin}s to {end}s")
        return xml

    def _get_all_lanes_on_edge(self, edge_id: str) -> List[str]:
        """
        Get all lane IDs for an edge (for全车道关闭).

        Args:
            edge_id: SUMO edge ID

        Returns:
            List of all lane IDs on the edge (e.g., ['-4688_0', '-4688_1'])
        """
        if not self.network:
            logger.warning(f"No network file provided, defaulting to 2 lanes for edge {edge_id}")
            return [f"{edge_id}_0", f"{edge_id}_1"]

        try:
            edge = self.network.getEdge(edge_id)
            num_lanes = edge.getLaneNumber()
            lane_ids = [f"{edge_id}_{i}" for i in range(num_lanes)]
            logger.info(f"Edge {edge_id} has {num_lanes} lanes: {lane_ids}")
            return lane_ids
        except Exception as e:
            logger.warning(f"Could not get lanes for edge {edge_id}: {e}. Defaulting to 2 lanes")
            return [f"{edge_id}_0", f"{edge_id}_1"]


class GeologicalInjector(EventInjector):
    """Generate rerouter with closingLaneReroute XML for geological disaster events"""

    def generate_xml(self, event_data: Dict[str, Any]) -> str:
        """
        Generate rerouter XML with closingLaneReroute elements for geological disasters.

        Geological disasters (地质灾害) such as landslides, rockfalls typically
        result in extended lane closures and may affect multiple lanes.

        Args:
            event_data: Dictionary with keys:
                - report_id: Unique event identifier
                - edge_id: SUMO edge ID where disaster occurred
                - affected_lanes: List of Chinese lane descriptions
                - start_time: Disaster start time (YYYY-MM-DD HH:MM:SS)
                - end_time: Disaster end time (YYYY-MM-DD HH:MM:SS)
                - sim_start_time (optional): Simulation start time

        Returns:
            XML string for rerouter with closingLaneReroute elements

        Example:
            <rerouter id="geological_54321" edges="-4688">
                <interval begin="0" end="36000">
                    <closingLaneReroute id="-4688_0" disallow="all"/>
                    <closingLaneReroute id="-4688_1" disallow="all"/>
                </interval>
            </rerouter>
        """
        # Validate required fields
        required_fields = ['report_id', 'edge_id', 'affected_lanes', 'start_time', 'end_time']
        for field in required_fields:
            if field not in event_data:
                raise ValueError(f"Missing required field: {field}")

        # Resolve lane IDs
        lane_ids = self._resolve_lane_ids(
            event_data['edge_id'],
            event_data['affected_lanes']
        )

        if not lane_ids:
            raise ValueError(
                f"No valid lanes resolved for geological disaster {event_data['report_id']}. "
                f"Provided lanes: {event_data['affected_lanes']}, edge: {event_data['edge_id']}"
            )

        # Convert times
        begin, end = self._convert_event_time(
            event_data['start_time'],
            event_data['end_time'],
            event_data.get('sim_start_time')
        )

        # Warn if duration seems short for geological disaster
        duration_hours = (end - begin) / 3600
        if duration_hours < 4:
            logger.warning(f"Geological disaster {event_data['report_id']} has short duration: "
                         f"{duration_hours:.2f} hours. Geological events typically last longer.")

        # Generate XML using SUMO's rerouter with closingLaneReroute elements
        xml_parts = []
        xml_parts.append(f'<rerouter id="geological_{event_data["report_id"]}" edges="{event_data["edge_id"]}">')
        xml_parts.append(f'    <interval begin="{begin}" end="{end}">')

        # Add closingLaneReroute for each lane
        for lane_id in lane_ids:
            xml_parts.append(f'        <closingLaneReroute id="{lane_id}" disallow="all"/>')

        xml_parts.append('    </interval>')
        xml_parts.append('</rerouter>')

        xml = '\n'.join(xml_parts)

        logger.info(f"Generated rerouter XML for geological disaster {event_data['report_id']}: "
                   f"{len(lane_ids)} lanes closed from {begin}s to {end}s")
        return xml


class BreakdownInjector(EventInjector):
    """Generate rerouter with closingLaneReroute XML for vehicle breakdown events"""

    def generate_xml(self, event_data: Dict[str, Any]) -> str:
        """
        Generate rerouter XML with closingLaneReroute elements for vehicle breakdowns.

        Vehicle breakdowns (车辆故障) typically result in short-term lane
        blockages, usually affecting emergency lanes or single lanes.

        Args:
            event_data: Dictionary with keys:
                - report_id: Unique event identifier
                - edge_id: SUMO edge ID where breakdown occurred
                - affected_lanes: List of Chinese lane descriptions
                - start_time: Breakdown start time (YYYY-MM-DD HH:MM:SS)
                - end_time: Breakdown end time (YYYY-MM-DD HH:MM:SS)
                - sim_start_time (optional): Simulation start time

        Returns:
            XML string for rerouter with closingLaneReroute elements

        Example:
            <rerouter id="breakdown_11223" edges="-4688">
                <interval begin="0" end="1800">
                    <closingLaneReroute id="-4688_0" disallow="all"/>
                </interval>
            </rerouter>
        """
        # Validate required fields
        required_fields = ['report_id', 'edge_id', 'affected_lanes', 'start_time', 'end_time']
        for field in required_fields:
            if field not in event_data:
                raise ValueError(f"Missing required field: {field}")

        # Resolve lane IDs
        lane_ids = self._resolve_lane_ids(
            event_data['edge_id'],
            event_data['affected_lanes']
        )

        if not lane_ids:
            raise ValueError(
                f"No valid lanes resolved for breakdown {event_data['report_id']}. "
                f"Provided lanes: {event_data['affected_lanes']}, edge: {event_data['edge_id']}"
            )

        # Convert times
        begin, end = self._convert_event_time(
            event_data['start_time'],
            event_data['end_time'],
            event_data.get('sim_start_time')
        )

        # Warn if duration seems very long for breakdown
        duration_hours = (end - begin) / 3600
        if duration_hours > 3:
            logger.warning(f"Breakdown {event_data['report_id']} has unusually long duration: "
                         f"{duration_hours:.2f} hours. Most breakdowns are cleared quickly.")

        # Generate XML using SUMO's rerouter with closingLaneReroute elements
        xml_parts = []
        xml_parts.append(f'<rerouter id="breakdown_{event_data["report_id"]}" edges="{event_data["edge_id"]}">')
        xml_parts.append(f'    <interval begin="{begin}" end="{end}">')

        # Add closingLaneReroute for each lane
        for lane_id in lane_ids:
            xml_parts.append(f'        <closingLaneReroute id="{lane_id}" disallow="all"/>')

        xml_parts.append('    </interval>')
        xml_parts.append('</rerouter>')

        xml = '\n'.join(xml_parts)

        logger.info(f"Generated rerouter XML for breakdown {event_data['report_id']}: "
                   f"{len(lane_ids)} lanes closed from {begin}s to {end}s")
        return xml


class WeatherInjector(EventInjector):
    """Generate rerouter with closingLaneReroute XML for severe weather events"""

    def generate_xml(self, event_data: Dict[str, Any]) -> str:
        """
        Generate rerouter XML with closingLaneReroute elements for severe weather events.

        Severe weather (恶劣天气) such as heavy rain, fog, snow may require
        lane closures for safety. In SUMO, we model this as lane closures.

        Note: Full weather simulation (visibility, friction) requires vType
        modifications which are not implemented in this phase.

        Args:
            event_data: Dictionary with keys:
                - report_id: Unique event identifier
                - edge_id: SUMO edge ID where weather affects traffic
                - affected_lanes: List of Chinese lane descriptions
                - start_time: Weather event start time (YYYY-MM-DD HH:MM:SS)
                - end_time: Weather event end time (YYYY-MM-DD HH:MM:SS)
                - sim_start_time (optional): Simulation start time

        Returns:
            XML string for rerouter with closingLaneReroute elements

        Example:
            <rerouter id="weather_99887" edges="-4688">
                <interval begin="0" end="5400">
                    <closingLaneReroute id="-4688_0" disallow="all"/>
                </interval>
            </rerouter>
        """
        # Validate required fields
        required_fields = ['report_id', 'edge_id', 'affected_lanes', 'start_time', 'end_time']
        for field in required_fields:
            if field not in event_data:
                raise ValueError(f"Missing required field: {field}")

        # Resolve lane IDs
        lane_ids = self._resolve_lane_ids(
            event_data['edge_id'],
            event_data['affected_lanes']
        )

        if not lane_ids:
            raise ValueError(
                f"No valid lanes resolved for weather event {event_data['report_id']}. "
                f"Provided lanes: {event_data['affected_lanes']}, edge: {event_data['edge_id']}"
            )

        # Convert times
        begin, end = self._convert_event_time(
            event_data['start_time'],
            event_data['end_time'],
            event_data.get('sim_start_time')
        )

        # Generate XML using SUMO's rerouter with closingLaneReroute elements
        xml_parts = []
        xml_parts.append(f'<rerouter id="weather_{event_data["report_id"]}" edges="{event_data["edge_id"]}">')
        xml_parts.append(f'    <interval begin="{begin}" end="{end}">')

        # Add closingLaneReroute for each lane
        for lane_id in lane_ids:
            xml_parts.append(f'        <closingLaneReroute id="{lane_id}" disallow="all"/>')

        xml_parts.append('    </interval>')
        xml_parts.append('</rerouter>')

        xml = '\n'.join(xml_parts)

        logger.info(f"Generated rerouter XML for weather event {event_data['report_id']}: "
                   f"{len(lane_ids)} lanes closed from {begin}s to {end}s")
        logger.info("Note: Weather simulation using lane closures only. "
                   "Advanced weather effects (visibility, friction) not implemented.")
        return xml


def create_event_injector(event_type: str, network_file: Optional[str] = None) -> EventInjector:
    """
    Factory function to create appropriate event injector.

    Args:
        event_type: Type of event (交通事故, 交通阻塞, 交通管制, 地质灾害, 车辆故障, 恶劣天气, 流量激增工况)
        network_file: Optional path to SUMO network file

    Returns:
        EventInjector instance for the specified event type

    Raises:
        ValueError: If event type is not supported

    Supported Event Types:
        - 交通事故 (Traffic Accident): rerouter with closingLaneReroute for accidents
        - 交通阻塞 (Traffic Congestion): rerouter XML (placeholder)
        - 交通管制 (Road Control): rerouter with closingLaneReroute for planned closures
        - 地质灾害 (Geological Disaster): rerouter with closingLaneReroute for landslides/rockfalls
        - 车辆故障 (Vehicle Breakdown): rerouter with closingLaneReroute for short-term blockages
        - 恶劣天气 (Severe Weather): rerouter with closingLaneReroute for weather-related closures
        - 流量激增工况 (Flow Surge Workload): No XML injection (control strategy only)
    """
    injectors = {
        "交通事故": AccidentInjector,
        "交通阻塞": CongestionInjector,
        "交通管制": RoadControlInjector,
        "地质灾害": GeologicalInjector,
        "车辆故障": BreakdownInjector,
        "恶劣天气": WeatherInjector,
        "流量激增工况": CongestionInjector,  # Flow surge uses same injector (no XML)
    }

    if event_type not in injectors:
        raise ValueError(
            f"Unsupported event type: {event_type}. "
            f"Supported types: {list(injectors.keys())}"
        )

    return injectors[event_type](network_file=network_file)
