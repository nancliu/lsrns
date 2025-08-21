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
