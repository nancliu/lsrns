"""
方案响应模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class ValidationWarning(BaseModel):
    """验证警告模型"""

    type: str = Field(..., description="警告类型", examples=["timing_coordination", "spatial_conflict"])
    severity: str = Field(..., description="严重程度", examples=["low", "medium", "high"])
    message: str = Field(..., description="警告信息")
    suggestion: Optional[str] = Field(None, description="改进建议")


class PlanValidationResponse(BaseModel):
    """方案验证响应"""

    is_valid: bool = Field(..., description="是否有效（警告模式始终为True）")
    warnings: List[ValidationWarning] = Field(default_factory=list, description="警告列表")
    suggestions: List[str] = Field(default_factory=list, description="优化建议列表")


class StrategyBriefInfo(BaseModel):
    """策略简要信息"""

    strategy_id: str = Field(..., description="策略ID")
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: str = Field(..., description="策略类型", examples=["VSS", "DHS", "TEC"])
    template_id: str = Field(..., description="使用的模板ID")


class PlanResponse(BaseModel):
    """方案响应模型"""

    plan_id: str = Field(..., description="方案ID")
    plan_name: str = Field(..., description="方案名称")
    description: Optional[str] = Field(None, description="描述")
    strategy_ids: List[str] = Field(default_factory=list, description="策略ID列表")
    strategy_count: int = Field(..., description="策略数量")
    tags: List[str] = Field(default_factory=list, description="标签")
    target_scenario: Optional[str] = Field(None, description="目标场景")
    expected_effects: Optional[dict] = Field(None, description="预期效果")
    additional_file_path: Optional[str] = Field(None, description="XML文件路径")
    is_baseline: bool = Field(..., description="是否为基准方案")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    validation: Optional[PlanValidationResponse] = Field(None, description="验证结果")


class PlanDetailResponse(PlanResponse):
    """方案详情响应（包含策略详情）"""

    strategies: List[StrategyBriefInfo] = Field(default_factory=list, description="包含的策略详情")


class PlanListItem(BaseModel):
    """方案列表项"""

    plan_id: str = Field(..., description="方案ID")
    plan_name: str = Field(..., description="方案名称")
    is_baseline: bool = Field(..., description="是否为基准方案")
    strategy_count: int = Field(..., description="策略数量")
    tags: List[str] = Field(default_factory=list, description="标签")
    created_at: datetime = Field(..., description="创建时间")

    model_config = {"extra": "allow"}  # 允许额外字段（如 collection, strategies, severity 等）


class PlanListResponse(BaseModel):
    """方案列表响应"""

    plans: List[PlanListItem] = Field(default_factory=list, description="方案列表")
    total: int = Field(..., description="总数量")


class AffectedPeriod(BaseModel):
    """影响时段"""

    start: int = Field(..., description="开始时间（秒）")
    end: int = Field(..., description="结束时间（秒）")


class StrategyPreviewInfo(BaseModel):
    """策略预览信息"""

    strategy_id: str = Field(..., description="策略ID")
    strategy_name: str = Field(..., description="策略名称")
    strategy_type: str = Field(..., description="策略类型")
    affected_objects: List[str] = Field(default_factory=list, description="影响的对象（edge/lane等）")
    active_periods: List[List[int]] = Field(default_factory=list, description="生效时段列表 [[start, end], ...]")


class PlanPreviewSummary(BaseModel):
    """方案预览摘要"""

    total_strategies: int = Field(..., description="总策略数")
    strategy_types: dict = Field(..., description="按类型统计", examples=[{"VSS": 1, "DHS": 1, "TEC": 1}])
    affected_edges: List[str] = Field(default_factory=list, description="影响的边列表")
    affected_edge_count: int = Field(..., description="影响的边数量")
    time_range: Optional[dict] = Field(None, description="时间范围", examples=[{"earliest": 24900, "latest": 32400}])


class PlanPreviewResponse(BaseModel):
    """方案预览响应"""

    plan_id: str = Field(..., description="方案ID")
    summary: PlanPreviewSummary = Field(..., description="摘要信息")
    strategies: List[StrategyPreviewInfo] = Field(default_factory=list, description="策略详情")
    xml_preview: str = Field(..., description="XML预览（前500行）")
