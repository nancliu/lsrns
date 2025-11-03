"""
批量优化仿真请求模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal


class OutputConfig(BaseModel):
    """仿真输出配置 (Phase 1: 新增)"""

    summary_xml: bool = Field(
        default=True,
        description="是否启用summary.xml输出（基础统计，总是启用）"
    )

    e1_detector_data: bool = Field(
        default=True,
        description="是否启用E1检测器数据输出（门架流量，总是启用）"
    )

    edgedata_xml: bool = Field(
        default=False,
        description="是否启用edgedata.xml输出（路段流量统计，性能提示：+20%仿真时间）"
    )

    tripinfo_xml: bool = Field(
        default=False,
        description="是否启用tripinfo.xml输出（车辆行程信息，性能提示：+30%仿真时间）"
    )


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

    output_level: Optional[Literal["minimal", "standard", "full"]] = Field(
        default=None,
        description="""
        仿真输出级别（已弃用，保留向后兼容）

        使用 output_config 替代此字段。
        如果同时提供了两者，output_config 优先。
        """,
        examples=["standard"]
    )

    output_config: Optional[OutputConfig] = Field(
        default_factory=OutputConfig,
        description="""
        仿真输出配置 (Phase 1: 新增)

        详细指定哪些输出文件需要生成，包括性能提示。
        """
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
                "output_config": {
                    "summary_xml": True,
                    "e1_detector_data": True,
                    "edgedata_xml": False,
                    "tripinfo_xml": False
                },
                "simulation_config": {
                    "begin": 0,
                    "end": 14400,
                    "step_length": 1
                }
            }
        }
