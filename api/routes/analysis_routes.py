"""
分析相关路由
"""

from fastapi import APIRouter
from typing import Optional
import logging
from ..models import AccuracyAnalysisRequest, EdgeDataAnalysisRequest, MechanismAnalysisRequest, PerformanceAnalysisRequest, BaseResponse
# 不再从api.services导入旧函数，直接使用服务类
from .middleware import handle_service_errors, create_success_response

logger = logging.getLogger(__name__)

# 创建分析路由器
router = APIRouter()


@router.post("/analyze_accuracy/", response_model=BaseResponse)
@handle_service_errors
async def analyze_accuracy(request: AccuracyAnalysisRequest):
    """
    精度分析
    """
    from ..services.accuracy_service import AccuracyAnalysisService
    from pathlib import Path
    
    # 创建精度分析服务实例
    cases_dir = Path("cases")
    accuracy_service = AccuracyAnalysisService(cases_dir)
    
    # 执行精度分析（目前只支持单个仿真）
    if len(request.simulation_ids) > 1:
        return create_success_response("精度分析暂不支持多仿真", {"error": "精度分析目前只支持单个仿真"})
    
    result = await accuracy_service.analyze_accuracy(request.case_id, request.simulation_ids[0])
    return create_success_response("精度分析成功", result)


@router.get("/analysis_history/{case_id}")
@handle_service_errors
async def get_analysis_history(case_id: str):
    """
    获取分析历史
    """
    from ..services.accuracy_service import AccuracyAnalysisService
    from pathlib import Path
    
    # 创建服务实例获取分析历史
    cases_dir = Path("cases")
    service = AccuracyAnalysisService(cases_dir)
    data = await service.get_case_analysis_history(case_id)
    return create_success_response("获取分析历史成功", data)


@router.get("/analysis_mapping/{case_id}")
@handle_service_errors
async def get_analysis_mapping(case_id: str, analysis_id: Optional[str] = None):
    """
    获取分析和仿真的对应关系
    """
    from ..services.accuracy_service import AccuracyAnalysisService
    from pathlib import Path
    
    # 创建服务实例获取分析映射
    cases_dir = Path("cases")
    service = AccuracyAnalysisService(cases_dir)
    data = await service.get_analysis_simulation_mapping(case_id, analysis_id)
    return create_success_response("获取对应关系成功", data)


@router.get("/analysis_results/{case_id}", response_model=BaseResponse)
@handle_service_errors
async def get_analysis_results(case_id: str, analysis_type: Optional[str] = "accuracy"):
    """
    获取分析结果列表
    """
    from pathlib import Path
    
    # 根据分析类型创建相应的服务实例
    cases_dir = Path("cases")
    
    if analysis_type == "mechanism":
        from ..services.mechanism_service import MechanismAnalysisService
        service = MechanismAnalysisService(cases_dir)
    elif analysis_type == "performance":
        from ..services.performance_service import PerformanceAnalysisService
        service = PerformanceAnalysisService(cases_dir)
    elif analysis_type == "edgedata":
        from ..services.edgedata_service import EdgeDataAnalysisService
        service = EdgeDataAnalysisService(cases_dir)
    else:
        # 默认使用精度分析服务
        from ..services.accuracy_service import AccuracyAnalysisService
        service = AccuracyAnalysisService(cases_dir)
    
    data = await service.list_analysis_results(case_id, analysis_type)
    return create_success_response("获取分析结果成功", data)


@router.post("/analyze_mechanism/", response_model=BaseResponse)
@handle_service_errors
async def analyze_mechanism(request: MechanismAnalysisRequest):
    """
    机理分析
    """
    from ..services.mechanism_service import MechanismAnalysisService
    from pathlib import Path
    
    # 创建机理分析服务实例
    cases_dir = Path("cases")
    mechanism_service = MechanismAnalysisService(cases_dir)
    
    # 执行机理分析
    result = await mechanism_service.analyze_mechanism(request.case_id, request.simulation_ids)
    return create_success_response("机理分析成功", result)


@router.post("/analyze_performance/", response_model=BaseResponse)
@handle_service_errors
async def analyze_performance(request: PerformanceAnalysisRequest):
    """
    性能分析
    """
    from ..services.performance_service import PerformanceAnalysisService
    from pathlib import Path
    
    # 创建性能分析服务实例
    cases_dir = Path("cases")
    performance_service = PerformanceAnalysisService(cases_dir)
    
    # 执行性能分析
    result = await performance_service.analyze_performance(request.case_id, request.simulation_ids)
    return create_success_response("性能分析成功", result)


