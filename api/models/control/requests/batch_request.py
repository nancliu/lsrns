"""
批量优化仿真请求模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class CreateBatchRequest(BaseModel):
    """创建批量仿真批次请求"""

    case_id: str = Field(
        ...,
        description="关联的案例ID",
        examples=["case_20251025_001"]
    )

    plan_ids: List[str] = Field(
        ...,
        description="待测试的方案ID列表（必须包含baseline_plan）",
        min_length=1,
        examples=[["baseline_plan", "plan_20251025_140530_a1b2c", "plan_20251025_141200_d3e4f"]]
    )

    num_seeds: int = Field(
        default=3,
        description="每个方案的随机种子数量",
        ge=1,
        le=10,
        examples=[3]
    )

    base_seed: int = Field(
        default=66,
        description="起始随机种子值",
        ge=0,
        examples=[66]
    )

    simulation_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="仿真配置参数（可选，覆盖默认值）",
        examples=[{
            "begin": 0,
            "end": 14400,
            "step_length": 1
        }]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "case_20251025_001",
                "plan_ids": [
                    "baseline_plan",
                    "plan_20251025_140530_a1b2c",
                    "plan_20251025_141200_d3e4f"
                ],
                "num_seeds": 3,
                "base_seed": 66,
                "simulation_config": {
                    "begin": 0,
                    "end": 14400,
                    "step_length": 1
                }
            }
        }
