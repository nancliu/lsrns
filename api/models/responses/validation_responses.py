"""
Validation Error Response Models

Pydantic models for parameter validation and XML validation error responses.
Used for detailed error reporting when strategy parameters or generated XML fail validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ValidationErrorDetail(BaseModel):
    """
    Single validation error with detailed information.

    Attributes:
        field: Field or attribute name that failed validation
        message: Human-readable error message
        type: Error type (constraint, format, validation, parse_error, etc.)
        value: Actual value that failed validation (optional)
        expected: Expected value or range (optional)
        constraint: Constraint definition (min, max, required, enum, etc.) (optional)
    """

    field: str = Field(..., description="Field or parameter name")
    message: str = Field(..., description="Human-readable error message")
    type: str = Field(..., description="Error type category")
    value: Optional[Any] = Field(None, description="Actual value that failed")
    expected: Optional[Any] = Field(None, description="Expected value or range")
    constraint: Optional[Dict[str, Any]] = Field(None, description="Constraint definition")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "field": "speed_steps[0].speed_kmh",
                    "message": "Speed 150 km/h exceeds maximum 130 km/h",
                    "type": "constraint",
                    "value": 150,
                    "expected": {"min": 30, "max": 130},
                    "constraint": {"min": 30, "max": 130}
                },
                {
                    "field": "affected_edges",
                    "message": "Required parameter 'affected_edges' not provided",
                    "type": "validation",
                    "constraint": {"required": True}
                }
            ]
        }
    }


class ParameterValidationErrorResponse(BaseModel):
    """
    Response for parameter validation failures.

    Returned when strategy parameters fail validation before XML generation.

    Attributes:
        error: Error type
        reason: Detailed reason for failure
        validation_errors: List of validation errors
        affected_strategies: List of strategy IDs that failed
        suggestion: Suggestion for fixing the issue (optional)
    """

    error: str = Field(
        ...,
        description="Error type (e.g., 'Parameter validation failed')"
    )
    reason: str = Field(
        ...,
        description="Detailed reason for validation failure"
    )
    validation_errors: List[ValidationErrorDetail] = Field(
        ...,
        description="List of specific validation errors"
    )
    affected_strategies: List[str] = Field(
        ...,
        description="Strategy IDs that failed validation"
    )
    suggestion: Optional[str] = Field(
        None,
        description="Suggestion for fixing the issue"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "Plan creation failed",
                    "reason": "Strategy parameter validation failed",
                    "validation_errors": [
                        {
                            "field": "strategy_001.speed_steps[0].speed_kmh",
                            "message": "Speed 150 km/h exceeds maximum 130 km/h",
                            "type": "constraint",
                            "value": 150,
                            "expected": {"min": 30, "max": 130},
                            "constraint": {"min": 30, "max": 130}
                        }
                    ],
                    "affected_strategies": ["strategy_001"],
                    "suggestion": "Reduce speed values to be within [30, 130] km/h range"
                }
            ]
        }
    }


class XMLValidationErrorDetail(BaseModel):
    """
    Single XML validation error with element and attribute information.

    Attributes:
        type: Error type (missing_attribute, invalid_type, out_of_bounds, etc.)
        element: XML element name
        attribute: Attribute name (if attribute-level error)
        message: Human-readable error message
        value: Actual value in XML (optional)
        bounds: Valid bounds if out-of-bounds error (optional)
    """

    type: str = Field(..., description="Error type")
    element: str = Field(..., description="XML element name")
    attribute: Optional[str] = Field(None, description="Attribute name")
    message: str = Field(..., description="Error message")
    value: Optional[Any] = Field(None, description="Actual XML value")
    bounds: Optional[List[Any]] = Field(None, description="Valid bounds")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "out_of_bounds",
                    "element": "step",
                    "attribute": "speed",
                    "message": "Speed 55.5m/s out of SUMO bounds [0.0, 50.0]",
                    "value": 55.5,
                    "bounds": [0.0, 50.0]
                },
                {
                    "type": "missing_attribute",
                    "element": "interval",
                    "attribute": "begin",
                    "message": "interval element requires 'begin' attribute"
                }
            ]
        }
    }


class XMLValidationErrorResponse(BaseModel):
    """
    Response for XML validation failures.

    Returned when generated control.add.xml fails validation against SUMO schema.

    Attributes:
        error: Error type
        reason: Detailed reason for validation failure
        validation_errors: List of XML validation errors
        xml_location: Location of generated XML file (optional)
        suggestion: Suggestion for fixing the issue (optional)
    """

    error: str = Field(
        ...,
        description="Error type (e.g., 'XML validation failed')"
    )
    reason: str = Field(
        ...,
        description="Detailed reason for validation failure"
    )
    validation_errors: List[XMLValidationErrorDetail] = Field(
        ...,
        description="List of XML validation errors"
    )
    xml_location: Optional[str] = Field(
        None,
        description="Path to generated XML file (for debugging)"
    )
    suggestion: Optional[str] = Field(
        None,
        description="Suggestion for fixing the issue"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "XML validation failed",
                    "reason": "Generated XML violates SUMO constraints",
                    "validation_errors": [
                        {
                            "type": "out_of_bounds",
                            "element": "step",
                            "attribute": "speed",
                            "message": "Speed 55.5m/s out of SUMO bounds [0.0, 50.0]",
                            "value": 55.5,
                            "bounds": [0.0, 50.0]
                        }
                    ],
                    "xml_location": "/path/to/control.add.xml",
                    "suggestion": "Check parameter conversion logic - speed_kmh likely was not properly converted to m/s"
                }
            ]
        }
    }


class ValidationWarningDetail(BaseModel):
    """
    Single validation warning (non-fatal).

    Attributes:
        type: Warning type (unusual_value, precision_warning, etc.)
        field: Field or element name
        message: Human-readable warning message
        value: Value that triggered warning (optional)
    """

    type: str = Field(..., description="Warning type")
    field: str = Field(..., description="Field or element name")
    message: str = Field(..., description="Warning message")
    value: Optional[Any] = Field(None, description="Value that triggered warning")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "type": "precision_warning",
                    "field": "step.speed",
                    "message": "Speed precision > 2 decimals: 27.777777",
                    "value": 27.777777
                }
            ]
        }
    }


class CompleteValidationResponse(BaseModel):
    """
    Complete validation response including both errors and warnings.

    Used for comprehensive validation results that may have warnings even if valid.

    Attributes:
        is_valid: Whether validation passed
        errors: List of validation errors (empty if valid)
        warnings: List of validation warnings (non-fatal)
        summary: Summary of validation results
    """

    is_valid: bool = Field(
        ...,
        description="Whether validation passed"
    )
    errors: List[ValidationErrorDetail] = Field(
        default_factory=list,
        description="List of validation errors (empty if valid)"
    )
    warnings: List[ValidationWarningDetail] = Field(
        default_factory=list,
        description="List of validation warnings"
    )
    summary: str = Field(
        ...,
        description="Human-readable summary of validation"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "is_valid": False,
                    "errors": [
                        {
                            "field": "speed_steps[0].speed_kmh",
                            "message": "Speed 150 km/h exceeds maximum 130 km/h",
                            "type": "constraint",
                            "value": 150,
                            "expected": {"min": 30, "max": 130}
                        }
                    ],
                    "warnings": [],
                    "summary": "Validation failed: 1 error, 0 warnings"
                },
                {
                    "is_valid": True,
                    "errors": [],
                    "warnings": [
                        {
                            "type": "precision_warning",
                            "field": "step.speed",
                            "message": "Speed precision > 2 decimals: 27.777777",
                            "value": 27.777777
                        }
                    ],
                    "summary": "Validation passed: 0 errors, 1 warning"
                }
            ]
        }
    }