@router.post("/analyze_edgedata/", response_model=BaseResponse)
@handle_service_errors
async def analyze_edgedata(request: EdgeDataAnalysisRequest):
    """
    EdgeData分析
    """
    from ..services.edgedata_service import EdgeDataAnalysisService
    from pathlib import Path
    
    # 创建EdgeData分析服务实例
    cases_dir = Path("cases")
    edgedata_service = EdgeDataAnalysisService(cases_dir)
    
    # 执行EdgeData分析
    result = await edgedata_service.analyze_edgedata(request.case_id, request.simulation_ids)
    return create_success_response("EdgeData分析成功", result)


@router.get("/edgedata_results/{case_id}")
@handle_service_errors
async def get_edgedata_results(case_id: str):
    """
    获取EdgeData分析结果
    """
    from ..services.edgedata_service import EdgeDataAnalysisService
    from pathlib import Path
    
    # 创建服务实例获取EdgeData分析结果
    cases_dir = Path("cases")
    service = EdgeDataAnalysisService(cases_dir)
    data = await service.list_analysis_results(case_id, "edgedata")
    return create_success_response("获取EdgeData分析结果成功", data)


@router.get("/accuracy_results/{case_id}")
@handle_service_errors
async def get_accuracy_results(case_id: str):
    """
    获取精度分析结果（兼容性端点）
    """
    from ..services.accuracy_service import AccuracyAnalysisService
    from pathlib import Path

    # 创建服务实例获取精度分析结果
    cases_dir = Path("cases")
    service = AccuracyAnalysisService(cases_dir)
    data = await service.list_analysis_results(case_id, "accuracy")
    return create_success_response("获取精度分析结果成功", data)


# ============================================================================
# Analysis Results Routes (Task 3.2 - Week 3 Phase 2)
# ============================================================================


@router.get("/results/{batch_id}", response_model=BaseResponse)
@handle_service_errors
async def get_analysis_results_by_batch(batch_id: str, case_id: str):
    """
    获取分析结果 (批次级别) - Task 3.2

    聚合多个仿真的 EdgeData/TripInfo 指标

    Args:
        batch_id: 分析批次ID
        case_id: 案例ID

    Returns:
        BaseResponse 包含 AnalysisResultsResponse:
            - summary: 分析结果总览
            - edgedata_metrics: EdgeData 指标列表
            - tripinfo_metrics: TripInfo 指标
            - comparison_metrics: 对比指标
            - aggregated_statistics: 聚合统计

    Example:
        ```
        GET /api/v1/analysis/results/batch_20251112_100000?case_id=case_001
        ```

    Response:
        ```json
        {
            "code": 200,
            "message": "获取分析结果成功",
            "data": {
                "summary": {
                    "batch_id": "batch_20251112_100000",
                    "total_simulations": 3,
                    "analyzed_simulations": 3,
                    ...
                },
                "edgedata_metrics": [...],
                "tripinfo_metrics": {...},
                "comparison_metrics": [...],
                "aggregated_statistics": {...}
            }
        }
        ```
    """
    from ..services.analysis_results_service import AnalysisResultsService

    logger.info(f"获取分析结果: batch_id={batch_id}, case_id={case_id}")

    service = AnalysisResultsService()
    result = await service.get_analysis_results(batch_id, case_id)

    return create_success_response("获取分析结果成功", result.dict())


