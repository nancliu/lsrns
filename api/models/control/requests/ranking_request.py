"""
策略排序请求模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class RankingCriteria(BaseModel):
    """排序评估标准权重配置"""

    effectiveness_weight: float = Field(
        default=0.40,
        description="有效性权重 (0-1)",
        ge=0,
        le=1,
        examples=[0.40]
    )

    coverage_weight: float = Field(
        default=0.25,
        description="覆盖率权重 (0-1)",
        ge=0,
        le=1,
        examples=[0.25]
    )

    efficiency_weight: float = Field(
        default=0.20,
        description="效率权重 (0-1)",
        ge=0,
        le=1,
        examples=[0.20]
    )

    reliability_weight: float = Field(
        default=0.15,
        description="可靠性权重 (0-1)",
        ge=0,
        le=1,
        examples=[0.15]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "effectiveness_weight": 0.40,
                "coverage_weight": 0.25,
                "efficiency_weight": 0.20,
                "reliability_weight": 0.15
            }
        }


class StrategyRankingRequest(BaseModel):
    """
    策略排序请求

    用于对批量仿真结果中的多个控制策略进行多准则排序评估
    """

    case_id: str = Field(
        ...,
        description="关联的案例ID",
        examples=["case_20251105_001"]
    )

    batch_id: str = Field(
        ...,
        description="批量仿真批次ID",
        examples=["batch_20251105_001"]
    )

    baseline_plan_id: str = Field(
        default="baseline_plan",
        description="基准方案ID（作为对比基线）",
        examples=["baseline_plan"]
    )

    strategy_plan_ids: Optional[List[str]] = Field(
        default=None,
        description="待排序的策略方案ID列表（如果不指定则自动检测批次中的所有方案）",
        examples=[["plan_vss_001", "plan_tec_001", "plan_dhs_001", "plan_vss_tec_combo"]]
    )

    ranking_criteria: Optional[RankingCriteria] = Field(
        default_factory=RankingCriteria,
        description="自定义排序评估标准权重（可选，默认为标准权重）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "case_id": "case_20251105_001",
                "batch_id": "batch_20251105_001",
                "baseline_plan_id": "baseline_plan",
                "strategy_plan_ids": ["plan_vss_001", "plan_tec_001", "plan_dhs_001"],
                "ranking_criteria": {
                    "effectiveness_weight": 0.40,
                    "coverage_weight": 0.25,
                    "efficiency_weight": 0.20,
                    "reliability_weight": 0.15
                }
            }
        }
