"""
场景案例映射管理 - 维护scenario_index.json中的案例创建信息

Purpose:
    维护事件场景与其创建的案例之间的多对多关系。
    当创建、删除或更新案例时，更新scenario_index.json中对应场景的案例列表。

Design Decision (Q15):
    - scenario_index.json中每个场景添加created_cases数组
    - created_cases包含该场景创建的所有案例的ID和状态
    - 当case创建/更新/删除时调用本模块更新映射

Metadata Structure (Proposed Enhancement):
    在scenario_index.json中添加created_cases字段:
    {
        "event_id": "10754",
        "event_type": "交通事故",
        "strategy": "NO_CONTROL",
        ...files...,
        "created_cases": [
            {
                "case_id": "case_20251113_120000",
                "created_at": "2025-11-13T12:00:00",
                "status": "created",
                "source_scenario": "scenario_10754_no_control"
            }
        ]
    }
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ScenarioCaseMapper:
    """场景案例映射管理器"""

    def __init__(self, scenario_index_path: Optional[Path] = None):
        """
        初始化映射管理器

        Args:
            scenario_index_path: scenario_index.json文件路径
                如果为None，使用默认路径 output/scenarios/scenario_index.json
        """
        if scenario_index_path is None:
            # 使用默认路径
            self.scenario_index_path = Path.cwd() / "output" / "scenarios" / "scenario_index.json"
        else:
            self.scenario_index_path = Path(scenario_index_path)

    def register_case_creation(
        self,
        scenario_id: str,
        case_id: str,
        case_name: str = "",
        case_status: str = "created"
    ) -> bool:
        """
        注册案例创建事件 - 在scenario_index.json中添加案例记录

        Args:
            scenario_id: 场景ID (e.g., "scenario_10754_no_control")
            case_id: 新创建的案例ID
            case_name: 案例名称（可选）
            case_status: 案例初始状态

        Returns:
            是否成功注册

        Example:
            mapper = ScenarioCaseMapper()
            mapper.register_case_creation(
                "scenario_10754_no_control",
                "case_20251113_120000",
                "Morning Peak Accident",
                "created"
            )
        """
        try:
            if not self.scenario_index_path.exists():
                logger.warning(f"scenario_index.json not found: {self.scenario_index_path}")
                return False

            # 读取scenario_index.json
            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            scenarios = index_data.get('scenarios', [])

            # 查找对应的场景
            target_scenario = None
            for scenario in scenarios:
                if scenario.get('files', {}).get('scenario_dir') == scenario_id:
                    target_scenario = scenario
                    break

            if not target_scenario:
                logger.warning(f"Scenario not found in index: {scenario_id}")
                return False

            # 初始化created_cases数组（如果不存在）
            if 'created_cases' not in target_scenario:
                target_scenario['created_cases'] = []

            # 检查案例是否已存在
            existing_case = next(
                (c for c in target_scenario['created_cases'] if c['case_id'] == case_id),
                None
            )

            if existing_case:
                # 更新已存在的案例信息
                existing_case['status'] = case_status
                existing_case['updated_at'] = datetime.now().isoformat()
                logger.info(f"Updated case {case_id} in scenario {scenario_id}")
            else:
                # 添加新案例
                case_record = {
                    'case_id': case_id,
                    'case_name': case_name or case_id,
                    'status': case_status,
                    'source_scenario': scenario_id,
                    'created_at': datetime.now().isoformat()
                }
                target_scenario['created_cases'].append(case_record)
                logger.info(f"Registered case {case_id} in scenario {scenario_id}")

            # 保存更新后的scenario_index.json
            with open(self.scenario_index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to register case creation: {e}")
            return False

    def update_case_status(
        self,
        scenario_id: str,
        case_id: str,
        new_status: str
    ) -> bool:
        """
        更新案例状态 - 在scenario_index.json中更新案例状态

        Args:
            scenario_id: 场景ID
            case_id: 案例ID
            new_status: 新状态 (e.g., "od_generating", "created", "simulating", "completed")

        Returns:
            是否成功更新

        Example:
            mapper.update_case_status(
                "scenario_10754_no_control",
                "case_20251113_120000",
                "simulating"
            )
        """
        try:
            if not self.scenario_index_path.exists():
                return False

            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            scenarios = index_data.get('scenarios', [])

            # 查找对应的场景和案例
            for scenario in scenarios:
                if scenario.get('files', {}).get('scenario_dir') == scenario_id:
                    for case_record in scenario.get('created_cases', []):
                        if case_record['case_id'] == case_id:
                            case_record['status'] = new_status
                            case_record['updated_at'] = datetime.now().isoformat()

                            # 保存更新
                            with open(self.scenario_index_path, 'w', encoding='utf-8') as f:
                                json.dump(index_data, f, ensure_ascii=False, indent=2)

                            logger.info(f"Updated status of {case_id} in {scenario_id} to {new_status}")
                            return True

            logger.warning(f"Case {case_id} not found in scenario {scenario_id}")
            return False

        except Exception as e:
            logger.error(f"Failed to update case status: {e}")
            return False

    def unregister_case(self, scenario_id: str, case_id: str) -> bool:
        """
        注销案例 - 从scenario_index.json中移除案例记录

        Args:
            scenario_id: 场景ID
            case_id: 案例ID

        Returns:
            是否成功注销

        Example:
            mapper.unregister_case("scenario_10754_no_control", "case_20251113_120000")
        """
        try:
            if not self.scenario_index_path.exists():
                return False

            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            scenarios = index_data.get('scenarios', [])

            # 查找对应的场景和案例
            for scenario in scenarios:
                if scenario.get('files', {}).get('scenario_dir') == scenario_id:
                    created_cases = scenario.get('created_cases', [])
                    original_count = len(created_cases)

                    # 移除对应的案例
                    scenario['created_cases'] = [
                        c for c in created_cases if c['case_id'] != case_id
                    ]

                    if len(scenario['created_cases']) < original_count:
                        # 保存更新
                        with open(self.scenario_index_path, 'w', encoding='utf-8') as f:
                            json.dump(index_data, f, ensure_ascii=False, indent=2)

                        logger.info(f"Unregistered case {case_id} from scenario {scenario_id}")
                        return True

            logger.warning(f"Case {case_id} not found in scenario {scenario_id}")
            return False

        except Exception as e:
            logger.error(f"Failed to unregister case: {e}")
            return False

    def get_cases_for_scenario(self, scenario_id: str) -> List[Dict[str, Any]]:
        """
        获取场景的所有案例

        Args:
            scenario_id: 场景ID

        Returns:
            案例列表，如果场景不存在返回空列表

        Example:
            cases = mapper.get_cases_for_scenario("scenario_10754_no_control")
            # [
            #     {
            #         "case_id": "case_20251113_120000",
            #         "status": "created",
            #         "created_at": "2025-11-13T12:00:00"
            #     }
            # ]
        """
        try:
            if not self.scenario_index_path.exists():
                return []

            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            scenarios = index_data.get('scenarios', [])

            # 查找对应的场景
            for scenario in scenarios:
                if scenario.get('files', {}).get('scenario_dir') == scenario_id:
                    return scenario.get('created_cases', [])

            return []

        except Exception as e:
            logger.error(f"Failed to get cases for scenario: {e}")
            return []

    def get_scenario_by_id(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """
        获取场景详细信息（包含其案例列表）

        Args:
            scenario_id: 场景ID

        Returns:
            场景信息，包含created_cases数组，如果不存在返回None

        Example:
            scenario = mapper.get_scenario_by_id("scenario_10754_no_control")
        """
        try:
            if not self.scenario_index_path.exists():
                return None

            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            scenarios = index_data.get('scenarios', [])

            for scenario in scenarios:
                if scenario.get('files', {}).get('scenario_dir') == scenario_id:
                    return scenario

            return None

        except Exception as e:
            logger.error(f"Failed to get scenario: {e}")
            return None

    def get_all_scenarios_with_cases(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取所有场景及其案例映射（用于scenario_browser.js加载）

        Returns:
            {
                "scenario_id_1": [case1, case2, ...],
                "scenario_id_2": [case3, ...],
                ...
            }

        Example:
            mapping = mapper.get_all_scenarios_with_cases()
            # {
            #     "scenario_10754_no_control": [
            #         {"case_id": "case_...", "status": "created"}
            #     ],
            #     ...
            # }
        """
        try:
            if not self.scenario_index_path.exists():
                return {}

            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            scenarios = index_data.get('scenarios', [])
            mapping = {}

            for scenario in scenarios:
                scenario_id = scenario.get('files', {}).get('scenario_dir')
                if scenario_id:
                    mapping[scenario_id] = scenario.get('created_cases', [])

            return mapping

        except Exception as e:
            logger.error(f"Failed to get all scenarios with cases: {e}")
            return {}

    def link_scenario_to_case(
        self,
        scenario_id: str,
        case_id: str,
        simulation_id: str
    ) -> bool:
        """
        Link scenario to case in scenario index.

        This is an alias for register_case_creation for compatibility with
        the event-based case architecture.

        Args:
            scenario_id: Scenario identifier
            case_id: Case identifier
            simulation_id: Simulation identifier

        Returns:
            True if successful, False otherwise
        """
        return self.register_case_creation(
            scenario_id=scenario_id,
            case_id=case_id,
            case_name=f"Case for {scenario_id}",
            case_status="created"
        )

    def unregister_case_from_all_scenarios(self, case_id: str) -> int:
        """
        从所有scenario中删除某个case（重置操作）

        Args:
            case_id: 案例ID

        Returns:
            删除的scenario数量

        Example:
            mapper.unregister_case_from_all_scenarios("case_event_10754")
        """
        try:
            if not self.scenario_index_path.exists():
                return 0

            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            scenarios = index_data.get('scenarios', [])
            removed_count = 0

            # 从所有scenario中删除该case
            for scenario in scenarios:
                created_cases = scenario.get('created_cases', [])
                original_count = len(created_cases)

                # 过滤掉该case
                scenario['created_cases'] = [
                    c for c in created_cases if c['case_id'] != case_id
                ]

                if len(scenario['created_cases']) < original_count:
                    removed_count += 1
                    logger.info(f"Removed {case_id} from scenario {scenario.get('files', {}).get('scenario_dir')}")

            # 如果有删除操作，保存更新
            if removed_count > 0:
                with open(self.scenario_index_path, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Unregistered case {case_id} from {removed_count} scenarios")

            return removed_count

        except Exception as e:
            logger.error(f"Failed to unregister case from all scenarios: {e}")
            return 0

    def clear_scenario_cases(self, scenario_id: str) -> int:
        """
        清空某个scenario的所有created_cases（重置操作）

        Args:
            scenario_id: 场景ID

        Returns:
            被清空的case数量

        Example:
            mapper.clear_scenario_cases("scenario_10754_no_control")
        """
        try:
            if not self.scenario_index_path.exists():
                return 0

            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            scenarios = index_data.get('scenarios', [])

            # 查找对应的场景
            for scenario in scenarios:
                if scenario.get('files', {}).get('scenario_dir') == scenario_id:
                    created_cases = scenario.get('created_cases', [])
                    removed_count = len(created_cases)

                    # 清空created_cases
                    scenario['created_cases'] = []

                    # 保存更新
                    if removed_count > 0:
                        with open(self.scenario_index_path, 'w', encoding='utf-8') as f:
                            json.dump(index_data, f, ensure_ascii=False, indent=2)
                        logger.info(f"Cleared {removed_count} cases from scenario {scenario_id}")

                    return removed_count

            logger.warning(f"Scenario not found: {scenario_id}")
            return 0

        except Exception as e:
            logger.error(f"Failed to clear scenario cases: {e}")
            return 0

    def reset_all_cases(self) -> Dict[str, int]:
        """
        重置整个scenario_index.json - 清空所有created_cases（仅供管理用途）

        Returns:
            {'total_cases_removed': int, 'total_scenarios_affected': int}

        Example:
            result = mapper.reset_all_cases()
            # {'total_cases_removed': 45, 'total_scenarios_affected': 477}
        """
        try:
            if not self.scenario_index_path.exists():
                return {'total_cases_removed': 0, 'total_scenarios_affected': 0}

            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            scenarios = index_data.get('scenarios', [])
            total_cases_removed = 0
            scenarios_affected = 0

            # 清空所有scenario的created_cases
            for scenario in scenarios:
                created_cases = scenario.get('created_cases', [])
                if created_cases:
                    total_cases_removed += len(created_cases)
                    scenario['created_cases'] = []
                    scenarios_affected += 1

            # 保存更新
            if total_cases_removed > 0:
                with open(self.scenario_index_path, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, ensure_ascii=False, indent=2)
                logger.info(f"Reset all cases: {total_cases_removed} cases removed from {scenarios_affected} scenarios")

            return {
                'total_cases_removed': total_cases_removed,
                'total_scenarios_affected': scenarios_affected
            }

        except Exception as e:
            logger.error(f"Failed to reset all cases: {e}")
            return {'total_cases_removed': 0, 'total_scenarios_affected': 0}
