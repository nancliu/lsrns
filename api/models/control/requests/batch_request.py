"""
批量优化仿真请求模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class CreateBatchRequest(BaseModel):
    """创建批量仿真批次请求 (Phase 3: 添加output_level配置)"""

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
        description="每个方案的随机种子数量（每个方案执行N次随机仿真以获取统计结果）",
        ge=1,
        le=10,
        examples=[3]
    )

    base_seed: int = Field(
        default=66,
        description="起始随机种子值（种子序列：base_seed, base_seed+1, ..., base_seed+num_seeds-1）",
        ge=0,
        examples=[66]
    )

    output_level: Literal["minimal", "standard", "full"] = Field(
        default="standard",
        description="""
        仿真输出级别（Phase 3新增）

        输出级别说明：
        - minimal: 最小化输出 - summary.xml + E1探测器数据（快速批量筛选）
        - standard: 标准输出 - summary.xml + E1探测器数据 + tripinfo.xml + edgedata.xml（详细分析）
        - full: 完整输出 - 所有输出文件（研究/演示用）

        注：summary.xml和E1探测器数据在所有级别均启用（预配置在网络拓扑中的门架位置）
        """,
        examples=["standard"]
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
                "output_level": "standard",
                "simulation_config": {
                    "begin": 0,
                    "end": 14400,
                    "step_length": 1
                }
            }
        }
