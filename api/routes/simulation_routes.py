"""
仿真管理相关路由
"""

from fastapi import APIRouter
from ..models import SimulationRequest, BaseResponse
from ..services import (
    run_simulation_service, get_simulation_progress_service,
    get_case_simulations_service, get_simulation_detail_service,
    delete_simulation_service
)
from .middleware import handle_service_errors, create_success_response

# 创建仿真管理路由器
router = APIRouter()


@router.post("/run_simulation/", response_model=BaseResponse)
@handle_service_errors
async def run_simulation(request: SimulationRequest):
    """
    运行仿真
    """
    result = await run_simulation_service(request)
    return create_success_response("仿真运行成功", result)


@router.get("/simulation_progress/{case_id}")
@handle_service_errors
async def get_simulation_progress(case_id: str):
    """
    获取仿真任务进度
    """
    data = await get_simulation_progress_service(case_id)
    return create_success_response("获取进度成功", data)


@router.get("/simulations/{case_id}")
@handle_service_errors
async def get_case_simulations(case_id: str):
    """
    获取案例下的所有仿真结果
    """
    simulations = await get_case_simulations_service(case_id)
    return create_success_response("获取仿真列表成功", {"simulations": simulations})


@router.get("/simulation/{simulation_id}")
@handle_service_errors
async def get_simulation_detail(simulation_id: str):
    """
    获取仿真详情
    """
    simulation = await get_simulation_detail_service(simulation_id)
    return create_success_response("获取仿真详情成功", simulation)


@router.delete("/simulation/{simulation_id}")
@handle_service_errors
async def delete_simulation(simulation_id: str):
    """
    删除仿真结果
    """
    await delete_simulation_service(simulation_id)
    return create_success_response("删除仿真成功")
