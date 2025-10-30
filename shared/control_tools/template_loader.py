"""
Template Loader - Strategy Template Loading and Validation

This module provides utilities for loading, validating, and managing
traffic control strategy templates from the file system.

Functions:
- load_template_from_file: Load template from JSON file with validation
- validate_template: Validate template structure and schema
- generate_templates_index: Generate index of all templates
- list_all_templates: Get all templates with metadata
- get_template_by_id: Retrieve specific template by ID
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import ValidationError

from shared.control_tools.entities import (
    ControlTemplate,
    TemplatesIndex,
    TemplateIndexEntry,
    StrategyType,
)

# Configure logging
logger = logging.getLogger(__name__)


def _load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load and parse JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Parsed JSON as dictionary, or None if error
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
        logger.error(f"Failed to load JSON from {file_path}: {e}")
        return None


def _validate_template_structure(data: Dict[str, Any]) -> bool:
    """
    Validate template structure using Pydantic model.

    Args:
        data: Template data dictionary

    Returns:
        True if valid, False otherwise
    """
    try:
        ControlTemplate(**data)
        return True
    except ValidationError as e:
        logger.error(f"Template validation failed: {e}")
        return False


def _validate_parameter_schema(params: List[Dict[str, Any]]) -> bool:
    """
    Validate parameter schema structure and types.

    Supports both v1.0 and v2.0 parameter type definitions.

    Args:
        params: List of parameter schema dictionaries

    Returns:
        True if all parameters are valid, False otherwise
    """
    if not params or len(params) == 0:
        logger.error("Template must have at least 1 parameter")
        return False

    if len(params) > 20:
        logger.error("Template cannot have more than 20 parameters")
        return False

    # v1.0 types + v2.0 types
    allowed_types = {
        # v1.0 types (legacy)
        "integer",
        "float",
        "string",
        "boolean",
        "array",
        # v2.0 types (new)
        "edge_array",
        "step_array",
        "flow_interval_array",
        "dhs_interval_array",  # NEW: DHS-specific interval array
        "tec_interval_array",   # NEW: TEC-specific interval array
        "enum_array",
        "number",
        "enum",
    }

    for param in params:
        param_type = param.get("parameter_type")
        if param_type not in allowed_types:
            logger.error(f"Invalid parameter_type: {param_type}")
            return False

    return True


def validate_template(data: Dict[str, Any]) -> bool:
    """
    Multi-layer validation of template data.

    Validates:
    - Required fields presence
    - Field types and formats
    - Parameter schema structure
    - Business rules

    Args:
        data: Template data dictionary

    Returns:
        True if template is valid, False otherwise
    """
    # Check required fields
    required_fields = [
        "template_id",
        "template_name",
        "description",
        "strategy_type",
        "parameters_schema",
        "version",
        "created_at",
        "updated_at",
    ]

    for field in required_fields:
        if field not in data:
            logger.error(f"Template missing required field: {field}")
            return False

    # Validate strategy type
    if data.get("strategy_type") not in ["VSS", "DHS", "TEC"]:
        logger.error(f"Invalid strategy_type: {data.get('strategy_type')}")
        return False

    # Validate parameter schema
    params = data.get("parameters_schema", [])
    if not _validate_parameter_schema(params):
        return False

    # Validate using Pydantic model
    return _validate_template_structure(data)


def _resolve_template_inheritance(
    data: Dict[str, Any],
    templates_dir: Path,
    loaded_templates: Optional[Dict[str, Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Resolve template inheritance by merging parent template with child template.

    Supports 'extends' keyword for template inheritance.

    Args:
        data: Child template data dictionary
        templates_dir: Root directory containing templates
        loaded_templates: Cache of loaded templates to prevent circular dependencies

    Returns:
        Merged template data with parent parameters inherited

    Raises:
        ValueError: If parent template not found or circular dependency detected
    """
    if loaded_templates is None:
        loaded_templates = {}

    # Check if template has extends field
    parent_template_id = data.get("extends")
    if not parent_template_id:
        # No inheritance, return as-is
        return data

    logger.info(f"Resolving inheritance: {data.get('template_id')} extends {parent_template_id}")

    # Check for circular dependency
    if parent_template_id in loaded_templates:
        raise ValueError(f"Circular dependency detected: {parent_template_id}")

    # Find parent template file
    parent_file = None
    for file_path in templates_dir.rglob("*.json"):
        if file_path.stem == parent_template_id or parent_template_id in str(file_path):
            parent_data = _load_json_file(file_path)
            if parent_data and parent_data.get("template_id") == parent_template_id:
                parent_file = file_path
                break

    if not parent_file:
        raise ValueError(f"Parent template not found: {parent_template_id}")

    # Load parent template
    parent_data = _load_json_file(parent_file)
    if not parent_data:
        raise ValueError(f"Failed to load parent template: {parent_template_id}")

    # Mark as loaded to detect circular dependencies
    loaded_templates[parent_template_id] = parent_data

    # Recursively resolve parent's inheritance
    parent_data = _resolve_template_inheritance(parent_data, templates_dir, loaded_templates)

    # Merge parent and child templates
    merged = parent_data.copy()

    # Override fields from child
    for key, value in data.items():
        if key == "extends":
            # Remove extends field from final output
            continue
        elif key == "parameters_schema":
            # Merge parameters: child parameters override parent parameters with same name
            parent_params = {p["parameter_name"]: p for p in merged.get("parameters_schema", [])}
            child_params = {p["parameter_name"]: p for p in value}

            # Update parent params with child params
            parent_params.update(child_params)

            # Preserve order: parent params first, then new child params
            merged_params = []
            for p in merged.get("parameters_schema", []):
                merged_params.append(parent_params.get(p["parameter_name"], p))

            # Add new child params not in parent
            for param_name, param in child_params.items():
                if param_name not in {p["parameter_name"] for p in merged.get("parameters_schema", [])}:
                    merged_params.append(param)

            merged["parameters_schema"] = merged_params
        else:
            # Override other fields directly
            merged[key] = value

    logger.debug(f"Template inheritance resolved: {merged.get('template_id')}")
    return merged


