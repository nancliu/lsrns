"""
案例管理相关请求模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class CreateCaseRequest(BaseModel):
    """创建案例请求模型"""
    case_name: str = Field(..., description="案例名称")
    description: Optional[str] = Field(None, description="案例描述")


class CaseCreationRequest(BaseModel):
    """案例创建请求模型"""
    time_range: Dict[str, str] = Field(..., description="时间范围")
    config: Dict[str, Any] = Field(..., description="配置参数")
    case_name: Optional[str] = Field(None, description="案例名称")
    description: Optional[str] = Field(None, description="案例描述")


class CaseCloneRequest(BaseModel):
    """案例克隆请求模型"""
    new_case_name: Optional[str] = Field(None, description="新案例名称")
    new_description: Optional[str] = Field(None, description="新案例描述")
