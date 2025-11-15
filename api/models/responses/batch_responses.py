"""
Event Batch Response Models

Response models for event-scenario batch operations.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class EventBatchCreatedResponse(BaseModel):
    """Response model for event batch creation"""

    batch_id: str = Field(..., description="Batch ID")
    event_id: str = Field(..., description="Event ID")
    event_type: str = Field(..., description="Event type")
    total_scenarios: int = Field(..., description="Total number of scenarios in batch")
    case_ids: List[str] = Field(..., description="List of created case IDs")
    simulation_ids: List[str] = Field(..., description="List of created simulation IDs")
    status: str = Field(..., description="Batch status")

    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_event_8210655_20251115_100000",
                "event_id": "8210655",
                "event_type": "congestion",
                "total_scenarios": 3,
                "case_ids": ["case_20251115_001", "case_20251115_002", "case_20251115_003"],
                "simulation_ids": ["sim_20251115_001", "sim_20251115_002", "sim_20251115_003"],
                "status": "created"
            }
        }


class SimulationStatusDetail(BaseModel):
    """Simulation status detail"""

    simulation_id: str = Field(..., description="Simulation ID")
    scenario_id: str = Field(..., description="Scenario ID")
    strategy_type: str = Field(..., description="Control strategy type")
    case_id: str = Field(..., description="Case ID")
    status: str = Field(..., description="Simulation status")
    progress: float = Field(..., description="Simulation progress (0-100)")


class EventBatchStatusResponse(BaseModel):
    """Response model for event batch status"""

    batch_id: str = Field(..., description="Batch ID")
    event_id: str = Field(..., description="Event ID")
    event_type: str = Field(..., description="Event type")
    status: str = Field(..., description="Batch status")
    total_simulations: int = Field(..., description="Total number of simulations")
    completed_simulations: int = Field(..., description="Number of completed simulations")
    running_simulations: int = Field(..., description="Number of running simulations")
    failed_simulations: int = Field(..., description="Number of failed simulations")
    progress_percent: int = Field(..., description="Overall progress percentage")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    simulations: List[SimulationStatusDetail] = Field(..., description="List of simulation statuses")

    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_event_8210655_20251115_100000",
                "event_id": "8210655",
                "event_type": "congestion",
                "status": "running",
                "total_simulations": 3,
                "completed_simulations": 1,
                "running_simulations": 2,
                "failed_simulations": 0,
                "progress_percent": 33,
                "estimated_completion": "2025-11-15T11:30:00",
                "simulations": [
                    {
                        "simulation_id": "sim_20251115_001",
                        "scenario_id": "scenario_8210655_no_control",
                        "strategy_type": "NO_CONTROL",
                        "case_id": "case_20251115_001",
                        "status": "completed",
                        "progress": 100
                    }
                ]
            }
        }


class EventBatchListItem(BaseModel):
    """Event batch list item"""

    batch_id: str = Field(..., description="Batch ID")
    event_id: str = Field(..., description="Event ID")
    event_type: str = Field(..., description="Event type")
    created_at: str = Field(..., description="Creation timestamp")
    status: str = Field(..., description="Batch status")
    total_simulations: int = Field(..., description="Total number of simulations")
    completed_simulations: int = Field(..., description="Number of completed simulations")
    analysis_batch_id: Optional[str] = Field(None, description="Analysis batch ID if available")


class EventBatchListResponse(BaseModel):
    """Response model for event batch list"""

    batches: List[EventBatchListItem] = Field(..., description="List of event batches")
    total_count: int = Field(..., description="Total number of batches")

    class Config:
        schema_extra = {
            "example": {
                "batches": [
                    {
                        "batch_id": "batch_event_8210655_20251115_100000",
                        "event_id": "8210655",
                        "event_type": "congestion",
                        "created_at": "2025-11-15T10:00:00",
                        "status": "completed",
                        "total_simulations": 3,
                        "completed_simulations": 3,
                        "analysis_batch_id": "analysis_20251115_101500"
                    }
                ],
                "total_count": 1
            }
        }


class EventBatchStartedResponse(BaseModel):
    """Response model for batch start"""

    batch_id: str = Field(..., description="Batch ID")
    status: str = Field(..., description="Batch status")
    simulation_ids: List[str] = Field(..., description="List of simulation IDs")
    message: str = Field(..., description="Status message")

    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_event_8210655_20251115_100000",
                "status": "running",
                "simulation_ids": ["sim_20251115_001", "sim_20251115_002", "sim_20251115_003"],
                "message": "Started 3 simulations"
            }
        }


class StrategyMetrics(BaseModel):
    """Metrics for a specific control strategy"""

    avg_speed: float = Field(..., description="Average speed (km/h)")
    avg_trip_duration: float = Field(..., description="Average trip duration (seconds)")
    completion_rate: float = Field(..., description="Completion rate (%)")
    total_vehicles: int = Field(..., description="Total vehicles")
    total_delay: float = Field(..., description="Total delay (seconds)")
    avg_waiting_time: float = Field(..., description="Average waiting time (seconds)")
    improvement_vs_baseline: Optional[Dict[str, float]] = Field(
        None,
        description="Improvement percentages vs baseline"
    )


class StrategyRanking(BaseModel):
    """Strategy ranking item"""

    strategy: str = Field(..., description="Strategy type")
    overall_improvement: float = Field(..., description="Overall improvement percentage")
    rank: int = Field(..., description="Rank (1=best)")


class EventBatchResultsResponse(BaseModel):
    """Response model for event batch results"""

    batch_id: str = Field(..., description="Batch ID")
    event_id: str = Field(..., description="Event ID")
    event_type: str = Field(..., description="Event type")
    analysis_batch_id: Optional[str] = Field(None, description="Analysis batch ID")
    strategy_comparison: Dict[str, StrategyMetrics] = Field(
        ...,
        description="Strategy comparison metrics"
    )
    strategy_ranking: List[StrategyRanking] = Field(
        ...,
        description="Strategy ranking by overall improvement"
    )

    class Config:
        schema_extra = {
            "example": {
                "batch_id": "batch_event_8210655_20251115_100000",
                "event_id": "8210655",
                "event_type": "congestion",
                "analysis_batch_id": "analysis_20251115_101500",
                "strategy_comparison": {
                    "NO_CONTROL": {
                        "avg_speed": 45.2,
                        "avg_trip_duration": 1200.0,
                        "completion_rate": 96.5,
                        "total_vehicles": 8934,
                        "total_delay": 45000.0,
                        "avg_waiting_time": 120.0
                    },
                    "VSS": {
                        "avg_speed": 52.8,
                        "avg_trip_duration": 1050.0,
                        "completion_rate": 98.2,
                        "total_vehicles": 8934,
                        "total_delay": 38000.0,
                        "avg_waiting_time": 95.0,
                        "improvement_vs_baseline": {
                            "avg_speed": 16.8,
                            "avg_trip_duration": -12.5,
                            "completion_rate": 1.76
                        }
                    }
                },
                "strategy_ranking": [
                    {"strategy": "VSS", "overall_improvement": 15.5, "rank": 1},
                    {"strategy": "TEC", "overall_improvement": 10.2, "rank": 2}
                ]
            }
        }
