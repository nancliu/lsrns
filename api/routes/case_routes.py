"""
案例管理相关路由
"""

from fastapi import APIRouter
from typing import Optional
from ..models.requests.case_requests import CaseCreationRequest, CaseCloneRequest
from ..models.responses.base_response import BaseResponse
from ..models.entities.case import CaseMetadata, CaseStatus
from ..models.responses.list_responses import CaseListResponse
from ..services.case_service import CaseService
from .middleware import handle_service_errors, create_success_response

# 创建案例管理路由器
router = APIRouter()


@router.post("/create_case/", response_model=BaseResponse)
@handle_service_errors
async def create_case(request: CaseCreationRequest):
    """
    创建案例
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
