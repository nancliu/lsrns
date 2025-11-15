"""
CSV Generation Request Models

For batch scenario generation from CSV files.
"""

from pydantic import BaseModel, Field


class CsvGenerationRequest(BaseModel):
    """Request to generate scenarios from CSV file."""

    csv_file: str = Field(
        ...,
        description="CSV filename in events/ folder (e.g., 'all_extracted_events.csv')",
        min_length=1
    )

    generate_all_strategies: bool = Field(
        default=True,
        description="Generate all control strategies (VSS/TEC/DHS) or just NO_CONTROL"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "csv_file": "all_extracted_events.csv",
                "generate_all_strategies": True
            }
        }
