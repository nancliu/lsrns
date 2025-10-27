"""
方案验证器

职责：
- 验证方案的策略组合合理性
- 检测潜在冲突和问题
- 返回警告信息（非阻塞模式）
"""

import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Set, Tuple, Optional

logger = logging.getLogger(__name__)


@dataclass
class Warning:
    """验证警告数据类"""
    type: str  # 警告类型: "spatial_conflict", "timing_coordination", "strategy_compatibility"
    severity: str  # 严重程度: "low", "medium", "high"
    message: str  # 警告信息
    suggestion: Optional[str] = None  # 改进建议


@dataclass
class ValidationResult:
    """验证结果数据类"""
    is_valid: bool  # 总是True（警告模式）
    warnings: List[Warning]  # 警告列表
    suggestions: List[str]  # 优化建议列表


def validate_plan(plan_data: Dict[str, Any], strategies: List[Dict[str, Any]]) -> ValidationResult:
    """
    验证方案配置

    检查规则：
    1. 空间冲突检测 - 多个策略是否控制相同的edge/lane
    2. 时间协调检查 - VSS和DHS的时间段是否协调
    3. 策略类型兼容性 - VSS+DHS+TEC组合的合理性

    Args:
        plan_data: 方案数据字典
        strategies: 策略实例列表（完整配置）

    Returns:
        ValidationResult: 验证结果（始终is_valid=True，仅提供警告）
    """
    logger.info(f"Validating plan: {plan_data.get('plan_name', 'Unknown')}")

    warnings: List[Warning] = []
    suggestions: List[str] = []

    # 如果是空方案（基准方案），直接通过
    if not strategies:
        logger.info("Empty plan (baseline), no validation needed")
        return ValidationResult(is_valid=True, warnings=[], suggestions=[])

    # 1. 空间冲突检测
    spatial_warnings = _check_spatial_conflicts(strategies)
    warnings.extend(spatial_warnings)

    # 2. 时间协调检查
    timing_warnings, timing_suggestions = _check_timing_coordination(strategies)
    warnings.extend(timing_warnings)
    suggestions.extend(timing_suggestions)

    # 3. 策略类型兼容性检查
    compat_warnings, compat_suggestions = _check_strategy_compatibility(strategies)
    warnings.extend(compat_warnings)
    suggestions.extend(compat_suggestions)

    logger.info(f"Plan validation complete: {len(warnings)} warnings, {len(suggestions)} suggestions")

    return ValidationResult(
        is_valid=True,  # 始终为True（警告模式）
        warnings=warnings,
        suggestions=suggestions
    )


def _check_spatial_conflicts(strategies: List[Dict[str, Any]]) -> List[Warning]:
    """
    检查空间冲突 - 多个策略是否控制相同的edge/lane

    警告条件：
    - 不同类型的策略控制相同的edge可能产生冲突
    - 多个VSS策略控制相同的edge会覆盖
    """
    warnings: List[Warning] = []

    # 收集每个策略的影响范围
    edge_to_strategies: Dict[str, List[Tuple[str, str]]] = {}  # edge -> [(strategy_id, strategy_type)]

    for strategy in strategies:
        strategy_id = strategy.get("strategy_id")
        strategy_type = strategy.get("template", {}).get("strategy_type")
        parameters = strategy.get("parameters", {})

        affected_edges = set()

        # VSS: affected_edges
        if strategy_type == "VSS":
            affected_edges = set(parameters.get("affected_edges", []))

        # DHS: affected_edges
        elif strategy_type == "DHS":
            affected_edges = set(parameters.get("affected_edges", []))

        # TEC: entrance_edge(s)
        elif strategy_type == "TEC":
            if "entrance_edge" in parameters:
                affected_edges.add(parameters["entrance_edge"])
            if "entrance_edges" in parameters:
                affected_edges.update(parameters["entrance_edges"])

        # 记录影响范围
        for edge in affected_edges:
            if edge not in edge_to_strategies:
                edge_to_strategies[edge] = []
            edge_to_strategies[edge].append((strategy_id, strategy_type))

    # 检测冲突
    for edge, strategy_list in edge_to_strategies.items():
        if len(strategy_list) > 1:
            # 多个策略控制同一edge
            types = [s_type for _, s_type in strategy_list]
            strategy_ids = [s_id for s_id, _ in strategy_list]

            if len(set(types)) > 1:
                # 不同类型策略控制相同edge
                warnings.append(Warning(
                    type="spatial_conflict",
                    severity="medium",
                    message=f"Edge '{edge}' 被多个不同类型策略控制: {', '.join(strategy_ids)}",
                    suggestion=f"检查策略组合是否合理，不同控制类型可能产生冲突"
                ))
            else:
                # 相同类型策略控制相同edge（如多个VSS）
                warnings.append(Warning(
                    type="spatial_conflict",
                    severity="low",
                    message=f"Edge '{edge}' 被多个{types[0]}策略控制: {', '.join(strategy_ids)}",
                    suggestion="后执行的策略配置将覆盖前面的配置"
                ))

    return warnings


