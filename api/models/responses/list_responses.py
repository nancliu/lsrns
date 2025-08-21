"""
列表相关响应模型
"""

from pydantic import BaseModel, Field
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..entities.case import CaseMetadata


class CaseListResponse(BaseModel):
    """案例列表响应模型"""
    cases: List["CaseMetadata"] = Field(..., description="案例列表")
    total_count: int = Field(..., description="总数量")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页数量")


# 延迟导入和模型重建
def rebuild_list_models():
    """重建响应模型以解决循环依赖"""
    try:
        from ..entities.case import CaseMetadata
        CaseListResponse.model_rebuild()
    except ImportError:
        pass

# 在模块导入时重建模型
rebuild_list_models()
