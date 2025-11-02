"""
SUMO XML Validator for Control Strategies

Validates generated SUMO control.add.xml files for:
- Well-formed XML structure
- SUMO-compliant element types and attributes
- Attribute value ranges and types
- SUMO constraint compliance (time bounds, speed bounds, edge existence)

Supports validation of VSS (Variable Speed Sign), DHS (Dynamic Hard Shoulder),
and TEC (Toll Entrance Control) elements.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from xml.etree.ElementTree import Element, ElementTree, parse
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


@dataclass
class XMLValidationResult:
    """Result of XML validation."""
    is_valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    element_count: int = 0
    element_types: List[str] = None


# SUMO XML constraints
SUMO_TIME_MIN_SECONDS = 0
SUMO_TIME_MAX_SECONDS = 86400  # 24 hours
SUMO_SPEED_MIN_MS = 0.0
SUMO_SPEED_MAX_MS = 50.0
SUMO_FLOW_MIN_VEHSHR = 0
SUMO_FLOW_MAX_VEHSHR = 3000

# Valid SUMO vehicle types for allow attributes
SUMO_VALID_VEHICLE_TYPES = {
    "passenger", "bus", "truck", "emergency", "authority",
    "motorcycle", "bicycle", "pedestrian", "delivery",
    "hov", "taxi", "rail", "rail_urban", "rail_fast"
}


def validate_xml_string(xml_content: str) -> XMLValidationResult:
    """
    Validate XML string for well-formedness and SUMO compliance.

    Args:
        xml_content: XML content as string

    Returns:
        XMLValidationResult with validation status and details
    """
    errors = []
    warnings = []
    element_count = 0
    element_types = []

    try:
        # Parse XML (will raise exception if malformed)
        root = ET.fromstring(xml_content)
        logger.debug(f"XML parsed successfully. Root element: {root.tag}")

        # Validate root element type - accept 'additional' as valid root
        if root.tag not in ["variableSpeedSign", "rerouter", "calibrator", "additional"]:
            errors.append({
                "type": "invalid_root_element",
                "message": f"Expected valid SUMO root element (additional, variableSpeedSign, rerouter, calibrator), got: {root.tag}",
                "element": root.tag
            })
            return XMLValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                element_count=0,
                element_types=[]
            )

        # Count and validate elements
        element_count, element_types, errs, warns = _validate_element_tree(root)
        errors.extend(errs)
        warnings.extend(warns)

        # Validate root attributes
        root_errs, root_warns = _validate_root_attributes(root)
        errors.extend(root_errs)
        warnings.extend(root_warns)

        is_valid = len(errors) == 0

        return XMLValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            element_count=element_count,
            element_types=element_types
        )

    except ET.ParseError as e:
        logger.error(f"XML parse error: {e}")
        errors.append({
            "type": "parse_error",
            "message": str(e),
            "position": str(e.position) if hasattr(e, 'position') else "unknown"
        })
        return XMLValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            element_count=0,
            element_types=[]
        )

    except Exception as e:
        logger.error(f"Unexpected error during XML validation: {e}", exc_info=True)
        errors.append({
            "type": "unexpected_error",
            "message": str(e)
        })
        return XMLValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            element_count=0,
            element_types=[]
        )


def _validate_element_tree(root: Element) -> Tuple[int, List[str], List[Dict], List[Dict]]:
    """
    Recursively validate element tree structure.

    Args:
        root: Root element

    Returns:
        Tuple of (element_count, element_types, errors, warnings)
    """
    errors = []
    warnings = []
    element_count = 0
    element_types_found = set()

    for element in root.iter():
        element_count += 1
        element_types_found.add(element.tag)

        # Validate element by type
        if root.tag == "variableSpeedSign":
            if element.tag == "step":
                errs, warns = _validate_vss_step(element)
                errors.extend(errs)
                warnings.extend(warns)

        elif root.tag == "rerouter":
            if element.tag == "interval":
                errs, warns = _validate_dhs_interval(element)
                errors.extend(errs)
                warnings.extend(warns)
            elif element.tag == "closingLaneReroute":
                errs, warns = _validate_closing_lane_reroute(element)
                errors.extend(errs)
                warnings.extend(warns)

        elif root.tag == "calibrator":
            if element.tag == "flow":
                errs, warns = _validate_tec_flow(element)
                errors.extend(errs)
                warnings.extend(warns)

    return element_count, list(element_types_found), errors, warnings


def _validate_root_attributes(root: Element) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate root element attributes.

    Args:
        root: Root element

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Check required id attribute (not required for 'additional' root element)
    if root.tag != "additional":
        strategy_id = root.get("id")
        if not strategy_id:
            errors.append({
                "type": "missing_attribute",
                "element": root.tag,
                "attribute": "id",
                "message": f"{root.tag} element requires 'id' attribute"
            })
        else:
            logger.debug(f"Strategy ID: {strategy_id}")

    # Validate edges attribute (for VSS and rerouter)
    if root.tag in ["variableSpeedSign", "rerouter"]:
        edges_str = root.get("edges")
        if not edges_str:
            warnings.append({
                "type": "empty_edges",
                "element": root.tag,
                "attribute": "edges",
                "message": f"{root.tag} has empty 'edges' attribute"
            })
        else:
            edges = edges_str.split()
            logger.debug(f"Strategy affects {len(edges)} edges")

            # Check for duplicate edges
            if len(edges) != len(set(edges)):
                duplicates = [e for e in edges if edges.count(e) > 1]
                warnings.append({
                    "type": "duplicate_edges",
                    "element": root.tag,
                    "attribute": "edges",
                    "message": f"Found duplicate edge IDs: {set(duplicates)}",
                    "duplicate_edges": list(set(duplicates))
                })

    return errors, warnings


def _validate_vss_step(element: Element) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate VSS step element.

    Structure: <step time="..." speed="..."/>

    Args:
        element: step Element

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Validate time attribute
    time_str = element.get("time")
    if not time_str:
        errors.append({
            "type": "missing_attribute",
            "element": "step",
            "attribute": "time",
            "message": "step element requires 'time' attribute"
        })
    else:
        try:
            time_sec = int(time_str)
            if not (SUMO_TIME_MIN_SECONDS <= time_sec <= SUMO_TIME_MAX_SECONDS):
                errors.append({
                    "type": "out_of_bounds",
                    "element": "step",
                    "attribute": "time",
                    "message": f"Time {time_sec}s out of SUMO bounds [{SUMO_TIME_MIN_SECONDS}, {SUMO_TIME_MAX_SECONDS}]",
                    "value": time_sec,
                    "bounds": [SUMO_TIME_MIN_SECONDS, SUMO_TIME_MAX_SECONDS]
                })
        except ValueError:
            errors.append({
                "type": "invalid_type",
                "element": "step",
                "attribute": "time",
                "message": f"time must be integer seconds, got: {time_str}",
                "value": time_str
            })

    # Validate speed attribute
    speed_str = element.get("speed")
    if not speed_str:
        errors.append({
            "type": "missing_attribute",
            "element": "step",
            "attribute": "speed",
            "message": "step element requires 'speed' attribute"
        })
    else:
        try:
            speed_ms = float(speed_str)
            if not (SUMO_SPEED_MIN_MS <= speed_ms <= SUMO_SPEED_MAX_MS):
                errors.append({
                    "type": "out_of_bounds",
                    "element": "step",
                    "attribute": "speed",
                    "message": f"Speed {speed_ms}m/s out of SUMO bounds [{SUMO_SPEED_MIN_MS}, {SUMO_SPEED_MAX_MS}]",
                    "value": speed_ms,
                    "bounds": [SUMO_SPEED_MIN_MS, SUMO_SPEED_MAX_MS]
                })

            # Check precision (should be 2 decimal places)
            if len(speed_str.split('.')[-1]) > 2:
                warnings.append({
                    "type": "precision_warning",
                    "element": "step",
                    "attribute": "speed",
                    "message": f"Speed precision > 2 decimals: {speed_ms}",
                    "value": speed_ms,
                    "recommended_precision": 2
                })

        except ValueError:
            errors.append({
                "type": "invalid_type",
                "element": "step",
                "attribute": "speed",
                "message": f"speed must be float m/s, got: {speed_str}",
                "value": speed_str
            })

    return errors, warnings


def _validate_dhs_interval(element: Element) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate DHS interval element.

    Structure: <interval begin="..." end="...">...</interval>

    Args:
        element: interval Element

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Validate begin attribute
    begin_str = element.get("begin")
    begin_sec = None
    if not begin_str:
        errors.append({
            "type": "missing_attribute",
            "element": "interval",
            "attribute": "begin",
            "message": "interval element requires 'begin' attribute"
        })
    else:
        try:
            begin_sec = int(begin_str)
            if not (SUMO_TIME_MIN_SECONDS <= begin_sec <= SUMO_TIME_MAX_SECONDS):
                errors.append({
                    "type": "out_of_bounds",
                    "element": "interval",
                    "attribute": "begin",
                    "message": f"Begin time {begin_sec}s out of SUMO bounds [{SUMO_TIME_MIN_SECONDS}, {SUMO_TIME_MAX_SECONDS}]",
                    "value": begin_sec,
                    "bounds": [SUMO_TIME_MIN_SECONDS, SUMO_TIME_MAX_SECONDS]
                })
        except ValueError:
            errors.append({
                "type": "invalid_type",
                "element": "interval",
                "attribute": "begin",
                "message": f"begin must be integer seconds, got: {begin_str}",
                "value": begin_str
            })

    # Validate end attribute
    end_str = element.get("end")
    end_sec = None
    if not end_str:
        errors.append({
            "type": "missing_attribute",
            "element": "interval",
            "attribute": "end",
            "message": "interval element requires 'end' attribute"
        })
    else:
        try:
            end_sec = int(end_str)
            if not (SUMO_TIME_MIN_SECONDS <= end_sec <= SUMO_TIME_MAX_SECONDS):
                errors.append({
                    "type": "out_of_bounds",
                    "element": "interval",
                    "attribute": "end",
                    "message": f"End time {end_sec}s out of SUMO bounds [{SUMO_TIME_MIN_SECONDS}, {SUMO_TIME_MAX_SECONDS}]",
                    "value": end_sec,
                    "bounds": [SUMO_TIME_MIN_SECONDS, SUMO_TIME_MAX_SECONDS]
                })
        except ValueError:
            errors.append({
                "type": "invalid_type",
                "element": "interval",
                "attribute": "end",
                "message": f"end must be integer seconds, got: {end_str}",
                "value": end_str
            })

    # Check begin < end
    if begin_sec is not None and end_sec is not None and begin_sec >= end_sec:
        errors.append({
            "type": "invalid_interval",
            "element": "interval",
            "message": f"begin ({begin_sec}s) must be < end ({end_sec}s)",
            "begin": begin_sec,
            "end": end_sec
        })

    return errors, warnings


def _validate_closing_lane_reroute(element: Element) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate closingLaneReroute element for DHS.

    Structure: <closingLaneReroute id="..." allow="..."/>

    Args:
        element: closingLaneReroute Element

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Validate id attribute (lane index)
    lane_id_str = element.get("id")
    if not lane_id_str:
        errors.append({
            "type": "missing_attribute",
            "element": "closingLaneReroute",
            "attribute": "id",
            "message": "closingLaneReroute element requires 'id' attribute (lane index)"
        })
    else:
        try:
            lane_id = int(lane_id_str)
            if lane_id < 0 or lane_id > 10:
                warnings.append({
                    "type": "unusual_lane_index",
                    "element": "closingLaneReroute",
                    "attribute": "id",
                    "message": f"Lane index {lane_id} is unusual (typically 0-10 for most roads)",
                    "value": lane_id
                })
        except ValueError:
            errors.append({
                "type": "invalid_type",
                "element": "closingLaneReroute",
                "attribute": "id",
                "message": f"id must be integer lane index, got: {lane_id_str}",
                "value": lane_id_str
            })

    # Validate allow attribute
    allow_str = element.get("allow", "")
    if allow_str:  # Not empty
        vehicle_types = allow_str.split()
        invalid_types = [vt for vt in vehicle_types if vt not in SUMO_VALID_VEHICLE_TYPES]
        if invalid_types:
            warnings.append({
                "type": "unknown_vehicle_type",
                "element": "closingLaneReroute",
                "attribute": "allow",
                "message": f"Unknown SUMO vehicle types: {invalid_types}",
                "unknown_types": invalid_types,
                "valid_types": sorted(list(SUMO_VALID_VEHICLE_TYPES))
            })

    return errors, warnings


def _validate_tec_flow(element: Element) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate TEC flow element.

    Structure: <flow begin="..." end="..." vehsPerHour="..." speed="..."/>

    Args:
        element: flow Element

    Returns:
        Tuple of (errors, warnings)
    """
    errors = []
    warnings = []

    # Validate begin/end times (same as interval)
    begin_str = element.get("begin")
    if begin_str:
        try:
            begin_sec = int(begin_str)
            if not (SUMO_TIME_MIN_SECONDS <= begin_sec <= SUMO_TIME_MAX_SECONDS):
                errors.append({
                    "type": "out_of_bounds",
                    "element": "flow",
                    "attribute": "begin",
                    "message": f"Begin time {begin_sec}s out of SUMO bounds",
                    "value": begin_sec,
                    "bounds": [SUMO_TIME_MIN_SECONDS, SUMO_TIME_MAX_SECONDS]
                })
        except ValueError:
            errors.append({
                "type": "invalid_type",
                "element": "flow",
                "attribute": "begin",
                "message": f"begin must be integer, got: {begin_str}",
                "value": begin_str
            })

    # Validate vehsPerHour
    flow_str = element.get("vehsPerHour")
    if not flow_str:
        errors.append({
            "type": "missing_attribute",
            "element": "flow",
            "attribute": "vehsPerHour",
            "message": "flow element requires 'vehsPerHour' attribute"
        })
    else:
        try:
            flow_rate = int(flow_str)
            if not (SUMO_FLOW_MIN_VEHSHR <= flow_rate <= SUMO_FLOW_MAX_VEHSHR):
                errors.append({
                    "type": "out_of_bounds",
                    "element": "flow",
                    "attribute": "vehsPerHour",
                    "message": f"Flow rate {flow_rate} veh/hr out of SUMO bounds [{SUMO_FLOW_MIN_VEHSHR}, {SUMO_FLOW_MAX_VEHSHR}]",
                    "value": flow_rate,
                    "bounds": [SUMO_FLOW_MIN_VEHSHR, SUMO_FLOW_MAX_VEHSHR]
                })
        except ValueError:
            errors.append({
                "type": "invalid_type",
                "element": "flow",
                "attribute": "vehsPerHour",
                "message": f"vehsPerHour must be integer, got: {flow_str}",
                "value": flow_str
            })

    # Validate speed (should be float m/s)
    speed_str = element.get("speed")
    if speed_str:
        try:
            speed_ms = float(speed_str)
            if not (SUMO_SPEED_MIN_MS <= speed_ms <= SUMO_SPEED_MAX_MS):
                errors.append({
                    "type": "out_of_bounds",
                    "element": "flow",
                    "attribute": "speed",
                    "message": f"Speed {speed_ms}m/s out of SUMO bounds [{SUMO_SPEED_MIN_MS}, {SUMO_SPEED_MAX_MS}]",
                    "value": speed_ms,
                    "bounds": [SUMO_SPEED_MIN_MS, SUMO_SPEED_MAX_MS]
                })
        except ValueError:
            errors.append({
                "type": "invalid_type",
                "element": "flow",
                "attribute": "speed",
                "message": f"speed must be float, got: {speed_str}",
                "value": speed_str
            })

    return errors, warnings
