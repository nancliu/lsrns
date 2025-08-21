"""
数据处理相关路由
"""

from fastapi import APIRouter
from ..models.requests.data_requests import TimeRangeRequest
from ..models.responses.base_response import BaseResponse
from ..services.data_service import DataService
from .middleware import handle_service_errors, create_success_response

# 创建数据处理路由器
router = APIRouter()


@router.post("/process_od_data/", response_model=BaseResponse)
@handle_service_errors
async def process_od_data(request: TimeRangeRequest):
    """
    处理OD数据
    """
    data_service = DataService()
    result = await data_service.process_od_data(request)
    return create_success_response("OD数据处理成功", result)
