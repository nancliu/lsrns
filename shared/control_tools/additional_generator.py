"""
SUMO Additional File Generator for Control Strategies (v2.0)

Generates SUMO additional XML files for control strategies based on v2.0
template specifications. Supports VSS (Variable Speed Sign), DHS (Dynamic Hard
Shoulder), and TEC (Toll Entrance Control) strategies.

Key enhancements (2025-11-02):
- Case metadata time handling: Loads case.metadata.time_range.start for context
- TWO-LAYER vehicle type conversion: UI types → vehicle_types.json → SUMO vClass
- Comprehensive parameter transformation validation
- Full assertions for data integrity

Functions:
- generate_strategy_xml: Main entry point for XML generation
- generate_vss_xml: Generate variableSpeedSign XML element
- generate_dhs_xml: Generate rerouter XML element for hard shoulder control
- generate_tec_xml: Generate calibrator or rerouter XML for toll control
- _map_vehicle_type_to_sumo: TWO-LAYER vehicle type conversion
- _extract_case_start_hour: Extract simulation start hour from case metadata
"""

import logging
from typing import Dict, Any, Optional, List
from xml.etree.ElementTree import Element, SubElement, tostring
import re
from datetime import datetime

logger = logging.getLogger(__name__)


def _extract_case_start_hour(case_metadata: Dict[str, Any]) -> Optional[int]:
    """
    Extract simulation start hour from case metadata.

    Per design specification (2025-11-02):
    - Source: case.metadata.time_range.start (UTC+8 timestamp)
    - Format: "2025/09/01 08:00:00"
    - Returns: Hour of day [0-23]
    - Note: Ignores timezone errors in metadata (timezone not always specified)

    Args:
        case_metadata: Case metadata dictionary with time_range

    Returns:
        Hour of day [0-23] or None if metadata not available

    Raises:
        ValueError: If time_range.start format is invalid
    """
    try:
        if not case_metadata or "time_range" not in case_metadata:
            logger.warning("Case metadata missing time_range, time conversion may be inaccurate")
            return None

        time_range = case_metadata.get("time_range", {})
        start_time_str = time_range.get("start")

        if not start_time_str:
            logger.warning("time_range.start not found in case metadata")
            return None

        # Parse timestamp format: "2025/09/01 08:00:00"
        # Handle both "/" and "-" date separators
        time_match = re.search(r'(\d{1,2}):(\d{2}):(\d{2})', start_time_str)
        if not time_match:
            raise ValueError(f"Cannot parse time from case metadata: {start_time_str}")

        hour = int(time_match.group(1))
        assert 0 <= hour <= 23, f"Hour out of range [0-23]: {hour}"

        logger.debug(f"Extracted case start hour: {hour} from {start_time_str}")
        return hour

    except Exception as e:
        logger.error(f"Error extracting case start hour: {e}")
        raise


def _map_vehicle_types_to_sumo(
    allowed_ui_types: List[str],
    vehicle_types_config: Optional[Dict[str, Any]] = None
) -> str:
    """
    TWO-LAYER vehicle type conversion: UI types → SUMO vClass.

    Per design specification (2025-11-02):
    - Layer 1: Validate UI types exist in vehicle_types.json categories
    - Layer 2: Map to SUMO vClass by extracting .category field

    UI types (from strategy instance):
    - "passenger", "truck", "delivery", etc.

    Conversion via vehicle_types.json:
    - "passenger_small" → category "passenger" → SUMO vClass "passenger"
    - "truck_large" → category "truck" → SUMO vClass "truck"
    - "special_small" → category "delivery" → SUMO vClass "delivery"

    Args:
        allowed_ui_types: UI vehicle types from strategy instance
                         (e.g., ["passenger", "truck", "delivery"])
        vehicle_types_config: Optional vehicle_types.json config for validation
                             If None, performs basic validation only

    Returns:
        Space-separated SUMO vClass string (e.g., "passenger truck")
        Empty string if no valid types

    Raises:
        ValueError: If UI type not found in vehicle_types.json categories
    """
    if not allowed_ui_types:
        logger.debug("No vehicle types specified, lane fully closed")
        return ""

    sumo_types = set()

    # If vehicle_types_config provided, validate against it
    if vehicle_types_config:
        # Layer 1: Build valid categories from vehicle_types.json
        valid_categories = set()
        for vehicle_key, vehicle_config in vehicle_types_config.get("vehicle_types", {}).items():
            category = vehicle_config.get("category")
            if category:
                valid_categories.add(category)

        logger.debug(f"Valid vehicle categories from config: {valid_categories}")

        # Layer 2: Map UI types to SUMO vClass (extract category field)
        for ui_type in allowed_ui_types:
            if ui_type not in valid_categories:
                raise ValueError(
                    f"Vehicle type '{ui_type}' not found in vehicle_types.json categories. "
                    f"Valid types: {sorted(valid_categories)}"
                )
            # Category IS the SUMO vClass
            sumo_types.add(ui_type)
            logger.debug(f"Mapped UI type '{ui_type}' to SUMO vClass '{ui_type}'")
    else:
        # Basic validation without config file
        logger.warning("vehicle_types_config not provided, using basic validation only")
        for ui_type in allowed_ui_types:
            sumo_types.add(ui_type)

    # Result: space-separated SUMO types for XML
    result = " ".join(sorted(sumo_types)) if sumo_types else ""
    logger.debug(f"TWO-LAYER vehicle type conversion result: '{result}'")
    return result


