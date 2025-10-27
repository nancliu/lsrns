"""
方案请求模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class CreatePlanRequest(BaseModel):
    """创建方案请求模型"""

    plan_name: str = Field(
        ...,
        description="方案名称",
        min_length=1,
        max_length=100,
        examples=["早高峰综合管控方案A", "节假日交通管理方案"]
    )

    description: Optional[str] = Field(
        None,
        description="方案详细描述",
        max_length=500,
        examples=["缓解K10-K15路段早高峰拥堵"]
    )

    strategy_ids: List[str] = Field(
        default_factory=list,
        description="包含的策略ID列表（可为空表示基准方案）",
        examples=[["strategy_001", "strategy_002", "strategy_003"]]
    )

    tags: List[str] = Field(
        default_factory=list,
        description="标签列表",
        examples=[["早高峰", "综合管控"]]
    )

    target_scenario: Optional[str] = Field(
        None,
        description="目标场景",
        max_length=200,
        examples=["工作日早高峰(7:00-9:00)"]
    )

    expected_effects: Optional[dict] = Field(
        None,
        description="预期效果（键值对）",
        examples=[{
            "reduce_congestion": "降低瓶颈路段拥堵20%",
            "improve_speed": "提升平均速度15%"
        }]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plan_name": "早高峰综合管控方案A",
                "description": "缓解K10-K15路段早高峰拥堵",
                "strategy_ids": ["strategy_001", "strategy_002", "strategy_003"],
                "tags": ["早高峰", "综合管控"],
                "target_scenario": "工作日早高峰(7:00-9:00)",
                "expected_effects": {
                    "reduce_congestion": "降低瓶颈路段拥堵20%",
                    "improve_speed": "提升平均速度15%"
                }
            }
        }


class UpdatePlanRequest(BaseModel):
    """更新方案请求模型（所有字段可选）"""

    plan_name: Optional[str] = Field(
        None,
        description="方案名称",
        min_length=1,
        max_length=100
    )

    description: Optional[str] = Field(
        None,
        description="方案详细描述",
        max_length=500
    )

    strategy_ids: Optional[List[str]] = Field(
        None,
        description="包含的策略ID列表"
    )

    tags: Optional[List[str]] = Field(
        None,
        description="标签列表"
    )

    target_scenario: Optional[str] = Field(
        None,
        description="目标场景",
        max_length=200
    )

    expected_effects: Optional[dict] = Field(
        None,
        description="预期效果（键值对）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plan_name": "早高峰综合管控方案A（优化版）",
                "tags": ["早高峰", "综合管控", "优化"],
                "strategy_ids": ["strategy_001", "strategy_002"]
            }
        }
