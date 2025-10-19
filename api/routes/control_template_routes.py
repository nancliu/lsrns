"""
Control Template API Routes

REST API endpoints for browsing and retrieving traffic control strategy templates.

Endpoints:
- GET /api/v1/control/templates/ - List all templates
- GET /api/v1/control/templates/{template_id} - Get template details
"""

import logging
from fastapi import APIRouter, HTTPException, status
from api.services.control_template_service import ControlTemplateService
from api.models.control.responses.template_responses import (
    TemplateListResponse,
    TemplateDetailResponse,
    ErrorResponse
)

logger = logging.getLogger(__name__)

# Create router with /api/v1/control prefix
router = APIRouter(
    prefix="/control",
    tags=["Control Templates"],
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Internal server error"
        }
    }
)

# Initialize service (singleton pattern)
template_service = ControlTemplateService()


@router.get(
    "/templates/",
    response_model=TemplateListResponse,
    summary="List all strategy templates",
    description="Retrieve all available traffic control strategy templates with metadata",
    responses={
        200: {
            "description": "Successfully retrieved template list",
            "model": TemplateListResponse
        }
    }
)
async def get_templates() -> TemplateListResponse:
    """
    List all available strategy templates.

    Returns:
        TemplateListResponse containing all valid templates and statistics

    Raises:
        HTTPException: 500 if server error occurs

    Example response:
        {
            "templates": [...],
            "total_count": 5,
            "by_type": {"VSS": 2, "DHS": 1, "TEC": 2}
        }
    """
    try:
        logger.info("GET /api/v1/control/templates/ - Listing templates")
        response = template_service.list_templates()
        logger.info(f"Successfully returned {response.total_count} templates")
        return response

    except Exception as e:
        logger.error(f"Error listing templates: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Failed to retrieve templates",
                "details": {"error_type": type(e).__name__}
            }
        )


@router.get(
    "/templates/{template_id}",
    response_model=TemplateDetailResponse,
    summary="Get template details",
    description="Retrieve complete details for a specific template including all parameters",
    responses={
        200: {
            "description": "Successfully retrieved template details",
            "model": TemplateDetailResponse
        },
        404: {
            "description": "Template not found",
            "model": ErrorResponse
        }
    }
)
async def get_template_by_id(template_id: str) -> TemplateDetailResponse:
    """
    Get detailed information for a specific template.

    Args:
        template_id: Unique template identifier (e.g., "vss_moderate")

    Returns:
        TemplateDetailResponse with complete template details

    Raises:
        HTTPException: 404 if template not found
        HTTPException: 500 if server error occurs

    Example response:
        {
            "template": {
                "template_id": "vss_moderate",
                "template_name": "ïØP - -I§6",
                "parameters_schema": [...]
            }
        }
    """
    try:
        logger.info(f"GET /api/v1/control/templates/{template_id} - Retrieving template")
        response = template_service.get_template_detail(template_id)

        if response is None:
            logger.warning(f"Template not found: {template_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "TEMPLATE_NOT_FOUND",
                    "message": f"Template with ID '{template_id}' not found",
                    "details": {"requested_id": template_id}
                }
            )

        logger.info(f"Successfully returned template: {template_id}")
        return response

    except HTTPException:
        # Re-raise HTTP exceptions (404)
        raise

    except Exception as e:
        logger.error(f"Error retrieving template {template_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "Failed to retrieve template",
                "details": {"template_id": template_id, "error_type": type(e).__name__}
            }
        )