def load_template_from_file(file_path: Path) -> Optional[ControlTemplate]:
    """
    Load template from JSON file with full validation.

    Supports template inheritance via 'extends' keyword.

    Args:
        file_path: Path to template JSON file

    Returns:
        ControlTemplate instance if valid, None if invalid or error
    """
    data = _load_json_file(file_path)
    if data is None:
        return None

    # Resolve inheritance if template extends another
    templates_dir = file_path.parent.parent  # Assuming templates are in subdirectories
    try:
        data = _resolve_template_inheritance(data, templates_dir)
    except ValueError as e:
        logger.error(f"Failed to resolve template inheritance for {file_path}: {e}")
        return None

    if not validate_template(data):
        logger.warning(f"Template validation failed for {file_path}")
        return None

    try:
        return ControlTemplate(**data)
    except ValidationError as e:
        logger.error(f"Failed to create ControlTemplate from {file_path}: {e}")
        return None


def scan_template_directory(templates_dir: Path) -> List[Path]:
    """
    Recursively scan template directory for JSON files.

    Args:
        templates_dir: Root directory containing template subdirectories

    Returns:
        List of paths to template JSON files
    """
    if not templates_dir.exists():
        logger.warning(f"Templates directory does not exist: {templates_dir}")
        return []

    json_files = list(templates_dir.rglob("*.json"))
    # Exclude the index file itself
    json_files = [f for f in json_files if f.name != "templates_index.json"]

    logger.info(f"Found {len(json_files)} template files in {templates_dir}")
    return json_files


def generate_templates_index(templates_dir: Path) -> TemplatesIndex:
    """
    Generate templates index by scanning directory.

    Auto-generates metadata for efficient template discovery.
    Invalid templates are logged and excluded from the index.

    Args:
        templates_dir: Root directory containing template subdirectories

    Returns:
        TemplatesIndex with all valid templates
    """
    template_files = scan_template_directory(templates_dir)

    valid_templates: List[TemplateIndexEntry] = []
    seen_ids: set = set()
    by_type: Dict[str, int] = {"VSS": 0, "DHS": 0, "TEC": 0}

    for file_path in template_files:
        template = load_template_from_file(file_path)

        if template is None:
            logger.warning(f"Skipping invalid template: {file_path}")
            continue

        # Check for duplicate IDs
        if template.template_id in seen_ids:
            logger.error(f"Duplicate template ID '{template.template_id}' in {file_path}, skipping")
            continue

        seen_ids.add(template.template_id)

        # Create index entry
        relative_path = file_path.relative_to(templates_dir).as_posix()
        description_preview = (
            template.description[:100] if len(template.description) > 100 else template.description
        )

        entry = TemplateIndexEntry(
            template_id=template.template_id,
            template_name=template.template_name,
            strategy_type=template.strategy_type.value,
            description_preview=description_preview,
            file_path=relative_path,
        )

        valid_templates.append(entry)
        by_type[template.strategy_type.value] += 1

    # Create index
    index = TemplatesIndex(
        templates=valid_templates,
        generated_at=datetime.utcnow(),
        total_count=len(valid_templates),
        by_type=by_type,
    )

    logger.info(f"Generated index with {index.total_count} templates")
    return index


def list_all_templates(templates_dir: Path) -> List[ControlTemplate]:
    """
    List all valid templates from directory.

    Loads and validates all templates, returning only valid ones.
    Automatically generates index if needed.

    Args:
        templates_dir: Root directory containing template subdirectories

    Returns:
        List of valid ControlTemplate instances
    """
    template_files = scan_template_directory(templates_dir)
    templates: List[ControlTemplate] = []
    seen_ids: set = set()

    for file_path in template_files:
        template = load_template_from_file(file_path)

        if template is None:
            continue

        # Enforce unique IDs
        if template.template_id in seen_ids:
            logger.error(f"Duplicate template ID '{template.template_id}', skipping")
            continue

        seen_ids.add(template.template_id)
        templates.append(template)

    logger.info(f"Loaded {len(templates)} valid templates")
    return templates


