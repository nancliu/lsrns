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
    EDGEDATA = "edgedata"


class StrategyType(str, Enum):
    """管控策略类型枚举"""
    VSS = "vss"  # Variable Speed Sign (可变限速)
    DHS = "dhs"  # Dynamic Hard Shoulder (动态硬路肩)
    TEC = "tec"  # Toll Entrance Control (入口匝道控制)


class BatchSimulationStatus(str, Enum):
    """批量仿真状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
