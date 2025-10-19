"""
Control Template Service

Business logic layer for traffic control strategy template management.
Handles template listing, retrieval, and validation.

Follows Single Responsibility principle - only manages template operations.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict
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
        logger.info(f"ControlTemplateService initialized with templates_dir: {self.templates_dir}")

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

        response = TemplateDetailResponse(template=template)
        logger.info(f"Template found: {template.template_name}")
        return response