@router.get("/comparison/{batch_id}", response_model=BaseResponse)
@handle_service_errors
async def get_comparison_report(batch_id: str, case_id: str):
    """
    获取对比报告 - Task 3.2

    生成基线 vs 事件 vs 控制策略的对比报告

    Args:
        batch_id: 分析批次ID
        case_id: 案例ID

    Returns:
        BaseResponse 包含 ComparisonReportResponse:
            - baseline_scenario: 基线场景信息
            - comparison_scenarios: 对比场景列表
            - comparison_metrics: 所有对比指标
            - improvement_ranking: 改善排名
            - visualization_data: 可视化数据

    Example:
        ```
        GET /api/v1/analysis/comparison/batch_20251112_100000?case_id=case_001
        ```

    Response:
        ```json
        {
            "code": 200,
            "message": "获取对比报告成功",
            "data": {
                "batch_id": "batch_20251112_100000",
                "baseline_scenario": {
                    "scenario_id": "scenario_001_none",
                    "scenario_name": "无控制策略",
                    ...
                },
                "comparison_scenarios": [
                    {
                        "scenario_id": "scenario_001_vss",
                        "scenario_name": "可变限速",
                        ...
                    }
                ],
                "comparison_metrics": [
                    {
                        "metric_name": "avg_speed",
                        "baseline_value": 45.2,
                        "comparison_value": 52.8,
                        "improvement_status": "improved",
                        "improvement_color": "green",
                        ...
                    }
                ],
                "improvement_ranking": [
                    {
                        "scenario_id": "scenario_001_vss",
                        "overall_improvement": 25.5,
                        "rank": 1
                    }
                ],
                "visualization_data": {
                    "charts": [...],
                    "heatmaps": [...],
                    "radar_charts": [...]
                }
            }
        }
        ```
    """
    from ..services.analysis_results_service import AnalysisResultsService

    logger.info(f"生成对比报告: batch_id={batch_id}, case_id={case_id}")

    service = AnalysisResultsService()
    result = await service.get_comparison_report(batch_id, case_id)

    return create_success_response("获取对比报告成功", result.dict())


@router.post("/strategy-comparison/generate/{case_id}", response_model=BaseResponse)
@handle_service_errors
async def generate_strategy_comparison_metrics(case_id: str):
    """
    生成策略对比分析数据 - Phase 2 新增功能

    提取多个控制策略的仿真结果中的8个交通性能指标，生成对比数据和时序数据，
    并存储在 case/analysis 目录中的JSON文件中

    Args:
        case_id: 案例ID

    Returns:
        BaseResponse 包含:
            - strategy_comparison: 各策略的最终指标值
            - timeseries: 各策略的时序数据
            - strategies: 检测到的策略列表
            - metrics: 8个交通性能指标定义

    Example:
        ```
        POST /api/v1/analysis/strategy-comparison/generate/case_event_10754
        ```

    Response:
        ```json
        {
            "code": 200,
            "message": "策略对比分析生成成功",
            "data": {
                "strategy_comparison": {
                    "NO_CONTROL": {
                        "current_vehicles": 150,
                        "avg_speed": 45.2,
                        "loaded_vehicles": 8500,
                        "chain_frequency": 12500,
                        "transmission_frequency": 8200,
                        "completed_vehicles": 8934,
                        "terminated_vehicles": 45,
                        "waiting_vehicles": 320
                    },
                    "TEC": {
                        "current_vehicles": 120,
                        "avg_speed": 48.5,
                        ...
                    }
                },
                "timeseries": {
                    "NO_CONTROL": {
                        "current_vehicles": [{"timestamp": "...", "value": 150}],
                        ...
                    }
                },
                "strategies": ["NO_CONTROL", "TEC", "VSS", "DHS"],
                "metrics": {
                    "current_vehicles": {
                        "label": "当前运行车数",
                        "unit": "辆",
                        "higher_is_better": false
                    },
                    ...
                }
            }
        }
        ```
    """
    from ..services import strategy_comparison_service

    logger.info(f"生成策略对比分析: case_id={case_id}")

    result = await strategy_comparison_service.generate_strategy_comparison(case_id)

    return create_success_response("策略对比分析生成成功", result)


@router.get("/strategy-comparison/{case_id}", response_model=BaseResponse)
@handle_service_errors
async def load_strategy_comparison_data(case_id: str):
    """
    加载预计算的策略对比数据 - 从JSON文件读取

    从 cases/{case_id}/analysis/strategy_comparison.json 加载已生成的对比数据

    Args:
        case_id: 案例ID

    Returns:
        BaseResponse 包含 8个交通性能指标的各策略对比数据

    Example:
        ```
        GET /api/v1/analysis/strategy-comparison/case_event_10754
        ```

    Response:
        ```json
        {
            "code": 200,
            "message": "获取策略对比数据成功",
            "data": {
                "NO_CONTROL": {...},
                "TEC": {...},
                "VSS": {...},
                "DHS": {...}
            }
        }
        ```
    """
    from ..services import strategy_comparison_service

    logger.info(f"加载策略对比数据: case_id={case_id}")

    result = await strategy_comparison_service.load_comparison_from_file(case_id)

    if result is None:
        return create_success_response("策略对比数据不存在或未生成", {})

    return create_success_response("获取策略对比数据成功", result)


