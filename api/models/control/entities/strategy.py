"""
管控策略实例实体模型
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List
from datetime import datetime


class Strategy(BaseModel):
    """管控策略实例模型"""

    strategy_id: str = Field(
        ...,
        description="策略唯一标识符（UUID或自增ID）",
        examples=["strategy_20251019_001", "strat_uuid_abc123"]
    )

    strategy_name: str = Field(
        ...,
        description="策略名称（用户自定义）",
        examples=["G4202分流点限速80", "高峰时段入口控制方案A"]
    )

    template_id: str = Field(
        ...,
        description="关联的模板ID（外键）",
        examples=["vss_moderate_001"]
    )

    parameters: Dict[str, Any] = Field(
        ...,
        description="参数值字典（键名匹配template的parameters_schema）",
        examples=[{
            "speed_limit": 80,
            "active_hours": [7, 8, 9, 17, 18, 19],
            "warning_threshold": 70
        }]
    )

    target_edges: List[str] = Field(
        ...,
        description="目标路段ID列表（SUMO edge_id）",
        examples=[["edge_e789012", "edge_e789013", "edge_e789015"]]
    )

    created_at: datetime = Field(
        default_factory=datetime.now,
        description="创建时间戳"
    )

    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="最后更新时间戳"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "strategy_20251019_001",
                "strategy_name": "G4202分流点限速80",
                "template_id": "vss_moderate_001",
                "parameters": {
                    "speed_limit": 80,
                    "active_hours": [7, 8, 9, 17, 18, 19]
                },
                "target_edges": ["edge_e789012", "edge_e789013"],
                "created_at": "2025-10-19T10:30:00",
                "updated_at": "2025-10-19T10:30:00"
            }
        }
