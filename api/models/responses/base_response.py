"""
基础响应模型
"""

from pydantic import BaseModel
from typing import Optional, Any, Dict, List


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None
    error_code: Optional[str] = None
    timestamp: Optional[str] = None


class SuccessResponse(BaseResponse):
    """成功响应模型"""
    success: bool = True
    message: str = "操作成功"


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    success: bool = False
    message: str = "操作失败"
    error_code: str = "UNKNOWN_ERROR"


class PaginatedResponse(BaseResponse):
    """分页响应模型"""
    data: Dict[str, Any] = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 10,
        "pages": 0
    }

