"""
场景管理服务 - 负责事件场景的查询和从场景创建案例 (Phase 5.3.3)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..models import (
    ScenarioInfo, ScenarioListResponse, CaseFromScenarioResponse,
    EventScenarioQuickCreateRequest, ScenarioListQueryRequest,
    ScenarioAnalysisRequest, AnalysisResult
)
from .base_service import BaseService, MetadataManager, DirectoryManager

logger = logging.getLogger(__name__)


class ScenarioService(BaseService):
    """场景管理服务类 - 处理事件场景到案例的映射"""

    def __init__(self):
        """初始化场景服务"""
        super().__init__()
        self.scenarios_dir = Path("output/scenarios")
        self.scenario_index_path = self.scenarios_dir / "scenario_index.json"
        self._scenario_index_cache: Optional[Dict[str, Any]] = None

    def _load_scenario_index(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        加载场景索引JSON

        Args:
            force_reload: 是否强制重新加载

        Returns:
            场景索引数据
        """
        if not force_reload and self._scenario_index_cache:
            return self._scenario_index_cache

        try:
            if not self.scenario_index_path.exists():
                logger.error(f"Scenario index not found: {self.scenario_index_path}")
                return {"scenarios": [], "metadata": {}}

            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                self._scenario_index_cache = json.load(f)
                logger.info(f"Loaded scenario index with {len(self._scenario_index_cache.get('scenarios', []))} scenarios")
                return self._scenario_index_cache
        except Exception as e:
            logger.error(f"Failed to load scenario index: {str(e)}")
            return {"scenarios": [], "metadata": {}}

    async def list_scenarios(self, query: ScenarioListQueryRequest) -> ScenarioListResponse:
        """
        列出场景，支持过滤和分页

        Args:
            query: 查询请求

        Returns:
            场景列表响应
        """
        index_data = self._load_scenario_index()
        scenarios = index_data.get("scenarios", [])

        # 应用过滤条件
        filtered_scenarios = scenarios

        if query.event_type:
            filtered_scenarios = [s for s in filtered_scenarios if s.get("event_type") == query.event_type]

        if query.strategy:
            filtered_scenarios = [s for s in filtered_scenarios if s.get("strategy") == query.strategy]

        if query.event_id:
            filtered_scenarios = [s for s in filtered_scenarios if s.get("event_id") == query.event_id]

        # 分页
        total_count = len(filtered_scenarios)
        start_idx = (query.page - 1) * query.page_size
        end_idx = start_idx + query.page_size
        paginated_scenarios = filtered_scenarios[start_idx:end_idx]

        # 转换为ScenarioInfo对象
        scenario_infos = [
            ScenarioInfo(
                scenario_id=s.get("files", {}).get("scenario_dir") or s.get("scenario_id", ""),
                event_id=s.get("event_id", ""),
                event_type=s.get("event_type", ""),
                strategy=s.get("strategy", ""),
                location=s.get("location"),
                time=s.get("time")
            )
            for s in paginated_scenarios
        ]

        total_pages = (total_count + query.page_size - 1) // query.page_size

        return ScenarioListResponse(
            scenarios=scenario_infos,
            total_count=total_count,
            page=query.page,
            page_size=query.page_size,
            total_pages=total_pages
        )

    async def get_scenario(self, event_id: str, strategy: str) -> Optional[Dict[str, Any]]:
        """
        查询单个场景

        Args:
            event_id: 事件ID
            strategy: 控制策略

        Returns:
            场景数据或None
        """
        index_data = self._load_scenario_index()
        scenarios = index_data.get("scenarios", [])

        for scenario in scenarios:
            if scenario.get("event_id") == event_id and scenario.get("strategy") == strategy:
                return scenario

        return None

    async def get_scenario_files(self, scenario_dir: str) -> Dict[str, Path]:
        """
        获取场景的所有配置文件

        Args:
            scenario_dir: 场景目录名 (e.g., 'scenario_12547_vss')

        Returns:
            文件路径字典
        """
        files = {}

        # 在output/scenarios中查找目录
        for event_type_dir in self.scenarios_dir.iterdir():
            if not event_type_dir.is_dir():
                continue

            scenario_path = event_type_dir / scenario_dir
            if scenario_path.exists():
                # 查找.add.xml文件
                add_xml_files = list(scenario_path.glob("*.add.xml"))
                if add_xml_files:
                    files["add_xml"] = add_xml_files[0]

                # 查找JSON配置文件
                event_desc = scenario_path / "event_description.json"
                if event_desc.exists():
                    files["event_description"] = event_desc

                traffic_config = scenario_path / "traffic_input_config.json"
                if traffic_config.exists():
                    files["traffic_input_config"] = traffic_config

                control_config = scenario_path / "control_strategy_config.json"
                if control_config.exists():
                    files["control_strategy_config"] = control_config

                return files

        logger.warning(f"Scenario directory not found: {scenario_dir}")
        return files

    async def create_case_from_scenario(self, request: EventScenarioQuickCreateRequest) -> CaseFromScenarioResponse:
        """
        从事件场景创建案例 (Phase 5.3.3核心方法)

        按照AD-7 (1:1 Case-Scenario Binding)实施:
        - 为每个场景变量创建独立的案例
        - 保存source_scenario_id到案例元数据
        - 强制执行不可变字段 (AD-8)

        Args:
            request: 案例创建请求

        Returns:
            创建的案例信息
        """
        try:
            # 生成案例ID
            case_id = request.case_id or self.generate_unique_id("case")

            # 创建案例目录结构
            case_dir = DirectoryManager.create_case_structure(case_id)

            # 获取场景文件
            scenario_files = await self.get_scenario_files(request.scenario_id)

            if not scenario_files:
                raise ValueError(f"Scenario files not found for {request.scenario_id}")

            # 加载事件描述
            event_desc = {}
            if "event_description" in scenario_files:
                with open(scenario_files["event_description"], 'r', encoding='utf-8') as f:
                    event_desc = json.load(f)

            # 加载控制策略配置
            control_config = {}
            if "control_strategy_config" in scenario_files:
                with open(scenario_files["control_strategy_config"], 'r', encoding='utf-8') as f:
                    control_config = json.load(f)

            # 加载流量输入配置
            traffic_config = {}
            if "traffic_input_config" in scenario_files:
                with open(scenario_files["traffic_input_config"], 'r', encoding='utf-8') as f:
                    traffic_config = json.load(f)

            # 构建案例元数据 - 按照AD-7和AD-8强制策略
            metadata = {
                "case_id": case_id,
                "case_name": request.case_name,
                "case_type": "event_scenario",  # 标记为事件场景案例
                "source_scenario_id": request.scenario_id,  # AD-7: 1:1绑定
                "source_event_id": request.event_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "description": request.description or f"Case from scenario {request.scenario_id}",
                "status": "created",

                # AD-8: 不可变字段 (从场景锁定)
                "immutable_fields": {
                    "event_id": request.event_id,
                    "event_type": request.event_type,
                    "strategy": request.strategy,
                    "location": event_desc.get("location", {}),
                    "affected_edges": event_desc.get("impact", {}).get("affected_edges", []),
                    "control_strategy_type": control_config.get("strategy_type", request.strategy)
                },

                # AD-8: 可覆盖字段
                "overridable_fields": {
                    "simulation_duration_hours": traffic_config.get("od_time_range", {}).get("duration_hours", 2.5),
                    "random_seed": None,
                    "output_config": {
                        "generate_edgedata": True,  # AD-8: 强制启用 (必需)
                        "generate_summary": True,
                        "generate_tripinfo": True,
                        "generate_vehroute": False
                    }
                },

                # 案例配置
                "config": {
                    "network_file": request.network_file,
                    "od_file": request.od_file,
                    "taz_file": request.taz_file,
                },

                # 流量和事件配置
                "traffic_config": traffic_config,
                "event_config": event_desc,
                "control_config": control_config,

                # 统计和文件信息
                "statistics": {},
                "files": {
                    "scenario_add_xml": str(scenario_files.get("add_xml", "")),
                    "event_description": str(scenario_files.get("event_description", "")),
                    "traffic_input_config": str(scenario_files.get("traffic_input_config", "")),
                    "control_strategy_config": str(scenario_files.get("control_strategy_config", ""))
                }
            }

            # 保存元数据
            MetadataManager.save_case_metadata(case_dir, metadata)

            logger.info(f"Created case {case_id} from scenario {request.scenario_id}")

            return CaseFromScenarioResponse(
                case_id=case_id,
                case_name=request.case_name,
                source_scenario_id=request.scenario_id,
                source_event_id=request.event_id,
                created_at=datetime.now(),
                case_dir=str(case_dir),
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Failed to create case from scenario: {str(e)}")
            raise

    async def validate_scenario_exists(self, scenario_id: str) -> bool:
        """
        验证场景是否存在

        Args:
            scenario_id: 场景ID

        Returns:
            场景是否存在
        """
        index_data = self._load_scenario_index()
        scenarios = index_data.get("scenarios", [])

        return any(s.get("scenario_id") == scenario_id or
                   s.get("files", {}).get("scenario_dir") == scenario_id
                   for s in scenarios)

    async def get_event_scenarios(self, event_id: str) -> List[ScenarioInfo]:
        """
        获取特定事件的所有场景变量

        Args:
            event_id: 事件ID

        Returns:
            该事件的所有场景变量列表
        """
        index_data = self._load_scenario_index()
        scenarios = index_data.get("scenarios", [])

        event_scenarios = [
            ScenarioInfo(
                scenario_id=s.get("files", {}).get("scenario_dir") or s.get("scenario_id", ""),
                event_id=s.get("event_id", ""),
                event_type=s.get("event_type", ""),
                strategy=s.get("strategy", ""),
                location=s.get("location"),
                time=s.get("time")
            )
            for s in scenarios if s.get("event_id") == event_id
        ]

        return event_scenarios

    async def run_analysis(self, request: ScenarioAnalysisRequest) -> AnalysisResult:
        """
        启动场景分析 (Phase 5.3.3)

        简化实现：接受分析请求，生成分析ID，创建分析目录
        具体的EdgeData/TripInfo分析逻辑在专门的分析服务中实现

        基于批量仿真第二层结果分析（EdgeData分析）设计：
        - EdgeData作为主要分析方式（必选）
        - TripInfo作为可选补充分析
        - 支持与无控制策略场景对比

        Args:
            request: 分析请求，包含:
              - case_id: 案例ID
              - scenario_id: 场景ID
              - event_id: 事件ID
              - compare_no_control: 是否与无控制策略比较
              - analysis_focus: 分析焦点 {edgedata, tripinfo}

        Returns:
            AnalysisResult: 分析结果，包含分析ID和状态
        """
        try:
            analysis_id = self.generate_unique_id("analysis")

            # 验证案例目录存在
            case_dir = Path(f"cases/{request.case_id}")
            if not case_dir.exists():
                logger.warning(f"Case directory not found: {case_dir}, will create during analysis")

            # 创建分析结果目录
            analysis_dir = case_dir / "analysis"
            analysis_dir.mkdir(parents=True, exist_ok=True)

            # 记录分析请求元数据
            analysis_metadata = {
                "analysis_id": analysis_id,
                "case_id": request.case_id,
                "scenario_id": request.scenario_id,
                "event_id": request.event_id,
                "created_at": datetime.now().isoformat(),
                "status": "initiated",
                "analysis_config": {
                    "compare_no_control": request.compare_no_control,
                    "analysis_focus": request.analysis_focus,
                    "edgedata_enabled": request.analysis_focus.get("edgedata", True),
                    "tripinfo_enabled": request.analysis_focus.get("tripinfo", False)
                }
            }

            # 保存分析元数据
            analysis_metadata_file = analysis_dir / "analysis_request.json"
            with open(analysis_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Analysis {analysis_id} initiated for case {request.case_id}, "
                       f"will focus on {'edgedata' if request.analysis_focus.get('edgedata') else 'tripinfo'}")

            # 返回分析结果
            return AnalysisResult(
                analysis_id=analysis_id,
                case_id=request.case_id,
                status="initiated",
                analysis_type="edgedata" if request.analysis_focus.get("edgedata") else "tripinfo",
                started_at=datetime.now(),
                result_path=str(analysis_dir),
                message="分析已初始化（EdgeData 为主要分析方式，TripInfo 为可选）"
            )

        except Exception as e:
            logger.error(f"Failed to initiate analysis: {str(e)}")
            raise
