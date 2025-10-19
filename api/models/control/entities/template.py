"""
管控策略模板实体模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from ...enums import StrategyType


class ControlTemplate(BaseModel):
    """管控策略模板模型"""

    template_id: str = Field(
        ...,
        description="模板唯一标识符",
        examples=["vss_moderate_001", "dhs_peak_hours_001"]
    )

    template_name: str = Field(
        ...,
        description="模板名称（用户可读）",
        examples=["可变限速-中等强度", "动态硬路肩-高峰时段"]
    )

    strategy_type: StrategyType = Field(
        ...,
        description="管控策略类型（VSS/DHS/TEC）"
    )

    parameters_schema: Dict[str, Any] = Field(
        ...,
        description="参数JSON Schema定义（类型、范围、默认值）",
        examples=[{
            "speed_limit": {
                "type": "integer",
                "minimum": 40,
                "maximum": 120,
                "default": 80,
                "unit": "km/h",
                "description": "限速值"
            },
            "active_hours": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0, "maximum": 23},
                "default": [7, 8, 9, 17, 18, 19],
                "description": "激活时段（小时）"
            }
        }]
    )

    description: Optional[str] = Field(
        None,
        description="模板详细说明（使用场景、注意事项）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "template_id": "vss_moderate_001",
                "template_name": "可变限速-中等强度",
                "strategy_type": "vss",
                "parameters_schema": {
                    "speed_limit": {
                        "type": "integer",
                        "minimum": 40,
                        "maximum": 120,
                        "default": 80,
                        "unit": "km/h"
                    }
                },
                "description": "适用于高峰时段流量疏导，限速范围40-120km/h"
            }
        }