def generate_strategy_xml(
    template_id: str,
    template: Dict[str, Any],
    parameters: Dict[str, Any]
) -> str:
    """
    Generate SUMO XML content for a strategy based on template and parameters.

    Dispatches to type-specific generators (VSS, DHS, TEC) based on template.

    Args:
        template_id: Unique template identifier
        template: Template dictionary with strategy_type and schema
        parameters: Validated and converted parameters

    Returns:
        XML string representation of the strategy

    Raises:
        ValueError: If strategy type is unsupported or parameters invalid
    """
    strategy_type = template.get("strategy_type")
    logger.info(f"Generating XML for {strategy_type} strategy: {template_id}")

    if strategy_type == "VSS":
        return generate_vss_xml(template_id, template, parameters)
    elif strategy_type == "DHS":
        return generate_dhs_xml(template_id, template, parameters)
    elif strategy_type == "TEC":
        return generate_tec_xml(template_id, template, parameters)
    else:
        raise ValueError(f"Unsupported strategy type: {strategy_type}")


def generate_vss_xml(
    strategy_id: str,
    template: Dict[str, Any],
    parameters: Dict[str, Any]
) -> str:
    """
    Generate SUMO variableSpeedSign XML element.

    Structure:
        <variableSpeedSign id="strategy_id" edges="edge1 edge2 ...">
            <step time="0" speed="27.78"/>
            <step time="25200" speed="22.22"/>
        </variableSpeedSign>

    Args:
        strategy_id: Strategy identifier (becomes element id)
        template: VSS template dictionary
        parameters: Strategy parameters with affected_edges and speed_steps

    Returns:
        XML string of variableSpeedSign element
    """
    logger.info(f"Generating VSS XML for strategy: {strategy_id}")

    try:
        # Extract parameters（严格从parameters获取，无回退）
        affected_edges = parameters.get("affected_edges", [])
        if not affected_edges:
            raise ValueError(f"VSS strategy {strategy_id} requires 'affected_edges' in parameters")
        speed_steps = parameters.get("speed_steps", [])

        # Create root element
        vss_elem = Element("variableSpeedSign")
        vss_elem.set("id", strategy_id)

        # Add edges attribute (space-separated)
        if affected_edges:
            vss_elem.set("edges", " ".join(affected_edges))

        # Add speed steps
        for step in speed_steps:
            step_elem = SubElement(vss_elem, "step")

            # Time in seconds (with assertions for SUMO bounds)
            time_seconds = None
            if "time_seconds" in step:
                time_seconds = int(step["time_seconds"])
            elif "time_hours" in step:
                # Convert hours to seconds if needed
                time_hours = float(step["time_hours"])
                assert 0 <= time_hours <= 24, f"time_hours {time_hours} out of range [0, 24]"
                time_seconds = int(time_hours * 3600)
            else:
                continue

            # ASSERTION: Validate time bounds for SUMO
            assert 0 <= time_seconds <= 86400, f"Time {time_seconds}s out of SUMO bounds [0, 86400]"
            step_elem.set("time", str(time_seconds))

            # Speed in m/s (with assertions for SUMO bounds and precision)
            speed_ms = None
            if "speed_ms" in step:
                speed_ms = round(float(step["speed_ms"]), 2)
            elif "speed_kmh" in step:
                # Convert km/h to m/s: divide by 3.6
                speed_kmh = float(step["speed_kmh"])
                assert 30 <= speed_kmh <= 130, f"speed_kmh {speed_kmh} out of range [30, 130]"
                speed_ms = round(speed_kmh / 3.6, 2)
            else:
                continue

            # ASSERTION: Validate speed bounds for SUMO
            assert 0 <= speed_ms <= 50.0, f"Speed {speed_ms}m/s out of SUMO bounds [0, 50]"
            # ASSERTION: Verify 2 decimal precision
            assert len(str(speed_ms).split('.')[-1]) <= 2, f"Speed precision error: {speed_ms}"

            step_elem.set("speed", str(speed_ms))
            logger.debug(f"VSS step: time={time_seconds}s, speed={speed_ms}m/s")

        # Convert to string
        xml_str = tostring(vss_elem, encoding="unicode")
        logger.debug(f"Generated VSS XML: {xml_str}")

        return xml_str

    except Exception as e:
        logger.error(f"Error generating VSS XML: {e}", exc_info=True)
        raise


