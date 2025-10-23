"""
Strategy Request Models

Pydantic models for strategy creation and update requests.
Provides frontend and backend validation.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class StrategyCreateRequest(BaseModel):
    """
    Request model for creating a new strategy instance.

    Attributes:
        strategy_name: User-defined display name (1-100 characters)
        template_id: Reference to existing template from Phase 1A
        parameters: Key-value pairs of configured parameters
        affected_edges: List of edge IDs (minimum 1 required)
    """

    strategy_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User-defined strategy name"
    )
    template_id: str = Field(
        ...,
        min_length=1,
        description="Template ID from Phase 1A"
    )
    parameters: Dict[str, Any] = Field(
        ...,
        description="Parameter values configured by user"
    )
    affected_edges: List[str] = Field(
        ...,
        min_length=1,
        description="List of edge IDs affected by this strategy"
    )

    @field_validator("strategy_name")
    @classmethod
    def validate_strategy_name(cls, v: str) -> str:
        """Validate strategy name is not just whitespace."""
        if not v or not v.strip():
            raise ValueError("Strategy name cannot be empty or whitespace")
        return v.strip()

    @field_validator("affected_edges")
    @classmethod
    def validate_affected_edges(cls, v: List[str]) -> List[str]:
        """Validate affected_edges has at least one item."""
        if not v or len(v) == 0:
            raise ValueError("At least one edge must be selected for this strategy")
        # Remove duplicates while preserving order
        seen = set()
        unique_edges = []
        for edge_id in v:
            if edge_id not in seen:
                seen.add(edge_id)
                unique_edges.append(edge_id)
        return unique_edges

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "strategy_name": "Morning Peak VSS Control - G4202",
                    "template_id": "vss_moderate",
                    "parameters": {
                        "speed_limit": 80,
                        "time_intervals": ["07:00-09:00", "17:00-19:00"],
                        "activation_threshold": 0.7
                    },
                    "affected_edges": ["1234567890", "1234567891", "1234567892"]
                }
            ]
        }
    }


class StrategyUpdateRequest(BaseModel):
    """
    Request model for updating an existing strategy instance.

    Attributes:
        strategy_name: Optional updated display name
        parameters: Optional updated parameter values
        affected_edges: Optional updated list of edge IDs
        original_updated_at: Timestamp for optimistic concurrency control
    """

    strategy_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Updated strategy name (optional)"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        None,
        description="Updated parameter values (optional)"
    )
    affected_edges: Optional[List[str]] = Field(
        None,
        min_length=1,
        description="Updated list of edge IDs (optional)"
    )
    original_updated_at: str = Field(
        ...,
        description="Original updated_at timestamp for concurrency check (ISO8601)"
    )

    @field_validator("strategy_name")
    @classmethod
    def validate_strategy_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate strategy name is not just whitespace if provided."""
        if v is not None:
            if not v.strip():
                raise ValueError("Strategy name cannot be empty or whitespace")
            return v.strip()
        return v

    @field_validator("affected_edges")
    @classmethod
    def validate_affected_edges(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate affected_edges has at least one item if provided."""
        if v is not None:
            if len(v) == 0:
                raise ValueError("At least one edge must be selected for this strategy")
            # Remove duplicates while preserving order
            seen = set()
            unique_edges = []
            for edge_id in v:
                if edge_id not in seen:
                    seen.add(edge_id)
                    unique_edges.append(edge_id)
            return unique_edges
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "strategy_name": "Updated Strategy Name",
                    "parameters": {
                        "speed_limit": 85,
                        "time_intervals": ["08:00-10:00"]
                    },
                    "original_updated_at": "2025-10-21T14:30:25Z"
                }
            ]
        }
    }
