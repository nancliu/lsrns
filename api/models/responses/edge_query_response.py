"""
Edge query response models for road segment filtering API.

This module defines Pydantic models for serializing edge information
and metadata responses to JSON format.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class EdgeInfoResponse(BaseModel):
    """
    Single edge information (response format).

    Corresponds to shared.data_access.edge_query.EdgeInfo dataclass.
    """

    edge_id: str = Field(..., description="SUMO edge ID")
    route_code: str = Field(..., description="Route code (e.g., G4202)")
    section_code: Optional[str] = Field(
        None,
        description="Section code (e.g., G4202001)"
    )
    start_stake: Optional[float] = Field(None, description="Start stake (km)")
    end_stake: Optional[float] = Field(None, description="End stake (km)")
    length: Optional[float] = Field(None, description="Length (meters)")
    num_lanes: Optional[int] = Field(None, description="Number of lanes")
    route_direction: Optional[str] = Field(
        None,
        description="Direction (clockwise/counterclockwise)"
    )
    node_type: Optional[str] = Field(
        None,
        description="Node type (diverging/merging/entrance/exit)"
    )
    gantry_count: int = Field(0, description="Number of gantries")
    gantry_ids: List[str] = Field(
        default_factory=list,
        description="List of gantry IDs"
    )

    @classmethod
    def from_edge_info(cls, edge_info) -> "EdgeInfoResponse":
        """
        Create response model from EdgeInfo dataclass.

        Args:
            edge_info: EdgeInfo dataclass from shared layer

        Returns:
            EdgeInfoResponse instance
        """
        return cls(
            edge_id=edge_info.edge_id,
            route_code=edge_info.route_code,
            section_code=edge_info.section_code,
            start_stake=edge_info.start_stake,
            end_stake=edge_info.end_stake,
            length=edge_info.length,
            num_lanes=edge_info.num_lanes,
            route_direction=edge_info.route_direction,
            node_type=edge_info.node_type,
            gantry_count=edge_info.gantry_count,
            gantry_ids=edge_info.gantry_ids
        )

    class Config:
        """Pydantic model configuration."""

        schema_extra = {
            "example": {
                "edge_id": "-5880",
                "route_code": "SA2",
                "section_code": "SA002002",
                "start_stake": 139.2,
                "end_stake": 140.6,
                "length": 1328.0,
                "num_lanes": 3,
                "route_direction": "counterclockwise",
                "node_type": "diverging",
                "gantry_count": 3,
                "gantry_ids": ["G001", "G002", "G003"]
            }
        }


class EdgeQueryResponse(BaseModel):
    """
    Edge query response with metadata.

    Wraps list of edges with total count and optional warnings.
    """

    edges: List[EdgeInfoResponse] = Field(
        ...,
        description="List of edges matching filters"
    )
    total_count: int = Field(..., description="Total number of edges found")
    warning: Optional[str] = Field(
        None,
        description="Warning message (e.g., too many results)"
    )

    @classmethod
    def from_edge_infos(cls, edge_infos: List) -> "EdgeQueryResponse":
        """
        Create response from list of EdgeInfo dataclasses.

        Automatically adds warnings based on result count:
        - >100 edges: Strong recommendation to add filters
        - >50 edges: Suggestion to refine filters

        Args:
            edge_infos: List of EdgeInfo dataclasses

        Returns:
            EdgeQueryResponse with edges and warnings
        """
        total_count = len(edge_infos)
        edges = [EdgeInfoResponse.from_edge_info(e) for e in edge_infos]

        warning = None
        if total_count > 100:
            warning = (
                f"Too many results ({total_count}), please add more "
                "filters to narrow down selection."
            )
        elif total_count > 50:
            warning = (
                f"Large result set ({total_count}), consider adding "
                "more filters for better precision."
            )

        return cls(
            edges=edges,
            total_count=total_count,
            warning=warning
        )

    class Config:
        """Pydantic model configuration."""

        schema_extra = {
            "example": {
                "edges": [
                    {
                        "edge_id": "-5880",
                        "route_code": "SA2",
                        "section_code": "SA002002",
                        "start_stake": 139.2,
                        "end_stake": 140.6,
                        "length": 1328.0,
                        "num_lanes": 3,
                        "route_direction": "counterclockwise",
                        "node_type": "diverging",
                        "gantry_count": 3,
                        "gantry_ids": ["G001", "G002", "G003"]
                    }
                ],
                "total_count": 1,
                "warning": None
            }
        }


class RouteInfo(BaseModel):
    """Route metadata for hierarchical filtering."""

    route_code: str = Field(..., description="Route code")
    edge_count: int = Field(
        ...,
        description="Number of edges on this route"
    )

    class Config:
        """Pydantic model configuration."""

        schema_extra = {
            "example": {
                "route_code": "G4202",
                "edge_count": 1198
            }
        }


class SectionInfo(BaseModel):
    """Section metadata for hierarchical filtering."""

    section_code: str = Field(..., description="Section code")
    route_code: str = Field(..., description="Parent route code")
    edge_count: int = Field(
        ...,
        description="Number of edges in this section"
    )
    min_stake: Optional[float] = Field(None, description="Minimum stake (km)")
    max_stake: Optional[float] = Field(None, description="Maximum stake (km)")
    stake_range: str = Field(
        ...,
        description="Stake range display (e.g., 'K10.0-K50.0')"
    )

    class Config:
        """Pydantic model configuration."""

        schema_extra = {
            "example": {
                "section_code": "G4202001",
                "route_code": "G4202",
                "edge_count": 621,
                "min_stake": 0.0,
                "max_stake": 85.68,
                "stake_range": "K0.0-K85.68"
            }
        }


class DemonstrationInfo(BaseModel):
    """Demonstration area metadata for filtering."""

    demonstration_id: int = Field(..., description="Demonstration area ID")
    route_code: str = Field(..., description="Route code")
    edge_count: int = Field(
        ...,
        description="Number of edges in demonstration area"
    )
    stake_range: str = Field(
        ...,
        description="Stake range display (e.g., '1.17-85.68km')"
    )

    class Config:
        """Pydantic model configuration."""

        schema_extra = {
            "example": {
                "demonstration_id": 5,
                "route_code": "G4202",
                "edge_count": 461,
                "stake_range": "1.17-85.68km"
            }
        }