def get_template_by_id(template_id: str, templates_dir: Path) -> Optional[ControlTemplate]:
    """
    Retrieve specific template by ID.

    Args:
        template_id: Unique template identifier
        templates_dir: Root directory containing templates

    Returns:
        ControlTemplate if found and valid, None otherwise
    """
    templates = list_all_templates(templates_dir)

    for template in templates:
        if template.template_id == template_id:
            return template

    logger.warning(f"Template not found: {template_id}")
    return None


def load_template_with_schema(
    template_id: str, templates_dir: Path
) -> Optional[Dict[str, Any]]:
    """
    Load template with full parameter schema including SUMO mappings.

    This function loads a template and returns it as a dictionary with all
    parameter schema details intact, suitable for parameter validation.

    Args:
        template_id: Unique template identifier
        templates_dir: Root directory containing templates

    Returns:
        Complete template dictionary including parameter schemas,
        or None if template not found or invalid
    """
    # Try to find the template file
    template_files = scan_template_directory(templates_dir)

    for file_path in template_files:
        data = _load_json_file(file_path)
        if data is None:
            continue

        if data.get("template_id") == template_id:
            # Resolve template inheritance if needed
            try:
                if "extends" in data:
                    logger.info(f"Resolving inheritance for template: {template_id}")
                    data = _resolve_template_inheritance(data, templates_dir)
            except Exception as e:
                logger.error(f"Failed to resolve template inheritance for {template_id}: {e}")
                return None

            # Validate the template structure
            if not validate_template(data):
                logger.warning(f"Template {template_id} failed validation")
                return None

            return data

    logger.warning(f"Template not found: {template_id}")
    return None


def validate_template_schema(template: Dict[str, Any]) -> bool:
    """
    Validate that template schema is well-formed and complete.

    Checks for:
    - Required fields (template_id, template_name, strategy_type, etc.)
    - Parameter schema validity (no duplicate names, valid types)
    - v2.0 specific requirements (SUMO mappings, conversion factors)
    - SUMO element consistency with strategy type

    Args:
        template: Template dictionary to validate

    Returns:
        True if template schema is valid, False otherwise
    """
    if not isinstance(template, dict):
        logger.error("Template must be a dictionary")
        return False

    # Check required fields
    required_fields = [
        "template_id",
        "template_name",
        "strategy_type",
        "parameters_schema",
    ]

    for field in required_fields:
        if field not in template:
            logger.error(f"Template missing required field: {field}")
            return False

    # Validate strategy type
    strategy_type = template.get("strategy_type")
    if strategy_type not in ["VSS", "DHS", "TEC"]:
        logger.error(f"Invalid strategy_type: {strategy_type}")
        return False

    # Validate parameter schema
    params = template.get("parameters_schema", [])
    if not isinstance(params, list) or len(params) == 0:
        logger.error("parameters_schema must be a non-empty list")
        return False

    # Check for duplicate parameter names
    param_names = set()
    for param in params:
        if not isinstance(param, dict):
            logger.error("Each parameter in schema must be a dictionary")
            return False

        param_name = param.get("parameter_name")
        if not param_name:
            logger.error("Each parameter must have parameter_name field")
            return False

        if param_name in param_names:
            logger.error(f"Duplicate parameter name: {param_name}")
            return False

        param_names.add(param_name)

    # Validate parameter types
    if not _validate_parameter_schema(params):
        return False

    # v2.0 specific validation
    if template.get("version", "").startswith("2"):
        sumo_element = template.get("sumo_element")

        # VSS should use variableSpeedSign
        if strategy_type == "VSS" and sumo_element != "variableSpeedSign":
            logger.warning(
                f"VSS template should use sumo_element='variableSpeedSign', "
                f"got '{sumo_element}'"
            )

        # DHS should use rerouter or closingReroute
        if strategy_type == "DHS" and sumo_element not in ["rerouter", "closingReroute"]:
            logger.warning(
                f"DHS template should use sumo_element='rerouter' or "
                f"'closingReroute', got '{sumo_element}'"
            )

        # TEC should use calibrator or rerouter
        if strategy_type == "TEC" and sumo_element not in ["calibrator", "rerouter"]:
            logger.warning(
                f"TEC template should use sumo_element='calibrator' or "
                f"'rerouter', got '{sumo_element}'"
            )

        # Check for conversion factors in interval_structure/step_structure for array types
        for param in params:
            param_type = param.get("parameter_type")
            if param_type == "step_array":
                # step_array uses step_structure
                step_structure = param.get("step_structure", {})
                if not step_structure:
                    logger.warning(
                        f"Parameter '{param.get('parameter_name')}' of type "
                        f"'step_array' should have step_structure metadata"
                    )
            elif param_type == "flow_interval_array":
                # flow_interval_array uses interval_structure
                interval_structure = param.get("interval_structure", {})
                if not interval_structure:
                    logger.warning(
                        f"Parameter '{param.get('parameter_name')}' of type "
                        f"'flow_interval_array' should have interval_structure metadata"
                    )

    return True
