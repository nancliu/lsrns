"""
批量优化仿真请求模型
"""

from pydantic import BaseModel, Field, field_validator
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

    simulation_duration: Optional[Dict[str, int]] = Field(
        default=None,
        description="""
        自定义仿真时长（P1-1: 新增）

        用于覆盖从case元数据推导的默认仿真时长。
        格式: {hours, minutes, total_minutes}

        示例：{hours: 4, minutes: 0, total_minutes: 240}

        约束条件:
        - total_minutes: 1-1440 (1分钟到24小时)
        - hours + minutes * 60 应等于 total_minutes
        """,
        examples=[{"hours": 4, "minutes": 0, "total_minutes": 240}]
    )

    @field_validator('simulation_duration', mode='after')
    @classmethod
    def validate_simulation_duration(cls, v: Optional[Dict[str, int]]) -> Optional[Dict[str, int]]:
        """验证simulation_duration字段的有效性"""
        if v is None:
            return v

        # 验证必需字段存在
        required_fields = {'hours', 'minutes', 'total_minutes'}
        if not required_fields.issubset(set(v.keys())):
            raise ValueError(
                f"simulation_duration必须包含字段: {required_fields}，"
                f"当前字段: {set(v.keys())}"
            )

        hours = v.get('hours', 0)
        minutes = v.get('minutes', 0)
        total_minutes = v.get('total_minutes', 0)

        # 验证数值范围
        if hours < 0 or hours > 24:
            raise ValueError(f"hours必须在0-24范围内，当前值: {hours}")

        if minutes < 0 or minutes >= 60:
            raise ValueError(f"minutes必须在0-59范围内，当前值: {minutes}")

        # 验证total_minutes范围 (1分钟到24小时)
        if total_minutes < 1 or total_minutes > 1440:
            raise ValueError(
                f"total_minutes必须在1-1440范围内（1分钟到24小时），当前值: {total_minutes}"
            )

        # 验证hours和minutes的总和是否匹配total_minutes
        calculated_total = hours * 60 + minutes
        if calculated_total != total_minutes:
            raise ValueError(
                f"hours({hours}) * 60 + minutes({minutes}) = {calculated_total} "
                f"不等于 total_minutes({total_minutes})"
            )

        return v

    edgedata_use_template_edges: Optional[bool] = Field(
        default=False,
        description="""
        EdgeData模板edges属性保留标志（P2-2: 新增）

        当output_edgedata启用时生效。控制生成的edgeData.add.xml是否保留edges属性。

        - False (默认): 移除edges属性，使用全量边集合
        - True: 保留edges属性，使用模板指定的特定边集合
        """,
        examples=[False, True]
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
                },
                "simulation_duration": {
                    "hours": 4,
                    "minutes": 0,
                    "total_minutes": 240
                },
                "edgedata_use_template_edges": False
            }
        }
