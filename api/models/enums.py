"""
业务枚举定义
"""

from enum import Enum


class SimulationType(str, Enum):
    """仿真类型枚举"""
    MICROSCOPIC = "microscopic"
    MESOSCOPIC = "mesoscopic"


class CaseStatus(str, Enum):
    """案例状态枚举"""
    CREATED = "created"
    PROCESSING = "processing"
    SIMULATING = "simulating"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisType(str, Enum):
    """分析类型枚举"""
    ACCURACY = "accuracy"
    MECHANISM = "mechanism"
    PERFORMANCE = "performance"
