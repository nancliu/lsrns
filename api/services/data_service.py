"""
数据处理服务 - 负责OD数据处理相关业务逻辑
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from ..models import TimeRangeRequest, CaseStatus
from .base_service import BaseService, MetadataManager, DirectoryManager


class DataService(BaseService):
    """OD数据处理服务类"""
    
    async def process_od_data(self, request: TimeRangeRequest) -> Dict[str, Any]:
        """
        处理OD数据的主要业务逻辑
        """
        try:
            request_started_at = datetime.now()
            
            # 导入处理器 (保持原有导入方式)
            from shared.data_processors.od_processor import ODProcessor
            from shared.utilities.time_utils import parse_datetime
            from shared.data_access.db_config import get_db_config  # 预留：若需要表名推断可另行实现
            from datetime import datetime as _dt
            
            # 创建OD处理器
            od_processor = ODProcessor()
            
            # 推断表名逻辑
            inferred_table_name = self._infer_table_name(request)
            
            # 生成case_id和目录结构
            case_id = self.generate_unique_id("case")
            case_dir = DirectoryManager.create_case_structure(case_id)
            
            # 构建处理参数
            request_params = self._build_od_request_params(request, inferred_table_name, case_dir)
            
            # 获取数据库连接并处理数据
            db_connection = self.get_db_connection()
            try:
                result = od_processor.process_od_data(db_connection, request_params)
                
                if result["success"]:
                    # 复制文件和生成元数据
                    self._copy_template_files(request, case_dir)
                    metadata = self._create_case_metadata(request, case_id, result, case_dir)
                    MetadataManager.save_case_metadata(case_dir, metadata)
                    
                    return self._build_success_response(request, case_id, result, case_dir)
                else:
                    raise Exception(result.get("error", "OD数据处理失败"))
                    
            finally:
                if db_connection:
                    db_connection.close()
                    
        except Exception as e:
            raise Exception(f"OD数据处理失败: {str(e)}")
    
    def _infer_table_name(self, request: TimeRangeRequest) -> str:
        """推断数据库表名"""
        from datetime import datetime as _dt
        from shared.data_access.od_table_resolver import get_table_names_from_date
        
        inferred_table_name = request.table_name
        if not inferred_table_name:
            try:
                start_dt = _dt.strptime(request.start_time, "%Y/%m/%d %H:%M:%S")
                table_names = get_table_names_from_date(start_dt)
                inferred_table_name = table_names.get("od_table")
            except Exception:
                inferred_table_name = None
        
        if not inferred_table_name:
            raise Exception("未提供有效的表名，且自动推断失败。请在请求中设置 table_name 或检查时间格式以便自动推断。")
        
        return inferred_table_name
    
    def _build_od_request_params(self, request: TimeRangeRequest, table_name: str, case_dir: Path) -> Dict[str, Any]:
        """构建OD处理器的请求参数"""
        return {
            "start_time": request.start_time,
            "end_time": request.end_time,
            "interval_minutes": request.interval_minutes,
            "taz_file": request.taz_file,
            "net_file": request.net_file,
            "schemas_name": request.schemas_name,
            "table_name": table_name,
            "output_dir": str(case_dir / "config")
        }
    
    def _copy_template_files(self, request: TimeRangeRequest, case_dir: Path) -> None:
        """复制模板文件到案例目录"""
        try:
            if request.taz_file and os.path.exists(request.taz_file):
                taz_source = Path(request.taz_file)
                taz_dest = case_dir / "config" / taz_source.name
                self.copy_file_safe(taz_source, taz_dest)
        except Exception as e:
            print(f"复制TAZ文件失败: {e}")
    
    def _detect_version(self, name: str) -> str:
        """检测模板版本"""
        if not name:
            return "unknown"
        low = name.lower()
        if "taz_5" in low:
            return "TAZ_5"
        if "v6" in low:
            return "v6"
        if "v5" in low:
            return "v5"
        return "unknown"
    
    def _create_case_metadata(self, request: TimeRangeRequest, case_id: str, 
                             od_result: Dict[str, Any], case_dir: Path) -> Dict[str, Any]:
        """创建案例元数据"""
        taz_file_name = Path(request.taz_file).name if request.taz_file else None
        network_file_name = Path(request.net_file).name if request.net_file else None
        
        return {
            "case_id": case_id,
            "case_name": request.case_name or case_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "time_range": {"start": request.start_time, "end": request.end_time},
            "config": {
                "interval_minutes": request.interval_minutes,
                "schemas_name": request.schemas_name,
            },
            "templates": {
                "taz_version": self._detect_version(taz_file_name),
                "network_version": self._detect_version(network_file_name),
                "taz_file_name": taz_file_name,
                "network_file_name": network_file_name
            },
            "status": CaseStatus.PROCESSING.value,
            "description": request.description,
            "files": {
                "od_file": self.to_posix_rel(od_result.get("od_file")),
                "routes_file": self.to_posix_rel(od_result.get("route_file")),
                "taz_file": self.to_posix_rel(str((case_dir / "config" / Path(request.taz_file).name))) if request.taz_file else None,
                "network_file": self.to_posix_rel(request.net_file) if request.net_file else None
            },
            "statistics": {
                "total_records": od_result.get("total_records"),
                "od_pairs": od_result.get("od_pairs")
            },
            "last_step": "od_processed"
        }
    
    def _build_success_response(self, request: TimeRangeRequest, case_id: str, 
                              od_result: Dict[str, Any], case_dir: Path) -> Dict[str, Any]:
        """构建成功响应"""
        return {
            "start_time": request.start_time,
            "end_time": request.end_time,
            "interval_minutes": request.interval_minutes,
            "processed_at": datetime.now().isoformat(),
            "status": "completed",
            "case_id": case_id,
            "run_folder": (case_dir / "config").as_posix(),
            "od_file": self.to_posix_rel(od_result.get("od_file")),
            "route_file": self.to_posix_rel(od_result.get("route_file")),
            "total_records": od_result.get("total_records"),
            "od_pairs": od_result.get("od_pairs")
        }


# 创建服务实例
data_service = DataService()


# 导出服务函数 (保持向后兼容)
async def process_od_data_service(request: TimeRangeRequest) -> Dict[str, Any]:
    """OD数据处理服务函数"""
    return await data_service.process_od_data(request)
