"""
策略排序响应模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class DimensionScores(BaseModel):
    """单个维度的评分"""

    effectiveness: float = Field(
        ...,
        description="有效性评分 (0-100)",
        ge=0,
        le=100,
        examples=[82.5]
    )

    coverage: float = Field(
        ...,
        description="覆盖率评分 (0-100)",
        ge=0,
        le=100,
        examples=[75.0]
    )

    efficiency: float = Field(
        ...,
        description="效率评分 (0-100)",
        ge=0,
        le=100,
        examples=[78.0]
    )

    reliability: float = Field(
        ...,
        description="可靠性评分 (0-100)",
        ge=0,
        le=100,
        examples=[76.0]
    )


class ImprovementMetrics(BaseModel):
    """策略相比基准的改进指标"""

    avg_speed_increase: Optional[str] = Field(
        default=None,
        description="平均速度提升百分比",
        examples=["+18.2%"]
    )

    travel_time_reduction: Optional[str] = Field(
        default=None,
        description="行程时间减少百分比",
        examples=["-22.5%"]
    )

    delay_reduction: Optional[str] = Field(
        default=None,
        description="延误时间减少百分比",
        examples=["-35.8%"]
    )

    affected_vehicles: Optional[str] = Field(
        default=None,
        description="受影响车辆比例",
        examples=["85% of network"]
    )


class RankedStrategy(BaseModel):
    """单个排序后的策略"""

    rank: int = Field(
        ...,
        description="排名位置 (1-N)",
        ge=1,
        examples=[1]
    )

    plan_id: str = Field(
        ...,
        description="方案ID",
        examples=["plan_vss_tec_combo"]
    )

    plan_name: str = Field(
        ...,
        description="方案名称",
        examples=["VSS+TEC协同控制"]
    )

    overall_score: float = Field(
        ...,
        description="总体评分 (0-100)",
        ge=0,
        le=100,
        examples=[78.5]
    )

    recommendation: str = Field(
        ...,
        description="推荐等级",
        examples=["强烈推荐"],
        json_schema_extra={
            "enum": ["强烈推荐", "推荐", "可选", "不推荐"]
        }
    )

    scores: DimensionScores = Field(
        ...,
        description="各维度的评分详情"
    )

    improvement_vs_baseline: Optional[Dict[str, float]] = Field(
        default=None,
        description="相比基准方案的改进幅度"
    )

    key_improvements: Optional[ImprovementMetrics] = Field(
        default=None,
        description="关键改进指标"
    )


class RankingMetadata(BaseModel):
    """排序元数据"""

    total_strategies: int = Field(
        ...,
        description="评估的策略总数",
        examples=[4]
    )

    baseline_plan_id: str = Field(
        ...,
        description="基准方案ID",
        examples=["baseline_plan"]
    )

    baseline_plan_name: str = Field(
        ...,
        description="基准方案名称",
        examples=["基准方案"]
    )

    baseline_score: float = Field(
        ...,
        description="基准方案的评分",
        examples=[50.0]
    )

    ranking_weights: Dict[str, float] = Field(
        ...,
        description="使用的权重配置",
        examples=[{
            "effectiveness": 0.40,
            "coverage": 0.25,
            "efficiency": 0.20,
            "reliability": 0.15
        }]
    )

    output_combination: str = Field(
        ...,
        description="使用的输出组合",
        examples=["summary+tripinfo+edgedata"],
        json_schema_extra={
            "enum": ["summary", "summary+tripinfo", "summary+edgedata", "summary+tripinfo+edgedata"]
        }
    )

    analysis_timestamp: Optional[str] = Field(
        default=None,
        description="分析时间戳 (ISO 8601格式)",
        examples=["2025-11-05T10:30:45.123456"]
    )


class StrategyRankingResponse(BaseModel):
    """
    策略排序响应

    包含排序结果、评分详情、推荐等级和可视化数据
    """

    ranking_id: str = Field(
        ...,
        description="排序任务ID",
        examples=["ranking_20251105_001"]
    )

    case_id: str = Field(
        ...,
        description="关联的案例ID",
        examples=["case_20251105_001"]
    )

    batch_id: str = Field(
        ...,
        description="关联的批次ID",
        examples=["batch_20251105_001"]
    )

    ranked_strategies: List[RankedStrategy] = Field(
        ...,
        description="排序后的策略列表（按评分从高到低）",
        min_length=1
    )

    ranking_metadata: RankingMetadata = Field(
        ...,
        description="排序元数据和配置信息"
    )

    comparison_table: Optional[Dict[str, Any]] = Field(
        default=None,
        description="策略对比表格数据（用于前端展示）"
    )

    report_file: Optional[str] = Field(
        default=None,
        description="生成的HTML报告文件路径",
        examples=["frontend/control/ranking_report_20251105_103045.html"]
    )

    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="响应生成时间",
        examples=["2025-11-05T10:30:45.123456"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "ranking_id": "ranking_20251105_001",
                "case_id": "case_20251105_001",
                "batch_id": "batch_20251105_001",
                "ranked_strategies": [
                    {
                        "rank": 1,
                        "plan_id": "plan_vss_tec_combo",
                        "plan_name": "VSS+TEC协同控制",
                        "overall_score": 78.5,
                        "recommendation": "强烈推荐",
                        "scores": {
                            "effectiveness": 82.0,
                            "coverage": 75.0,
                            "efficiency": 78.0,
                            "reliability": 76.0
                        },
                        "improvement_vs_baseline": {
                            "effectiveness": 32.0,
                            "coverage": 25.0,
                            "efficiency": 28.0,
                            "reliability": 26.0,
                            "overall": 28.5
                        }
                    }
                ],
                "ranking_metadata": {
                    "total_strategies": 4,
                    "baseline_plan_id": "baseline_plan",
                    "baseline_plan_name": "基准方案",
                    "baseline_score": 50.0,
                    "ranking_weights": {
                        "effectiveness": 0.40,
                        "coverage": 0.25,
                        "efficiency": 0.20,
                        "reliability": 0.15
                    },
                    "output_combination": "summary+tripinfo+edgedata"
                },
                "report_file": "frontend/control/ranking_report_20251105_103045.html",
                "timestamp": "2025-11-05T10:30:45.123456"
            }
        }
