"""
Parameter Validator for Strategy Templates (v2.0)

Validates strategy parameters against template v2.0 schema constraints.
Supports unit conversion (hours↔seconds, km/h↔m/s), SUMO-specific validation,
and comprehensive constraint checking for all parameter types.
"""

import logging
import re
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of parameter validation."""
    valid: bool
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    converted_parameters: Optional[Dict[str, Any]] = None


# Unit conversion constants
HOURS_TO_SECONDS = 3600
KMH_TO_MS = 1 / 3.6  # 0.277778
VEHSHR_TO_VEHSHR = 1.0  # No conversion needed

# SUMO constraint constants
SUMO_VEHICLE_TYPES = {"passenger", "bus", "truck", "emergency", "authority"}
SUMO_VCLASS_TYPES = {"passenger", "bus", "truck", "delivery", "emergency", "authority"}
MIN_SPEED_KMH = 30
MAX_SPEED_KMH = 130
MIN_FLOW_RATE = 0
MAX_FLOW_RATE = 2000


def validate_strategy_parameters(
    parameters_schema: List[Dict[str, Any]],
    parameters: Dict[str, Any],
    strategy_type: Optional[str] = None
) -> ValidationResult:
    """
    Validate strategy parameters against template v2.0 schema.

    Args:
        parameters_schema: List of parameter definitions from template v2.0
        parameters: Actual parameter values to validate
        strategy_type: Strategy type (VSS, DHS, TEC) for type-specific validation

    Returns:
        ValidationResult with valid flag, errors list, warnings list, and converted parameters
    """
    errors = []
    warnings = []
    converted_params = {}

    # Convert old schema format to new format if needed
    if isinstance(parameters_schema, dict):
        parameters_schema = [{"parameter_name": k, **v} for k, v in parameters_schema.items()]

    for param_def in parameters_schema:
        param_name = param_def.get("parameter_name")
        param_type = param_def.get("parameter_type")
        required = param_def.get("required", False)
        param_value = parameters.get(param_name)

        # Check required fields
        if required and param_value is None:
            errors.append({
                "parameter": param_name,
                "message": f"Required parameter '{param_name}' not provided",
                "constraint": {"required": True},
                "provided_value": None
            })
            continue

        # Skip validation if optional and not provided
        if param_value is None:
            continue

        # Validate by new parameter types
        if param_type == "edge_array":
            errs, warns = _validate_edge_array(param_name, param_value, param_def)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = param_value

        elif param_type == "step_array":
            errs, warns, converted = _validate_step_array(param_name, param_value, param_def, strategy_type)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = converted or param_value

        elif param_type == "flow_interval_array":
            errs, warns, converted = _validate_flow_interval_array(param_name, param_value, param_def)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = converted or param_value

        elif param_type in ("dhs_interval_array", "tec_interval_array"):
            # DHS and TEC interval arrays (time-based, no flow rates)
            errs, warns, converted = _validate_tec_dhs_interval_array(param_name, param_value, param_def)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = converted or param_value

        elif param_type == "enum_array":
            errs, warns = _validate_enum_array(param_name, param_value, param_def)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = param_value

        elif param_type == "integer":
            errs, warns = _validate_integer(param_name, param_value, param_def)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = param_value

        elif param_type == "number":
            errs, warns = _validate_number(param_name, param_value, param_def)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = param_value

        elif param_type == "enum":
            errs, warns = _validate_enum(param_name, param_value, param_def)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = param_value

        elif param_type == "array":
            errs, warns = _validate_array(param_name, param_value, param_def)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = param_value

        elif param_type == "string":
            errs, warns = _validate_string(param_name, param_value, param_def)
            errors.extend(errs)
            warnings.extend(warns)
            converted_params[param_name] = param_value

    # Log results
    if errors:
        logger.warning(f"Parameter validation failed with {len(errors)} error(s)",
                      extra={"errors": errors})
    if warnings:
        logger.info(f"Parameter validation produced {len(warnings)} warning(s)",
                   extra={"warnings": warnings})

    return ValidationResult(
        valid=(len(errors) == 0),
        errors=errors,
        warnings=warnings,
        converted_parameters=converted_params if converted_params else None
    )


# ==================== New Validator Functions for v2.0 Parameter Types ====================

def _validate_edge_array(param_name: str, value: Any, schema: Dict[str, Any]) -> Tuple[List, List]:
    """Validate edge_array parameter (list of SUMO edge IDs)."""
    errors = []
    warnings = []

    # Type check
    if not isinstance(value, list):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be an array of edge IDs",
            "constraint": {"type": "edge_array"},
            "provided_value": value
        })
        return errors, warnings

    # Check if empty (may be required)
    if len(value) == 0 and schema.get("required", False):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' requires at least one edge ID",
            "constraint": {"min_items": 1},
            "provided_value": []
        })
        return errors, warnings

    # Validate each edge ID format
    for idx, edge_id in enumerate(value):
        if not isinstance(edge_id, str):
            errors.append({
                "parameter": param_name,
                "message": f"Edge ID at index {idx} must be a string, got {type(edge_id).__name__}",
                "constraint": {"item_type": "string"},
                "provided_value": edge_id
            })
        elif not edge_id.strip():
            errors.append({
                "parameter": param_name,
                "message": f"Edge ID at index {idx} cannot be empty",
                "constraint": {"non_empty": True},
                "provided_value": edge_id
            })

    return errors, warnings


def _validate_step_array(
    param_name: str, value: Any, schema: Dict[str, Any], strategy_type: Optional[str] = None
) -> Tuple[List, List, Optional[List]]:
    """Validate step_array parameter (speed or control steps with time progression)."""
    errors = []
    warnings = []
    converted = []

    # Type check
    if not isinstance(value, list):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be an array of steps",
            "constraint": {"type": "step_array"},
            "provided_value": value
        })
        return errors, warnings, None

    # Get constraints
    constraints = schema.get("constraints", {})
    min_steps = constraints.get("min_steps", 1)
    max_steps = constraints.get("max_steps", 10)

    # Check step count
    if len(value) < min_steps:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' requires at least {min_steps} step(s)",
            "constraint": {"min_steps": min_steps},
            "provided_value": len(value)
        })
        return errors, warnings, None

    if len(value) > max_steps:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' cannot exceed {max_steps} step(s)",
            "constraint": {"max_steps": max_steps},
            "provided_value": len(value)
        })
        return errors, warnings, None

    # Validate each step
    step_structure = schema.get("step_structure", {})
    time_conversion = step_structure.get("time_conversion_factor", 3600)
    speed_conversion = step_structure.get("speed_conversion_factor", 0.277778)

    previous_time = -1
    for idx, step in enumerate(value):
        if not isinstance(step, dict):
            errors.append({
                "parameter": param_name,
                "message": f"Step {idx} must be a dictionary with time and speed",
                "constraint": {"item_type": "dict"},
                "provided_value": step
            })
            continue

        # Validate time field
        time_key = "time_hours" if "time_hours" in step else "time_seconds"
        time_val = step.get(time_key)
        if time_val is None:
            errors.append({
                "parameter": param_name,
                "message": f"Step {idx}: missing 'time_hours' or 'time_seconds' field",
                "constraint": {"required_field": time_key},
                "provided_value": step
            })
            continue

        # Convert time to hours for comparison if needed
        time_hours = time_val if time_key == "time_hours" else time_val / 3600
        if time_hours < previous_time:
            errors.append({
                "parameter": param_name,
                "message": f"Step {idx}: time values must be in ascending order",
                "constraint": {"ordered": True},
                "provided_value": time_hours
            })
        previous_time = time_hours

        # Validate speed field
        speed_key = "speed_kmh" if "speed_kmh" in step else "speed"
        speed_val = step.get(speed_key)
        if speed_val is None:
            errors.append({
                "parameter": param_name,
                "message": f"Step {idx}: missing 'speed_kmh' or 'speed' field",
                "constraint": {"required_field": speed_key},
                "provided_value": step
            })
            continue

        # Check speed range
        speed_kmh = speed_val if speed_key == "speed_kmh" else speed_val / speed_conversion
        if speed_kmh < MIN_SPEED_KMH or speed_kmh > MAX_SPEED_KMH:
            warnings.append({
                "parameter": param_name,
                "message": f"Step {idx}: speed {speed_kmh:.1f} km/h is outside typical range {MIN_SPEED_KMH}-{MAX_SPEED_KMH} km/h",
                "constraint": {"speed_range": [MIN_SPEED_KMH, MAX_SPEED_KMH]},
                "provided_value": speed_kmh
            })

        # Build converted step
        converted_step = {
            "time_seconds": int(time_hours * time_conversion),
            "speed_ms": round(speed_kmh * speed_conversion, 2)
        }
        converted.append(converted_step)

    return errors, warnings, converted if not errors else None


def _validate_flow_interval_array(
    param_name: str, value: Any, schema: Dict[str, Any]
) -> Tuple[List, List, Optional[List]]:
    """Validate flow_interval_array parameter (time-varying flow control)."""
    errors = []
    warnings = []
    converted = []

    # Type check
    if not isinstance(value, list):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be an array of flow intervals",
            "constraint": {"type": "flow_interval_array"},
            "provided_value": value
        })
        return errors, warnings, None

    # Check item count
    constraints = schema.get("constraints", {})
    min_items = constraints.get("min_intervals", 1)
    if len(value) < min_items:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' requires at least {min_items} interval(s)",
            "constraint": {"min_intervals": min_items},
            "provided_value": len(value)
        })
        return errors, warnings, None

    # Validate each interval
    previous_end = -1
    for idx, interval in enumerate(value):
        if not isinstance(interval, dict):
            errors.append({
                "parameter": param_name,
                "message": f"Interval {idx} must be a dictionary",
                "constraint": {"item_type": "dict"},
                "provided_value": interval
            })
            continue

        # Get begin time
        begin_key = "begin_hours" if "begin_hours" in interval else "begin_seconds"
        begin_val = interval.get(begin_key)
        if begin_val is None:
            errors.append({
                "parameter": param_name,
                "message": f"Interval {idx}: missing 'begin_hours' or 'begin_seconds'",
                "constraint": {"required_field": begin_key},
                "provided_value": interval
            })
            continue

        begin_hours = begin_val if begin_key == "begin_hours" else begin_val / 3600

        # Get end time
        end_key = "end_hours" if "end_hours" in interval else "end_seconds"
        end_val = interval.get(end_key)
        if end_val is None:
            errors.append({
                "parameter": param_name,
                "message": f"Interval {idx}: missing 'end_hours' or 'end_seconds'",
                "constraint": {"required_field": end_key},
                "provided_value": interval
            })
            continue

        end_hours = end_val if end_key == "end_hours" else end_val / 3600

        # Validate time ordering
        if begin_hours >= end_hours:
            errors.append({
                "parameter": param_name,
                "message": f"Interval {idx}: begin time must be less than end time",
                "constraint": {"begin_lt_end": True},
                "provided_value": f"[{begin_hours}, {end_hours}]"
            })

        # Validate vehsPerHour
        flow_rate = interval.get("vehsPerHour")
        if flow_rate is not None:
            if not isinstance(flow_rate, (int, float)):
                errors.append({
                    "parameter": param_name,
                    "message": f"Interval {idx}: vehsPerHour must be a number",
                    "constraint": {"type": "number"},
                    "provided_value": flow_rate
                })
            elif flow_rate < MIN_FLOW_RATE or flow_rate > MAX_FLOW_RATE:
                warnings.append({
                    "parameter": param_name,
                    "message": f"Interval {idx}: flow rate {flow_rate} is outside recommended range",
                    "constraint": {"flow_range": [MIN_FLOW_RATE, MAX_FLOW_RATE]},
                    "provided_value": flow_rate
                })

        # Build converted interval
        converted_interval = {
            "begin_seconds": int(begin_hours * 3600),
            "end_seconds": int(end_hours * 3600)
        }
        if flow_rate is not None:
            converted_interval["vehsPerHour"] = flow_rate
        if "target_speed" in interval:
            converted_interval["target_speed"] = interval["target_speed"]
        converted.append(converted_interval)

        previous_end = end_hours

    return errors, warnings, converted if not errors else None


def _validate_tec_dhs_interval_array(
    param_name: str, value: Any, schema: Dict[str, Any]
) -> Tuple[List, List, Optional[List]]:
    """Validate DHS/TEC interval array parameter (time-based intervals with status/vehicle types)."""
    errors = []
    warnings = []
    converted = []

    # Type check
    if not isinstance(value, list):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be an array of intervals",
            "constraint": {"type": "interval_array"},
            "provided_value": value
        })
        return errors, warnings, None

    # Check item count
    constraints = schema.get("constraints", {})
    min_items = constraints.get("min_intervals", 1)
    max_items = constraints.get("max_intervals", 10)

    if len(value) < min_items:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' requires at least {min_items} interval(s)",
            "constraint": {"min_intervals": min_items},
            "provided_value": len(value)
        })
        return errors, warnings, None

    if len(value) > max_items:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' cannot exceed {max_items} interval(s)",
            "constraint": {"max_intervals": max_items},
            "provided_value": len(value)
        })
        return errors, warnings, None

    # Validate each interval
    previous_end = -1
    for idx, interval in enumerate(value):
        if not isinstance(interval, dict):
            errors.append({
                "parameter": param_name,
                "message": f"Interval {idx} must be a dictionary",
                "constraint": {"item_type": "dict"},
                "provided_value": interval
            })
            continue

        # Get begin time
        begin_key = "begin_hours" if "begin_hours" in interval else "begin_seconds"
        begin_val = interval.get(begin_key)
        if begin_val is None:
            errors.append({
                "parameter": param_name,
                "message": f"Interval {idx}: missing 'begin_hours' or 'begin_seconds'",
                "constraint": {"required_field": begin_key},
                "provided_value": interval
            })
            continue

        begin_hours = begin_val if begin_key == "begin_hours" else begin_val / 3600

        # Get end time
        end_key = "end_hours" if "end_hours" in interval else "end_seconds"
        end_val = interval.get(end_key)
        if end_val is None:
            errors.append({
                "parameter": param_name,
                "message": f"Interval {idx}: missing 'end_hours' or 'end_seconds'",
                "constraint": {"required_field": end_key},
                "provided_value": interval
            })
            continue

        end_hours = end_val if end_key == "end_hours" else end_val / 3600

        # Validate time ordering
        if begin_hours >= end_hours:
            errors.append({
                "parameter": param_name,
                "message": f"Interval {idx}: begin time must be less than end time",
                "constraint": {"begin_lt_end": True},
                "provided_value": f"[{begin_hours}, {end_hours}]"
            })

        # Build converted interval
        converted_interval = {
            "begin_seconds": int(begin_hours * 3600),
            "end_seconds": int(end_hours * 3600)
        }

        # Copy optional fields (status, allowed_vehicle_types, etc.)
        for key in interval:
            if key not in (begin_key, end_key):
                converted_interval[key] = interval[key]

        converted.append(converted_interval)
        previous_end = end_hours

    return errors, warnings, converted if not errors else None


def _validate_enum_array(param_name: str, value: Any, schema: Dict[str, Any]) -> Tuple[List, List]:
    """Validate enum_array parameter (multiple selection from enumerated values)."""
    errors = []
    warnings = []

    # Type check
    if not isinstance(value, list):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be an array of enum values",
            "constraint": {"type": "enum_array"},
            "provided_value": value
        })
        return errors, warnings

    # Get allowed values
    enum_values = schema.get("enum_values", [])
    allowed = {ev.get("value") if isinstance(ev, dict) else ev for ev in enum_values}

    # Validate each value
    for idx, val in enumerate(value):
        if val not in allowed:
            errors.append({
                "parameter": param_name,
                "message": f"Value '{val}' at index {idx} is not a valid option. Valid options: {', '.join(sorted(allowed))}",
                "constraint": {"enum_values": list(allowed)},
                "provided_value": val
            })

    # SUMO-specific: validate vehicle types
    if "vehicle" in param_name.lower() or "type" in param_name.lower():
        for val in value:
            if val not in SUMO_VEHICLE_TYPES:
                warnings.append({
                    "parameter": param_name,
                    "message": f"Vehicle type '{val}' may not be standard SUMO vClass",
                    "constraint": {"sumo_vehicle_types": list(SUMO_VEHICLE_TYPES)},
                    "provided_value": val
                })

    return errors, warnings


def _validate_integer(param_name: str, value: Any, schema: Dict[str, Any]) -> Tuple[List, List]:
    """Validate integer parameter."""
    errors = []
    warnings = []

    # Type check
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be an integer",
            "constraint": {"type": "integer"},
            "provided_value": value
        })
        return errors, warnings

    # Min constraint
    min_val = schema.get("min_value")
    if min_val is not None and value < min_val:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be at least {min_val}",
            "constraint": {"min_value": min_val},
            "provided_value": value
        })

    # Max constraint
    max_val = schema.get("max_value")
    if max_val is not None and value > max_val:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be at most {max_val}",
            "constraint": {"max_value": max_val},
            "provided_value": value
        })

    return errors, warnings


def _validate_number(param_name: str, value: Any, schema: Dict[str, Any]) -> Tuple[List, List]:
    """Validate number (float) parameter."""
    errors = []
    warnings = []

    # Type check
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be a number",
            "constraint": {"type": "number"},
            "provided_value": value
        })
        return errors, warnings

    # Min constraint
    min_val = schema.get("min_value")
    if min_val is not None and value < min_val:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be at least {min_val}",
            "constraint": {"min_value": min_val},
            "provided_value": value
        })

    # Max constraint
    max_val = schema.get("max_value")
    if max_val is not None and value > max_val:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be at most {max_val}",
            "constraint": {"max_value": max_val},
            "provided_value": value
        })

    return errors, warnings


def _validate_enum(param_name: str, value: Any, schema: Dict[str, Any]) -> Tuple[List, List]:
    """Validate enum parameter (single selection)."""
    errors = []
    warnings = []

    # Get allowed values
    enum_values = schema.get("enum_values", [])
    allowed = {ev.get("value") if isinstance(ev, dict) else ev for ev in enum_values}

    # Check if value is in allowed set
    if value not in allowed:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be one of: {', '.join(sorted(str(v) for v in allowed))}",
            "constraint": {"enum_values": list(allowed)},
            "provided_value": value
        })

    return errors, warnings


def _validate_array(param_name: str, value: Any, schema: Dict[str, Any]) -> Tuple[List, List]:
    """Validate generic array parameter."""
    errors = []
    warnings = []

    # Type check
    if not isinstance(value, list):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be an array",
            "constraint": {"type": "array"},
            "provided_value": value
        })
        return errors, warnings

    # Check constraints
    constraints = schema.get("constraints", {})
    min_items = constraints.get("min_items")
    if min_items is not None and len(value) < min_items:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must have at least {min_items} item(s)",
            "constraint": {"min_items": min_items},
            "provided_value": len(value)
        })

    max_items = constraints.get("max_items")
    if max_items is not None and len(value) > max_items:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' cannot exceed {max_items} item(s)",
            "constraint": {"max_items": max_items},
            "provided_value": len(value)
        })

    return errors, warnings


def _validate_string(param_name: str, value: Any, schema: Dict[str, Any]) -> Tuple[List, List]:
    """Validate string parameter."""
    errors = []
    warnings = []

    # Type check
    if not isinstance(value, str):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be a string",
            "constraint": {"type": "string"},
            "provided_value": value
        })
        return errors, warnings

    # Check constraints
    if not value.strip():
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' cannot be empty",
            "constraint": {"non_empty": True},
            "provided_value": value
        })

    return errors, warnings


# ==================== Legacy Function Support ====================

def validate_time_interval_format(time_interval: str) -> bool:
    """
    Validate time interval format (HH:MM-HH:MM).

    Args:
        time_interval: Time interval string to validate

    Returns:
        True if valid format, False otherwise
    """
    pattern = r"^\d{2}:\d{2}-\d{2}:\d{2}$"
    if not re.match(pattern, time_interval):
        return False

    # Additional validation: hours and minutes should be valid
    parts = time_interval.split("-")
    for part in parts:
        hours, minutes = map(int, part.split(":"))
        if hours > 23 or minutes > 59:
            return False

    return True


def validate_edges_exist(edge_ids: List[str]) -> Dict[str, Any]:
    """
    Validate that edge IDs exist in the database.

    This function will be enhanced with actual database query in future tasks.
    For now, it provides the interface expected by the validation workflow.

    Args:
        edge_ids: List of edge IDs to validate

    Returns:
        Dict with validation result
    """
    # TODO: Implement with Phase 1B edge_query.py integration
    return {"valid": True, "invalid_edges": [], "message": "Edge validation not yet implemented"}
