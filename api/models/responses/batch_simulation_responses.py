"""
批量仿真响应模型 (Task 2.6 - Week 2 Phase 2)

支持实时进度监控和状态查询
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class SimulationProgressInfo(BaseModel):
    """
    单个仿真进度信息
    """

    simulation_id: str = Field(..., description="仿真ID")
    status: str = Field(..., description="状态 (queued|running|completed|failed)")
    progress_percent: int = Field(default=0, ge=0, le=100, description="进度百分比")
    started_at: Optional[str] = Field(None, description="开始时间 (ISO格式)")
    completed_at: Optional[str] = Field(None, description="完成时间 (ISO格式)")
    elapsed_seconds: Optional[float] = Field(None, description="已用时间 (秒)")
    error: Optional[str] = Field(None, description="错误信息 (如果失败)")

    class Config:
        json_schema_extra = {
            "example": {
                "simulation_id": "sim_112001",
                "status": "running",
                "progress_percent": 45,
                "started_at": "2025-11-12T10:30:00",
                "completed_at": None,
                "elapsed_seconds": 120.5,
                "error": None
            }
        }


class BatchExecutionStatusResponse(BaseModel):
    """
    批量执行状态响应

    提供实时进度监控 (每5-10秒轮询)
    """

    batch_id: str = Field(..., description="批次ID")
    case_id: str = Field(..., description="案例ID")

    # 状态统计
    total_simulations: int = Field(..., description="总仿真数")
    completed: int = Field(..., description="已完成")
    failed: int = Field(..., description="失败")
    in_progress: int = Field(..., description="进行中")
    queued: int = Field(..., description="等待中")

    # 批次状态
    batch_status: str = Field(
        ...,
        description="批次状态 (created|running|completed|failed|cancelled)"
    )

    # 时间信息
    created_at: str = Field(..., description="创建时间 (ISO)")
    started_at: Optional[str] = Field(None, description="开始时间 (ISO)")
    estimated_completion: Optional[str] = Field(None, description="预计完成时间 (ISO)")
    elapsed_seconds: float = Field(default=0, description="已用时间 (秒)")

    # 详细信息
    simulations: List[SimulationProgressInfo] = Field(
        default=[],
        description="所有仿真的详细进度"
    )

    # 当前任务
    current_tasks: List[str] = Field(
        default=[],
        description="当前正在执行的仿真ID列表"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251112_100000",
                "case_id": "case_20251112_001",
                "total_simulations": 10,
                "completed": 4,
                "failed": 1,
                "in_progress": 2,
                "queued": 3,
                "batch_status": "running",
                "created_at": "2025-11-12T10:00:00",
                "started_at": "2025-11-12T10:05:00",
                "estimated_completion": "2025-11-12T12:30:00",
                "elapsed_seconds": 1500.0,
                "simulations": [],
                "current_tasks": ["sim_112005", "sim_112006"]
            }
        }


class BatchSimulationStartResponse(BaseModel):
    """
    批量仿真启动响应
    """

    batch_id: str = Field(..., description="批次ID (用于后续查询)")
    case_id: str = Field(..., description="案例ID")
    total_simulations: int = Field(..., description="总仿真数")
    parallel_workers: int = Field(..., description="并发数")
    status: str = Field(..., description="初始状态 (created|queued)")
    created_at: str = Field(..., description="创建时间 (ISO)")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251112_100000",
                "case_id": "case_20251112_001",
                "total_simulations": 10,
                "parallel_workers": 4,
                "status": "queued",
                "created_at": "2025-11-12T10:00:00"
            }
        }
