"""
基础服务类 - 提供所有服务的公共功能
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 导入shared中的功能
from shared.utilities.file_utils import (
    load_metadata, save_metadata, update_timestamp, copy_file_safe,
    MetadataManager, DirectoryManager
)
from shared.data_access.connection import open_db_connection

class BaseService:
    """基础服务类 - 提供通用功能"""
    
    def __init__(self):
        """初始化基础服务"""
        self.cases_dir = Path("cases")
        self.templates_dir = Path("templates")
        self._ensure_base_directories()
    
    def _ensure_base_directories(self):
        """确保基础目录存在 - 调用shared层功能"""
        from shared.utilities.file_utils import ensure_directory
        ensure_directory(self.cases_dir)
        ensure_directory(self.templates_dir)
    
    def load_metadata(self, file_path: Path) -> Dict[str, Any]:
        """加载JSON元数据文件"""
        return load_metadata(file_path)
    
    def save_metadata(self, file_path: Path, metadata: Dict[str, Any]) -> None:
        """保存JSON元数据文件"""
        save_metadata(file_path, metadata)
    
    def update_timestamp(self, metadata: Dict[str, Any]) -> None:
        """更新元数据的时间戳"""
        update_timestamp(metadata)
    
    def generate_unique_id(self, prefix: str = "item") -> str:
        """生成唯一ID"""
        return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def to_posix_rel(self, path_str: str) -> str:
        """转换为相对于项目根目录的POSIX相对路径"""
        if not path_str:
            return path_str
        try:
            abs_p = Path(path_str).resolve()
            rel = abs_p.relative_to(Path.cwd())
            return rel.as_posix()
        except Exception:
            try:
                return Path(path_str).relative_to(Path.cwd()).as_posix()
            except Exception:
                return Path(path_str).as_posix()
    
    def copy_file_safe(self, source: Path, destination: Path) -> bool:
        """安全复制文件"""
        return copy_file_safe(source, destination)
    
    def get_db_connection(self):
        """获取数据库连接（使用shared统一实现）"""
        return open_db_connection()

    def ensure_directory(self, directory: Path) -> None:
        """确保目录存在 - 调用shared层功能"""
        from shared.utilities.file_utils import ensure_directory
        ensure_directory(directory)

    # ===== Metadata Version Support (Task 1.0 - Week 1 Phase 2) =====

    def detect_metadata_version(self, metadata: Dict[str, Any]) -> str:
        """
        检测元数据版本以支持向后兼容性

        Args:
            metadata: 案例或仿真元数据字典

        Returns:
            "1.0" (现有OD案例，隐式) 或 "2.0" (事件场景案例，显式)

        Design Decision Q5, Q6, Q7:
            - Version 1.0: 无 metadata_version 字段 (隐式)
            - Version 2.0: 有 metadata_version 字段 (显式)
            - 向后兼容: v1.0 案例继续正常工作
        """
        if "metadata_version" in metadata:
            return metadata["metadata_version"]
        return "1.0"  # 默认为现有案例

    def is_event_scenario_case(self, metadata: Dict[str, Any]) -> bool:
        """
        检查是否为事件场景案例

        Args:
            metadata: 案例元数据字典

        Returns:
            True 如果是事件场景案例 (v2.0, 有 source_scenario 字段)
            False 如果是传统OD案例 (v1.0)

        Implementation:
            - 空安全处理 source_scenario 字段
            - 不破坏现有工作流
        """
        version = self.detect_metadata_version(metadata)
        if version == "2.0":
            return "source_scenario" in metadata and metadata["source_scenario"] is not None
        return False

    def get_source_scenario_id(self, metadata: Dict[str, Any]) -> str | None:
        """
        获取源场景ID（如果存在）

        Args:
            metadata: 案例或仿真元数据

        Returns:
            scenario_id 字符串，如果不是事件场景案例则返回 None

        Safety:
            - 空安全，不会抛出异常
            - 兼容 v1.0 元数据
        """
        if not self.is_event_scenario_case(metadata):
            return None

        source_scenario = metadata.get("source_scenario", {})
        if isinstance(source_scenario, dict):
            return source_scenario.get("scenario_id")
        return None


# 使用shared中的MetadataManager
MetadataManager = MetadataManager

# 使用shared中的DirectoryManager  
DirectoryManager = DirectoryManager
