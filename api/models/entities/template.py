"""
模板和文件相关实体模型
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TemplateInfo(BaseModel):
    """模板信息模型"""
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    file_path: str = Field(..., description="文件路径")
    version: str = Field(..., description="版本号")
    created_date: str = Field(..., description="创建日期")
    status: str = Field(..., description="状态")


class FolderInfo(BaseModel):
    """文件夹信息模型"""
    name: str = Field(..., description="文件夹名称")
    path: str = Field(..., description="文件夹路径")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    size: Optional[int] = Field(None, description="文件夹大小（字节）")
    file_count: Optional[int] = Field(None, description="文件数量")
