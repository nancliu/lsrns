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
from .requests.analysis_requests import AccuracyAnalysisRequest, EdgeDataAnalysisRequest, MechanismAnalysisRequest, PerformanceAnalysisRequest
from .requests.case_requests import CaseCreationRequest, CaseCloneRequest, EventScenarioQuickCreateRequest, ScenarioListQueryRequest, BatchScenarioSimulationRequest, ScenarioAnalysisRequest
from .requests.batch_simulation_requests import BatchSimulationStartRequest, BatchSimulationCancelRequest
from .requests.csv_generation_request import CsvGenerationRequest

# 导入响应模型
from .responses.list_responses import CaseListResponse
from .responses.scenario_responses import ScenarioInfo, ScenarioListResponse, CaseFromScenarioResponse, BatchCaseCreationResponse, ScenarioQueryResponse, AnalysisResult
from .responses.batch_simulation_responses import BatchSimulationStartResponse, BatchExecutionStatusResponse, SimulationProgressInfo
from .responses.csv_generation_response import CsvGenerationResponse, CsvGenerationStateFile, EventGenerationSuccess, EventGenerationFailure

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
    "TimeRangeRequest", "SimulationRequest", "AccuracyAnalysisRequest", "EdgeDataAnalysisRequest", "MechanismAnalysisRequest", "PerformanceAnalysisRequest",
    "CaseCreationRequest", "CaseCloneRequest", "EventScenarioQuickCreateRequest", "ScenarioListQueryRequest", "BatchScenarioSimulationRequest", "ScenarioAnalysisRequest",
    "BatchSimulationStartRequest", "BatchSimulationCancelRequest",
    "CsvGenerationRequest",

    # 响应
    "CaseListResponse", "ScenarioInfo", "ScenarioListResponse", "CaseFromScenarioResponse", "BatchCaseCreationResponse", "ScenarioQueryResponse", "AnalysisResult",
    "BatchSimulationStartResponse", "BatchExecutionStatusResponse", "SimulationProgressInfo",
    "CsvGenerationResponse", "CsvGenerationStateFile", "EventGenerationSuccess", "EventGenerationFailure",
    
    # 实体
    "CaseMetadata", "CaseStatistics", "CaseFiles",
    "SimulationResult", "AnalysisStatus", "TemplateInfo", "FolderInfo"
]
