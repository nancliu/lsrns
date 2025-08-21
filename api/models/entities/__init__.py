"""
实体模型模块
"""

from .case import CaseMetadata, CaseStatistics, CaseFiles
from .simulation import SimulationResult
from .analysis import AnalysisStatus
from .template import TemplateInfo, FolderInfo

__all__ = [
    "CaseMetadata", "CaseStatistics", "CaseFiles",
    "SimulationResult", 
    "AnalysisStatus",
    "TemplateInfo", "FolderInfo"
]
