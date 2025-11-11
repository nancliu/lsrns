"""
仿真相关请求模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from ..enums import SimulationType


class SimulationRequest(BaseModel):
    """仿真请求模型"""
    case_id: str = Field(..., description="案例ID")
    gui: Optional[bool] = Field(False, description="是否启用GUI")
    simulation_type: Optional[SimulationType] = Field(SimulationType.MICROSCOPIC, description="仿真类型")
    simulation_name: Optional[str] = Field(None, description="仿真名称")
    simulation_description: Optional[str] = Field(None, description="仿真描述")
    simulation_params: Optional[Dict[str, Any]] = Field({}, description="仿真参数配置")
    expected_duration: Optional[int] = Field(None, description="预期仿真时长（秒），用于进度估算；为空则根据metadata.time_range计算")

    # 批量仿真上下文（用于生成唯一ID和目录结构）
    batch_context: Optional[Dict[str, str]] = Field(None, description="批量仿真上下文，包含batch_id, plan_id, seed等信息")


class EventScenarioSimulationRequest(BaseModel):
    """应用事件场景的仿真请求模型 (Phase 5.3.5)"""
    case_id: str = Field(..., description="案例ID")
    event_type: str = Field(..., description="事件类型 (e.g., '01_交通事故')")
    strategy: str = Field(..., description="控制策略 (vss|dhs|tec)")
    scenario_id: str = Field(..., description="事件场景ID (e.g., 'scenario_12547_vss')")
    gui: Optional[bool] = Field(False, description="是否启用GUI")
    simulation_type: Optional[SimulationType] = Field(SimulationType.MICROSCOPIC, description="仿真类型")
    simulation_name: Optional[str] = Field(None, description="仿真名称")
    simulation_description: Optional[str] = Field(None, description="仿真描述")
    simulation_params: Optional[Dict[str, Any]] = Field({}, description="仿真参数配置")
    expected_duration: Optional[int] = Field(None, description="预期仿真时长（秒）")
    batch_context: Optional[Dict[str, str]] = Field(None, description="批量仿真上下文")