def generate_dhs_xml(
    strategy_id: str,
    template: Dict[str, Any],
    parameters: Dict[str, Any]
) -> str:
    """
    Generate SUMO rerouter XML element for hard shoulder control.

    Structure:
        <rerouter id="strategy_id" edges="edge1 edge2 ...">
            <interval begin="0" end="25200">
                <closingLaneReroute id="0" allow="passenger bus truck emergency"/>
            </interval>
            <interval begin="25200" end="32400">
                <closingLaneReroute id="0" allow=""/>
            </interval>
        </rerouter>

    Args:
        strategy_id: Strategy identifier (becomes element id)
        template: DHS template dictionary
        parameters: Strategy parameters with affected_edges, intervals, etc.

    Returns:
        XML string of rerouter element
    """
    logger.info(f"Generating DHS XML for strategy: {strategy_id}")

    try:
        # Extract parameters（严格从parameters获取，无回退）
        affected_edges = parameters.get("affected_edges", [])
        if not affected_edges:
            raise ValueError(f"DHS strategy {strategy_id} requires 'affected_edges' in parameters")
        hard_shoulder_lane = parameters.get("hard_shoulder_lane_index", 3)
        intervals = parameters.get("intervals", [])

        # Create root element
        rerouter_elem = Element("rerouter")
        rerouter_elem.set("id", strategy_id)

        # Add edges attribute (space-separated)
        if affected_edges:
            rerouter_elem.set("edges", " ".join(affected_edges))

        # Add intervals
        for interval in intervals:
            interval_elem = SubElement(rerouter_elem, "interval")

            # Begin time in seconds
            if "begin_seconds" in interval:
                begin_seconds = int(interval["begin_seconds"])
            elif "begin_hours" in interval:
                begin_seconds = int(interval["begin_hours"] * 3600)
            else:
                continue

            # End time in seconds
            if "end_seconds" in interval:
                end_seconds = int(interval["end_seconds"])
            elif "end_hours" in interval:
                end_seconds = int(interval["end_hours"] * 3600)
            else:
                continue

            # ASSERTION: Validate time bounds
            assert 0 <= begin_seconds <= 86400, f"Begin time {begin_seconds}s out of SUMO bounds [0, 86400]"
            assert 0 <= end_seconds <= 86400, f"End time {end_seconds}s out of SUMO bounds [0, 86400]"
            assert begin_seconds < end_seconds, f"Begin time {begin_seconds}s must be < end time {end_seconds}s"

            interval_elem.set("begin", str(begin_seconds))
            interval_elem.set("end", str(end_seconds))

            # Add closingLaneReroute element for hard shoulder
            status = interval.get("status", "CLOSED")
            allowed_types = interval.get("allowed_vehicle_types", [])

            # Create closingLaneReroute for the hard shoulder lane
            closing_elem = SubElement(interval_elem, "closingLaneReroute")
            closing_elem.set("id", str(hard_shoulder_lane))

            # TWO-LAYER vehicle type conversion (2025-11-02 enhancement)
            # Layer 1: Validate UI types exist in vehicle_types.json
            # Layer 2: Map to SUMO vClass by extracting category field
            if status == "OPEN" and allowed_types:
                try:
                    sumo_allow = _map_vehicle_types_to_sumo(allowed_types, vehicle_types_config=None)
                    closing_elem.set("allow", sumo_allow)
                    logger.debug(f"DHS interval {begin_seconds}-{end_seconds}: vehicle types {allowed_types} → '{sumo_allow}'")
                except ValueError as e:
                    logger.error(f"Vehicle type conversion failed for DHS: {e}")
                    raise
            else:
                # Closed interval
                closing_elem.set("allow", "")

        # Convert to string
        xml_str = tostring(rerouter_elem, encoding="unicode")
        logger.debug(f"Generated DHS XML: {xml_str}")

        return xml_str

    except Exception as e:
        logger.error(f"Error generating DHS XML: {e}", exc_info=True)
        raise


