"""
分析相关实体模型
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AnalysisStatus(BaseModel):
    """分析状态模型"""
    result_folder: str = Field(..., description="结果文件夹")
    status: str = Field(..., description="分析状态")
    progress: Optional[float] = Field(None, description="进度百分比")
    message: Optional[str] = Field(None, description="状态消息")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
