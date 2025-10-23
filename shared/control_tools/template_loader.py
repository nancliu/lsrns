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

    allowed_types = {"integer", "float", "string", "boolean", "array"}

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


def load_template_from_file(file_path: Path) -> Optional[ControlTemplate]:
    """
    Load template from JSON file with full validation.

    Args:
        file_path: Path to template JSON file

    Returns:
        ControlTemplate instance if valid, None if invalid or error
    """
    data = _load_json_file(file_path)
    if data is None:
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
