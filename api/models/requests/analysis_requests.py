"""
分析相关请求模型
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from ..enums import AnalysisType


class AccuracyAnalysisRequest(BaseModel):
    """精度分析请求模型"""
    case_id: str = Field(..., description="案例ID")
    simulation_ids: List[str] = Field(..., description="仿真结果ID列表")
    analysis_type: Optional[AnalysisType] = Field(AnalysisType.ACCURACY, description="分析类型")


class MechanismAnalysisRequest(BaseModel):
    """机理分析请求模型"""
    case_id: str = Field(..., description="案例ID")
    simulation_ids: List[str] = Field(..., description="仿真结果ID列表")
    analysis_type: Optional[AnalysisType] = Field(AnalysisType.MECHANISM, description="分析类型")


class PerformanceAnalysisRequest(BaseModel):
    """性能分析请求模型"""
    case_id: str = Field(..., description="案例ID")
    simulation_ids: List[str] = Field(..., description="仿真结果ID列表")
    analysis_type: Optional[AnalysisType] = Field(AnalysisType.PERFORMANCE, description="分析类型")
