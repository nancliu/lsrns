"""
案例管理服务 - 负责案例的CRUD操作和管理
"""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from ..models import (
    CaseCreationRequest, CaseCloneRequest, CaseMetadata, 
    CaseListResponse, CaseStatus
)
from .base_service import BaseService, MetadataManager, DirectoryManager


class CaseService(BaseService):
    """案例管理服务类"""
    
    async def create_case(self, request: CaseCreationRequest) -> Dict[str, Any]:
        """创建新案例"""
        try:
            # 生成案例ID
            case_id = self.generate_unique_id("case")
            
            # 创建案例目录结构
            case_dir = DirectoryManager.create_case_structure(case_id)
            
            # 创建标准子目录结构
            self._create_standard_directories(case_dir)
            
            # 创建元数据
            metadata = self._create_initial_metadata(case_id, request)
            
            # 保存元数据
            MetadataManager.save_case_metadata(case_dir, metadata)
            
            return {
                "case_id": case_id,
                "case_dir": str(case_dir),
                "metadata": metadata
            }
            
        except Exception as e:
            raise Exception(f"案例创建失败: {str(e)}")
    
    def _create_standard_directories(self, case_dir: Path) -> None:
        """创建标准的案例目录结构 - 调用shared层功能"""
        from shared.utilities.file_utils import DirectoryManager
        
        # 使用shared层的标准案例结构创建功能
        DirectoryManager.create_case_structure(case_dir.name)
    
    def _create_initial_metadata(self, case_id: str, request: CaseCreationRequest) -> Dict[str, Any]:
        """创建初始元数据"""
        return {
            "case_id": case_id,
            "case_name": request.case_name or case_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "time_range": request.time_range,
            "config": request.config,
            "status": CaseStatus.CREATED.value,
            "description": request.description,
            "statistics": {},
            "files": {}
        }
    
    async def list_cases(self, page: int = 1, page_size: int = 10, 
                        status: Optional[CaseStatus] = None, 
                        search: Optional[str] = None) -> CaseListResponse:
        """列出案例"""
        try:
            if not self.cases_dir.exists():
                return CaseListResponse(cases=[], total_count=0, page=page, page_size=page_size)
            
            # 获取所有案例目录
            case_dirs = [d for d in self.cases_dir.iterdir() 
                        if d.is_dir() and d.name.startswith("case_")]
            
            # 加载并过滤案例
            filtered_cases = []
            for case_dir in case_dirs:
                try:
                    metadata = MetadataManager.load_case_metadata(case_dir)
                    
                    # 状态过滤
                    if status and metadata.get("status") != status.value:
                        continue
                    
                    # 搜索过滤
                    if search and not self._matches_search(metadata, search):
                        continue
                    
                    filtered_cases.append(metadata)
                    
                except Exception:
                    continue  # 跳过无效的案例
            
            # 排序
            filtered_cases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            # 分页
            total_count = len(filtered_cases)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            page_cases = filtered_cases[start_idx:end_idx]
            
            # 转换为CaseMetadata对象
            case_metadata_list = []
            for case_data in page_cases:
                case_metadata = CaseMetadata(**case_data)
                case_metadata_list.append(case_metadata)
            
            return CaseListResponse(
                cases=case_metadata_list,
                total_count=total_count,
                page=page,
                page_size=page_size
            )
            
        except Exception as e:
            raise Exception(f"获取案例列表失败: {str(e)}")
    
    def _matches_search(self, metadata: Dict[str, Any], search: str) -> bool:
        """检查案例是否匹配搜索条件"""
        search_lower = search.lower()
        case_name = metadata.get("case_name", "").lower()
        description = metadata.get("description", "").lower()
        return search_lower in case_name or search_lower in description
    
    async def get_case(self, case_id: str) -> CaseMetadata:
        """获取案例详情"""
        try:
            case_dir = self.cases_dir / case_id
            if not case_dir.exists():
                raise Exception(f"案例 {case_id} 不存在")
            
            metadata = MetadataManager.load_case_metadata(case_dir)
            return CaseMetadata(**metadata)
            
        except Exception as e:
            raise Exception(f"获取案例详情失败: {str(e)}")
    
    async def delete_case(self, case_id: str) -> Dict[str, Any]:
        """删除案例"""
        try:
            case_dir = self.cases_dir / case_id
            
            if not case_dir.exists():
                raise Exception(f"案例 {case_id} 不存在")
            
            # 删除案例目录
            shutil.rmtree(case_dir)
            
            return {
                "case_id": case_id,
                "deleted_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"删除案例失败: {str(e)}")
    
    async def clone_case(self, case_id: str, request: CaseCloneRequest) -> Dict[str, Any]:
        """克隆案例"""
        try:
            source_case_dir = self.cases_dir / case_id
            if not source_case_dir.exists():
                raise Exception(f"源案例 {case_id} 不存在")
            
            # 生成新案例ID
            new_case_id = self.generate_unique_id("case")
            new_case_dir = self.cases_dir / new_case_id
            
            # 复制案例目录
            shutil.copytree(source_case_dir, new_case_dir)
            
            # 更新元数据
            self._update_cloned_metadata(new_case_dir, new_case_id, case_id, request)
            
            return {
                "original_case_id": case_id,
                "new_case_id": new_case_id,
                "new_case_dir": str(new_case_dir),
                "cloned_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"克隆案例失败: {str(e)}")
    
    def _update_cloned_metadata(self, new_case_dir: Path, new_case_id: str, 
                               original_case_id: str, request: CaseCloneRequest) -> None:
        """更新克隆案例的元数据"""
        try:
            metadata = MetadataManager.load_case_metadata(new_case_dir)
            
            # 获取原案例名称
            original_name = metadata.get('case_name', original_case_id)
            
            metadata.update({
                "case_id": new_case_id,
                "case_name": request.new_case_name or f"{original_name}_copy",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "description": request.new_description or f"克隆自 {original_case_id}",
                "status": CaseStatus.CREATED.value
            })
            
            MetadataManager.save_case_metadata(new_case_dir, metadata)
            
        except Exception as e:
            print(f"更新克隆案例元数据失败: {e}")


# 创建服务实例
case_service = CaseService()


# 导出服务函数 (保持向后兼容)
async def create_case_service(request: CaseCreationRequest) -> Dict[str, Any]:
    """案例创建服务函数"""
    return await case_service.create_case(request)


async def list_cases_service(page: int = 1, page_size: int = 10,
                           status: Optional[CaseStatus] = None,
                           search: Optional[str] = None) -> CaseListResponse:
    """案例列表服务函数"""
    return await case_service.list_cases(page, page_size, status, search)


async def get_case_service(case_id: str) -> CaseMetadata:
    """获取案例详情服务函数"""
    return await case_service.get_case(case_id)


async def delete_case_service(case_id: str) -> Dict[str, Any]:
    """删除案例服务函数"""
    return await case_service.delete_case(case_id)


async def clone_case_service(case_id: str, request: CaseCloneRequest) -> Dict[str, Any]:
    """克隆案例服务函数"""
    return await case_service.clone_case(case_id, request)
