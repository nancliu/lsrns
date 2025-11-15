"""
场景管理服务 - 负责事件场景的查询和从场景创建案例 (Phase 5.3.3)
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

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
            # Phase 2: 添加 metadata_version 字段以支持向后兼容
            metadata = {
                "metadata_version": "2.0",  # Phase 2: v2.0 元数据 (显式版本)
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

    async def generate_scenarios_from_csv(
        self,
        csv_file: str,
        generate_all_strategies: bool = True
    ) -> Dict[str, Any]:
        """
        Generate scenarios from CSV file in batch.

        Args:
            csv_file: CSV filename in events/ folder
            generate_all_strategies: Generate all strategies (VSS/TEC/DHS) or just NO_CONTROL

        Returns:
            {
                "task_id": "csv_gen_...",
                "csv_file": "...",
                "status": "processing",
                "message": "...",
                "state_file": "...",
                "generated_count": None
            }

        Process:
            1. Validate CSV exists
            2. Create state tracking file
            3. Load CSV and filter events
            4. Check duplicates against scenario_index.json
            5. Generate scenarios for new events
            6. Update state file with results
            7. Update scenario_index.json
        """
        from datetime import datetime
        import pandas as pd
        from pathlib import Path
        import json
        from shared.control_tools.scenario_generator import ScenarioGenerator

        # Generate task ID
        task_id = f"csv_gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"Starting CSV scenario generation: {task_id} for file: {csv_file}")

        # 1. Validate CSV exists
        csv_path = Path("events") / csv_file
        if not csv_path.exists():
            logger.error(f"CSV file not found: {csv_path}")
            raise FileNotFoundError(f"CSV file not found: {csv_file}")

        # 2. Create state tracking file
        state_file_path = self._create_state_file(csv_file, task_id)
        logger.info(f"Created state file: {state_file_path}")

        try:
            # 3. Load CSV
            logger.info(f"Loading CSV file: {csv_path}")
            df = pd.read_csv(csv_path, encoding='utf-8')
            total_events = len(df)
            logger.info(f"Loaded {total_events} events from CSV")

            # Update state file with total count
            self._update_state_file(state_file_path, {
                "total_events_in_csv": total_events,
                "status": "processing"
            })

            # 4. Initialize ScenarioGenerator
            network_file = "templates/network_files/sichuan202508v7.net.xml"
            generator = ScenarioGenerator(
                network_file=network_file,
                output_base_dir="output/scenarios"
            )

            # 5. Process events
            events_processed = 0
            events_skipped = 0
            events_generated = 0
            scenarios_count = {"no_control": 0, "vss": 0, "tec": 0, "dhs": 0, "total": 0}
            successful_events = []
            failed_events = []

            # Determine strategies to generate
            if generate_all_strategies:
                strategies = ["NO_CONTROL", "VSS", "TEC"]  # DHS not commonly used
            else:
                strategies = ["NO_CONTROL"]

            for idx, row in df.iterrows():
                events_processed += 1
                report_id = str(row.get('报告编号', ''))

                if not report_id:
                    logger.warning(f"Row {idx}: Missing report_id, skipping")
                    failed_events.append({
                        "report_id": f"row_{idx}",
                        "event_type": "unknown",
                        "error": "Missing 报告编号",
                        "timestamp": datetime.now().isoformat()
                    })
                    continue

                # Check if any scenario for this event already exists
                existing_strategies = []
                new_strategies = []
                for strategy in strategies:
                    if self._is_scenario_exists(report_id, strategy):
                        existing_strategies.append(strategy)
                    else:
                        new_strategies.append(strategy)

                if not new_strategies:
                    logger.debug(f"Event {report_id}: All scenarios exist, skipping")
                    events_skipped += 1
                    continue

                # Generate scenarios for new strategies
                try:
                    generated_scenarios = []
                    for strategy in new_strategies:
                        # Prepare event data
                        event_data = self._prepare_event_data(row, report_id)

                        # Prepare control parameters with csv_control marking
                        control_params = self._prepare_control_params(row, strategy)

                        # Generate scenario
                        logger.info(f"Generating scenario: {report_id}_{strategy}")
                        result = generator.generate_scenario(
                            event_data=event_data,
                            strategy_type=strategy,
                            control_params=control_params
                        )

                        if result:
                            scenario_id = f"scenario_{report_id}_{strategy.lower()}"
                            generated_scenarios.append(scenario_id)
                            scenarios_count[strategy.lower()] += 1
                            scenarios_count["total"] += 1

                    if generated_scenarios:
                        events_generated += 1
                        successful_events.append({
                            "report_id": report_id,
                            "event_type": str(row.get('事件类型', 'unknown')),
                            "scenarios": generated_scenarios,
                            "timestamp": datetime.now().isoformat()
                        })
                        logger.info(f"Event {report_id}: Generated {len(generated_scenarios)} scenarios")

                        # Update scenario_index.json for new scenarios
                        self._update_scenario_index_batch(generated_scenarios)

                except Exception as e:
                    logger.error(f"Event {report_id}: Generation failed - {str(e)}")
                    failed_events.append({
                        "report_id": report_id,
                        "event_type": str(row.get('事件类型', 'unknown')),
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    })

                # Update state file every 10 events
                if events_processed % 10 == 0:
                    self._update_state_file(state_file_path, {
                        "events_processed": events_processed,
                        "events_skipped_existing": events_skipped,
                        "events_generated": events_generated,
                        "scenarios_generated": scenarios_count
                    })

            # 6. Finalize state file
            self._finalize_state_file(
                state_file_path,
                status="completed",
                final_data={
                    "events_processed": events_processed,
                    "events_skipped_existing": events_skipped,
                    "events_generated": events_generated,
                    "scenarios_generated": scenarios_count,
                    "successful_events": successful_events,
                    "failed_events": failed_events
                }
            )

            logger.info(f"CSV generation completed: {events_generated} events generated, {events_skipped} skipped")

            return {
                "task_id": task_id,
                "csv_file": csv_file,
                "status": "completed",
                "message": f"场景生成完成：{events_generated}个事件生成，{events_skipped}个已存在",
                "state_file": str(state_file_path),
                "generated_count": scenarios_count["total"]
            }

        except Exception as e:
            logger.error(f"CSV generation failed: {str(e)}")
            # Mark state file as failed
            self._finalize_state_file(state_file_path, status="failed", error=str(e))
            raise

    def _is_scenario_exists(self, report_id: str, strategy: str) -> bool:
        """
        Check if scenario already exists in scenario_index.json.

        Args:
            report_id: Event report ID
            strategy: Strategy type (NO_CONTROL, VSS, TEC, DHS)

        Returns:
            True if scenario exists, False otherwise
        """
        scenario_id = f"scenario_{report_id}_{strategy.lower()}"

        # Load scenario_index.json
        index_path = Path("output/scenarios/scenario_index.json")
        if not index_path.exists():
            return False

        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)

            # Check if scenario_id exists
            for scenario in index.get("scenarios", []):
                if scenario.get("files", {}).get("scenario_dir") == scenario_id:
                    return True

            return False

        except Exception as e:
            logger.warning(f"Failed to check scenario existence: {str(e)}")
            return False

    def _prepare_event_data(self, row: 'pd.Series', report_id: str) -> Dict[str, Any]:
        """
        Prepare event data from CSV row for ScenarioGenerator.

        Args:
            row: Pandas Series from CSV
            report_id: Event report ID

        Returns:
            Event data dictionary
        """
        return {
            "report_id": report_id,
            "event_type": str(row.get('事件类型', '交通事故')),
            "event_description": str(row.get('内容', '')),
            "start_time": str(row.get('开始时间', '')),
            "end_time": str(row.get('结束时间', '')),
            "road": str(row.get('道路', 'G4202')),
            "direction": str(row.get('方向', '上行')),
            "mileage": str(row.get('里程', '')),
            "junction_id": str(row.get('路段编号', '')),
            "edge_id": str(row.get('edge_id', '')),
            "affected_lanes": [str(row.get('车道', '主路'))]
        }

    def _prepare_control_params(self, row: 'pd.Series', strategy: str) -> Dict[str, Any]:
        """
        Prepare control strategy parameters from CSV row.

        This method extracts control strategy parameters from the event CSV
        and marks them with csv_control=True to indicate they were extracted
        from CSV operational data (as opposed to simulated event-based control).

        Args:
            row: Pandas Series from CSV
            strategy: Strategy type (NO_CONTROL, VSS, TEC, DHS)

        Returns:
            Control parameters dictionary with csv_control field
        """
        edge_id = str(row.get('edge_id', ''))
        affected_lanes = str(row.get('车道', ''))
        event_type = str(row.get('事件类型', '交通事故'))

        # NO_CONTROL strategy - no actual control applied
        if strategy.upper() == "NO_CONTROL":
            return {
                "description": "Event-only baseline (no control strategy applied)",
                "event_only": True,
                "csv_control": False  # No control, so not CSV control
            }

        # VSS Strategy: Variable speed limit
        if strategy.upper() == "VSS":
            # Determine speed based on affected lanes
            if '应急车道' in affected_lanes or '紧急停车带' in affected_lanes:
                speed_limit_kmh = 70  # Emergency lane only, less severe
            elif '第一车道' in affected_lanes or '行车道' in affected_lanes:
                speed_limit_kmh = 50  # Main lane blocked, more severe
            else:
                speed_limit_kmh = 60  # Default

            return {
                "speed_limit_kmh": speed_limit_kmh,
                "affected_edges": [edge_id] if edge_id else [],
                "response_delay_seconds": 300,  # 5 min detection + activation
                "recovery_period_seconds": 600,  # 10 min after event clears
                "csv_control": True  # Extracted from CSV
            }

        # TEC Strategy: Toll Entrance Control
        if strategy.upper() == "TEC":
            # Determine flow reduction based on severity
            if '第一车道' in affected_lanes or '第二车道' in affected_lanes:
                flow_reduction = 0.4  # Severe blockage
            else:
                flow_reduction = 0.2  # Minor blockage

            # Check if CSV has actual toll control data (simplified check)
            # In full implementation, would parse 收费站 columns
            has_toll_data = pd.notna(row.get('收费站', None))

            params = {
                "flow_reduction": flow_reduction,
                "entrance_edges": [edge_id] if edge_id else [],
                "response_delay_seconds": 300,
                "recovery_period_seconds": 600,
                "csv_control": has_toll_data  # True if CSV has toll station data
            }

            # Add toll station info if available
            if has_toll_data:
                params["toll_station_ids"] = [str(row.get('收费站', ''))]
                params["control_measure"] = str(row.get('管制措施', ''))
                params["control_range"] = str(row.get('管制范围', ''))

            return params

        # DHS Strategy: Dynamic Hard Shoulder
        if strategy.upper() == "DHS":
            return {
                "open_shoulder": True,
                "affected_edges": [edge_id] if edge_id else [],
                "response_delay_seconds": 300,
                "recovery_period_seconds": 600,
                "csv_control": True  # Extracted from CSV
            }

        # Default fallback
        return {
            "csv_control": False,
            "description": f"Unknown strategy type: {strategy}"
        }

    def _create_state_file(self, csv_file: str, task_id: str) -> Path:
        """
        Create initial state tracking file.

        Args:
            csv_file: CSV filename
            task_id: Task ID

        Returns:
            Path to state file
        """
        from datetime import datetime
        import json

        # Create directory if not exists
        state_dir = Path("events/csv_extraction_status")
        state_dir.mkdir(parents=True, exist_ok=True)

        # Generate state filename
        csv_name = Path(csv_file).stem
        state_file = state_dir / f"{csv_name}_status.json"

        # Initial state
        state = {
            "csv_file": csv_file,
            "task_id": task_id,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "status": "processing",
            "total_events_in_csv": 0,
            "events_processed": 0,
            "events_skipped_existing": 0,
            "events_generated": 0,
            "scenarios_generated": {
                "no_control": 0,
                "vss": 0,
                "tec": 0,
                "dhs": 0,
                "total": 0
            },
            "failed_events": [],
            "successful_events": []
        }

        # Write initial state
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)

        return state_file

    def _update_state_file(self, state_file: Path, updates: Dict[str, Any]):
        """
        Update state file with new data.

        Args:
            state_file: Path to state file
            updates: Dictionary of fields to update
        """
        import json

        try:
            # Read current state
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # Update fields
            state.update(updates)

            # Write back
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"Failed to update state file: {str(e)}")

    def _finalize_state_file(
        self,
        state_file: Path,
        status: str,
        final_data: Dict[str, Any] = None,
        error: str = None
    ):
        """
        Finalize state file with completion status.

        Args:
            state_file: Path to state file
            status: Final status (completed|failed)
            final_data: Final statistics
            error: Error message if failed
        """
        from datetime import datetime
        import json

        try:
            # Read current state
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # Update final fields
            state["completed_at"] = datetime.now().isoformat()
            state["status"] = status

            if final_data:
                state.update(final_data)

            if error:
                state["error"] = error

            # Write back
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

            logger.info(f"State file finalized: {status}")

        except Exception as e:
            logger.error(f"Failed to finalize state file: {str(e)}")

    def _update_scenario_index_batch(self, scenario_dir_names: List[str]) -> None:
        """
        Update scenario_index.json with newly generated scenarios.

        Args:
            scenario_dir_names: List of scenario directory names (e.g., scenario_12345_tec)
        """
        from shared.utilities.scenario_index_updater import ScenarioIndexUpdater

        try:
            updater = ScenarioIndexUpdater()
            result = updater.add_scenarios_batch(scenario_dir_names)

            logger.info(
                f"Index update: {result['added']} added, "
                f"{result['skipped']} skipped, {result['failed']} failed"
            )

        except Exception as e:
            logger.error(f"Failed to update scenario index: {str(e)}")
