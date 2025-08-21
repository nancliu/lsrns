"""
文件管理相关路由
"""

from fastapi import APIRouter
from typing import List
from ..models import FolderInfo
from ..services import get_folders_service
from .middleware import handle_service_errors

# 创建文件管理路由器
router = APIRouter()


@router.get("/get_folders/{prefix}", response_model=List[FolderInfo])
@handle_service_errors
async def get_folders(prefix: str):
    """
    获取文件夹列表
    """
    return await get_folders_service(prefix)
