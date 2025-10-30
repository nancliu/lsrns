"""
批量仿真任务实体模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from ...enums import BatchSimulationStatus


class BatchSimulationTask(BaseModel):
    """单个批量仿真任务模型（方案×种子组合）"""

    task_id: str = Field(
        ...,
        description="任务唯一标识符",
        examples=["task_001"]
    )

    plan_id: str = Field(
        ...,
        description="关联的方案ID",
        examples=["plan_20251025_140530_a1b2c"]
    )

    plan_name: str = Field(
        ...,
        description="方案名称（用于显示）",
        examples=["早高峰综合管控方案A"]
    )

    seed: int = Field(
        ...,
        description="随机种子值",
        examples=[66]
    )

    status: BatchSimulationStatus = Field(
        default=BatchSimulationStatus.PENDING,
        description="任务状态（PENDING/RUNNING/COMPLETED/FAILED）"
    )

    simulation_id: Optional[str] = Field(
        default=None,
        description="生成的仿真ID（完成后填充）",
        examples=["sim_20251025_001"]
    )

    started_at: Optional[datetime] = Field(
        default=None,
        description="任务开始时间"
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        description="任务完成时间"
    )

    error: Optional[str] = Field(
        default=None,
        description="错误信息（失败时填充）"
    )

    progress: int = Field(
        default=0,
        description="仿真进度百分比（0-100）",
        ge=0,
        le=100,
        examples=[85]
    )

    live_status: Optional[Dict[str, Any]] = Field(
        default=None,
        description="实时运行状态（仅当status=running时填充）",
        examples=[{
            "current_step": 7200,
            "total_steps": 14400,
            "progress_percent": 50.0,
            "running_vehicles": 320,
            "ended_vehicles": 150,
            "loaded_vehicles": 470,
            "estimated_remaining_seconds": 300
        }]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_001",
                "plan_id": "baseline_plan",
                "plan_name": "基准方案（无管控）",
                "seed": 66,
                "status": "running",
                "simulation_id": "sim_20251025_143100_001",
                "started_at": "2025-10-25T14:30:05",
                "completed_at": None,
                "error": None,
                "progress": 50,
                "live_status": {
                    "current_step": 7200,
                    "total_steps": 14400,
                    "progress_percent": 50.0,
                    "running_vehicles": 320,
                    "ended_vehicles": 150,
                    "loaded_vehicles": 470
                }
            }
        }


class BatchSimulation(BaseModel):
    """批量仿真批次模型"""

    batch_id: str = Field(
        ...,
        description="批次唯一标识符（格式：batch_YYYYMMDD_HHMMSS）",
        examples=["batch_20251025_143000"]
    )

    case_id: str = Field(
        ...,
        description="关联的案例ID（外键，引用已有Case）",
        examples=["case_20251015_baseline"]
    )

    plan_ids: List[str] = Field(
        ...,
        description="待测试的方案ID列表（外键）",
        min_length=1,
        examples=[["baseline_plan", "plan_20251025_140530_a1b2c", "plan_20251025_141200_d3e4f"]]
    )

    num_seeds: int = Field(
        default=3,
        description="每个方案的随机种子数量",
        ge=1,
        examples=[3]
    )

    base_seed: int = Field(
        default=66,
        description="起始随机种子值",
        ge=0,
        examples=[66]
    )

    tasks: List[BatchSimulationTask] = Field(
        default_factory=list,
        description="所有仿真任务列表（plans × seeds）"
    )

    status: BatchSimulationStatus = Field(
        default=BatchSimulationStatus.PENDING,
        description="批次状态（PENDING/RUNNING/COMPLETED/FAILED）"
    )

    progress: float = Field(
        default=0.0,
        description="批次进度（0.0-1.0）",
        ge=0.0,
        le=1.0,
        examples=[0.33]
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间戳"
    )

    started_at: Optional[datetime] = Field(
        default=None,
        description="批次开始时间"
    )

    completed_at: Optional[datetime] = Field(
        default=None,
        description="批次完成时间"
    )

    @property
    def total_tasks(self) -> int:
        """总任务数"""
        return len(self.tasks)

    @property
    def completed_tasks(self) -> int:
        """已完成任务数"""
        return sum(1 for task in self.tasks if task.status == BatchSimulationStatus.COMPLETED)

    @property
    def failed_tasks(self) -> int:
        """失败任务数"""
        return sum(1 for task in self.tasks if task.status == BatchSimulationStatus.FAILED)

    @property
    def running_tasks(self) -> int:
        """运行中任务数"""
        return sum(1 for task in self.tasks if task.status == BatchSimulationStatus.RUNNING)

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251025_143000",
                "case_id": "case_20251015_baseline",
                "plan_ids": ["baseline_plan", "plan_20251025_140530_a1b2c"],
                "num_seeds": 3,
                "base_seed": 66,
                "tasks": [
                    {
                        "task_id": "task_001",
                        "plan_id": "baseline_plan",
                        "plan_name": "基准方案（无管控）",
                        "seed": 66,
                        "status": "completed",
                        "simulation_id": "sim_001",
                        "started_at": "2025-10-25T14:30:05",
                        "completed_at": "2025-10-25T14:35:30",
                        "error": None,
                        "progress": 100
                    }
                ],
                "status": "running",
                "progress": 0.33,
                "created_at": "2025-10-25T14:30:00",
                "started_at": "2025-10-25T14:30:05",
                "completed_at": None
            }
        }