@router.get("/strategy-timeseries/{case_id}", response_model=BaseResponse)
@handle_service_errors
async def load_strategy_timeseries_data(case_id: str):
    """
    加载预计算的策略时序数据 - 从JSON文件读取

    从 cases/{case_id}/analysis/strategy_timeseries.json 加载已生成的时序数据，
    包含8个交通性能指标在仿真过程中的时间序列变化

    Args:
        case_id: 案例ID

    Returns:
        BaseResponse 包含各策略各指标的时序数据

    Example:
        ```
        GET /api/v1/analysis/strategy-timeseries/case_event_10754
        ```

    Response:
        ```json
        {
            "code": 200,
            "message": "获取时序数据成功",
            "data": {
                "NO_CONTROL": {
                    "current_vehicles": [
                        {"timestamp": "2025-11-16T10:00:00", "value": 150},
                        {"timestamp": "2025-11-16T10:01:00", "value": 155}
                    ],
                    ...
                },
                "TEC": {...}
            }
        }
        ```
    """
    from ..services import strategy_comparison_service

    logger.info(f"加载时序数据: case_id={case_id}")

    result = await strategy_comparison_service.load_timeseries_from_file(case_id)

    if result is None:
        return create_success_response("时序数据不存在或未生成", {})

    return create_success_response("获取时序数据成功", result)


@router.get("/strategy_comparison/{batch_id}", response_model=BaseResponse)
@handle_service_errors
async def get_strategy_comparison(batch_id: str, case_id: str):
    """
    获取策略对比结果 - 用于前端影响分析页面（兼容性端点）

    将分析结果转换为前端期望的strategy_comparison和strategy_ranking格式

    NOTE: 此端点基于批量优化结果。对于事件场景分析，请使用 /api/v1/analysis/strategy-comparison/{case_id}

    Args:
        batch_id: 分析批次ID
        case_id: 案例ID

    Returns:
        BaseResponse 包含 StrategyComparisonResponse:
            - strategy_comparison: 按策略名称分组的指标数据
                - NO_CONTROL: 基准策略的指标
                - VSS: 可变限速策略的指标和改善百分比
                - TEC: 收费站管控策略的指标和改善百分比
                - DHS: 动态硬路肩策略的指标和改善百分比
            - strategy_ranking: 按改善程度排序的策略排名列表

    Example:
        ```
        GET /api/v1/analysis/strategy_comparison/batch_20251112_100000?case_id=case_001
        ```

    Response:
        ```json
        {
            "code": 200,
            "message": "获取策略对比结果成功",
            "data": {
                "strategy_comparison": {
                    "NO_CONTROL": {
                        "avg_speed": 45.2,
                        "avg_trip_duration": 1200,
                        "completion_rate": 96.5,
                        "total_vehicles": 8934,
                        "total_delay": 45000,
                        "avg_waiting_time": 120,
                        "improvement_vs_baseline": null
                    },
                    "VSS": {
                        "avg_speed": 52.8,
                        "avg_trip_duration": 1050,
                        "completion_rate": 98.2,
                        "total_vehicles": 8934,
                        "total_delay": 38000,
                        "avg_waiting_time": 95,
                        "improvement_vs_baseline": {
                            "avg_speed": 16.8,
                            "avg_trip_duration": -12.5,
                            "completion_rate": 1.76
                        }
                    }
                },
                "strategy_ranking": [
                    {
                        "strategy": "VSS",
                        "overall_improvement": 25.5,
                        "rank": 1
                    },
                    {
                        "strategy": "TEC",
                        "overall_improvement": 18.3,
                        "rank": 2
                    }
                ]
            }
        }
        ```
    """
    from ..services.analysis_results_service import AnalysisResultsService

    logger.info(f"获取策略对比结果: batch_id={batch_id}, case_id={case_id}")

    service = AnalysisResultsService()
    result = await service.get_strategy_comparison(batch_id, case_id)

    return create_success_response("获取策略对比结果成功", result.dict())