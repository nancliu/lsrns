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
    event_type: str = Field(..., description="事件类型 (e.g., '01_交通事故')")
    strategy: str = Field(..., description="控制策略 (vss|dhs|tec)")
    scenario_id: str = Field(..., description="事件场景ID (e.g., 'scenario_12547_vss')")
    network_file: str = Field(..., description="网络文件路径")
    od_file: str = Field(..., description="OD/路由文件路径")
    taz_file: Optional[str] = Field(None, description="TAZ文件路径（可选）")
    description: Optional[str] = Field(None, description="案例描述")
