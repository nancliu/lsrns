"""
批量仿真任务实体模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from ...enums import BatchSimulationStatus


class BatchSimulation(BaseModel):
    """批量仿真任务模型"""

    batch_id: str = Field(
        ...,
        description="批次唯一标识符",
        examples=["batch_20251019_001"]
    )

    batch_name: str = Field(
        ...,
        description="批次名称（用户自定义）",
        examples=["高峰时段方案对比测试"]
    )

    case_id: str = Field(
        ...,
        description="关联的案例ID（外键，引用已有Case）",
        examples=["case_20251015_baseline"]
    )

    plan_ids: List[str] = Field(
        ...,
        description="待测试的方案ID列表（外键）",
        min_length=1,
        examples=[["plan_baseline", "plan_001", "plan_002", "plan_003"]]
    )

    status: BatchSimulationStatus = Field(
        default=BatchSimulationStatus.PENDING,
        description="批次状态（PENDING/RUNNING/COMPLETED/FAILED）"
    )

    progress: Dict[str, int] = Field(
        default_factory=lambda: {"total": 0, "completed": 0, "failed": 0},
        description="进度统计",
        examples=[{"total": 4, "completed": 2, "failed": 0}]
    )

    simulation_ids: List[str] = Field(
        default_factory=list,
        description="生成的仿真ID列表（外键，引用Simulation）",
        examples=[["sim_001_plan_baseline", "sim_002_plan_001"]]
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
                "batch_id": "batch_20251019_001",
                "batch_name": "高峰时段方案对比测试",
                "case_id": "case_20251015_baseline",
                "plan_ids": ["plan_baseline", "plan_001", "plan_002"],
                "status": "running",
                "progress": {"total": 3, "completed": 1, "failed": 0},
                "simulation_ids": ["sim_001_plan_baseline"],
                "created_at": "2025-10-19T14:00:00",
                "updated_at": "2025-10-19T14:15:00"
            }
        }
