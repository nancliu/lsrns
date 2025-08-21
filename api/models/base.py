"""
基础模型定义
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")


class TimestampMixin(BaseModel):
    """时间戳混入类"""
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class IdentifierMixin(BaseModel):
    """标识符混入类"""
    id: str = Field(..., description="唯一标识符")
    name: Optional[str] = Field(None, description="名称")
    description: Optional[str] = Field(None, description="描述")
