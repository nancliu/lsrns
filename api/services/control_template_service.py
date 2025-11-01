"""
Control Template Service

Business logic layer for traffic control strategy template management.
Handles template listing, retrieval, and validation.

Follows Single Responsibility principle - only manages template operations.
"""

import logging
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from api.models.control.entities.template import ControlTemplate
from api.models.control.responses.template_responses import (
    TemplateListResponse,
    TemplateDetailResponse
)
from shared.control_tools.template_loader import (
    list_all_templates,
    get_template_by_id,
    generate_templates_index
)

logger = logging.getLogger(__name__)


class ControlTemplateService:
    """
    Service for managing traffic control strategy templates.

    Responsibilities:
    - List all available templates
    - Retrieve specific template by ID
    - Generate template metadata

    Depends on:
    - TemplateLoader (shared/control_tools/template_loader.py)
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize the service.

        Args:
            templates_dir: Path to templates directory
                          Defaults to 'templates/control_strategies/'
        """
        if templates_dir is None:
            # Default to project root / templates / control_strategies
            project_root = Path(__file__).parent.parent.parent
            templates_dir = project_root / "templates" / "control_strategies"

        self.templates_dir = templates_dir
        self._enum_cache: Dict[str, Any] = {}  # Cache for enum definitions
        logger.info(f"ControlTemplateService initialized with templates_dir: {self.templates_dir}")

    def _load_enum_definition(self, enum_name: str) -> Optional[List[Dict[str, Any]]]:
        """
        Load enum definition from configuration file.

        Args:
            enum_name: Enum identifier (e.g., 'vehicle_types_category')

        Returns:
            List of enum value definitions, or None if not found
        """
        # Check cache first
        if enum_name in self._enum_cache:
            return self._enum_cache[enum_name]

        # Construct path to enum file
        project_root = Path(__file__).parent.parent.parent
        enum_path = project_root / "control_data" / "templates" / "common" / f"{enum_name}.json"

        if not enum_path.exists():
            logger.warning(f"Enum definition not found: {enum_path}")
            return None

        try:
            with open(enum_path, "r", encoding="utf-8") as f:
                enum_data = json.load(f)

            # Extract values array
            enum_values = enum_data.get("values", [])

            # Cache the result
            self._enum_cache[enum_name] = enum_values

            logger.info(f"Loaded {len(enum_values)} values for enum: {enum_name}")
            return enum_values

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading enum {enum_name}: {e}")
            return None

    def _enrich_template_with_enums(self, template: ControlTemplate) -> ControlTemplate:
        """
        Enrich template parameters with enum_values from configuration.

        Scans parameters_schema for enum_name references and populates enum_values.

        Args:
            template: Template to enrich

        Returns:
            Enriched template with enum_values populated
        """
        for param in template.parameters_schema:
            # Check if parameter has enum_name attribute (indicates enum-based parameter)
            enum_name = getattr(param, "enum_name", None)

            if enum_name:
                # Load enum values from configuration
                enum_values = self._load_enum_definition(enum_name)

                if enum_values:
                    # Populate enum_values in parameter schema
                    param.enum_values = enum_values
                    logger.debug(f"Enriched parameter '{param.parameter_name}' with {len(enum_values)} enum values")

        return template

    def list_templates(self) -> TemplateListResponse:
        """
        List all available strategy templates.

        Returns:
            TemplateListResponse with all valid templates and metadata

        Example:
            >>> service = ControlTemplateService()
            >>> response = service.list_templates()
            >>> print(f"Found {response.total_count} templates")
        """
        logger.info("Listing all templates")

        # Load all valid templates
        templates = list_all_templates(self.templates_dir)

        # Calculate statistics
        by_type: Dict[str, int] = {}
        for template in templates:
            strategy_type = template.strategy_type.value
            by_type[strategy_type] = by_type.get(strategy_type, 0) + 1

        response = TemplateListResponse(
            templates=templates,
            total_count=len(templates),
            by_type=by_type
        )

        logger.info(f"Returning {response.total_count} templates: {response.by_type}")
        return response

    def get_template_detail(self, template_id: str) -> Optional[TemplateDetailResponse]:
        """
        Get detailed information for a specific template.

        Automatically enriches template parameters with enum_values from configuration.

        Args:
            template_id: Unique template identifier

        Returns:
            TemplateDetailResponse if template found, None otherwise

        Example:
            >>> service = ControlTemplateService()
            >>> response = service.get_template_detail("vss_moderate")
            >>> if response:
            >>>     print(response.template.template_name)
        """
        logger.info(f"Retrieving template: {template_id}")

        template = get_template_by_id(template_id, self.templates_dir)

        if template is None:
            logger.warning(f"Template not found: {template_id}")
            return None

        # Enrich template with enum values from configuration
        enriched_template = self._enrich_template_with_enums(template)

        response = TemplateDetailResponse(template=enriched_template)
        logger.info(f"Template found and enriched: {template.template_name}")
        return response
