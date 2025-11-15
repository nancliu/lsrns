"""
案例管理相关路由
"""

from fastapi import APIRouter
from typing import Optional
from ..models.requests.case_requests import (
    CaseCreationRequest,
    CaseCloneRequest,
    EventScenarioQuickCreateRequest,
    CreateCaseWithSimulationRequest
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
    对于事件场景，请使用 POST /from-event-scenario
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


@router.delete("/case/{case_id}", response_model=BaseResponse)
@handle_service_errors
async def delete_case(case_id: str):
    """
    删除案例
    """
    case_service = CaseService()
    result = await case_service.delete_case(case_id)
    return create_success_response("案例删除成功", result)


@router.post("/case/{case_id}/clone", response_model=BaseResponse)
@handle_service_errors
async def clone_case(case_id: str, request: CaseCloneRequest):
    """
    克隆案例
    """
    case_service = CaseService()
    result = await case_service.clone_case(case_id, request)
    return create_success_response("案例克隆成功", result)


@router.post("/from-event-scenario", response_model=BaseResponse)
@handle_service_errors
async def create_case_from_event_scenario(request: CreateCaseWithSimulationRequest):
    """
    从事件场景创建案例并自动创建仿真 (Event Scenario Workflow)

    这是事件场景的统一端点。在一次原子操作中创建案例并立即准备仿真：
    1. 创建案例目录和元数据
    2. 处理OD数据（异步，非阻塞）
    3. 复制TAZ文件
    4. 生成sumocfg配置
    5. 创建仿真元数据
    6. 注册到场景索引

    这确保了案例-场景-仿真的完整元数据链接在创建时就建立，
    而不是在用户点击"仿真"按钮时才创建。

    Args:
        request: 包含场景信息、案例参数和仿真配置

    Returns:
        包含case_id、simulation_id和完整状态信息的响应
    """
    case_service = CaseService()
    result = await case_service.create_case_with_simulation(request)
    return create_success_response("从事件场景创建案例成功", result)
