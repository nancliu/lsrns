"""
案例管理相关路由
"""

from fastapi import APIRouter
from typing import Optional
from ..models.requests.case_requests import (
    CaseCreationRequest,
    CaseCloneRequest,
    EventScenarioQuickCreateRequest
)
from ..models.responses.base_response import BaseResponse
from ..models.entities.case import CaseMetadata, CaseStatus
from ..models.responses.list_responses import CaseListResponse
from ..services.case_service import CaseService
from .middleware import handle_service_errors, create_success_response

# 创建案例管理路由器
router = APIRouter()


@router.post("/", response_model=BaseResponse)
@handle_service_errors
async def create_case(request: CaseCreationRequest):
    """
    创建OD案例 (OD Workflow)

    这是基础的案例创建端点，用于OD提取工作流。
    """
    case_service = CaseService()
    result = await case_service.create_case(request)
    return create_success_response("案例创建成功", result)


@router.get("/list_cases/", response_model=CaseListResponse)
@handle_service_errors
async def list_cases(
    page: int = 1,
    page_size: int = 10,
    status: Optional[CaseStatus] = None,
    search: Optional[str] = None
):
    """
    获取案例列表
    """
    case_service = CaseService()
    return await case_service.list_cases(page, page_size, status, search)


@router.get("/case/{case_id}", response_model=CaseMetadata)
@handle_service_errors
async def get_case(case_id: str):
    """
    获取案例详情
    """
    case_service = CaseService()
    return await case_service.get_case(case_id)


@router.get("/case/{case_id}/od-status", response_model=BaseResponse)
@handle_service_errors
async def get_od_status(case_id: str):
    """
    获取OD数据生成状态

    用于检查OD数据是否生成完成，以及SUMOCFG文件是否已重新修正。
    这个端点用于前端轮询，确保用户在OD数据和SUMOCFG都就绪后才能启动仿真。

    返回数据结构：
    {
        "od_status": "generating" | "completed" | "failed",
        "sumocfg_ready": boolean,
        "generated_at": timestamp or null,
        "error": error message or null
    }
    """
    case_service = CaseService()
    result = await case_service.get_od_status(case_id)
    return create_success_response("获取OD状态成功", result)


@router.delete("/case/{case_id}", response_model=BaseResponse)
@handle_service_errors
async def delete_case(case_id: str):
    """
    删除案例
    """
    case_service = CaseService()
    result = await case_service.delete_case(case_id)
    return create_success_response("案例删除成功", result)


@router.delete("/case/{case_id}/delete-with-reset", response_model=BaseResponse)
@handle_service_errors
async def delete_case_with_reset(case_id: str):
    """
    删除案例并重置scenario_index.json中的关联

    此端点用于批量创建页面中的删除操作。
    删除操作包括：
    1. 删除案例的所有文件夹
    2. 从scenario_index.json中清除该case的所有created_cases关联

    参数：
    - case_id: 案例ID

    返回：
    {
        "success": true,
        "case_id": "case_event_10754",
        "scenarios_affected": 3,
        "message": "删除成功"
    }
    """
    case_service = CaseService()
    result = await case_service.delete_case_with_reset(case_id)
    return create_success_response("案例删除成功", result)


@router.post("/case/{case_id}/reset-simulation-status", response_model=BaseResponse)
@handle_service_errors
async def reset_case_simulation_status(case_id: str):
    """
    重置案例的仿真状态

    将案例状态从 simulating 重置为 created，允许用户重新启动仿真。
    用于取消批次仿真后恢复案例到可启动状态。

    Args:
        case_id: 案例ID (e.g., "case_event_6120705")

    Returns:
        {
            "success": true,
            "case_id": "case_event_6120705",
            "old_status": "simulating",
            "new_status": "created",
            "message": "案例仿真状态已重置"
        }
    """
    case_service = CaseService()
    result = await case_service.reset_case_simulation_status(case_id)
    return create_success_response("案例仿真状态已重置", result)


@router.post("/case/{case_id}/clone", response_model=BaseResponse)
@handle_service_errors
async def clone_case(case_id: str, request: CaseCloneRequest):
    """
    克隆案例
    """
    case_service = CaseService()
    result = await case_service.clone_case(case_id, request)
    return create_success_response("案例克隆成功", result)