def generate_tec_xml(
    strategy_id: str,
    template: Dict[str, Any],
    parameters: Dict[str, Any]
) -> str:
    """
    Generate SUMO calibrator or rerouter XML for toll entrance control.

    Supports two modes:
    1. Metering mode (calibrator): Controls flow rates
    2. Closure/restriction mode (rerouter): Blocks or restricts vehicles

    Metering structure:
        <calibrator id="strategy_id" edge="edge_id" pos="0">
            <flow begin="0" end="25200" vehsPerHour="480" speed="15"/>
            <flow begin="25200" end="32400" vehsPerHour="180" speed="12"/>
        </calibrator>

    Closure structure:
        <rerouter id="strategy_id" edges="edge1 ...">
            <interval begin="0" end="86400">
                <closingReroute allow=""/>
            </interval>
        </rerouter>

    Args:
        strategy_id: Strategy identifier (becomes element id)
        template: TEC template dictionary
        parameters: Strategy parameters with entrance info, flow intervals, etc.

    Returns:
        XML string of calibrator or rerouter element
    """
    logger.info(f"Generating TEC XML for strategy: {strategy_id}")

    try:
        # Determine control mode (metering, closure, restriction)
        control_mode = parameters.get("control_mode", "metering")

        if control_mode == "metering":
            return _generate_tec_metering_xml(strategy_id, template, parameters)
        elif control_mode in ["closure", "restriction"]:
            return _generate_tec_closure_xml(strategy_id, template, parameters)
        else:
            logger.warning(f"Unknown TEC control mode: {control_mode}, defaulting to closure")
            return _generate_tec_closure_xml(strategy_id, template, parameters)

    except Exception as e:
        logger.error(f"Error generating TEC XML: {e}", exc_info=True)
        raise


def _generate_tec_metering_xml(
    strategy_id: str,
    template: Dict[str, Any],
    parameters: Dict[str, Any]
) -> str:
    """Generate TEC metering (ramp metering) XML with flow control.

    Requires entrance_edges in parameters (strict format, no fallback).
    """
    logger.debug(f"Generating TEC metering XML: {strategy_id}")

    # 严格从parameters获取entrance_edges（无回退）
    entrance_edges = parameters.get("entrance_edges", [])
    if not entrance_edges:
        raise ValueError(f"TEC strategy {strategy_id} requires 'entrance_edges' in parameters")

    # For now, only use the first entrance edge (single calibrator)
    # Future enhancement: generate multiple calibrators for multiple entrances
    entrance_edge = entrance_edges[0]

    if len(entrance_edges) > 1:
        logger.warning(f"TEC metering currently supports only one entrance. Using first: {entrance_edge}")

    # Create calibrator element
    calibrator_elem = Element("calibrator")
    calibrator_elem.set("id", strategy_id)
    calibrator_elem.set("edge", entrance_edge)
    calibrator_elem.set("pos", "0")

    # Add flow intervals
    flow_intervals = parameters.get("flow_intervals", [])
    for flow in flow_intervals:
        flow_elem = SubElement(calibrator_elem, "flow")

        # Begin time
        if "begin_seconds" in flow:
            begin_seconds = int(flow["begin_seconds"])
        elif "begin_hours" in flow:
            begin_seconds = int(flow["begin_hours"] * 3600)
        else:
            continue

        # End time
        if "end_seconds" in flow:
            end_seconds = int(flow["end_seconds"])
        elif "end_hours" in flow:
            end_seconds = int(flow["end_hours"] * 3600)
        else:
            continue

        flow_elem.set("begin", str(begin_seconds))
        flow_elem.set("end", str(end_seconds))

        # Flow rate (vehicles per hour)
        if "vehsPerHour" in flow:
            flow_elem.set("vehsPerHour", str(int(flow["vehsPerHour"])))

        # Target speed (m/s)
        if "target_speed" in flow:
            target_speed = flow["target_speed"]
            if isinstance(target_speed, float):
                flow_elem.set("speed", str(round(target_speed, 2)))
            else:
                flow_elem.set("speed", str(target_speed))

    # Convert to string
    xml_str = tostring(calibrator_elem, encoding="unicode")
    logger.debug(f"Generated TEC metering XML: {xml_str}")

    return xml_str


