"""
控制方案实体模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Plan(BaseModel):
    """控制方案模型"""

    plan_id: str = Field(
        ...,
        description="方案唯一标识符",
        examples=["plan_20251019_001", "plan_baseline"]
    )

    plan_name: str = Field(
        ...,
        description="方案名称（用户自定义）",
        examples=["高峰时段综合管控方案A", "基线方案（无管控）"]
    )

    description: Optional[str] = Field(
        None,
        description="方案详细描述（目标、适用场景）",
        examples=["针对早高峰7-9点，结合限速和入口控制"]
    )

    strategy_ids: List[str] = Field(
        default_factory=list,
        description="包含的策略ID列表（外键，允许空表示基线方案）",
        examples=[["strategy_001", "strategy_002", "strategy_003"]]
    )

    additional_file_path: Optional[str] = Field(
        None,
        description="生成的SUMO Additional文件路径（相对路径）",
        examples=["control_data/plans/plan_20251019_001/control.add.xml"]
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间戳"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="最后更新时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "plan_20251019_001",
                "plan_name": "高峰时段综合管控方案A",
                "description": "结合G4202分流点限速和入口控制",
                "strategy_ids": ["strategy_001", "strategy_002"],
                "additional_file_path": "control_data/plans/plan_20251019_001/control.add.xml",
                "created_at": "2025-10-19T11:00:00",
                "updated_at": "2025-10-19T11:00:00"
            }
        }
