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
from shared.utilities.scenario_case_mapping import ScenarioCaseMapper


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
        从事件场景快速创建案例并生成OD文件 (Phase 5.3.3)

        工作流：
        1. 调用QuickCaseCreator创建case结构和元数据
        2. 如果OD文件是数据库表参考，立即启动OD生成（非阻塞）
        3. 更新case状态为"od_generating"
        4. 返回case信息和OD生成状态

        Args:
            request: 包含event scenario和case输入文件信息

        Returns:
            包含新创建case的信息和OD生成状态
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

            # 为事件场景案例添加源类型标记和初始状态
            import json
            case_path = Path(result.get('case_path'))
            metadata_file = case_path / "metadata.json"
            od_generation_started = False

            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    metadata['source_type'] = 'event_scenario'

                    # 如果OD文件是待生成状态，标记为od_generating
                    od_file_metadata = result.get('od_file_metadata', {})
                    if od_file_metadata.get('od_file_status') == 'pending' and \
                       od_file_metadata.get('od_file_type') == 'database':
                        metadata['status'] = 'od_generating'
                        logger.info(f"Case {case_id} marked as od_generating")

                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                except Exception as e:
                    logger.warning(f"Failed to update metadata source_type: {e}")

            # 如果OD文件是数据库表参考，立即启动OD生成（后台，非阻塞）
            od_file_metadata = result.get('od_file_metadata', {})
            if od_file_metadata.get('od_file_status') == 'pending' and \
               od_file_metadata.get('od_file_type') == 'database':
                # 启动OD生成任务（后台处理）
                od_generation_started = await self._start_od_generation_async(
                    case_id=case_id,
                    case_path=case_path,
                    od_file_info=od_file_metadata,
                    od_file_info_json=case_path / "config" / "od_file_info.json"
                )
                logger.info(f"OD generation task started for case {case_id}: {od_generation_started}")

            # 注册案例创建到场景元数据 (AD-12: 三层元数据追踪)
            # 在scenario_index.json中添加案例记录，建立scenario->case链接
            case_status_for_mapping = metadata.get('status', 'created') if 'metadata' in locals() else 'created'
            try:
                mapper = ScenarioCaseMapper()
                mapper.register_case_creation(
                    scenario_id=request.scenario_id,  # e.g., "scenario_10754_no_control"
                    case_id=case_id,
                    case_name=request.case_name,
                    case_status=case_status_for_mapping
                )
                logger.info(f"Registered case {case_id} in scenario {request.scenario_id}")
            except Exception as e:
                logger.warning(f"Failed to register case in scenario index: {e}")
                # 继续执行，不中断case创建流程

            # 返回成功结果，包含OD文件生成状态
            return {
                "case_id": case_id,
                "case_path": str(case_path),
                "case_name": request.case_name,
                "event_scenario": {
                    "event_type": request.event_type,
                    "strategy": request.strategy,
                    "scenario_id": request.scenario_id
                },
                "od_file_metadata": od_file_metadata,
                "od_file_status": od_file_metadata.get('od_file_status'),
                "od_file_type": od_file_metadata.get('od_file_type'),
                "od_generation_started": od_generation_started,
                "created_at": datetime.now().isoformat(),
                "source_type": "event_scenario",
                "case_status": case_status_for_mapping
            }

        except Exception as e:
            raise Exception(f"从事件场景创建案例失败: {str(e)}")

    async def _start_od_generation_async(
        self,
        case_id: str,
        case_path: Path,
        od_file_info: Dict[str, Any],
        od_file_info_json: Path
    ) -> bool:
        """
        启动异步OD文件生成任务（后台执行，不阻塞）

        Args:
            case_id: 案例ID
            case_path: 案例路径
            od_file_info: OD文件元数据
            od_file_info_json: OD文件信息JSON路径

        Returns:
            是否成功启动生成任务
        """
        try:
            # 从od_file_info.json读取时间范围
            import json
            if od_file_info_json.exists():
                with open(od_file_info_json, 'r', encoding='utf-8') as f:
                    od_info = json.load(f)
                    time_range = od_info.get('time_range', {})
            else:
                logger.warning(f"od_file_info.json not found: {od_file_info_json}")
                return False

            # 准备OD生成请求参数
            from ..models.requests.data_requests import TimeRangeRequest

            start_time = time_range.get('start_time')
            end_time = time_range.get('end_time')
            od_file_ref = od_file_info.get('od_file')

            if not (start_time and end_time and od_file_ref):
                logger.warning(f"Missing time range info for OD generation: {time_range}")
                return False

            # 解析schema.table格式（前端发送格式: dwd.dwd_od_weekly）
            if '.' in od_file_ref:
                schema_name, table_name = od_file_ref.split('.', 1)
            else:
                # 如果没有点，假设是dwd schema
                schema_name = "dwd"
                table_name = od_file_ref

            # 创建OD处理请求（为事件场景提供默认TAZ文件）
            od_request = TimeRangeRequest(
                start_time=start_time,
                end_time=end_time,
                table_name=table_name,
                schemas_name=schema_name,
                net_file=None,
                taz_file="templates/taz_files/TAZ_6.add.xml",  # 使用默认TAZ文件
                interval_minutes=5  # 使用默认5分钟间隔（而不是30分钟）
            )

            # 在后台线程启动OD生成（不阻塞）
            import threading
            od_generation_thread = threading.Thread(
                target=self._run_od_generation_in_background,
                args=(case_id, case_path, od_request, od_file_info_json),
                daemon=True
            )
            od_generation_thread.start()

            logger.info(f"OD generation thread started for case {case_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to start OD generation: {e}")
            return False

    def _run_od_generation_in_background(
        self,
        case_id: str,
        case_path: Path,
        od_request,
        od_file_info_json: Path
    ) -> None:
        """
        在后台线程中运行OD生成（非阻塞）

        直接调用ODProcessor而不是data_service，以确保文件生成在正确的case文件夹中

        Args:
            case_id: 案例ID
            case_path: 案例路径
            od_request: OD处理请求
            od_file_info_json: OD文件信息JSON路径
        """
        try:
            import json
            from pathlib import Path
            from shared.data_processors.od_processor import ODProcessor
            from shared.data_access.connection import open_db_connection

            logger.info(f"Starting OD generation for case {case_id}...")

            # 复制TAZ文件到case配置目录
            if od_request.taz_file:
                try:
                    taz_source = Path(od_request.taz_file)
                    if taz_source.exists():
                        taz_dest = case_path / "config" / taz_source.name
                        # 确保目标目录存在
                        taz_dest.parent.mkdir(parents=True, exist_ok=True)
                        # 复制文件
                        import shutil
                        shutil.copy2(str(taz_source), str(taz_dest))
                        logger.info(f"✓ TAZ file copied: {taz_source.name} → {taz_dest}")
                    else:
                        logger.warning(f"TAZ file not found: {taz_source}")
                except Exception as e:
                    logger.error(f"Failed to copy TAZ file: {e}")

            # 验证车型模板
            vehicle_template_path = "templates/config_templates/vehicle_templates/vehicle_types.json"

            # 创建OD处理器
            od_processor = ODProcessor(vehicle_config_path=vehicle_template_path)

            # 构建处理参数（关键：指定output_dir为case的config目录）
            output_dir = str(case_path / "config")
            request_params = {
                "start_time": od_request.start_time,
                "end_time": od_request.end_time,
                "interval_minutes": od_request.interval_minutes,
                "taz_file": od_request.taz_file,
                "net_file": od_request.net_file,
                "schemas_name": od_request.schemas_name,
                "table_name": od_request.table_name,
                "output_dir": output_dir  # 🔑 确保文件输出到正确的case文件夹
            }

            # 获取数据库连接
            db_connection = open_db_connection()
            try:
                # 调用OD处理器处理数据
                result = od_processor.process_od_data(db_connection, request_params)

                if result.get('success'):
                    # 更新od_file_info.json状态为已生成
                    if od_file_info_json.exists():
                        with open(od_file_info_json, 'r', encoding='utf-8') as f:
                            od_info = json.load(f)

                        od_info['od_file_status'] = 'exists'
                        od_info['generated_at'] = datetime.now().isoformat()
                        od_info['od_file'] = result.get('od_file', od_info.get('od_file'))

                        with open(od_file_info_json, 'w', encoding='utf-8') as f:
                            json.dump(od_info, f, indent=2, ensure_ascii=False)

                        logger.info(f"✓ OD file generated for case {case_id}: {od_info['od_file']}")

                    # 更新case元数据状态为created（完成OD生成）
                    metadata_file = case_path / "metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                        if metadata.get('status') == 'od_generating':
                            metadata['status'] = 'created'
                            metadata['od_generated_at'] = datetime.now().isoformat()

                        with open(metadata_file, 'w', encoding='utf-8') as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=2)

                        logger.info(f"✓ Case {case_id} status updated to created after OD generation")
                else:
                    raise Exception(result.get("error", "OD data processing failed"))

            finally:
                if db_connection:
                    db_connection.close()

        except Exception as e:
            logger.error(f"Error in OD generation thread for case {case_id}: {e}", exc_info=True)

            # 更新失败状态到metadata.json
            try:
                metadata_file = case_path / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    if metadata.get('status') == 'od_generating':
                        metadata['status'] = 'od_generation_failed'
                        metadata['od_generation_error'] = str(e)
                        metadata['failed_at'] = datetime.now().isoformat()

                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    logger.info(f"✓ Case {case_id} status updated to od_generation_failed after exception")
            except Exception as meta_error:
                logger.error(f"Failed to update metadata after OD generation error: {meta_error}")

    async def create_case_with_simulation(self, request: "CreateCaseWithSimulationRequest") -> Dict[str, Any]:
        """
        统一案例+仿真创建 (Unified case+simulation creation)

        在一次原子操作中创建案例并立即准备仿真：
        1. 创建案例目录和元数据
        2. 处理OD数据（异步，非阻塞）
        3. 复制TAZ文件
        4. 生成sumocfg配置
        5. 创建仿真元数据（带source_scenario）
        6. 注册到场景索引
        7. 更新案例状态为ready_to_simulate

        这确保了案例-场景-仿真的完整元数据链接在创建时就建立，
        而不是在用户点击"仿真"按钮时才创建。

        Args:
            request: CreateCaseWithSimulationRequest - 包含场景信息、案例参数和仿真配置

        Returns:
            dict with keys: case_id, simulation_id, case_status, simulation_status, files_created
        """
        try:
            # Step 1: 生成ID
            case_id = self.generate_unique_id("case")
            simulation_id = self.generate_unique_id("simulation")
            case_name = request.case_name or f"case_{request.scenario_id}_{case_id.split('_')[-1]}"

            # Step 2: 调用existing方法快速创建案例（复用现有流程）
            from ..models.requests.case_requests import EventScenarioQuickCreateRequest
            quick_create_request = EventScenarioQuickCreateRequest(
                case_name=case_name,
                case_id=case_id,
                event_type=request.event_type,
                strategy=request.strategy,
                scenario_id=request.scenario_id,
                event_id=request.event_id,
                network_file=request.network_file,
                od_file=request.od_file,
                taz_file=request.taz_file,
                description=request.description
            )

            result = await self.quick_create_case_from_event(quick_create_request)
            if not result.get('success'):
                raise Exception(result.get('error', '案例创建失败'))

            case_path = Path(result.get('case_path'))

            # Step 3: 准备仿真（生成仿真元数据和sumocfg）
            await self._prepare_simulation_for_case(
                case_id=case_id,
                simulation_id=simulation_id,
                case_path=case_path,
                request=request
            )

            # Step 4: 更新案例元数据状态为ready_to_simulate
            metadata_file = case_path / "metadata.json"
            if metadata_file.exists():
                try:
                    import json
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    metadata['status'] = 'ready_to_simulate'
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    logger.info(f"Case {case_id} status updated to ready_to_simulate")
                except Exception as e:
                    logger.warning(f"Failed to update case metadata status: {e}")

            return {
                "success": True,
                "case_id": case_id,
                "simulation_id": simulation_id,
                "case_status": "ready_to_simulate",
                "simulation_status": "pending",
                "message": "统一案例+仿真创建成功，仿真已准备就绪",
                "files_created": {
                    "case_metadata": str(metadata_file),
                    "simulation_metadata": str(case_path / "simulations" / simulation_id / "simulation_metadata.json"),
                    "sumocfg": str(case_path / "simulations" / simulation_id / "simulation.sumocfg")
                }
            }

        except Exception as e:
            logger.error(f"Failed to create case with simulation: {str(e)}")
            raise Exception(f"统一创建失败: {str(e)}")

    async def _prepare_simulation_for_case(self, case_id: str, simulation_id: str, case_path: Path, request: "CreateCaseWithSimulationRequest") -> None:
        """
        准备仿真：生成sumocfg和仿真元数据

        Args:
            case_id: 案例ID
            simulation_id: 仿真ID
            case_path: 案例目录路径
            request: CreateCaseWithSimulationRequest - 包含仿真配置
        """
        try:
            from shared.utilities.sumo_utils import generate_sumocfg_for_simulation
            import json

            # 创建仿真目录
            sim_dir = case_path / "simulations" / simulation_id
            sim_dir.mkdir(parents=True, exist_ok=True)

            # 生成sumocfg
            config_dir = case_path / "config"
            sumocfg_file = sim_dir / "simulation.sumocfg"

            # 构建仿真参数
            sim_params = {
                "duration_hours": request.simulation_duration_hours,
                "random_seed": request.random_seed,
                "simulation_type": request.simulation_type,
                "output_config": request.output_config
            }

            # 调用sumo工具生成sumocfg
            generate_sumocfg_for_simulation(
                case_dir=str(case_path),
                sim_id=simulation_id,
                duration_hours=request.simulation_duration_hours,
                random_seed=request.random_seed,
                simulation_type=request.simulation_type,
                output_config=request.output_config
            )

            # 创建仿真元数据
            case_metadata_file = case_path / "metadata.json"
            case_metadata = {}
            if case_metadata_file.exists():
                with open(case_metadata_file, 'r', encoding='utf-8') as f:
                    case_metadata = json.load(f)

            sim_metadata = {
                "metadata_version": "2.0",
                "simulation_id": simulation_id,
                "case_id": case_id,
                "status": "pending",
                "created_at": datetime.now().isoformat(),

                # AD-12: 三层元数据追踪 - 保持source_scenario
                "source_scenario": {
                    "scenario_id": request.scenario_id,
                    "event_id": request.event_id,
                    "event_type": request.event_type,
                    "control_strategy_type": request.strategy
                },

                "simulation_params": sim_params
            }

            # 保存仿真元数据
            sim_metadata_file = sim_dir / "simulation_metadata.json"
            with open(sim_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(sim_metadata, f, ensure_ascii=False, indent=2)

            logger.info(f"✓ Simulation metadata created: {sim_metadata_file}")

        except Exception as e:
            logger.error(f"Failed to prepare simulation: {str(e)}")
            raise


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
