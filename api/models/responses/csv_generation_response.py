"""
CSV Generation Response Models

For batch scenario generation from CSV files.
"""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime


class CsvGenerationResponse(BaseModel):
    """Response from CSV scenario generation."""

    task_id: str = Field(..., description="Unique task ID for tracking")
    csv_file: str = Field(..., description="CSV filename processed")
    status: str = Field(..., description="Status: processing|completed|failed")
    message: str = Field(..., description="Human-readable status message")
    state_file: str = Field(..., description="Path to state tracking JSON file")
    generated_count: Optional[int] = Field(None, description="Number of scenarios generated (after completion)")

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "csv_gen_20251114_143000",
                "csv_file": "all_extracted_events.csv",
                "status": "processing",
                "message": "CSV场景生成已启动",
                "state_file": "events/csv_extraction_status/all_extracted_events_status.json",
                "generated_count": None
            }
        }


class EventGenerationSuccess(BaseModel):
    """Successful event generation record."""

    report_id: str
    event_type: str
    scenarios: List[str]  # e.g., ["scenario_12547_no_control", "scenario_12547_vss"]
    timestamp: str


class EventGenerationFailure(BaseModel):
    """Failed event generation record."""

    report_id: str
    event_type: str
    error: str
    timestamp: str


class CsvGenerationStateFile(BaseModel):
    """Structure of the CSV generation state tracking file."""

    csv_file: str
    task_id: str
    started_at: str
    completed_at: Optional[str] = None
    status: str  # processing|completed|failed|cancelled

    total_events_in_csv: int = 0
    events_processed: int = 0
    events_skipped_existing: int = 0
    events_generated: int = 0

    scenarios_generated: Dict[str, int] = Field(
        default_factory=lambda: {
            "no_control": 0,
            "vss": 0,
            "tec": 0,
            "dhs": 0,
            "total": 0
        }
    )

    failed_events: List[EventGenerationFailure] = Field(default_factory=list)
    successful_events: List[EventGenerationSuccess] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "csv_file": "all_extracted_events.csv",
                "task_id": "csv_gen_20251114_143000",
                "started_at": "2025-11-14T14:30:00",
                "completed_at": "2025-11-14T14:35:00",
                "status": "completed",
                "total_events_in_csv": 150,
                "events_processed": 150,
                "events_skipped_existing": 100,
                "events_generated": 50,
                "scenarios_generated": {
                    "no_control": 50,
                    "vss": 50,
                    "tec": 50,
                    "dhs": 0,
                    "total": 150
                },
                "failed_events": [],
                "successful_events": []
            }
        }
