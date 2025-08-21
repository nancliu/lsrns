"""
仿真相关实体模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from ..enums import SimulationType


class SimulationResult(BaseModel):
    """仿真结果模型"""
    simulation_id: str = Field(..., description="仿真结果ID")
    case_id: str = Field(..., description="所属案例ID")
    simulation_name: Optional[str] = Field(None, description="仿真名称")
    simulation_type: SimulationType = Field(..., description="仿真类型")
    simulation_params: Optional[Dict[str, Any]] = Field({}, description="仿真参数")
    status: str = Field(..., description="仿真状态")
    created_at: datetime = Field(..., description="创建时间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    duration: Optional[int] = Field(None, description="仿真耗时（秒）")
    result_folder: str = Field(..., description="结果文件夹路径")
    config_file: Optional[str] = Field(None, description="配置文件路径")
    description: Optional[str] = Field(None, description="仿真描述")
    statistics: Optional[Dict[str, Any]] = Field(None, description="仿真统计信息")
