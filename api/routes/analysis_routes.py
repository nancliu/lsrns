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