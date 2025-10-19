"""
Response Models for Template Management API

This module defines the response schemas for template-related API endpoints.
All responses follow a consistent structure with proper typing for FastAPI.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from ..entities.template import ControlTemplate


class TemplateListResponse(BaseModel):
    """
    Response model for GET /api/v1/control/templates/

    Returns a list of all valid templates with summary statistics.

    Attributes:
        templates: List of all valid templates with full details
        total_count: Total number of templates
        by_type: Template count grouped by strategy type (VSS/DHS/TEC)
    """
    templates: List[ControlTemplate] = Field(..., description="List of all valid templates")
    total_count: int = Field(..., description="Total number of templates", ge=0)
    by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Template count grouped by strategy type (VSS/DHS/TEC)"
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "templates": [
                    {
                        "template_id": "vss_moderate",
                        "template_name": "VSS Moderate Control",
                        "description": "Variable Speed Sign moderate control strategy",
                        "strategy_type": "VSS",
                        "parameters_schema": [],
                        "version": "1.0",
                        "created_at": "2025-10-19T00:00:00Z",
                        "updated_at": "2025-10-19T00:00:00Z"
                    }
                ],
                "total_count": 5,
                "by_type": {"VSS": 2, "DHS": 1, "TEC": 2}
            }
        }


class TemplateDetailResponse(BaseModel):
    """
    Response model for GET /api/v1/control/templates/{id}

    Returns complete template details including all parameters.

    Attributes:
        template: Complete template with parameters_schema
    """
    template: ControlTemplate = Field(..., description="Complete template with parameters_schema")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "template": {
                    "template_id": "vss_moderate",
                    "template_name": "VSS Moderate Control",
                    "description": "Variable Speed Sign moderate control strategy (80-100 km/h)",
                    "strategy_type": "VSS",
                    "parameters_schema": [
                        {
                            "parameter_name": "speed_limit",
                            "parameter_type": "integer",
                            "description": "Speed limit value in km/h",
                            "required": True,
                            "default_value": 80,
                            "min_value": 40,
                            "max_value": 100,
                            "unit": "km/h"
                        }
                    ],
                    "version": "1.0",
                    "created_at": "2025-10-19T00:00:00Z",
                    "updated_at": "2025-10-19T00:00:00Z"
                }
            }
        }


class ErrorResponse(BaseModel):
    """
    Structured error response per FR-009.

    Used for all error cases (404, 500, validation errors).

    Attributes:
        error: Error code string (e.g., 'TEMPLATE_NOT_FOUND', 'VALIDATION_ERROR')
        message: Human-readable error description
        details: Optional contextual information (error stack, field names, etc.)
    """
    error: str = Field(..., description="Error code (e.g., 'TEMPLATE_NOT_FOUND', 'VALIDATION_ERROR')")
    message: str = Field(..., description="Human-readable error description")
    details: Optional[Dict] = Field(None, description="Optional contextual information")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "error": "TEMPLATE_NOT_FOUND",
                "message": "Template with ID 'invalid_id' not found",
                "details": {"requested_id": "invalid_id", "available_count": 5}
            }
        }