"""
Analysis Results Response Models (Task 3.4 - Week 3 Phase 2)

支持事件场景分析结果展示和对比
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class EdgeDataMetrics(BaseModel):
    """
    EdgeData 指标模型

    包含道路段的流量、速度、密度等统计数据
    """

    edge_id: str = Field(..., description="道路段ID")
    edge_name: Optional[str] = Field(None, description="道路段名称")

    # 流量指标
    total_vehicles: int = Field(default=0, description="总车辆数")
    avg_vehicles_per_hour: float = Field(default=0.0, description="平均每小时车辆数")
    max_vehicles_per_hour: int = Field(default=0, description="最大每小时车辆数")

    # 速度指标
    avg_speed: float = Field(default=0.0, description="平均速度 (km/h)")
    min_speed: float = Field(default=0.0, description="最小速度 (km/h)")
    max_speed: float = Field(default=0.0, description="最大速度 (km/h)")
    speed_std: float = Field(default=0.0, description="速度标准差")

    # 密度指标
    avg_density: float = Field(default=0.0, description="平均密度 (veh/km)")
    max_density: float = Field(default=0.0, description="最大密度 (veh/km)")

    # 占用率
    avg_occupancy: float = Field(default=0.0, ge=0, le=100, description="平均占用率 (%)")
    max_occupancy: float = Field(default=0.0, ge=0, le=100, description="最大占用率 (%)")

    # 拥堵指标
    congestion_level: str = Field(
        default="smooth",
        description="拥堵等级 (smooth|moderate|congested|severe)"
    )
    congestion_duration_minutes: float = Field(default=0.0, description="拥堵持续时间 (分钟)")

    class Config:
        json_schema_extra = {
            "example": {
                "edge_id": "edge_001",
                "edge_name": "Main Street",
                "total_vehicles": 1500,
                "avg_vehicles_per_hour": 375,
                "max_vehicles_per_hour": 520,
                "avg_speed": 45.2,
                "min_speed": 15.3,
                "max_speed": 65.8,
                "speed_std": 12.5,
                "avg_density": 25.3,
                "max_density": 45.7,
                "avg_occupancy": 35.2,
                "max_occupancy": 78.5,
                "congestion_level": "moderate",
                "congestion_duration_minutes": 45.0
            }
        }


class TripInfoMetrics(BaseModel):
    """
    TripInfo 指标模型

    包含车辆行程的时间、距离、延误等统计数据
    """

    # 行程统计
    total_trips: int = Field(default=0, description="总行程数")
    completed_trips: int = Field(default=0, description="完成的行程数")
    incomplete_trips: int = Field(default=0, description="未完成的行程数")
    completion_rate: float = Field(default=0.0, ge=0, le=100, description="完成率 (%)")

    # 时间指标
    avg_trip_duration: float = Field(default=0.0, description="平均行程时间 (秒)")
    min_trip_duration: float = Field(default=0.0, description="最短行程时间 (秒)")
    max_trip_duration: float = Field(default=0.0, description="最长行程时间 (秒)")
    total_trip_duration: float = Field(default=0.0, description="总行程时间 (秒)")

    # 距离指标
    avg_trip_length: float = Field(default=0.0, description="平均行程距离 (km)")
    total_trip_length: float = Field(default=0.0, description="总行程距离 (km)")

    # 延误指标
    avg_delay: float = Field(default=0.0, description="平均延误 (秒)")
    total_delay: float = Field(default=0.0, description="总延误 (秒)")
    avg_waiting_time: float = Field(default=0.0, description="平均等待时间 (秒)")

    # 速度指标
    avg_trip_speed: float = Field(default=0.0, description="平均行程速度 (km/h)")

    class Config:
        json_schema_extra = {
            "example": {
                "total_trips": 2500,
                "completed_trips": 2450,
                "incomplete_trips": 50,
                "completion_rate": 98.0,
                "avg_trip_duration": 1250.5,
                "min_trip_duration": 180.2,
                "max_trip_duration": 3600.8,
                "total_trip_duration": 3126250.0,
                "avg_trip_length": 12.5,
                "total_trip_length": 31250.0,
                "avg_delay": 125.3,
                "total_delay": 313250.0,
                "avg_waiting_time": 45.2,
                "avg_trip_speed": 36.0
            }
        }


class ComparisonMetrics(BaseModel):
    """
    对比指标模型

    展示基线与对比场景之间的差异
    """

    metric_name: str = Field(..., description="指标名称")
    metric_type: str = Field(..., description="指标类型 (edgedata|tripinfo|summary)")

    # 基线值
    baseline_value: float = Field(..., description="基线场景值")
    baseline_scenario_id: str = Field(..., description="基线场景ID")

    # 对比值
    comparison_value: float = Field(..., description="对比场景值")
    comparison_scenario_id: str = Field(..., description="对比场景ID")

    # 差异计算
    absolute_difference: float = Field(..., description="绝对差异")
    relative_difference_percent: float = Field(..., description="相对差异 (%)")

    # 改善判断
    improvement_status: str = Field(
        ...,
        description="改善状态 (improved|deteriorated|unchanged)"
    )
    improvement_color: str = Field(
        ...,
        description="展示颜色 (green|red|gray)"
    )

    # 统计显著性 (可选)
    is_significant: Optional[bool] = Field(None, description="是否统计显著")
    confidence_level: Optional[float] = Field(None, description="置信水平")

    class Config:
        json_schema_extra = {
            "example": {
                "metric_name": "avg_speed",
                "metric_type": "edgedata",
                "baseline_value": 45.2,
                "baseline_scenario_id": "scenario_001_none",
                "comparison_value": 52.8,
                "comparison_scenario_id": "scenario_001_vss",
                "absolute_difference": 7.6,
                "relative_difference_percent": 16.8,
                "improvement_status": "improved",
                "improvement_color": "green",
                "is_significant": True,
                "confidence_level": 0.95
            }
        }


class AnalysisResultsSummary(BaseModel):
    """
    分析结果总览

    包含所有分析类型的汇总指标
    """

    batch_id: str = Field(..., description="分析批次ID")
    case_id: str = Field(..., description="案例ID")

    # 仿真信息
    total_simulations: int = Field(..., description="总仿真数")
    analyzed_simulations: int = Field(..., description="已分析仿真数")
    simulation_ids: List[str] = Field(default=[], description="仿真ID列表")

    # 场景信息
    baseline_scenario_id: Optional[str] = Field(None, description="基线场景ID")
    comparison_scenario_ids: List[str] = Field(default=[], description="对比场景ID列表")

    # 时间信息
    analysis_started_at: str = Field(..., description="分析开始时间 (ISO)")
    analysis_completed_at: str = Field(..., description="分析完成时间 (ISO)")
    analysis_duration_seconds: float = Field(..., description="分析耗时 (秒)")

    # 分析类型状态
    analysis_types_completed: List[str] = Field(
        default=[],
        description="已完成的分析类型 (edgedata, tripinfo, summary)"
    )

    # 关键指标摘要
    key_metrics: Dict[str, Any] = Field(
        default={},
        description="关键指标摘要"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251112_100000",
                "case_id": "case_20251112_001",
                "total_simulations": 3,
                "analyzed_simulations": 3,
                "simulation_ids": ["sim_001", "sim_002", "sim_003"],
                "baseline_scenario_id": "scenario_001_none",
                "comparison_scenario_ids": ["scenario_001_vss", "scenario_001_tec"],
                "analysis_started_at": "2025-11-12T10:00:00",
                "analysis_completed_at": "2025-11-12T10:15:30",
                "analysis_duration_seconds": 930.0,
                "analysis_types_completed": ["edgedata", "tripinfo", "summary"],
                "key_metrics": {
                    "avg_speed_improvement": 12.5,
                    "total_delay_reduction": 1500.0,
                    "congestion_reduction": 35.0
                }
            }
        }


class AnalysisResultsResponse(BaseModel):
    """
    完整分析结果响应

    包含 EdgeData, TripInfo, 对比指标的完整数据
    """

    summary: AnalysisResultsSummary = Field(..., description="分析结果总览")

    # EdgeData 结果
    edgedata_metrics: List[EdgeDataMetrics] = Field(
        default=[],
        description="所有道路段的EdgeData指标"
    )

    # TripInfo 结果
    tripinfo_metrics: TripInfoMetrics = Field(
        ...,
        description="行程信息指标"
    )

    # 对比结果
    comparison_metrics: List[ComparisonMetrics] = Field(
        default=[],
        description="基线与对比场景的差异指标"
    )

    # 聚合统计
    aggregated_statistics: Dict[str, Any] = Field(
        default={},
        description="聚合统计数据 (用于图表展示)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "summary": {
                    "batch_id": "batch_20251112_100000",
                    "case_id": "case_20251112_001",
                    "total_simulations": 3,
                    "analyzed_simulations": 3,
                    "analysis_started_at": "2025-11-12T10:00:00",
                    "analysis_completed_at": "2025-11-12T10:15:30",
                    "analysis_duration_seconds": 930.0
                },
                "edgedata_metrics": [],
                "tripinfo_metrics": {
                    "total_trips": 2500,
                    "completed_trips": 2450,
                    "completion_rate": 98.0
                },
                "comparison_metrics": [],
                "aggregated_statistics": {
                    "time_series": {},
                    "spatial_distribution": {}
                }
            }
        }


class StrategyMetrics(BaseModel):
    """
    单个策略的关键指标

    用于策略对比表格展示
    """

    avg_speed: float = Field(default=0.0, description="平均速度 (km/h)")
    avg_trip_duration: float = Field(default=0.0, description="平均行程时间 (秒)")
    completion_rate: float = Field(default=0.0, description="完成率 (%)")
    total_vehicles: int = Field(default=0, description="总车辆数")
    total_delay: float = Field(default=0.0, description="总延误 (秒)")
    avg_waiting_time: float = Field(default=0.0, description="平均等待时间 (秒)")
    improvement_vs_baseline: Optional[Dict[str, float]] = Field(None, description="相比基准的改善百分比")


class StrategyRankingItem(BaseModel):
    """
    策略排名项
    """

    strategy: str = Field(..., description="策略名称 (NO_CONTROL|VSS|TEC|DHS)")
    overall_improvement: float = Field(..., description="综合改善百分比")
    rank: int = Field(..., description="排名 (1为最好)")


class StrategyComparisonResponse(BaseModel):
    """
    策略对比响应

    针对前端影响分析页面的响应格式，包含策略对比和排名数据
    """

    strategy_comparison: Dict[str, StrategyMetrics] = Field(
        ...,
        description="按策略名称分组的指标数据"
    )
    strategy_ranking: List[StrategyRankingItem] = Field(
        default=[],
        description="按改善程度排序的策略列表"
    )


class ComparisonReportResponse(BaseModel):
    """
    对比报告响应

    专门用于场景对比展示
    """

    batch_id: str = Field(..., description="分析批次ID")
    case_id: str = Field(..., description="案例ID")

    # 场景信息
    baseline_scenario: Dict[str, Any] = Field(..., description="基线场景信息")
    comparison_scenarios: List[Dict[str, Any]] = Field(..., description="对比场景列表")

    # 对比指标
    comparison_metrics: List[ComparisonMetrics] = Field(
        ...,
        description="所有对比指标"
    )

    # 改善排名
    improvement_ranking: List[Dict[str, Any]] = Field(
        default=[],
        description="按改善程度排序的场景列表"
    )

    # 可视化数据
    visualization_data: Dict[str, Any] = Field(
        default={},
        description="可视化数据 (图表配置)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "batch_20251112_100000",
                "case_id": "case_20251112_001",
                "baseline_scenario": {
                    "scenario_id": "scenario_001_none",
                    "scenario_name": "无控制策略",
                    "event_type": "accident"
                },
                "comparison_scenarios": [
                    {
                        "scenario_id": "scenario_001_vss",
                        "scenario_name": "可变限速",
                        "control_type": "VSS"
                    }
                ],
                "comparison_metrics": [],
                "improvement_ranking": [
                    {
                        "scenario_id": "scenario_001_vss",
                        "overall_improvement": 25.5,
                        "rank": 1
                    }
                ],
                "visualization_data": {}
            }
        }


class StrategyMetrics(BaseModel):
    """
    单个策略的聚合指标

    用于多场景对比分析
    """

    strategy_type: str = Field(..., description="策略类型 (NO_CONTROL, VSS, TEC, DHS)")
    scenario_count: int = Field(..., description="该策略的场景数量")

    # Summary.xml 指标
    total_vehicles: int = Field(default=0, description="总车辆数")
    avg_speed: float = Field(default=0.0, description="平均速度 (km/h)")
    avg_trip_duration: float = Field(default=0.0, description="平均行程时间 (秒)")
    completion_rate: float = Field(default=0.0, description="完成率 (%)")
    total_delay: float = Field(default=0.0, description="总延误 (秒)")
    avg_waiting_time: float = Field(default=0.0, description="平均等待时间 (秒)")

    # EdgeData 指标 (事件影响路段)
    event_edge_avg_speed: float = Field(default=0.0, description="事件路段平均速度 (km/h)")
    event_edge_avg_density: float = Field(default=0.0, description="事件路段平均密度 (veh/km)")
    event_edge_avg_occupancy: float = Field(default=0.0, description="事件路段平均占用率 (%)")

    # 相对于基线的改善百分比 (如果是基线则为None)
    improvement_vs_baseline: Optional[Dict[str, float]] = Field(
        None,
        description="相对于基线的改善百分比"
    )


class MultiScenarioComparisonResponse(BaseModel):
    """
    多场景对比分析响应

    对同一事件的多个控制策略进行对比分析
    """

    event_id: str = Field(..., description="事件ID")
    event_type: str = Field(..., description="事件类型 (accident, congestion, etc.)")

    # 场景信息
    scenarios: List[Dict[str, Any]] = Field(..., description="所有场景信息")

    # 按策略分组的指标
    strategy_metrics: Dict[str, StrategyMetrics] = Field(
        ...,
        description="按策略分组的聚合指标 (key: strategy_type)"
    )

    # 基线策略
    baseline_strategy: str = Field(default="NO_CONTROL", description="基线策略类型")

    # 策略排名 (按整体改善程度)
    strategy_ranking: List[Dict[str, Any]] = Field(
        ...,
        description="策略排名列表 (按改善程度排序)"
    )

    # 详细对比数据 (用于图表)
    comparison_charts_data: Dict[str, Any] = Field(
        default={},
        description="对比图表数据"
    )

    # 元数据
    analysis_timestamp: datetime = Field(..., description="分析时间戳")
    total_scenarios_analyzed: int = Field(..., description="分析的场景总数")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "8210655",
                "event_type": "congestion",
                "scenarios": [
                    {"scenario_id": "scenario_8210655_no_control", "strategy": "NO_CONTROL"},
                    {"scenario_id": "scenario_8210655_vss", "strategy": "VSS"},
                    {"scenario_id": "scenario_8210655_tec", "strategy": "TEC"}
                ],
                "strategy_metrics": {
                    "NO_CONTROL": {
                        "strategy_type": "NO_CONTROL",
                        "scenario_count": 1,
                        "avg_speed": 45.2,
                        "avg_trip_duration": 1200.0,
                        "completion_rate": 96.5,
                        "improvement_vs_baseline": None
                    },
                    "VSS": {
                        "strategy_type": "VSS",
                        "scenario_count": 1,
                        "avg_speed": 52.8,
                        "avg_trip_duration": 1050.0,
                        "completion_rate": 98.2,
                        "improvement_vs_baseline": {
                            "avg_speed": 16.8,
                            "avg_trip_duration": -12.5,
                            "completion_rate": 1.76
                        }
                    }
                },
                "baseline_strategy": "NO_CONTROL",
                "strategy_ranking": [
                    {"strategy": "VSS", "overall_improvement": 15.5, "rank": 1},
                    {"strategy": "TEC", "overall_improvement": 10.2, "rank": 2}
                ],
                "comparison_charts_data": {},
                "analysis_timestamp": "2025-11-15T10:00:00",
                "total_scenarios_analyzed": 3
            }
        }
