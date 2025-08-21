"""
案例相关实体模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, TYPE_CHECKING
from datetime import datetime
from ..enums import CaseStatus

if TYPE_CHECKING:
    from .simulation import SimulationResult


class CaseStatistics(BaseModel):
    """案例统计信息模型"""
    total_vehicles: Optional[int] = Field(None, description="总车辆数")
    simulation_duration: Optional[int] = Field(None, description="仿真时长（秒）")
    detector_count: Optional[int] = Field(None, description="检测器数量")
    gantry_count: Optional[int] = Field(None, description="门架数量")


class CaseFiles(BaseModel):
    """案例文件路径模型"""
    od_file: Optional[str] = Field(None, description="OD数据文件路径")
    routes_file: Optional[str] = Field(None, description="路由文件路径")
    config_file: Optional[str] = Field(None, description="配置文件路径")
    taz_file: Optional[str] = Field(None, description="TAZ文件路径")
    network_file: Optional[str] = Field(None, description="网络文件路径")


class CaseMetadata(BaseModel):
    """案例元数据模型"""
    case_id: str = Field(..., description="案例ID")
    case_name: Optional[str] = Field(None, description="案例名称")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    time_range: Dict[str, str] = Field(..., description="时间范围")
    config: Dict[str, Any] = Field(..., description="配置参数")
    status: CaseStatus = Field(..., description="案例状态")
    description: Optional[str] = Field(None, description="案例描述")
    statistics: Optional[Dict[str, Any]] = Field(None, description="统计信息")
    files: Optional[Dict[str, str]] = Field(None, description="文件路径")
    simulations: Optional[List["SimulationResult"]] = Field([], description="仿真结果列表")
    analysis: Optional[Dict[str, Any]] = Field(None, description="分析结果摘要（accuracy/mechanism/performance 最新产物信息）")


# 延迟导入和模型重建
def rebuild_models():
    """重建模型以解决循环依赖"""
    try:
        from .simulation import SimulationResult
        CaseMetadata.model_rebuild()
    except ImportError:
        pass

# 在模块导入时重建模型
rebuild_models()
