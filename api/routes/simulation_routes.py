"""
仿真管理相关路由
"""

from fastapi import APIRouter
from ..models import SimulationRequest, BaseResponse
from ..models.requests.simulation_requests import EventScenarioSimulationRequest
from ..services import (
    run_simulation_service, get_simulation_progress_service,
    get_case_simulations_service, get_simulation_detail_service,
    delete_simulation_service,
    prepare_simulation_service, start_simulation_service,
    start_simulation_with_event_service
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


@router.post("/prepare_simulation/", response_model=BaseResponse)
@handle_service_errors
async def prepare_simulation(request: SimulationRequest):
    """
    准备仿真：生成配置但不启动
    """
    result = await prepare_simulation_service(request)
    return create_success_response("准备仿真成功", result)


@router.post("/start_simulation/", response_model=BaseResponse)
@handle_service_errors
async def start_simulation(case_id: str, simulation_id: str, gui: bool = False):
    """
    启动仿真：基于已准备的 sim 目录
    """
    result = await start_simulation_service(case_id, simulation_id, gui)
    return create_success_response("启动仿真成功", result)


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


@router.post("/cancel_simulation/", response_model=BaseResponse)
@handle_service_errors
async def cancel_simulation(case_id: str, simulation_id: str):
    """
    取消运行中的仿真，杀死SUMO子进程
    """
    from ..services import simulation_service
    result = await simulation_service.cancel_simulation(case_id, simulation_id)
    if result.get("success"):
        return create_success_response("仿真已取消", result)
    else:
        return create_success_response(result.get("message", "取消仿真失败"), result)


@router.post("/start-with-event/", response_model=BaseResponse)
@handle_service_errors
async def start_simulation_with_event(request: EventScenarioSimulationRequest):
    """
    启动应用事件场景的仿真 (Phase 5.3.5)

    将事件场景的.add.xml合并到仿真配置中，并执行仿真。

    Args:
        request: 包含事件场景信息和仿真参数的请求

    Returns:
        包含仿真ID和状态的响应
    """
    result = await start_simulation_with_event_service(request)
    return create_success_response("仿真启动成功", result)
