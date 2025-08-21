"""
分析相关路由
"""

from fastapi import APIRouter
from typing import Optional
import logging
from ..models import AccuracyAnalysisRequest, MechanismAnalysisRequest, PerformanceAnalysisRequest, BaseResponse
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