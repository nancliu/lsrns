"""
场景管理相关响应模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ScenarioMetadataInfo(BaseModel):
    """场景元数据信息"""
    event_id: str = Field(..., description="事件ID")
    event_type: str = Field(..., description="事件类型")
    strategy: str = Field(..., description="控制策略")
    location: Dict[str, Any] = Field(..., description="事件位置信息")
    time: Dict[str, Any] = Field(..., description="事件时间信息")
    files: Dict[str, str] = Field(..., description="场景文件信息")


class ScenarioInfo(BaseModel):
    """场景信息"""
    scenario_id: str = Field(..., description="场景ID")
    event_id: str = Field(..., description="事件ID")
    event_type: str = Field(..., description="事件类型 (e.g., '01_accident')")
    strategy: str = Field(..., description="控制策略 (vss|dhs|tec|no_control)")
    location: Optional[Dict[str, Any]] = Field(None, description="事件位置")
    time: Optional[Dict[str, Any]] = Field(None, description="事件时间")

    class Config:
        extra = "allow"  # 允许额外字段


class ScenarioListResponse(BaseModel):
    """场景列表响应模型"""
    scenarios: List[ScenarioInfo] = Field(..., description="场景列表")
    total_count: int = Field(..., description="总数")
    page: int = Field(..., description="当前页")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")


class CaseFromScenarioResponse(BaseModel):
    """从场景创建的案例响应"""
    case_id: str = Field(..., description="新创建的案例ID")
    case_name: str = Field(..., description="案例名称")
    source_scenario_id: str = Field(..., description="源场景ID")
    source_event_id: str = Field(..., description="源事件ID")
    created_at: datetime = Field(..., description="创建时间")
    case_dir: str = Field(..., description="案例目录路径")
    metadata: Dict[str, Any] = Field(..., description="案例元数据")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class BatchCaseCreationResponse(BaseModel):
    """批量案例创建响应"""
    batch_id: str = Field(..., description="批量操作ID")
    total_scenarios: int = Field(..., description="总场景数")
    created_cases: int = Field(..., description="成功创建的案例数")
    failed_count: int = Field(..., description="失败数")
    cases: List[CaseFromScenarioResponse] = Field(..., description="创建的案例列表")
    errors: List[Dict[str, str]] = Field(default_factory=list, description="错误列表")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ScenarioQueryResponse(BaseModel):
    """场景查询响应"""
    scenario: ScenarioInfo = Field(..., description="场景信息")
    config: Dict[str, Any] = Field(..., description="场景配置")
    add_xml_path: str = Field(..., description=".add.xml文件路径")
    metadata_files: Dict[str, str] = Field(..., description="元数据文件路径")


class AnalysisResult(BaseModel):
    """分析结果模型"""
    analysis_id: str = Field(..., description="分析ID")
    case_id: str = Field(..., description="案例ID")
    status: str = Field(default="initiated", description="分析状态 (initiated|running|completed|failed)")
    analysis_type: str = Field(..., description="分析类型 (edgedata|tripinfo|all)")
    started_at: datetime = Field(..., description="分析启动时间")
    result_path: Optional[str] = Field(None, description="分析结果路径")
    message: str = Field(default="", description="状态信息")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
