"""
OD数据处理与仿真系统 - 数据模型模块

按功能领域重构的模型结构:
- enums.py: 枚举定义
- base.py: 基础模型和混入类
- requests/: 请求模型
- responses/: 响应模型  
- entities/: 实体模型
"""

# 导入枚举类型
from .enums import SimulationType, CaseStatus, AnalysisType

# 导入基础模型
from .base import BaseResponse, TimestampMixin, IdentifierMixin

# 导入请求模型
from .requests.data_requests import TimeRangeRequest
from .requests.simulation_requests import SimulationRequest
from .requests.analysis_requests import AccuracyAnalysisRequest, MechanismAnalysisRequest, PerformanceAnalysisRequest
from .requests.case_requests import CaseCreationRequest, CaseCloneRequest

# 导入响应模型
from .responses.list_responses import CaseListResponse

# 导入实体模型
from .entities.case import CaseMetadata, CaseStatistics, CaseFiles
from .entities.simulation import SimulationResult
from .entities.analysis import AnalysisStatus
from .entities.template import TemplateInfo, FolderInfo

# 为了保持向后兼容，导出所有原有的类名
__all__ = [
    # 枚举
    "SimulationType", "CaseStatus", "AnalysisType",
    
    # 基础
    "BaseResponse", "TimestampMixin", "IdentifierMixin",
    
    # 请求
    "TimeRangeRequest", "SimulationRequest", "AccuracyAnalysisRequest", "MechanismAnalysisRequest", "PerformanceAnalysisRequest",
    "CaseCreationRequest", "CaseCloneRequest",
    
    # 响应
    "CaseListResponse",
    
    # 实体
    "CaseMetadata", "CaseStatistics", "CaseFiles",
    "SimulationResult", "AnalysisStatus", "TemplateInfo", "FolderInfo"
]
