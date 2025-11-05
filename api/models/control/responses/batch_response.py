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

    # 仿真配置信息
    num_seeds: int = Field(default=3, description="每个方案的随机种子数")
    base_seed: int = Field(default=66, description="起始随机种子值")
    simulation_duration: Optional[Dict[str, Any]] = Field(None, description="仿真时长配置 (hours, minutes, total_minutes)")
    output_config: Optional[Dict[str, Any]] = Field(None, description="详细输出配置 (output_tripinfo, output_edgedata等)")

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251025_143000",
                "case_id": "case_20251025_001",
                "plan_ids": ["baseline_plan", "plan_20251025_140530_a1b2c", "plan_20251025_141200_d3e4f"],
                "total_tasks": 9,
                "num_seeds": 3,
                "base_seed": 66,
                "simulation_duration": {
                    "hours": 4,
                    "minutes": 0,
                    "total_minutes": 240
                },
                "output_config": {
                    "output_tripinfo": True,
                    "output_edgedata": True,
                    "output_netstate": True,
                    "output_vehroute": False,
                    "output_fcd": False,
                    "output_emission": True
                },
                "status": "pending",
                "created_at": "2025-10-25T14:30:00"
            }
        }


class LiveTimeSeries(BaseModel):
    """实时时间序列数据"""

    time_points: List[int] = Field(
        ...,
        description="时间点列表（秒数）",
        examples=[[0, 10, 20, 30]]
    )

    total_running: List[int] = Field(
        ...,
        description="每个时间点的在网车辆总数",
        examples=[[100, 150, 200, 180]]
    )

    task_count: int = Field(
        ...,
        description="贡献数据的运行中任务数",
        examples=[3]
    )

    last_update: datetime = Field(
        ...,
        description="最后更新时间"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "time_points": [0, 10, 20, 30],
                "total_running": [100, 150, 200, 180],
                "task_count": 3,
                "last_update": "2025-10-29T10:25:00"
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

    estimated_remaining_seconds: Optional[int] = Field(
        default=None,
        description="预计剩余秒数"
    )

    live_time_series: Optional[LiveTimeSeries] = Field(
        default=None,
        description="实时时间序列数据（用于动态曲线）"
    )

    # 仿真配置信息
    num_seeds: int = Field(default=3, description="每个方案的随机种子数")
    base_seed: int = Field(default=66, description="起始随机种子值")
    simulation_duration: Optional[Dict[str, Any]] = Field(None, description="仿真时长配置 (hours, minutes, total_minutes)")
    output_config: Optional[Dict[str, Any]] = Field(None, description="详细输出配置 (output_tripinfo, output_edgedata等)")

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
                "num_seeds": 3,
                "base_seed": 66,
                "simulation_duration": {
                    "hours": 4,
                    "minutes": 0,
                    "total_minutes": 240
                },
                "output_config": {
                    "output_tripinfo": True,
                    "output_edgedata": True,
                    "output_netstate": False,
                    "output_vehroute": False,
                    "output_fcd": False,
                    "output_emission": True
                },
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
                "estimated_completion": "2025-10-25T15:30:00",
                "estimated_remaining_seconds": 3600,
                "live_time_series": {
                    "time_points": [0, 10, 20, 30],
                    "total_running": [100, 150, 200, 180],
                    "task_count": 2,
                    "last_update": "2025-10-25T15:00:00"
                }
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

    case_id: str = Field(..., description="关联的案例ID")

    status: BatchSimulationStatus = Field(..., description="批次状态")

    plan_results: List[PlanResultSummary] = Field(
        ...,
        description="所有方案的结果汇总"
    )

    created_at: datetime = Field(..., description="批次创建时间")
    completed_at: Optional[datetime] = Field(None, description="批次完成时间")

    # 仿真配置信息
    num_seeds: int = Field(default=3, description="每个方案的随机种子数")
    base_seed: int = Field(default=66, description="起始随机种子值")
    output_level: Optional[str] = Field(None, description="输出级别 (minimal/standard/full)")
    simulation_duration: Optional[Dict[str, Any]] = Field(None, description="仿真时长配置 (hours, minutes, total_minutes)")
    duration_seconds: Optional[float] = Field(None, description="批次执行总耗时（秒）")
    output_config: Optional[Dict[str, Any]] = Field(None, description="详细输出配置 (output_tripinfo, output_edgedata, output_netstate等)")

    # 案例信息
    case_info: Optional[Dict[str, Any]] = Field(None, description="案例信息 (case_name, case_id, time_range, description)")

    metric_config: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="指标配置元数据（含中文标签、单位、方向等）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251025_143000",
                "case_id": "case_20251025_001",
                "status": "completed",
                "num_seeds": 3,
                "base_seed": 66,
                "output_level": "standard",
                "simulation_duration": {
                    "hours": 4,
                    "minutes": 0,
                    "total_minutes": 240
                },
                "duration_seconds": 3600,
                "output_config": {
                    "output_tripinfo": True,
                    "output_vehroute": True,
                    "output_netstate": True,
                    "output_fcd": True,
                    "output_emission": True,
                    "output_edgedata": True
                },
                "case_info": {
                    "case_name": "G4202绕城高速工作日仿真",
                    "case_id": "case_20251025_001",
                    "time_range": {
                        "start": "07:00:00",
                        "end": "11:00:00"
                    },
                    "description": "测试用例"
                },
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
                                "total_vehicles": 4200,
                                "progress": 100
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
                "metric_config": {
                    "step": {
                        "label": "仿真步数",
                        "unit": "秒",
                        "direction": "verification",
                        "is_verification_metric": True,
                        "expected_value": 3600,
                        "description": "整个仿真运行的总时长 - 用于验证仿真是否完整执行到预定时长"
                    },
                    "ended": {
                        "label": "已完成车数",
                        "unit": "辆",
                        "direction": "higher",
                        "description": "仿真结束时已完成行程的车数"
                    },
                    "waiting": {
                        "label": "等待车数",
                        "unit": "辆",
                        "direction": "lower",
                        "description": "因信号灯、拥堵等原因停止等待的车数"
                    },
                    "running": {
                        "label": "当前运行车数",
                        "unit": "辆",
                        "direction": "lower",
                        "description": "仿真结束时仍在网络中的车数"
                    },
                    "avgSpeed": {
                        "label": "平均速度",
                        "unit": "m/s",
                        "direction": "higher",
                        "description": "所有已完成车的平均行驶速度（核心性能指标）"
                    },
                    "teleports": {
                        "label": "传送次数",
                        "unit": "次",
                        "direction": "lower",
                        "description": "SUMO进行的传送操作次数（拥堵严重程度指标）"
                    },
                    "inserted": {
                        "label": "已插入车数",
                        "unit": "辆",
                        "direction": "higher",
                        "description": "成功插入道路网络的车数"
                    },
                    "collisions": {
                        "label": "碰撞次数",
                        "unit": "次",
                        "direction": "lower",
                        "description": "仿真中发生的车辆碰撞事件数"
                    },
                    "loaded": {
                        "label": "已加载车数",
                        "unit": "辆",
                        "direction": "neutral",
                        "description": "已加载到仿真中的车数"
                    },
                    "total_delay": {
                        "label": "总延误时间",
                        "unit": "秒",
                        "direction": "lower",
                        "description": "所有车辆累计延误时间（来自tripinfo.xml）"
                    },
                    "avg_travel_time": {
                        "label": "平均行程时间",
                        "unit": "秒",
                        "direction": "lower",
                        "description": "车辆平均行程时间（来自tripinfo.xml）"
                    }
                },
                "created_at": "2025-10-25T14:30:00",
                "completed_at": "2025-10-25T15:45:30"
            }
        }
