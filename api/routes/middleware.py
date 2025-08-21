"""
公共中间件和异常处理
"""

from fastapi import HTTPException
from typing import Callable, Any
import functools

from ..models import BaseResponse


def handle_service_errors(func: Callable) -> Callable:
    """
    统一的服务错误处理装饰器
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return wrapper


def create_success_response(message: str, data: Any = None) -> BaseResponse:
    """
    创建成功响应
    """
    return BaseResponse(
        success=True,
        message=message,
        data=data
    )


def create_error_response(message: str, data: Any = None) -> BaseResponse:
    """
    创建错误响应
    """
    return BaseResponse(
        success=False,
        message=message,
        data=data
    )
