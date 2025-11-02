"""
控制方案管理服务

职责：
- 方案CRUD操作的业务逻辑
- 策略验证和XML生成协调
- 策略引用管理
- 方案预览和验证
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any

from shared.control_tools import plan_file_manager
from shared.control_tools import strategy_file_manager
from shared.control_tools.additional_generator import generate_plan_additional
from shared.control_tools.plan_validator import validate_plan

logger = logging.getLogger(__name__)

# 配置路径
STRATEGIES_DIR = "control_data/strategies"
PLANS_BASE_DIR = "control_data/plans"


class ControlPlanService:
    """控制方案管理服务"""

    def __init__(self):
        """初始化服务"""
        self.strategies_dir = STRATEGIES_DIR
        self.plans_base_dir = PLANS_BASE_DIR

    def create_plan(self, plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新方案

        Args:
            plan_data: 方案数据（来自CreatePlanRequest）

        Returns:
            Dict: 完整的方案响应数据

        Raises:
            ValueError: 验证失败或策略不存在
        """
        logger.info(f"Creating plan: {plan_data.get('plan_name')}")

        try:
            # 1. 验证所有strategy_ids存在
            strategy_ids = plan_data.get("strategy_ids", [])
            strategies = []

            for sid in strategy_ids:
                strategy = strategy_file_manager.load_strategy(sid, self.strategies_dir)
                if not strategy:
                    raise ValueError(f"策略不存在: {sid}")
                strategies.append(strategy)

            # 2. 创建方案（生成ID和保存元数据）
            plan_id = plan_file_manager.create_plan(plan_data)

            # 3. 加载完整的方案数据
            plan_metadata = plan_file_manager.get_plan(plan_id)

            # 4. 生成control.add.xml
            xml_content = generate_plan_additional(
                plan_id=plan_id, plan_name=plan_metadata["plan_name"], strategies=strategies
            )

            # 5. 保存XML文件
            plan_dir = Path(self.plans_base_dir) / plan_id
            xml_file = plan_dir / "control.add.xml"
            xml_file.write_text(xml_content, encoding="utf-8")

            logger.info(f"Plan XML saved: {xml_file}")

            # 6. 更新策略引用计数
            for sid in strategy_ids:
                strategy_file_manager.increment_strategy_reference(
                    sid, plan_id, self.strategies_dir
                )

            # 7. 验证方案（获取警告）
            validation_result = validate_plan(plan_metadata, strategies)

            # 8. 构建响应
            response = {
                **plan_metadata,
                "strategy_count": len(strategy_ids),
                "is_baseline": plan_id == "baseline_plan",
                "validation": {
                    "is_valid": validation_result.is_valid,
                    "warnings": [
                        {
                            "type": w.type,
                            "severity": w.severity,
                            "message": w.message,
                            "suggestion": w.suggestion,
                        }
                        for w in validation_result.warnings
                    ],
                    "suggestions": validation_result.suggestions,
                },
            }

            logger.info(f"Plan created successfully: {plan_id}")
            return response

        except Exception as e:
            logger.error(f"Failed to create plan: {e}", exc_info=True)
            raise

    def get_plan(self, plan_id: str, include_strategies: bool = False) -> Dict[str, Any]:
        """
        获取方案详情

        Args:
            plan_id: 方案ID
            include_strategies: 是否包含策略详情

        Returns:
            Dict: 方案数据

        Raises:
            FileNotFoundError: 方案不存在
        """
        logger.info(f"Getting plan: {plan_id}")

        try:
            # 加载方案元数据
            plan_metadata = plan_file_manager.get_plan(plan_id)

            response = {
                **plan_metadata,
                "strategy_count": len(plan_metadata.get("strategy_ids", [])),
                "is_baseline": plan_id == "baseline_plan",
            }

            # 如果需要包含策略详情
            if include_strategies:
                strategies = plan_file_manager.get_plan_strategies(plan_id)
                response["strategies"] = [
                    {
                        "strategy_id": s.get("strategy_id"),
                        "strategy_name": s.get("strategy_name"),
                        "strategy_type": s.get("strategy_type"),
                        "template_id": s.get("template_id"),
                    }
                    for s in strategies
                ]

            return response

        except Exception as e:
            logger.error(f"Failed to get plan [{plan_id}]: {e}", exc_info=True)
            raise

    def list_plans(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        列出所有方案

        Args:
            filters: 过滤条件

        Returns:
            Dict: 方案列表响应
        """
        logger.info(f"Listing plans with filters: {filters}")

        try:
            plans = plan_file_manager.list_plans(filters)

            return {"plans": plans, "total": len(plans)}

        except Exception as e:
            logger.error(f"Failed to list plans: {e}", exc_info=True)
            raise

    def update_plan(self, plan_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        更新方案

        Args:
            plan_id: 方案ID
            updates: 要更新的字段

        Returns:
            Dict: 更新后的方案数据

        Raises:
            FileNotFoundError: 方案不存在
            ValueError: 策略不存在或尝试修改基准方案的策略列表
        """
        logger.info(f"Updating plan: {plan_id}")

        try:
            # 获取原方案数据
            original_plan = plan_file_manager.get_plan(plan_id)
            original_strategy_ids = set(original_plan.get("strategy_ids", []))

            # 如果strategy_ids变化，需要验证新策略并重新生成XML
            strategy_ids_changed = "strategy_ids" in updates

            # 基准方案保护：禁止修改strategy_ids
            if plan_id == "baseline_plan" and strategy_ids_changed:
                new_strategy_ids = updates.get("strategy_ids", [])
                if len(new_strategy_ids) > 0:
                    raise ValueError("基准方案的strategy_ids必须为空，不能添加策略")

            if strategy_ids_changed:
                new_strategy_ids = set(updates["strategy_ids"])

                # 验证所有新策略存在
                for sid in new_strategy_ids:
                    strategy = strategy_file_manager.load_strategy(sid, self.strategies_dir)
                    if not strategy:
                        raise ValueError(f"策略不存在: {sid}")

                # 更新引用计数
                # 移除的策略：减少引用
                removed_strategies = original_strategy_ids - new_strategy_ids
                for sid in removed_strategies:
                    strategy_file_manager.decrement_strategy_reference(
                        sid, plan_id, self.strategies_dir
                    )

                # 新增的策略：增加引用
                added_strategies = new_strategy_ids - original_strategy_ids
                for sid in added_strategies:
                    strategy_file_manager.increment_strategy_reference(
                        sid, plan_id, self.strategies_dir
                    )

            # 更新元数据
            plan_file_manager.update_plan(plan_id, updates)

            # 如果strategy_ids变化，重新生成XML
            if strategy_ids_changed:
                self.regenerate_plan_xml(plan_id)

            # 返回更新后的方案
            return self.get_plan(plan_id)

        except Exception as e:
            logger.error(f"Failed to update plan [{plan_id}]: {e}", exc_info=True)
            raise

    def delete_plan(self, plan_id: str) -> Dict[str, bool]:
        """
        删除方案

        Args:
            plan_id: 方案ID

        Returns:
            Dict: 删除结果

        Raises:
            ValueError: 尝试删除基准方案
            FileNotFoundError: 方案不存在
        """
        logger.info(f"Deleting plan: {plan_id}")

        try:
            # 获取方案数据（用于减少策略引用）
            plan_metadata = plan_file_manager.get_plan(plan_id)
            strategy_ids = plan_metadata.get("strategy_ids", [])

            # 删除方案
            plan_file_manager.delete_plan(plan_id)

            # 减少所有策略的引用计数
            for sid in strategy_ids:
                strategy_file_manager.decrement_strategy_reference(
                    sid, plan_id, self.strategies_dir
                )

            logger.info(f"Plan deleted successfully: {plan_id}")
            return {"deleted": True}

        except Exception as e:
            logger.error(f"Failed to delete plan [{plan_id}]: {e}", exc_info=True)
            raise

    def regenerate_plan_xml(self, plan_id: str) -> Dict[str, Any]:
        """
        重新生成方案的control.add.xml

        Args:
            plan_id: 方案ID

        Returns:
            Dict: 操作结果

        Raises:
            FileNotFoundError: 方案不存在
        """
        logger.info(f"Regenerating XML for plan: {plan_id}")

        try:
            plan_file_manager.regenerate_plan_xml(plan_id)

            return {"regenerated": True, "plan_id": plan_id, "message": "XML文件已重新生成"}

        except Exception as e:
            logger.error(f"Failed to regenerate XML [{plan_id}]: {e}", exc_info=True)
            raise

    def validate_plan_config(self, plan_id: str) -> Dict[str, Any]:
        """
        验证方案配置

        Args:
            plan_id: 方案ID

        Returns:
            Dict: 验证结果

        Raises:
            FileNotFoundError: 方案不存在
        """
        logger.info(f"Validating plan: {plan_id}")

        try:
            # 加载方案和策略
            plan_metadata = plan_file_manager.get_plan(plan_id)
            strategies = plan_file_manager.get_plan_strategies(plan_id)

            # 执行验证
            validation_result = validate_plan(plan_metadata, strategies)

            return {
                "is_valid": validation_result.is_valid,
                "warnings": [
                    {
                        "type": w.type,
                        "severity": w.severity,
                        "message": w.message,
                        "suggestion": w.suggestion,
                    }
                    for w in validation_result.warnings
                ],
                "suggestions": validation_result.suggestions,
            }

        except Exception as e:
            logger.error(f"Failed to validate plan [{plan_id}]: {e}", exc_info=True)
            raise

    def preview_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        预览方案效果

        Args:
            plan_id: 方案ID

        Returns:
            Dict: 预览信息（摘要、策略详情、XML预览）

        Raises:
            FileNotFoundError: 方案不存在
        """
        logger.info(f"Previewing plan: {plan_id}")

        try:
            # 加载方案和策略
            plan_metadata = plan_file_manager.get_plan(plan_id)
            strategies = plan_file_manager.get_plan_strategies(plan_id)

            # 统计策略类型
            strategy_types_count = {}
            affected_edges_set = set()
            time_range = {"earliest": None, "latest": None}
            strategy_preview_list = []

            for strategy in strategies:
                strategy_type = strategy.get("strategy_type")
                strategy_types_count[strategy_type] = strategy_types_count.get(strategy_type, 0) + 1

                # 提取影响的边（严格从parameters获取）
                parameters = strategy.get("parameters", {})
                if strategy_type == "TEC":
                    # TEC使用entrance_edges
                    entrance_edges = parameters.get("entrance_edges", [])
                    affected_edges_set.update(entrance_edges)
                else:
                    # VSS/DHS使用affected_edges
                    affected_edges = parameters.get("affected_edges", [])
                    affected_edges_set.update(affected_edges)

                # 提取时间范围
                # VSS: speed_steps
                if strategy_type == "VSS":
                    for step in parameters.get("speed_steps", []):
                        time_sec = step.get("time_seconds") or step.get("time_hours", 0) * 3600
                        if time_range["earliest"] is None or time_sec < time_range["earliest"]:
                            time_range["earliest"] = int(time_sec)
                        if time_range["latest"] is None or time_sec > time_range["latest"]:
                            time_range["latest"] = int(time_sec)

                # DHS: intervals
                elif strategy_type == "DHS":
                    for interval in parameters.get("intervals", []):
                        begin = (
                            interval.get("begin_seconds") or interval.get("begin_hours", 0) * 3600
                        )
                        end = interval.get("end_seconds") or interval.get("end_hours", 0) * 3600
                        if time_range["earliest"] is None or begin < time_range["earliest"]:
                            time_range["earliest"] = int(begin)
                        if time_range["latest"] is None or end > time_range["latest"]:
                            time_range["latest"] = int(end)

                # TEC: flow_intervals or closure_intervals
                elif strategy_type == "TEC":
                    for interval in parameters.get("flow_intervals", []) + parameters.get(
                        "closure_intervals", []
                    ):
                        begin = (
                            interval.get("begin_seconds") or interval.get("begin_hours", 0) * 3600
                        )
                        end = interval.get("end_seconds") or interval.get("end_hours", 0) * 3600
                        if time_range["earliest"] is None or begin < time_range["earliest"]:
                            time_range["earliest"] = int(begin)
                        if time_range["latest"] is None or end > time_range["latest"]:
                            time_range["latest"] = int(end)

                # 添加策略预览信息
                strategy_preview_list.append(
                    {
                        "strategy_id": strategy.get("strategy_id"),
                        "strategy_name": strategy.get("strategy_name"),
                        "strategy_type": strategy_type,
                        "affected_objects": affected_edges,
                        "active_periods": [],  # 简化版本，不详细展开时段
                    }
                )

            # 读取XML内容（前500行）
            xml_file = Path(self.plans_base_dir) / plan_id / "control.add.xml"
            xml_preview = ""
            if xml_file.exists():
                with open(xml_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    xml_preview = "".join(lines[:500])
                    if len(lines) > 500:
                        xml_preview += "\n... (剩余内容已省略)"

            # 构建响应
            return {
                "plan_id": plan_id,
                "summary": {
                    "total_strategies": len(strategies),
                    "strategy_types": strategy_types_count,
                    "affected_edges": list(affected_edges_set),
                    "affected_edge_count": len(affected_edges_set),
                    "time_range": time_range if time_range["earliest"] is not None else None,
                },
                "strategies": strategy_preview_list,
                "xml_preview": xml_preview,
            }

        except Exception as e:
            logger.error(f"Failed to preview plan [{plan_id}]: {e}", exc_info=True)
            raise
