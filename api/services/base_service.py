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
        """确保基础目录存在"""
        self.cases_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)
    
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
        """确保目录存在"""
        directory.mkdir(parents=True, exist_ok=True)


# 使用shared中的MetadataManager
MetadataManager = MetadataManager

# 使用shared中的DirectoryManager  
DirectoryManager = DirectoryManager
