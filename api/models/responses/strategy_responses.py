"""
Strategy Response Models

Pydantic models for strategy API responses.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class StrategyCreateResponse(BaseModel):
    """
    Response model for strategy creation.

    Attributes:
        strategy_id: Unique identifier of created strategy
        message: Success message
    """

    strategy_id: str = Field(
        ...,
        description="Unique strategy identifier"
    )
    message: str = Field(
        ...,
        description="Success message"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "strategy_id": "strat_20251021143025_a3f7b9",
                    "message": "Strategy created successfully"
                }
            ]
        }
    }


class EdgeDetail(BaseModel):
    """
    Detailed edge information for strategy response.

    Attributes:
        edge_id: Edge identifier
        route_code: Route code (e.g., "G4202")
        stake_range: Stake range (e.g., "K10+500-K12+300")
        length: Edge length in meters
    """

    edge_id: str = Field(..., description="Edge identifier")
    route_code: Optional[str] = Field(None, description="Route code")
    stake_range: Optional[str] = Field(None, description="Stake range")
    length: Optional[float] = Field(None, description="Edge length in meters")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "edge_id": "1234567890",
                    "route_code": "G4202",
                    "stake_range": "K10+500-K12+300",
                    "length": 1800.0
                }
            ]
        }
    }


class StrategyMetadata(BaseModel):
    """Strategy metadata for responses."""

    created_at: str = Field(..., description="Creation timestamp (ISO8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO8601)")
    created_by: str = Field(..., description="Creator system identifier")
    version: int = Field(..., description="Version number (incremented on updates)")


class StrategyListItem(BaseModel):
    """
    Strategy list item for paginated list response.

    Attributes:
        strategy_id: Unique identifier
        strategy_name: Display name
        strategy_type: Strategy type (VSS/DHS/TEC)
        template_id: Reference to template
        template_name: Template display name
        edges_count: Number of affected edges
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    strategy_id: str
    strategy_name: str
    strategy_type: str
    template_id: str
    template_name: str
    edges_count: int
    created_at: str
    updated_at: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "strategy_id": "strat_20251021143025_a3f7b9",
                    "strategy_name": "Morning Peak VSS Control",
                    "strategy_type": "VSS",
                    "template_id": "vss_moderate",
                    "template_name": "VSS Moderate Speed Control",
                    "edges_count": 15,
                    "created_at": "2025-10-21T14:30:25Z",
                    "updated_at": "2025-10-21T15:45:10Z"
                }
            ]
        }
    }


class StrategyListResponse(BaseModel):
    """
    Paginated list of strategies.

    Attributes:
        strategies: List of strategy items
        total_count: Total number of strategies matching filter
        page: Current page number (1-indexed)
        page_size: Items per page
    """

    strategies: List[StrategyListItem]
    total_count: int
    page: int
    page_size: int

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "strategies": [
                        {
                            "strategy_id": "strat_20251021143025_a3f7b9",
                            "strategy_name": "Morning Peak VSS Control",
                            "strategy_type": "VSS",
                            "template_id": "vss_moderate",
                            "template_name": "VSS Moderate Speed Control",
                            "edges_count": 15,
                            "created_at": "2025-10-21T14:30:25Z",
                            "updated_at": "2025-10-21T14:30:25Z"
                        }
                    ],
                    "total_count": 1,
                    "page": 1,
                    "page_size": 20
                }
            ]
        }
    }


class StrategyDetailResponse(BaseModel):
    """
    Complete strategy details for single strategy retrieval.

    Attributes:
        strategy_id: Unique identifier
        strategy_name: Display name
        template_id: Reference to template
        template_name: Template display name
        strategy_type: Strategy type (VSS/DHS/TEC)
        parameters: Configured parameter values
        affected_edges: List of affected edges with details
        metadata: Creation/update metadata
        is_used_in_plans: Whether strategy is used in any plans (Phase 2 integration)
    """

    strategy_id: str
    strategy_name: str
    template_id: str
    template_name: str
    strategy_type: str
    parameters: Dict[str, Any]
    affected_edges: List[EdgeDetail]
    metadata: StrategyMetadata
    is_used_in_plans: bool = Field(
        default=False,
        description="Whether strategy is used in plans (Phase 2 integration)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "strategy_id": "strat_20251021143025_a3f7b9",
                    "strategy_name": "Morning Peak VSS Control - G4202",
                    "template_id": "vss_moderate",
                    "template_name": "VSS Moderate Speed Control",
                    "strategy_type": "VSS",
                    "parameters": {
                        "speed_limit": 80,
                        "time_intervals": ["07:00-09:00", "17:00-19:00"],
                        "activation_threshold": 0.7
                    },
                    "affected_edges": [
                        {
                            "edge_id": "1234567890",
                            "route_code": "G4202",
                            "stake_range": "K10+500-K12+300",
                            "length": 1800.0
                        }
                    ],
                    "metadata": {
                        "created_at": "2025-10-21T14:30:25Z",
                        "updated_at": "2025-10-21T15:45:10Z",
                        "created_by": "WIN-SERVER-01",
                        "version": 3
                    },
                    "is_used_in_plans": False
                }
            ]
        }
    }
