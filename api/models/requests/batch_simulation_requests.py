"""
批量仿真请求模型 (Task 2.6 - Week 2 Phase 2)

支持事件场景批量仿真工作流
"""

from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any, Optional


class BatchSimulationStartRequest(BaseModel):
    """
    批量启动仿真请求

    用于事件场景批量仿真 (Phase 2)
    """

    simulation_ids: List[str] = Field(
        ...,
        description="仿真ID列表 (已通过 prepare_simulation 创建)",
        min_length=1,
        max_length=100,
        example=["sim_001", "sim_002", "sim_003"]
    )

    case_id: str = Field(
        ...,
        description="案例ID (所有仿真必须属于同一案例)",
        example="case_20251112_001"
    )

    parallel_workers: Optional[int] = Field(
        default=None,
        ge=2,
        le=64,
        description="并发工作线程数 (2-64)。如不指定，从 config/system_config.json 读取默认值"
    )

    auto_run_analysis: bool = Field(
        default=True,
        description="完成后自动运行分析"
    )

    analysis_types: List[str] = Field(
        default=["summary", "edgedata"],
        description="自动分析类型 (summary, edgedata, tripinfo, vehroute)"
    )

    @model_validator(mode='after')
    def set_default_parallel_workers(self):
        """如果 parallel_workers 为 None，从配置文件读取默认值"""
        if self.parallel_workers is None:
            from shared.utilities.config_utils import get_parallel_workers
            self.parallel_workers = get_parallel_workers()
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "simulation_ids": ["sim_112001", "sim_112002", "sim_112003"],
                "case_id": "case_20251112_001",
                "parallel_workers": 4,
                "auto_run_analysis": True,
                "analysis_types": ["summary", "edgedata"]
            }
        }


class BatchSimulationCancelRequest(BaseModel):
    """
    批量取消仿真请求
    """

    batch_id: str = Field(
        ...,
        description="批次ID",
        example="batch_20251112_100000"
    )

    graceful: bool = Field(
        default=True,
        description="优雅停止 (允许当前任务完成)"
    )
