"""
OD数据处理与仿真系统 - 数据模型定义
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# ==================== 枚举类型定义 ====================

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
    TRAFFIC_FLOW = "traffic_flow"
    PERFORMANCE = "performance"

# ==================== 请求模型 ====================

class TimeRangeRequest(BaseModel):
    """时间范围请求模型"""
    start_time: str = Field(..., description="开始时间，格式：YYYY/MM/DD HH:MM:SS")
    end_time: str = Field(..., description="结束时间，格式：YYYY/MM/DD HH:MM:SS")
    schemas_name: Optional[str] = Field("dwd", description="数据库模式名称")
    interval_minutes: Optional[int] = Field(5, description="时间间隔（分钟）")
    taz_file: Optional[str] = Field(None, description="TAZ文件路径")
    net_file: Optional[str] = Field(None, description="网络文件路径")
    table_name: Optional[str] = Field(None, description="可选的表名用于OD查询")
    case_name: Optional[str] = Field(None, description="案例名称")
    description: Optional[str] = Field(None, description="案例描述")
    # 仿真输出控制（默认满足机理对比最小集合：summary+tripinfo 开）
    output_summary: Optional[bool] = Field(True, description="是否输出summary.xml")
    output_tripinfo: Optional[bool] = Field(True, description="是否输出tripinfo.xml")
    output_vehroute: Optional[bool] = Field(False, description="是否输出vehroute.xml")
    output_netstate: Optional[bool] = Field(False, description="是否输出netstate.xml")
    output_fcd: Optional[bool] = Field(False, description="是否输出fcd.xml")
    output_emission: Optional[bool] = Field(False, description="是否输出emission.xml")

class SimulationRequest(BaseModel):
    """仿真请求模型"""
    run_folder: str = Field(..., description="运行文件夹路径")
    gui: Optional[bool] = Field(False, description="是否启用GUI")
    simulation_type: Optional[SimulationType] = Field(SimulationType.MICROSCOPIC, description="仿真类型")
    config_file: Optional[str] = Field(None, description="SUMO配置文件绝对或相对路径")
    expected_duration: Optional[int] = Field(None, description="预期仿真时长（秒），用于进度估算；为空则根据metadata.time_range计算")

class AccuracyAnalysisRequest(BaseModel):
    """精度分析请求模型"""
    result_folder: str = Field(..., description="结果文件夹路径")
    analysis_type: Optional[AnalysisType] = Field(AnalysisType.ACCURACY, description="分析类型")

class CaseCreationRequest(BaseModel):
    """案例创建请求模型"""
    time_range: Dict[str, str] = Field(..., description="时间范围")
    config: Dict[str, Any] = Field(..., description="配置参数")
    case_name: Optional[str] = Field(None, description="案例名称")
    description: Optional[str] = Field(None, description="案例描述")

class CaseCloneRequest(BaseModel):
    """案例克隆请求模型"""
    new_case_name: Optional[str] = Field(None, description="新案例名称")
    new_description: Optional[str] = Field(None, description="新案例描述")

# ==================== 响应模型 ====================

class BaseResponse(BaseModel):
    """基础响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="响应数据")

class CaseMetadata(BaseModel):
    """案例元数据模型"""
    case_id: str = Field(..., description="案例ID")
    case_name: Optional[str] = Field(None, description="案例名称")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    time_range: Dict[str, str] = Field(..., description="时间范围")
    config: Dict[str, Any] = Field(..., description="配置参数")
    status: CaseStatus = Field(..., description="案例状态")
    description: Optional[str] = Field(None, description="案例描述")
    statistics: Optional[Dict[str, Any]] = Field(None, description="统计信息")
    files: Optional[Dict[str, str]] = Field(None, description="文件路径")
    analysis: Optional[Dict[str, Any]] = Field(None, description="分析结果摘要（accuracy/mechanism/performance 最新产物信息）")

class CaseListResponse(BaseModel):
    """案例列表响应模型"""
    cases: List[CaseMetadata] = Field(..., description="案例列表")
    total_count: int = Field(..., description="总数量")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(10, description="每页数量")

class FolderInfo(BaseModel):
    """文件夹信息模型"""
    name: str = Field(..., description="文件夹名称")
    path: str = Field(..., description="文件夹路径")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    size: Optional[int] = Field(None, description="文件夹大小（字节）")
    file_count: Optional[int] = Field(None, description="文件数量")

class AnalysisStatus(BaseModel):
    """分析状态模型"""
    result_folder: str = Field(..., description="结果文件夹")
    status: str = Field(..., description="分析状态")
    progress: Optional[float] = Field(None, description="进度百分比")
    message: Optional[str] = Field(None, description="状态消息")
    created_at: Optional[datetime] = Field(None, description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

# ==================== 内部模型 ====================

class CaseStatistics(BaseModel):
    """案例统计信息模型"""
    total_vehicles: Optional[int] = Field(None, description="总车辆数")
    simulation_duration: Optional[int] = Field(None, description="仿真时长（秒）")
    detector_count: Optional[int] = Field(None, description="检测器数量")
    gantry_count: Optional[int] = Field(None, description="门架数量")

class CaseFiles(BaseModel):
    """案例文件路径模型"""
    od_file: Optional[str] = Field(None, description="OD数据文件路径")
    routes_file: Optional[str] = Field(None, description="路由文件路径")
    config_file: Optional[str] = Field(None, description="配置文件路径")
    taz_file: Optional[str] = Field(None, description="TAZ文件路径")
    network_file: Optional[str] = Field(None, description="网络文件路径")

class TemplateInfo(BaseModel):
    """模板信息模型"""
    name: str = Field(..., description="模板名称")
    description: str = Field(..., description="模板描述")
    file_path: str = Field(..., description="文件路径")
    version: str = Field(..., description="版本号")
    created_date: str = Field(..., description="创建日期")
    status: str = Field(..., description="状态") 