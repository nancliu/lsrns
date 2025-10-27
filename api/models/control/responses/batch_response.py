"""
批量优化仿真响应模型
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..entities.batch_simulation import BatchSimulation, BatchSimulationTask
from ...enums import BatchSimulationStatus


class BatchCreatedResponse(BaseModel):
    """批次创建成功响应"""

    batch_id: str = Field(
        ...,
        description="批次唯一标识符",
        examples=["batch_20251025_143000"]
    )

    case_id: str = Field(
        ...,
        description="关联的案例ID",
        examples=["case_20251025_001"]
    )

    plan_ids: List[str] = Field(
        ...,
        description="方案ID列表",
        examples=[["baseline_plan", "plan_20251025_140530_a1b2c"]]
    )

    total_tasks: int = Field(
        ...,
        description="总任务数（plans × seeds）",
        examples=[9]
    )

    status: BatchSimulationStatus = Field(
        ...,
        description="批次状态",
        examples=[BatchSimulationStatus.PENDING]
    )

    created_at: datetime = Field(
        ...,
        description="创建时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251025_143000",
                "case_id": "case_20251025_001",
                "plan_ids": ["baseline_plan", "plan_20251025_140530_a1b2c", "plan_20251025_141200_d3e4f"],
                "total_tasks": 9,
                "status": "pending",
                "created_at": "2025-10-25T14:30:00"
            }
        }


class BatchProgressResponse(BaseModel):
    """批次进度查询响应"""

    batch_id: str = Field(
        ...,
        description="批次唯一标识符",
        examples=["batch_20251025_143000"]
    )

    status: BatchSimulationStatus = Field(
        ...,
        description="批次状态",
        examples=[BatchSimulationStatus.RUNNING]
    )

    progress: float = Field(
        ...,
        description="批次进度（0.0-1.0）",
        examples=[0.33]
    )

    total_tasks: int = Field(
        ...,
        description="总任务数",
        examples=[9]
    )

    completed_tasks: int = Field(
        ...,
        description="已完成任务数",
        examples=[3]
    )

    failed_tasks: int = Field(
        ...,
        description="失败任务数",
        examples=[0]
    )

    running_tasks: int = Field(
        ...,
        description="运行中任务数",
        examples=[2]
    )

    tasks: List[BatchSimulationTask] = Field(
        ...,
        description="所有任务详情列表"
    )

    estimated_completion: Optional[datetime] = Field(
        default=None,
        description="预计完成时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251025_143000",
                "status": "running",
                "progress": 0.33,
                "total_tasks": 9,
                "completed_tasks": 3,
                "failed_tasks": 0,
                "running_tasks": 2,
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
                        "error": None
                    }
                ],
                "estimated_completion": "2025-10-25T15:30:00"
            }
        }


class SimulationMetrics(BaseModel):
    """单次仿真的性能指标"""

    seed: int = Field(..., description="随机种子值")
    simulation_id: str = Field(..., description="仿真ID")

    # 基础指标（从summary.xml或tripinfo.xml提取）
    avg_travel_time: Optional[float] = Field(None, description="平均行程时间（秒）")
    total_delay: Optional[float] = Field(None, description="总延误时间（秒）")
    avg_speed: Optional[float] = Field(None, description="平均速度（km/h）")
    total_vehicles: Optional[int] = Field(None, description="总车辆数")

    class Config:
        json_schema_extra = {
            "example": {
                "seed": 66,
                "simulation_id": "sim_001",
                "avg_travel_time": 1450.2,
                "total_delay": 58000,
                "avg_speed": 22.5,
                "total_vehicles": 4200
            }
        }


class AggregatedMetrics(BaseModel):
    """聚合统计指标"""

    mean: float = Field(..., description="平均值")
    std: float = Field(..., description="标准差")
    min: float = Field(..., description="最小值")
    max: float = Field(..., description="最大值")

    class Config:
        json_schema_extra = {
            "example": {
                "mean": 1448.5,
                "std": 5.2,
                "min": 1442.0,
                "max": 1455.0
            }
        }


class PlanResultSummary(BaseModel):
    """单个方案的结果汇总"""

    plan_id: str = Field(..., description="方案ID")
    plan_name: str = Field(..., description="方案名称")

    simulations: List[SimulationMetrics] = Field(
        ...,
        description="所有随机种子的仿真结果"
    )

    aggregated_metrics: Dict[str, AggregatedMetrics] = Field(
        ...,
        description="聚合统计指标（按指标名称分组）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "plan_id": "baseline_plan",
                "plan_name": "基准方案（无管控）",
                "simulations": [
                    {
                        "seed": 66,
                        "simulation_id": "sim_001",
                        "avg_travel_time": 1450.2,
                        "total_delay": 58000,
                        "avg_speed": 22.5,
                        "total_vehicles": 4200
                    },
                    {
                        "seed": 67,
                        "simulation_id": "sim_002",
                        "avg_travel_time": 1448.0,
                        "total_delay": 57800,
                        "avg_speed": 22.6,
                        "total_vehicles": 4210
                    }
                ],
                "aggregated_metrics": {
                    "avg_travel_time": {
                        "mean": 1448.5,
                        "std": 5.2,
                        "min": 1442.0,
                        "max": 1455.0
                    },
                    "avg_speed": {
                        "mean": 22.55,
                        "std": 0.15,
                        "min": 22.4,
                        "max": 22.7
                    }
                }
            }
        }


class BatchResultsResponse(BaseModel):
    """批次结果汇总响应"""

    batch_id: str = Field(..., description="批次ID")

    status: BatchSimulationStatus = Field(..., description="批次状态")

    plan_results: List[PlanResultSummary] = Field(
        ...,
        description="所有方案的结果汇总"
    )

    created_at: datetime = Field(..., description="批次创建时间")
    completed_at: Optional[datetime] = Field(None, description="批次完成时间")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251025_143000",
                "status": "completed",
                "plan_results": [
                    {
                        "plan_id": "baseline_plan",
                        "plan_name": "基准方案（无管控）",
                        "simulations": [
                            {
                                "seed": 66,
                                "simulation_id": "sim_001",
                                "avg_travel_time": 1450.2,
                                "total_delay": 58000,
                                "avg_speed": 22.5,
                                "total_vehicles": 4200
                            }
                        ],
                        "aggregated_metrics": {
                            "avg_travel_time": {
                                "mean": 1448.5,
                                "std": 5.2,
                                "min": 1442.0,
                                "max": 1455.0
                            }
                        }
                    }
                ],
                "created_at": "2025-10-25T14:30:00",
                "completed_at": "2025-10-25T15:45:30"
            }
        }
