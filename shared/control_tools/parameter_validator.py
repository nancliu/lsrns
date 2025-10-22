"""
Parameter Validator

Validates strategy parameters against template schema constraints.
Supports integer, string, array, boolean, and enum types with comprehensive validation rules.
"""

import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


def validate_strategy_parameters(
    schema: Dict[str, Dict[str, Any]],
    parameters: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Validate strategy parameters against template schema.

    Args:
        schema: Template's parameters_schema defining validation rules
        parameters: Actual parameter values to validate

    Returns:
        List of validation errors. Empty list if all valid.
        Each error: {"parameter": str, "message": str, "constraint": dict, "provided_value": any}

    Examples:
        >>> schema = {"speed_limit": {"type": "integer", "required": True, "min": 40, "max": 120}}
        >>> params = {"speed_limit": 80}
        >>> validate_strategy_parameters(schema, params)
        []

        >>> params = {"speed_limit": 150}
        >>> errors = validate_strategy_parameters(schema, params)
        >>> errors[0]["parameter"]
        'speed_limit'
        >>> "120" in errors[0]["message"]
        True
    """
    errors = []

    for param_name, param_schema in schema.items():
        param_type = param_schema.get("type")
        required = param_schema.get("required", False)
        param_value = parameters.get(param_name)

        # Check required fields
        if required and param_value is None:
            errors.append({
                "parameter": param_name,
                "message": f"Parameter '{param_name}' is required",
                "constraint": {"required": True},
                "provided_value": None
            })
            continue

        # Skip validation if parameter is optional and not provided
        if param_value is None:
            continue

        # Validate by type
        if param_type == "integer":
            errors.extend(_validate_integer(param_name, param_value, param_schema))
        elif param_type == "string":
            errors.extend(_validate_string(param_name, param_value, param_schema))
        elif param_type == "array":
            errors.extend(_validate_array(param_name, param_value, param_schema))
        elif param_type == "boolean":
            errors.extend(_validate_boolean(param_name, param_value, param_schema))
        elif param_type == "enum":
            errors.extend(_validate_enum(param_name, param_value, param_schema))

    # Log validation errors
    if errors:
        logger.warning(
            f"Parameter validation failed with {len(errors)} error(s)",
            extra={"errors": errors}
        )

    return errors


def _validate_integer(
    param_name: str,
    value: Any,
    schema: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Validate integer parameter with min/max/required constraints."""
    errors = []

    # Type check
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be an integer",
            "constraint": {"type": "integer"},
            "provided_value": value
        })
        return errors

    # Min constraint
    if "min" in schema and value < schema["min"]:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be at least {schema['min']} (minimum)",
            "constraint": {"min": schema["min"]},
            "provided_value": value
        })

    # Max constraint
    if "max" in schema and value > schema["max"]:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be at most {schema['max']} (maximum)",
            "constraint": {"max": schema["max"]},
            "provided_value": value
        })

    return errors


def _validate_string(
    param_name: str,
    value: Any,
    schema: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Validate string parameter with maxLength, pattern, required constraints."""
    errors = []

    # Type check
    if not isinstance(value, str):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be a string",
            "constraint": {"type": "string"},
            "provided_value": value
        })
        return errors

    # MaxLength constraint
    if "maxLength" in schema and len(value) > schema["maxLength"]:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' exceeds maximum length of {schema['maxLength']}",
            "constraint": {"maxLength": schema["maxLength"]},
            "provided_value": value
        })

    # Pattern constraint
    if "pattern" in schema:
        pattern = schema["pattern"]
        if not re.match(pattern, value):
            errors.append({
                "parameter": param_name,
                "message": f"Parameter '{param_name}' does not match required format pattern",
                "constraint": {"pattern": pattern},
                "provided_value": value
            })

    return errors


def _validate_array(
    param_name: str,
    value: Any,
    schema: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Validate array parameter with minItems, itemType, required constraints."""
    errors = []

    # Type check
    if not isinstance(value, list):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be an array",
            "constraint": {"type": "array"},
            "provided_value": value
        })
        return errors

    # MinItems constraint
    if "minItems" in schema and len(value) < schema["minItems"]:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must have at least {schema['minItems']} item(s) (minimum)",
            "constraint": {"minItems": schema["minItems"]},
            "provided_value": value
        })

    # ItemType validation (optional, for future enhancement)
    # if "itemType" in schema:
    #     # Validate each item matches the expected type
    #     pass

    return errors


def _validate_boolean(
    param_name: str,
    value: Any,
    schema: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Validate boolean parameter."""
    errors = []

    # Type check
    if not isinstance(value, bool):
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be a boolean (true or false)",
            "constraint": {"type": "boolean"},
            "provided_value": value
        })

    return errors


def _validate_enum(
    param_name: str,
    value: Any,
    schema: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Validate enum parameter with allowed_values constraint."""
    errors = []

    allowed_values = schema.get("allowed_values", [])

    if value not in allowed_values:
        errors.append({
            "parameter": param_name,
            "message": f"Parameter '{param_name}' must be one of: {', '.join(map(str, allowed_values))}",
            "constraint": {"allowed_values": allowed_values},
            "provided_value": value
        })

    return errors


def validate_time_interval_format(time_interval: str) -> bool:
    """
    Validate time interval format (HH:MM-HH:MM).

    Args:
        time_interval: Time interval string to validate

    Returns:
        True if valid format, False otherwise

    Examples:
        >>> validate_time_interval_format("08:00-10:00")
        True
        >>> validate_time_interval_format("8-10")
        False
        >>> validate_time_interval_format("25:00-26:00")
        False
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
        Dict with:
            - "valid": bool - True if all edges exist
            - "invalid_edges": List[str] - List of edge IDs not found
            - "message": str - Validation message

    Note:
        This is a stub that will be implemented with Phase 1B edge_query integration.
    """
    # TODO: Implement with Phase 1B edge_query.py integration
    # from shared.data_access.edge_query import query_edges_by_ids
    # result = query_edges_by_ids(edge_ids)
    # ...

    # Stub implementation for now
    return {
        "valid": True,
        "invalid_edges": [],
        "message": "Edge validation not yet implemented"
    }