def _generate_tec_closure_xml(
    strategy_id: str,
    template: Dict[str, Any],
    parameters: Dict[str, Any]
) -> str:
    """Generate TEC closure/restriction XML using rerouter."""
    logger.debug(f"Generating TEC closure/restriction XML: {strategy_id}")

    # 严格从parameters获取entrance_edges（无回退）
    entrance_edges = parameters.get("entrance_edges", [])
    if not entrance_edges:
        raise ValueError(f"TEC strategy {strategy_id} requires 'entrance_edges' in parameters")

    # Create rerouter element
    rerouter_elem = Element("rerouter")
    rerouter_elem.set("id", strategy_id)
    rerouter_elem.set("edges", " ".join(entrance_edges))

    # Add closure intervals
    closure_intervals = parameters.get("closure_intervals", [])
    allowed_types = parameters.get("allowed_vehicle_types", [])

    # If no intervals specified, create a single interval covering full day
    if not closure_intervals:
        closure_intervals = [
            {"begin_hours": 0, "end_hours": 24}
        ]

    for interval in closure_intervals:
        interval_elem = SubElement(rerouter_elem, "interval")

        # Begin time
        if "begin_seconds" in interval:
            begin_seconds = int(interval["begin_seconds"])
        elif "begin_hours" in interval:
            begin_seconds = int(interval["begin_hours"] * 3600)
        else:
            begin_seconds = 0

        # End time
        if "end_seconds" in interval:
            end_seconds = int(interval["end_seconds"])
        elif "end_hours" in interval:
            end_seconds = int(interval["end_hours"] * 3600)
        else:
            end_seconds = 86400  # Full day

        interval_elem.set("begin", str(begin_seconds))
        interval_elem.set("end", str(end_seconds))

        # Add closingReroute element
        closing_elem = SubElement(interval_elem, "closingReroute")

        # Set allow attribute
        if allowed_types:
            closing_elem.set("allow", " ".join(allowed_types))
        else:
            closing_elem.set("allow", "")  # Empty = block all vehicles

    # Convert to string
    xml_str = tostring(rerouter_elem, encoding="unicode")
    logger.debug(f"Generated TEC closure XML: {xml_str}")

    return xml_str


