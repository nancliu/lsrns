"""
Edge query request models for filtering road segments.

This module defines Pydantic models for validating query parameters
used in edge filtering API endpoints.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional


class EdgeQueryRequest(BaseModel):
    """
    Edge filtering request parameters.

    All fields are optional - empty request returns all edges.
    Supports multi-dimensional filtering by route, section, stake range,
    length, lanes, direction, node type, demonstration areas, and gantry presence.
    """

    route_codes: Optional[str] = Field(
        None,
        description="Comma-separated route codes (e.g., 'G4202,SA2')"
    )
    section_codes: Optional[str] = Field(
        None,
        description="Comma-separated section codes (e.g., 'G4202001,G4202002')"
    )
    node_types: Optional[str] = Field(
        None,
        description="Comma-separated node types (normal,diverging,merging,lane_increase,lane_decrease,entrance,exit)"
    )
    min_stake: Optional[float] = Field(
        None,
        ge=0,
        description="Minimum stake number in kilometers (≥0)"
    )
    max_stake: Optional[float] = Field(
        None,
        ge=0,
        description="Maximum stake number in kilometers (≥0)"
    )
    min_length: Optional[float] = Field(
        None,
        gt=0,
        description="Minimum edge length in meters (>0)"
    )
    max_length: Optional[float] = Field(
        None,
        gt=0,
        description="Maximum edge length in meters (>0)"
    )
    route_direction: Optional[str] = Field(
        None,
        description="Route direction: 'upstream', 'downstream', 'clockwise', or 'counterclockwise'"
    )
    demonstration_ids: Optional[str] = Field(
        None,
        description="Comma-separated demonstration IDs (e.g., '5,7')"
    )
    min_lanes: Optional[int] = Field(
        None,
        ge=1,
        description="Minimum number of lanes (≥1)"
    )
    with_gantry: bool = Field(
        False,
        description="If true, return only edges with at least one gantry"
    )

    @validator('max_stake')
    def validate_stake_range(cls, v, values):
        """Ensure max_stake >= min_stake when both are provided."""
        if v is not None and 'min_stake' in values and values['min_stake'] is not None:
            if v < values['min_stake']:
                raise ValueError('max_stake must be >= min_stake')
        return v

    @validator('max_length')
    def validate_length_range(cls, v, values):
        """Ensure max_length >= min_length when both are provided."""
        if v is not None and 'min_length' in values and values['min_length'] is not None:
            if v < values['min_length']:
                raise ValueError('max_length must be >= min_length')
        return v

    @validator('route_direction')
    def validate_direction(cls, v):
        """Validate route direction values."""
        valid_directions = ['upstream', 'downstream', 'clockwise', 'counterclockwise']
        if v is not None and v not in valid_directions:
            raise ValueError(f'route_direction must be one of: {valid_directions}')
        return v

    @validator('node_types')
    def validate_node_types(cls, v):
        """Validate node type values."""
        if v is not None:
            valid_types = {'normal', 'diverging', 'merging', 'lane_increase', 'lane_decrease', 'entrance', 'exit'}
            types = [t.strip() for t in v.split(',')]
            invalid = [t for t in types if t not in valid_types]
            if invalid:
                raise ValueError(
                    f'Invalid node types: {invalid}. '
                    f'Must be one of: {valid_types}'
                )
        return v

    def to_query_params(self) -> dict:
        """
        Convert request model to query function parameters.

        Splits comma-separated strings into lists for database queries.

        Returns:
            Dict with filter parameters ready for query function
        """
        return {
            'route_codes': (
                self.route_codes.split(',') if self.route_codes else None
            ),
            'section_codes': (
                self.section_codes.split(',') if self.section_codes else None
            ),
            'node_types': (
                self.node_types.split(',') if self.node_types else None
            ),
            'min_stake': self.min_stake,
            'max_stake': self.max_stake,
            'min_length': self.min_length,
            'max_length': self.max_length,
            'route_direction': self.route_direction,
            'demonstration_ids': (
                [int(d) for d in self.demonstration_ids.split(',')]
                if self.demonstration_ids else None
            ),
            'min_lanes': self.min_lanes,
            'with_gantry': self.with_gantry
        }

    class Config:
        """Pydantic model configuration."""

        schema_extra = {
            "example": {
                "route_codes": "G4202",
                "section_codes": "G4202001",
                "min_stake": 10.0,
                "max_stake": 50.0,
                "min_length": 500,
                "max_length": 2000,
                "min_lanes": 3,
                "route_direction": "clockwise",
                "with_gantry": True
            }
        }
