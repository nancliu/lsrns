"""
案例管理服务 - 负责案例的CRUD操作和管理
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

from ..models import (
    CaseCreationRequest, CaseCloneRequest, CaseMetadata,
    CaseListResponse, CaseStatus, EventScenarioQuickCreateRequest
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
                # Phase 2: 案例来源类型映射
                # 如果metadata中有case_type字段，将其映射为source_type
                if 'case_type' in case_data and 'source_type' not in case_data:
                    case_data['source_type'] = case_data['case_type']

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

            # Phase 2: 案例来源类型映射
            # 如果metadata中有case_type字段，将其映射为source_type
            if 'case_type' in metadata and 'source_type' not in metadata:
                metadata['source_type'] = metadata['case_type']

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

    async def create_case_from_scenario(self, request: EventScenarioQuickCreateRequest) -> Dict[str, Any]:
        """
        从事件场景创建案例 (Task 1.3 - Week 1 Phase 2)

        创建 v2.0 元数据案例:
        - metadata_version: "2.0"
        - source_scenario 字段
        - immutable_fields 和 overridable_fields

        Design Decision Q4: 独立端点 (不修改现有 create_case)

        Args:
            request: 事件场景快速创建请求

        Returns:
            包含新创建案例的信息

        Note: 与 quick_create_case_from_event 不同,此方法创建 v2.0 元数据
        """
        try:
            # 生成案例ID
            case_id = request.case_id or self.generate_unique_id("case")

            # 创建案例目录结构
            case_dir = DirectoryManager.create_case_structure(case_id)

            # 创建标准子目录
            self._create_standard_directories(case_dir)

            # 创建 v2.0 元数据 (事件场景案例)
            metadata = self._create_v2_metadata_from_scenario(case_id, request)

            # 保存元数据
            MetadataManager.save_case_metadata(case_dir, metadata)

            logger.info(f"创建事件场景案例: {case_id}, 场景: {request.scenario_id}")

            return {
                "case_id": case_id,
                "case_dir": str(case_dir),
                "metadata": metadata,
                "metadata_version": "2.0"
            }

        except Exception as e:
            raise Exception(f"从场景创建案例失败: {str(e)}")

    def _create_v2_metadata_from_scenario(
        self,
        case_id: str,
        request: EventScenarioQuickCreateRequest
    ) -> Dict[str, Any]:
        """
        创建 v2.0 元数据 (事件场景案例)

        Args:
            case_id: 案例ID
            request: 事件场景请求

        Returns:
            v2.0 元数据字典

        Structure (design.md):
            - metadata_version: "2.0"
            - source_scenario: {...}
            - immutable_fields: {...}
            - overridable_fields: {...}
        """
        return {
            "metadata_version": "2.0",
            "case_id": case_id,
            "case_name": request.case_name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": CaseStatus.CREATED.value,

            # 源场景信息 (AD-12: 场景溯源)
            "source_scenario": {
                "scenario_id": request.scenario_id,
                "event_id": request.event_id,
                "event_type": request.event_type,
                "control_strategy_type": request.strategy,
                "description": f"事件 {request.event_id}, 策略 {request.strategy}"
            },

            # 不可变字段 (AD-8: 配置覆盖策略)
            "immutable_fields": {
                "event_id": request.event_id,
                "event_type": request.event_type,
                "control_strategy_type": request.strategy,
                # 位置和影响道路从场景元数据中提取 (TODO)
            },

            # 可覆盖字段 (AD-8)
            "overridable_fields": {
                "simulation_duration_hours": 2.5,  # 默认值
                "random_seed": None,  # 运行时分配
                "output_config": {
                    "generate_edgedata": True,
                    "generate_summary": True,
                    "generate_tripinfo": True,
                    "generate_vehroute": False
                }
            },

            # 案例配置
            "case_config": {
                "network_file": request.network_file,
                "od_file": request.od_file,
                "taz_file": request.taz_file
            },

            "description": request.description or f"从场景 {request.scenario_id} 创建",
            "statistics": {},
            "files": {}
        }

    async def quick_create_case_from_event(self, request: EventScenarioQuickCreateRequest) -> Dict[str, Any]:
        """
        从事件场景快速创建案例 (Phase 5.3.3)

        调用scripts中的QuickCaseCreator来创建case，包括：
        - 验证event scenario存在
        - 验证输入文件
        - 复制文件到case目录
        - 创建case metadata（记录event关联）

        Args:
            request: 包含event scenario和case输入文件信息

        Returns:
            包含新创建case的信息
        """
        try:
            # 动态导入QuickCaseCreator
            import sys
            from pathlib import Path
            scripts_path = Path(__file__).parent.parent.parent / "scripts"
            if str(scripts_path) not in sys.path:
                sys.path.insert(0, str(scripts_path))

            from initialize_scenario_library import QuickCaseCreator

            # 生成case_id（如果未提供）
            case_id = request.case_id or self.generate_unique_id("case_event")

            # 调用QuickCaseCreator创建case
            # project_root 默认为当前工作目录，case_dir 使用相对路径
            creator = QuickCaseCreator(
                project_root=None,  # 使用默认 Path.cwd()
                case_dir=self.cases_dir
            )

            result = creator.create_case_from_event(
                case_name=request.case_name,
                case_id=case_id,
                event_type=request.event_type,
                strategy=request.strategy,
                scenario_id=request.scenario_id,
                network_file=request.network_file,
                od_file=request.od_file,
                taz_file=request.taz_file,
                description=request.description or f"从事件场景 {request.scenario_id} 创建"
            )

            if not result.get('success'):
                raise Exception(result.get('error', '未知错误'))

            # 为事件场景案例添加源类型标记
            import json
            metadata_file = self.cases_dir / case_id / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    metadata['source_type'] = 'event_scenario'
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.warning(f"Failed to update metadata source_type: {e}")

            # 返回成功结果，包含OD文件元数据（用于异步生成）
            return {
                "case_id": case_id,
                "case_path": result.get('case_path'),
                "case_name": request.case_name,
                "event_scenario": {
                    "event_type": request.event_type,
                    "strategy": request.strategy,
                    "scenario_id": request.scenario_id
                },
                "od_file_metadata": result.get('od_file_metadata'),
                "od_file_status": result.get('od_file_metadata', {}).get('od_file_status'),
                "od_file_type": result.get('od_file_metadata', {}).get('od_file_type'),
                "created_at": datetime.now().isoformat(),
                "source_type": "event_scenario"
            }

        except Exception as e:
            raise Exception(f"从事件场景创建案例失败: {str(e)}")


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
