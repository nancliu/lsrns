"""
Traffic Control Strategy Template Entity Models

This module defines the core data structures for traffic control strategy templates.
Templates serve as blueprints for creating strategy instances in Phase 1C.

Entities:
- StrategyType: Enumeration of supported strategy types (VSS, DHS, TEC)
- ParameterSchema: Defines configurable parameters within a template
- ControlTemplate: Root entity representing a strategy template
- TemplateIndexEntry: Summary entry for template discovery
- TemplatesIndex: Auto-generated metadata for efficient template listing
"""

from enum import Enum
from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field, validator


class StrategyType(str, Enum):
    """
    Enumeration of supported traffic control strategy types.

    Values:
    - VSS: Variable Speed Signs - Dynamic speed limit control
    - DHS: Dynamic Hard Shoulder - Temporary shoulder lane opening
    - TEC: Toll Entrance Control - Ramp metering or entrance closure
    """

    VSS = "VSS"
    DHS = "DHS"
    TEC = "TEC"

    @property
    def display_name(self) -> str:
        """Get Chinese display name for the strategy type."""
        names = {"VSS": "可变限速", "DHS": "动态硬路肩", "TEC": "收费站入口管控"}
        return names[self.value]

    @property
    def description(self) -> str:
        """Get detailed description of the strategy type."""
        descriptions = {
            "VSS": "高速公路路段动态限速控制",
            "DHS": "高峰期临时开放硬路肩车道",
            "TEC": "匝道流量控制或入口关闭",
        }
        return descriptions[self.value]


class ParameterSchema(BaseModel):
    """
    Defines a single configurable parameter within a strategy template.

    Supports both v1.0 and v2.0 schema formats.

    v1.0 Attributes (legacy):
        parameter_name: Parameter identifier (lowercase, alphanumeric, underscores)
        parameter_type: Data type (integer, float, string, boolean, array)
        description: Parameter explanation (Chinese)
        required: Whether parameter is mandatory
        default_value: Default value if not specified
        min_value: Minimum value for numeric types
        max_value: Maximum value for numeric types
        allowed_values: Enum values for restricted choices
        unit: Display unit (e.g., "km/h", "seconds") for numeric types

    v2.0 Attributes (new):
        parameter_type: Enhanced types (edge_array, step_array, flow_interval_array,
                       enum_array, integer, number, enum, array, string)
        unit: Display unit with conversion metadata
        constraints: Dict with min_value, max_value, min_length, max_length, etc.
        sumo_mapping: SUMO element/attribute where this maps
        enum_values: List of {value, label} dicts for enums
        interval_structure: Metadata for array-based types (conversion factors, units)
    """

    parameter_name: str = Field(..., min_length=1, max_length=50, pattern="^[a-z0-9_]+$")
    parameter_type: str = Field(
        ...,
        pattern=(
            "^(integer|float|string|boolean|array|"
            "edge_array|step_array|flow_interval_array|"
            "dhs_interval_array|tec_interval_array|"
            "enum_array|number|enum)$"
        ),
    )
    description: str = Field(..., min_length=1, max_length=500)
    required: bool
    default_value: Optional[Any] = None

    # v1.0 attributes
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    allowed_values: Optional[List[Any]] = None

    # v2.0 attributes
    unit: Optional[str] = Field(None, max_length=50)
    constraints: Optional[Dict[str, Any]] = None
    sumo_mapping: Optional[str] = None
    enum_values: Optional[List[Dict[str, str]]] = None
    interval_structure: Optional[Dict[str, Any]] = None
    note: Optional[str] = None
    supplementary: Optional[bool] = False

    class Config:
        """Allow extra fields for forward compatibility."""

        extra = "allow"

    @validator("max_value")
    def max_greater_than_min(cls, v, values):
        """Validate that max_value > min_value when both are set."""
        if v is not None and "min_value" in values and values["min_value"] is not None:
            if v <= values["min_value"]:
                raise ValueError("max_value must be greater than min_value")
        return v

    @validator("default_value")
    def default_in_allowed_values(cls, v, values):
        """Validate that default_value is in allowed_values if allowed_values is set."""
        if v is not None and "allowed_values" in values and values["allowed_values"] is not None:
            if v not in values["allowed_values"]:
                raise ValueError("default_value must be one of allowed_values")
        return v


class ControlTemplate(BaseModel):
    """
    Root entity representing a traffic control strategy template.

    Templates are stored as JSON files and serve as blueprints for creating
    strategy instances. Supports both v1.0 and v2.0 schema formats.

    Attributes:
        template_id: Unique identifier (lowercase, alphanumeric, underscores)
        template_name: Display name (Chinese)
        description: Detailed explanation (Chinese)
        strategy_type: Strategy category (VSS/DHS/TEC)
        parameters_schema: List of parameter definitions (1-20 parameters)
        version: Template version (semantic versioning: "X.Y" or "X.Y.Z")
        created_at: Creation timestamp
        updated_at: Last modification timestamp

    v2.0 Additional Attributes:
        sumo_element: SUMO XML element type (variableSpeedSign, rerouter, calibrator)
        critical_warnings: List of critical warnings for users
        best_practices: Dict with usage guidelines
        visualization_guidance: UI rendering hints
        flow_reference_table: Reference data (for TEC templates)
        implementation_note: Implementation guidance
    """

    template_id: str = Field(..., min_length=1, max_length=50, pattern="^[a-z0-9_]+$")
    template_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=1000)
    strategy_type: StrategyType
    parameters_schema: List[ParameterSchema] = Field(..., min_items=1, max_items=20)
    version: str = Field(..., pattern=r"^\d+\.\d+(\.\d+)?$")
    created_at: datetime
    updated_at: datetime

    # v2.0 attributes
    sumo_element: Optional[str] = None
    critical_warnings: Optional[List[str]] = None
    best_practices: Optional[Dict[str, str]] = None
    visualization_guidance: Optional[Dict[str, Any]] = None
    flow_reference_table: Optional[Dict[str, Any]] = None
    implementation_note: Optional[Dict[str, str]] = None

    @validator("updated_at")
    def updated_after_created(cls, v, values):
        """Validate that updated_at >= created_at."""
        if "created_at" in values and v < values["created_at"]:
            raise ValueError("updated_at must be >= created_at")
        return v

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
        extra = "allow"  # Allow extra fields for forward compatibility


class TemplateIndexEntry(BaseModel):
    """
    Summary entry for a single template in the templates index.

    Used for efficient template discovery and listing without loading
    full template files.

    Attributes:
        template_id: Unique template identifier
        template_name: Display name
        strategy_type: Strategy type code (VSS/DHS/TEC)
        description_preview: First 100 characters of description
        file_path: Relative path to template JSON file
    """

    template_id: str
    template_name: str
    strategy_type: str
    description_preview: str = Field(..., max_length=100)
    file_path: str


class TemplatesIndex(BaseModel):
    """
    Auto-generated metadata for template discovery.

    Generated at API startup by scanning the templates directory.
    Provides fast access to template summaries without loading full files.

    Attributes:
        templates: List of template summary entries
        generated_at: Index generation timestamp
        total_count: Total number of valid templates
        by_type: Count of templates per strategy type (VSS/DHS/TEC)
    """

    templates: List[TemplateIndexEntry]
    generated_at: datetime
    total_count: int = Field(..., ge=0)
    by_type: Dict[str, int] = Field(default_factory=dict)

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}
