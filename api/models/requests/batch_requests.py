"""
Event Batch Request Models

Request models for event-scenario batch operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CreateEventBatchRequest(BaseModel):
    """Request model for creating an event-scenario batch"""

    event_id: str = Field(..., description="Event ID")
    scenario_ids: Optional[List[str]] = Field(
        None,
        description="List of scenario IDs to include (if None, use all scenarios for this event)"
    )
    simulation_config: Optional[Dict[str, Any]] = Field(
        default_factory=lambda: {},
        description="Simulation configuration"
    )

    class Config:
        schema_extra = {
            "example": {
                "event_id": "8210655",
                "scenario_ids": [
                    "scenario_8210655_no_control",
                    "scenario_8210655_vss",
                    "scenario_8210655_tec"
                ],
                "simulation_config": {
                    "duration_hours": None,
                    "random_seed": 12345,
                    "output_config": {
                        "tripinfo": True,
                        "edgedata": True,
                        "summary": True
                    }
                }
            }
        }


class StartEventBatchRequest(BaseModel):
    """Request model for starting an event-scenario batch"""

    batch_id: str = Field(..., description="Batch ID")
    parallel_workers: int = Field(4, description="Number of parallel simulation workers", ge=1, le=8)
    auto_run_analysis: bool = Field(
        True,
        description="Whether to automatically run analysis after simulation completion"
    )

    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_event_8210655_20251115_100000",
                "parallel_workers": 4,
                "auto_run_analysis": True
            }
        }
