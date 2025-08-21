"""
模板管理相关路由
"""

from fastapi import APIRouter
from typing import List
from ..models import TemplateInfo
from ..services import (
    get_taz_templates_service, get_network_templates_service,
    get_simulation_templates_service
)
from .middleware import handle_service_errors

# 创建模板管理路由器
router = APIRouter()


@router.get("/templates/taz", response_model=List[TemplateInfo])
@handle_service_errors
async def get_taz_templates():
    """
    获取TAZ模板列表
    """
    return await get_taz_templates_service()


@router.get("/templates/network", response_model=List[TemplateInfo])
@handle_service_errors
async def get_network_templates():
    """
    获取网络模板列表
    """
    return await get_network_templates_service()


@router.get("/templates/simulation", response_model=List[TemplateInfo])
@handle_service_errors
async def get_simulation_templates():
    """
    获取仿真配置模板列表
    """
    return await get_simulation_templates_service()
