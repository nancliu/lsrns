"""
策略实体与响应模型。

提供策略类型/状态枚举、策略实体、列表与批量生成响应模型。
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class StrategyType(str, Enum):
    """策略类型枚举。"""

    VSL = "VSL"
    DHS = "DHS"
    RM = "RM"
    DTG = "DTG"
    BASELINE = "BASELINE"
    ZONE_RESTRICTION = "zone_restriction"


class StrategyStatus(str, Enum):
    """策略状态枚举。"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Strategy(BaseModel):
    """策略实体。"""

    id: str = Field(..., description="策略ID")
    name: str = Field(..., min_length=1, max_length=100, description="策略名称")
    type: StrategyType = Field(..., description="策略类型")
    description: Optional[str] = Field(None, description="策略描述")

    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    affected_edges: Optional[List[str]] = Field(None, description="影响的边列表")
    tags: List[str] = Field(default_factory=list, description="标签列表")

    status: StrategyStatus = Field(default=StrategyStatus.ACTIVE, description="状态")
    reference_count: int = Field(default=0, description="被引用次数")

    template_id: Optional[str] = Field(None, description="模板ID")
    batch_id: Optional[str] = Field(None, description="批次ID")

    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}
        arbitrary_types_allowed = True


class StrategyListResponse(BaseModel):
    """策略列表响应模型。"""

    items: List[Strategy] = Field(..., description="策略列表")
    total: int = Field(..., description="总数")
    limit: int = Field(..., description="每页数量")
    offset: int = Field(..., description="偏移量")


class BatchGenerateResponse(BaseModel):
    """批量生成响应。"""

    created_count: int = Field(..., description="创建数量")
    items: List[Strategy] = Field(..., description="创建的策略列表")
    batch_id: str = Field(..., description="批次ID")

"""
Strategy Entity Models
策略实体模型
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StrategyType(str, Enum):
    """策略类型枚举"""
    VSL = "VSL"  # 可变限速
    DHS = "DHS"  # 动态硬路肩
    RM = "RM"    # 匝道控制
    DTG = "DTG"  # 动态诱导
    BASELINE = "BASELINE"  # 基准场景
    ZONE_RESTRICTION = "zone_restriction"  # 区域限行


class StrategyStatus(str, Enum):
    """策略状态枚举"""
    ACTIVE = "active"      # 启用
    INACTIVE = "inactive"  # 禁用
    ARCHIVED = "archived"  # 归档


class Strategy(BaseModel):
    """策略实体"""
    id: str = Field(..., description="策略ID")
    name: str = Field(..., description="策略名称", min_length=1, max_length=100)
    type: StrategyType = Field(..., description="策略类型")
    description: Optional[str] = Field(None, description="策略描述")

    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    affected_edges: Optional[List[str]] = Field(None, description="影响的边列表")
    tags: List[str] = Field(default_factory=list, description="标签列表")

    status: StrategyStatus = Field(default=StrategyStatus.ACTIVE, description="状态")
    reference_count: int = Field(default=0, description="被引用次数")

    template_id: Optional[str] = Field(None, description="模板ID")
    batch_id: Optional[str] = Field(None, description="批次ID")

    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    created_by: Optional[str] = Field(None, description="创建者")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        # 确保datetime字段正确序列化
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "id": "strategy_20251004_143000_abc123",
                "name": "VSL-K10-K15-60-早高峰",
                "type": "VSL",
                "description": "K10-K15路段限速60km/h,早高峰时段",
                "parameters": {
                    "speed_limit": 60,
                    "begin_time": 25200,
                    "end_time": 32400
                },
                "affected_edges": ["edge1", "edge2"],
                "tags": ["早高峰", "VSL"],
                "status": "active",
                "reference_count": 0,
                "created_at": "2025-10-04T14:30:00"
            }
        }


class CreateStrategyRequest(BaseModel):
    """创建策略请求"""
    name: str = Field(..., description="策略名称", min_length=1, max_length=100)
    type: StrategyType = Field(..., description="策略类型")
    description: Optional[str] = Field(None, description="策略描述", max_length=500)

    parameters: Dict[str, Any] = Field(default_factory=dict, description="策略参数")
    affected_edges: Optional[List[str]] = Field(None, description="影响的边列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")

    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('策略名称不能为空')
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "VSL-K10-K15-60-早高峰",
                "type": "VSL",
                "description": "K10-K15路段限速60km/h",
                "parameters": {
                    "speed_limit": 60,
                    "begin_time": 25200,
                    "end_time": 32400
                },
                "affected_edges": ["edge1", "edge2"],
                "tags": ["早高峰", "VSL"]
            }
        }


class UpdateStrategyRequest(BaseModel):
    """更新策略请求"""
    name: Optional[str] = Field(None, description="策略名称", min_length=1, max_length=100)
    description: Optional[str] = Field(None, description="策略描述", max_length=500)
    parameters: Optional[Dict[str, Any]] = Field(None, description="策略参数")
    affected_edges: Optional[List[str]] = Field(None, description="影响的边列表")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    status: Optional[StrategyStatus] = Field(None, description="状态")

    @validator('name')
    def validate_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('策略名称不能为空')
        return v.strip() if v else v


class BatchGenerateRequest(BaseModel):
    """批量生成策略请求"""
    template_name: str = Field(..., description="模板名称", min_length=1)
    strategy_type: StrategyType = Field(..., description="策略类型")
    parameter_ranges: Dict[str, List[Any]] = Field(..., description="参数范围(笛卡尔积)")

    @validator('template_name')
    def validate_template_name(cls, v):
        if not v or not v.strip():
            raise ValueError('模板名称不能为空')
        return v.strip()

    @validator('parameter_ranges')
    def validate_parameter_ranges(cls, v):
        if not v or len(v) == 0:
            raise ValueError('至少需要一个参数范围')
        for key, values in v.items():
            if not isinstance(values, list) or len(values) == 0:
                raise ValueError(f'参数 "{key}" 需要至少一个值')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "早高峰VSL组合",
                "strategy_type": "VSL",
                "parameter_ranges": {
                    "speed_limit": [60, 80, 100],
                    "segment": ["K10-K15", "K30-K38"]
                }
            }
        }


class StrategyListResponse(BaseModel):
    """策略列表响应"""
    items: List[Strategy] = Field(..., description="策略列表")
    total: int = Field(..., description="总数")
    limit: int = Field(..., description="每页数量")
    offset: int = Field(..., description="偏移量")


class BatchGenerateResponse(BaseModel):
    """批量生成响应"""
    created_count: int = Field(..., description="创建数量")
    items: List[Strategy] = Field(..., description="创建的策略列表")
    batch_id: str = Field(..., description="批次ID")

    class Config:
        json_schema_extra = {
            "example": {
                "created_count": 6,
                "batch_id": "batch_20251004_143000_xyz789",
                "items": []
            }
        }