def _check_timing_coordination(strategies: List[Dict[str, Any]]) -> Tuple[List[Warning], List[str]]:
    """
    检查时间协调性 - VSS和DHS的时间段是否协调

    警告条件：
    - DHS开放应有VSS提前降速准备（建议提前5-10分钟）
    - 策略结束时间不协调
    """
    warnings: List[Warning] = []
    suggestions: List[str] = []

    # 提取VSS和DHS策略
    vss_strategies = []
    dhs_strategies = []

    for strategy in strategies:
        strategy_type = strategy.get("template", {}).get("strategy_type")
        if strategy_type == "VSS":
            vss_strategies.append(strategy)
        elif strategy_type == "DHS":
            dhs_strategies.append(strategy)

    # 如果没有VSS或DHS，跳过检查
    if not vss_strategies or not dhs_strategies:
        return warnings, suggestions

    # 提取DHS开始时间
    for dhs in dhs_strategies:
        dhs_id = dhs.get("strategy_id")
        dhs_intervals = dhs.get("parameters", {}).get("intervals", [])

        for interval in dhs_intervals:
            if interval.get("status") == "OPEN":
                # DHS开放时间
                dhs_begin = interval.get("begin_seconds") or interval.get("begin_hours", 0) * 3600

                # 检查是否有VSS提前生效
                has_advance_vss = False
                for vss in vss_strategies:
                    vss_id = vss.get("strategy_id")
                    speed_steps = vss.get("parameters", {}).get("speed_steps", [])

                    for step in speed_steps:
                        vss_time = step.get("time_seconds") or step.get("time_hours", 0) * 3600

                        # 如果VSS提前5-10分钟生效，视为合理
                        if 300 <= (dhs_begin - vss_time) <= 600:  # 5-10分钟
                            has_advance_vss = True
                            break

                if not has_advance_vss:
                    warnings.append(Warning(
                        type="timing_coordination",
                        severity="medium",
                        message=f"DHS策略 {dhs_id} 开放前缺少提前降速的VSS策略",
                        suggestion="建议在DHS开放前5-10分钟启动VSS限速，以避免急刹车"
                    ))
                    suggestions.append("考虑添加上游预警限速策略，提前引导车辆降速")

    return warnings, suggestions


def _check_strategy_compatibility(strategies: List[Dict[str, Any]]) -> Tuple[List[Warning], List[str]]:
    """
    检查策略类型兼容性 - VSS+DHS+TEC组合的合理性

    警告条件：
    - 仅有DHS无VSS: 建议添加上游限速
    - 仅有TEC无VSS: 建议添加下游诱导
    """
    warnings: List[Warning] = []
    suggestions: List[str] = []

    # 统计策略类型
    strategy_types = set()
    for strategy in strategies:
        strategy_type = strategy.get("template", {}).get("strategy_type")
        strategy_types.add(strategy_type)

    # 检查组合合理性
    if "DHS" in strategy_types and "VSS" not in strategy_types:
        warnings.append(Warning(
            type="strategy_compatibility",
            severity="medium",
            message="方案包含DHS策略但缺少VSS上游限速",
            suggestion="建议在DHS路段上游增加VSS限速策略，提前降速准备"
        ))
        suggestions.append("添加上游VSS限速策略以改善DHS开放效果")

    if "TEC" in strategy_types and "VSS" not in strategy_types:
        warnings.append(Warning(
            type="strategy_compatibility",
            severity="low",
            message="方案包含TEC入口控制但缺少下游诱导",
            suggestion="建议在下游增加VSS策略，引导车流平稳通过"
        ))

    return warnings, suggestions
