"""
仿真管理相关路由
"""

from fastapi import APIRouter
from ..models import SimulationRequest, BaseResponse
from ..models.requests.simulation_requests import EventScenarioSimulationRequest
from ..models.requests.batch_simulation_requests import (
    BatchSimulationStartRequest,
    BatchSimulationCancelRequest
)
from ..models.responses.batch_simulation_responses import (
    BatchSimulationStartResponse,
    BatchExecutionStatusResponse
)
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


# ============================================================================
# Batch Simulation Routes (Task 2.3 - Week 2 Phase 2)
# ============================================================================


@router.post("/batch-start", response_model=BaseResponse)
@handle_service_errors
async def batch_start_simulations(request: BatchSimulationStartRequest):
    """
    批量启动仿真 (Task 2.3)

    支持事件场景批量仿真工作流:
    - 并发执行多个仿真 (2-16 workers)
    - 实时进度跟踪
    - 自动结果验证
    - 可选自动分析

    Args:
        request: 批量仿真启动请求
            - simulation_ids: 仿真ID列表 (1-100)
            - case_id: 案例ID
            - parallel_workers: 并发数 (default: 4)
            - auto_run_analysis: 完成后自动分析 (default: True)

    Returns:
        BaseResponse 包含:
            - batch_id: 批次ID (用于后续查询状态)
            - total_simulations: 总仿真数
            - status: 批次状态

    Example:
        ```
        POST /api/v1/simulation/batch-start
        {
            "simulation_ids": ["sim_001", "sim_002", "sim_003"],
            "case_id": "case_20251112_001",
            "parallel_workers": 4,
            "auto_run_analysis": true
        }
        ```

    Response:
        ```
        {
            "code": 200,
            "message": "批量仿真已启动",
            "data": {
                "batch_id": "batch_20251112_100000",
                "total_simulations": 3,
                "status": "queued"
            }
        }
        ```
    """
    # Import here to avoid circular dependency
    from ..services import simulation_orchestrator

    result = await simulation_orchestrator.batch_start_simulations(
        simulation_ids=request.simulation_ids,
        case_id=request.case_id,
        parallel_workers=request.parallel_workers,
        auto_run_analysis=request.auto_run_analysis,
        analysis_types=request.analysis_types
    )

    return create_success_response("批量仿真已启动", result)


@router.get("/batch-status/{batch_id}", response_model=BaseResponse)
@handle_service_errors
async def get_batch_execution_status(batch_id: str):
    """
    获取批量仿真执行状态 (Task 2.3)

    实时监控批量仿真进度:
    - 总体进度统计 (completed/failed/in_progress/queued)
    - 每个仿真的详细状态
    - ETA估算
    - 当前执行任务列表

    轮询间隔建议: 5-10秒

    Args:
        batch_id: 批次ID (从 batch-start 响应获取)

    Returns:
        BaseResponse 包含 BatchExecutionStatusResponse:
            - batch_status: 批次状态 (running|completed|failed)
            - total_simulations: 总数
            - completed/failed/in_progress/queued: 各状态数量
            - simulations: 每个仿真的详细进度
            - estimated_completion: 预计完成时间

    Example:
        ```
        GET /api/v1/simulation/batch-status/batch_20251112_100000
        ```

    Response:
        ```
        {
            "code": 200,
            "message": "获取批次状态成功",
            "data": {
                "batch_id": "batch_20251112_100000",
                "case_id": "case_20251112_001",
                "total_simulations": 10,
                "completed": 4,
                "failed": 1,
                "in_progress": 2,
                "queued": 3,
                "batch_status": "running",
                "estimated_completion": "2025-11-12T12:30:00",
                "simulations": [
                    {
                        "simulation_id": "sim_001",
                        "status": "completed",
                        "progress_percent": 100,
                        "elapsed_seconds": 320.5
                    },
                    {
                        "simulation_id": "sim_002",
                        "status": "running",
                        "progress_percent": 45,
                        "elapsed_seconds": 150.2
                    }
                ]
            }
        }
        ```
    """
    from ..services import simulation_orchestrator

    result = await simulation_orchestrator.get_batch_execution_status(batch_id)

    return create_success_response("获取批次状态成功", result)


@router.post("/batch-cancel", response_model=BaseResponse)
@handle_service_errors
async def cancel_batch_simulations(request: BatchSimulationCancelRequest):
    """
    取消批量仿真 (Task 2.3)

    支持两种取消模式:
    - graceful=True: 允许当前运行的仿真完成,停止队列中的任务
    - graceful=False: 立即终止所有仿真 (杀死SUMO进程)

    Args:
        request: 取消请求
            - batch_id: 批次ID
            - graceful: 是否优雅停止 (default: True)

    Returns:
        BaseResponse 包含:
            - cancelled_count: 已取消的仿真数
            - in_flight_count: 正在完成的仿真数 (graceful模式)

    Example:
        ```
        POST /api/v1/simulation/batch-cancel
        {
            "batch_id": "batch_20251112_100000",
            "graceful": true
        }
        ```
    """
    from ..services import simulation_orchestrator

    result = await simulation_orchestrator.cancel_batch_simulations(
        batch_id=request.batch_id,
        graceful=request.graceful
    )

    return create_success_response("批次已取消", result)
