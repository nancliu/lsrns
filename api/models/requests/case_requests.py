"""
案例管理相关请求模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class CreateCaseRequest(BaseModel):
    """创建案例请求模型"""
    case_name: str = Field(..., description="案例名称")
    description: Optional[str] = Field(None, description="案例描述")


class CaseCreationRequest(BaseModel):
    """案例创建请求模型"""
    time_range: Dict[str, str] = Field(..., description="时间范围")
    config: Dict[str, Any] = Field(..., description="配置参数")
    case_name: Optional[str] = Field(None, description="案例名称")
    description: Optional[str] = Field(None, description="案例描述")


class CaseCloneRequest(BaseModel):
    """案例克隆请求模型"""
    new_case_name: Optional[str] = Field(None, description="新案例名称")
    new_description: Optional[str] = Field(None, description="新案例描述")


class EventScenarioQuickCreateRequest(BaseModel):
    """从事件场景快速创建案例请求模型 (Phase 5.3.3)"""
    case_name: str = Field(..., description="案例名称")
    case_id: Optional[str] = Field(None, description="案例ID（如不指定则自动生成）")
    event_type: str = Field(..., description="事件类型 (e.g., '01_accident')")
    strategy: str = Field(..., description="控制策略 (vss|dhs|tec|no_control)")
    scenario_id: str = Field(..., description="事件场景ID (e.g., 'scenario_12547_vss')")
    event_id: str = Field(..., description="事件ID (e.g., '12547')")
    network_file: str = Field(..., description="网络文件路径")
    od_file: str = Field(..., description="OD/路由文件路径")
    taz_file: Optional[str] = Field(None, description="TAZ文件路径（可选）")
    description: Optional[str] = Field(None, description="案例描述")


class ScenarioListQueryRequest(BaseModel):
    """场景列表查询请求模型"""
    event_type: Optional[str] = Field(None, description="按事件类型筛选")
    strategy: Optional[str] = Field(None, description="按控制策略筛选")
    event_id: Optional[str] = Field(None, description="按事件ID查询")
    page: int = Field(1, description="页码", ge=1)
    page_size: int = Field(20, description="每页数量", ge=1, le=100)


class ScenarioAnalysisRequest(BaseModel):
    """场景分析请求模型 (Phase 5.3.3)"""
    case_id: str = Field(..., description="案例ID")
    scenario_id: str = Field(..., description="场景ID")
    event_id: str = Field(..., description="事件ID")
    compare_no_control: bool = Field(default=False, description="是否与无控制策略比较")
    analysis_focus: Dict[str, bool] = Field(
        default_factory=lambda: {"edgedata": True, "tripinfo": False},
        description="分析聚焦：edgedata为主，tripinfo可选"
    )

    class Config:
        example = {
            "case_id": "case_20251111_001",
            "scenario_id": "scenario_12547_vss",
            "event_id": "12547",
            "compare_no_control": True,
            "analysis_focus": {
                "edgedata": True,
                "tripinfo": False
            }
        }


class BatchScenarioSimulationRequest(BaseModel):
    """批量场景仿真请求模型 (Phase 5.3.3扩展)"""
    scenario_ids: list[str] = Field(..., description="场景ID列表")
    case_name_prefix: str = Field("scenario_batch", description="批量创建的案例名称前缀")
    network_file: str = Field(..., description="网络文件路径")
    od_file: str = Field(..., description="OD/路由文件路径")
    taz_file: Optional[str] = Field(None, description="TAZ文件路径（可选）")
    parallel_workers: int = Field(4, description="并发仿真数", ge=2, le=8)
    description: Optional[str] = Field(None, description="批量案例描述")
