"""
分析相关路由
"""

from fastapi import APIRouter
from typing import Optional
from ..models import AccuracyAnalysisRequest, MechanismAnalysisRequest, PerformanceAnalysisRequest, BaseResponse
from ..services import (
    analyze_accuracy_service, get_case_analysis_history,
    get_analysis_simulation_mapping, list_analysis_results_service
)
from .middleware import handle_service_errors, create_success_response

# 创建分析路由器
router = APIRouter()


@router.post("/analyze_accuracy/", response_model=BaseResponse)
@handle_service_errors
async def analyze_accuracy(request: AccuracyAnalysisRequest):
    """
    精度分析
    """
    result = await analyze_accuracy_service(request)
    return create_success_response("精度分析成功", result)


@router.get("/analysis_history/{case_id}")
@handle_service_errors
async def get_analysis_history(case_id: str):
    """
    获取分析历史
    """
    data = await get_case_analysis_history(case_id)
    return create_success_response("获取分析历史成功", data)


@router.get("/analysis_mapping/{case_id}")
@handle_service_errors
async def get_analysis_mapping(case_id: str, analysis_id: Optional[str] = None):
    """
    获取分析和仿真的对应关系
    """
    data = await get_analysis_simulation_mapping(case_id, analysis_id)
    return create_success_response("获取对应关系成功", data)


@router.get("/analysis_results/{case_id}", response_model=BaseResponse)
@handle_service_errors
async def get_analysis_results(case_id: str, analysis_type: Optional[str] = "accuracy"):
    """
    获取分析结果列表
    """
    data = await list_analysis_results_service(case_id, analysis_type)
    return create_success_response("获取分析结果成功", data)


@router.post("/analyze_mechanism/", response_model=BaseResponse)
@handle_service_errors
async def analyze_mechanism(request: MechanismAnalysisRequest):
    """
    机理分析
    """
    # 机理分析逻辑（暂时返回模拟结果）
    result = {
        "analysis_type": "mechanism",
        "case_id": request.case_id,
        "simulation_ids": request.simulation_ids,
        "status": "completed",
        "message": "机理分析功能正在开发中"
    }
    return create_success_response("机理分析成功", result)


@router.post("/analyze_performance/", response_model=BaseResponse)
@handle_service_errors
async def analyze_performance(request: PerformanceAnalysisRequest):
    """
    性能分析
    """
    # 性能分析逻辑（暂时返回模拟结果）
    result = {
        "analysis_type": "performance",
        "case_id": request.case_id,
        "simulation_ids": request.simulation_ids,
        "status": "completed",
        "message": "性能分析功能正在开发中",
        "efficiency": {
            "total_time": "N/A",
            "chart_count": "N/A",
            "report_size": "N/A"
        }
    }
    return create_success_response("性能分析成功", result)


@router.get("/accuracy_results/{case_id}")
@handle_service_errors
async def get_accuracy_results(case_id: str):
    """
    获取精度分析结果（兼容性端点）
    """
    data = await list_analysis_results_service(case_id, "accuracy")
    return create_success_response("获取精度分析结果成功", data)