def validate_generated_xml(xml_content: str) -> tuple[bool, str]:
    """
    Validate that generated XML is well-formed.

    Uses ElementTree to parse the XML and check for structural validity.

    Args:
        xml_content: XML string to validate

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if XML is well-formed
        - error_message: Error description if invalid, empty string if valid
    """
    try:
        from xml.etree.ElementTree import fromstring

        # Try to parse the XML
        fromstring(xml_content)

        logger.debug("XML validation passed")
        return True, ""

    except Exception as e:
        error_msg = f"XML validation failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def generate_plan_additional(
    plan_id: str,
    plan_name: str,
    strategies: List[Dict[str, Any]]
) -> str:
    """
    Generate plan-level control.add.xml by combining multiple strategies.

    Merges multiple strategy XML elements into a single <additional> root,
    organized by strategy type (VSS, DHS, TEC).

    Args:
        plan_id: Plan identifier
        plan_name: Plan name for documentation
        strategies: List of strategy instance dictionaries with complete configuration

    Returns:
        Formatted XML string with all strategies combined

    Example output:
        <?xml version="1.0" encoding="UTF-8"?>
        <additional>
            <!-- 方案: 早高峰综合管控方案A (plan_20251025_140530_a1b2c) -->
            <!-- 生成时间: 2025-10-25 14:05:30 -->

            <!-- ==================== VSS策略组 ==================== -->
            <!-- 策略: strategy_001 - K10-K15路段限速80km/h -->
            <variableSpeedSign id="strategy_001" lanes="...">
                ...
            </variableSpeedSign>

            <!-- ==================== DHS策略组 ==================== -->
            ...
        </additional>
    """
    from datetime import datetime
    from xml.etree.ElementTree import Element, SubElement, fromstring, tostring
    from xml.dom.minidom import parseString

    logger.info(f"Generating plan additional XML: {plan_id}")

    # Create root element
    additional = Element("additional")

    # Add plan header comments
    header_comment = (
        f"\n    方案: {plan_name} ({plan_id})\n"
        f"    生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n    "
    )

    # Group strategies by type
    vss_strategies = []
    dhs_strategies = []
    tec_strategies = []

    for strategy in strategies:
        strategy_type = strategy.get("template", {}).get("strategy_type")
        if strategy_type == "VSS":
            vss_strategies.append(strategy)
        elif strategy_type == "DHS":
            dhs_strategies.append(strategy)
        elif strategy_type == "TEC":
            tec_strategies.append(strategy)
        else:
            logger.warning(f"Unknown strategy type: {strategy_type}, strategy_id: {strategy.get('strategy_id')}")

    # Build XML content parts
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>\n<additional>']
    xml_parts.append(f"    <!--{header_comment}-->")

    # Add VSS strategies
    if vss_strategies:
        xml_parts.append("\n    <!-- ==================== VSS策略组 ==================== -->")
        for strategy in vss_strategies:
            strategy_id = strategy.get("strategy_id")
            strategy_name = strategy.get("strategy_name", "")
            xml_parts.append(f"\n    <!-- 策略: {strategy_id} - {strategy_name} -->")

            try:
                # Generate strategy XML
                template = strategy.get("template", {})
                parameters = strategy.get("parameters", {})
                
                # 验证edges在parameters中（严格检查）
                if "affected_edges" not in parameters:
                    raise ValueError(
                        f"VSS strategy {strategy_id} missing 'affected_edges' in parameters. "
                        f"Available keys: {list(parameters.keys())}"
                    )
                
                strategy_xml = generate_strategy_xml(
                    template_id=strategy.get("template_id", ""),
                    template=template,
                    parameters=parameters
                )

                # Format and indent the XML
                xml_parts.append(f"    {strategy_xml}")

            except Exception as e:
                logger.error(f"Error generating XML for strategy {strategy_id}: {e}")

    # Add DHS strategies
    if dhs_strategies:
        xml_parts.append("\n    <!-- ==================== DHS策略组 ==================== -->")
        for strategy in dhs_strategies:
            strategy_id = strategy.get("strategy_id")
            strategy_name = strategy.get("strategy_name", "")
            xml_parts.append(f"\n    <!-- 策略: {strategy_id} - {strategy_name} -->")

            try:
                template = strategy.get("template", {})
                parameters = strategy.get("parameters", {})
                
                # 验证edges在parameters中（严格检查）
                if "affected_edges" not in parameters:
                    raise ValueError(
                        f"DHS strategy {strategy_id} missing 'affected_edges' in parameters. "
                        f"Available keys: {list(parameters.keys())}"
                    )
                
                strategy_xml = generate_strategy_xml(
                    template_id=strategy.get("template_id", ""),
                    template=template,
                    parameters=parameters
                )
                xml_parts.append(f"    {strategy_xml}")

            except Exception as e:
                logger.error(f"Error generating XML for strategy {strategy_id}: {e}")

    # Add TEC strategies
    if tec_strategies:
        xml_parts.append("\n    <!-- ==================== TEC策略组 ==================== -->")
        for strategy in tec_strategies:
            strategy_id = strategy.get("strategy_id")
            strategy_name = strategy.get("strategy_name", "")
            xml_parts.append(f"\n    <!-- 策略: {strategy_id} - {strategy_name} -->")

            try:
                template = strategy.get("template", {})
                parameters = strategy.get("parameters", {})
                
                # 验证entrance_edges在parameters中（严格检查）
                if "entrance_edges" not in parameters:
                    raise ValueError(
                        f"TEC strategy {strategy_id} missing 'entrance_edges' in parameters. "
                        f"Available keys: {list(parameters.keys())}"
                    )
                
                strategy_xml = generate_strategy_xml(
                    template_id=strategy.get("template_id", ""),
                    template=template,
                    parameters=parameters
                )
                xml_parts.append(f"    {strategy_xml}")

            except Exception as e:
                logger.error(f"Error generating XML for strategy {strategy_id}: {e}")

    # Handle empty plan (baseline)
    if not strategies:
        xml_parts.append("\n    <!-- 基准方案：无管控 -->")

    xml_parts.append("\n</additional>")

    # Combine all parts
    xml_content = "\n".join(xml_parts)

    # Validate XML
    is_valid, error_msg = validate_generated_xml(xml_content)
    if not is_valid:
        logger.error(f"Generated plan XML is invalid: {error_msg}")
        raise ValueError(f"Invalid XML generated for plan {plan_id}: {error_msg}")

    logger.info(f"Plan additional XML generated successfully: {plan_id}")
    return xml_content
