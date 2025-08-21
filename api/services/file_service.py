"""
文件管理服务 - 负责文件和目录的管理操作
"""

from datetime import datetime
from pathlib import Path
from typing import List

from ..models import FolderInfo
from .base_service import BaseService


class FileService(BaseService):
    """文件管理服务类"""
    
    async def get_folders(self, prefix: str) -> List[FolderInfo]:
        """获取指定前缀的文件夹列表"""
        try:
            folders = []
            base_dir = Path(".")
            
            # 查找匹配前缀的文件夹
            for item in base_dir.iterdir():
                if item.is_dir() and item.name.startswith(prefix):
                    folder_info = FolderInfo(
                        name=item.name,
                        path=str(item),
                        created_at=datetime.fromtimestamp(item.stat().st_ctime),
                        size=self._get_folder_size(item),
                        file_count=self._count_files(item)
                    )
                    folders.append(folder_info)
            
            return folders
            
        except Exception as e:
            raise Exception(f"获取文件夹列表失败: {str(e)}")
    
    def _get_folder_size(self, folder_path: Path) -> int:
        """获取文件夹大小（字节）"""
        total_size = 0
        try:
            for item in folder_path.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except:
            pass
        return total_size
    
    def _count_files(self, folder_path: Path) -> int:
        """统计文件夹中的文件数量"""
        file_count = 0
        try:
            for item in folder_path.rglob("*"):
                if item.is_file():
                    file_count += 1
        except:
            pass
        return file_count


# 创建服务实例
file_service = FileService()


# 导出服务函数 (保持向后兼容)
async def get_folders_service(prefix: str) -> List[FolderInfo]:
    """获取文件夹列表服务函数"""
    return await file_service.get_folders(prefix)
