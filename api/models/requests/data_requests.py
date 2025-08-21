"""
数据处理相关请求模型
"""

from pydantic import BaseModel, Field
from typing import Optional


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
