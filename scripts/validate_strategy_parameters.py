"""
验证策略实例参数结构一致性

检查保留的14个真实数据分析策略实例，确保它们的参数结构与API创建策略实例的结构一致，
以便能够正常用于方案生成。
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_template(template_id: str) -> Optional[Dict[str, Any]]:
    """加载模板定义"""
    # 查找模板文件
    template_dirs = [
        Path("templates/control_strategies"),
        Path("control_data/templates"),
    ]
    
    for base_dir in template_dirs:
        if not base_dir.exists():
            continue
            
        # 尝试不同路径
        for pattern in [
            f"{template_id}.json",
            f"**/{template_id}.json"
        ]:
            for path in base_dir.glob(pattern):
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except Exception as e:
                    logger.warning(f"无法加载模板 {path}: {e}")
                    continue
    
    return None


def extract_parameters_from_strategy(strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    从策略实例中提取参数，支持两种schema格式
    
    Returns:
        参数字典
    """
    if "parameters" in strategy:
        # API创建格式
        return strategy["parameters"]
    elif "configured_params" in strategy:
        # 真实数据分析格式
        return strategy["configured_params"]
    else:
        return {}


def check_strategy_structure(strategy_file: Path, template: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    检查单个策略实例的结构
    
    Returns:
        检查结果字典
    """
    try:
        strategy = json.loads(strategy_file.read_text(encoding="utf-8"))
    except Exception as e:
        return {
            "status": "error",
            "error": f"无法读取文件: {e}"
        }
    
    strategy_id = strategy.get("strategy_id", "unknown")
    strategy_type = strategy.get("strategy_type", "UNKNOWN")
    template_id = strategy.get("template_id", "")
    
    issues = []
    warnings = []
    
    # 1. 检查是否有template字段（方案生成需要）
    if "template" not in strategy:
        issues.append("缺少 'template' 字段（方案生成需要）")
        # 尝试加载模板
        if template:
            warnings.append(f"可以自动添加template字段（模板已加载）")
    
    # 2. 检查参数结构
    has_parameters = "parameters" in strategy
    has_configured_params = "configured_params" in strategy
    
    if has_configured_params and not has_parameters:
        issues.append("使用 'configured_params' 而非 'parameters'（应统一为'parameters'）")
        warnings.append("可以通过转换将configured_params映射到parameters")
    
    # 3. 检查affected_edges位置
    params = extract_parameters_from_strategy(strategy)
    has_affected_edges_in_params = "affected_edges" in params
    has_affected_edges_top_level = "affected_edges" in strategy
    
    if strategy_type in ["VSS", "DHS"]:
        if not has_affected_edges_top_level and not has_affected_edges_in_params:
            issues.append("缺少 'affected_edges' 字段")
        elif has_affected_edges_in_params and not has_affected_edges_top_level:
            issues.append("'affected_edges' 在参数内，应在顶层或parameters内")
    
    # 4. 检查TEC的entrance_edges
    if strategy_type == "TEC":
        has_entrance_edges = "entrance_edges" in params
        has_entrance_edge = "entrance_edge" in params
        if not has_entrance_edges and not has_entrance_edge:
            issues.append("TEC策略缺少 'entrance_edges' 或 'entrance_edge'")
        elif has_entrance_edge and not has_entrance_edges:
            issues.append("TEC策略使用 'entrance_edge'（单数），应使用 'entrance_edges'（复数数组）")
    
    # 5. 检查metadata结构
    has_metadata = "metadata" in strategy
    has_top_level_metadata = any(
        key in strategy 
        for key in ["created_at", "updated_at", "created_by"]
    )
    
    if not has_metadata and has_top_level_metadata:
        issues.append("使用顶层metadata字段，应统一为嵌套'metadata'对象")
        warnings.append("可以自动转换为metadata对象格式")
    
    # 6. 检查参数是否符合模板schema（如果有模板）
    if template:
        params_schema = template.get("parameters_schema", [])
        params = extract_parameters_from_strategy(strategy)
        
        # 检查必需的参数
        for param_def in params_schema:
            param_name = param_def.get("parameter_name", "")
            required = param_def.get("required", False)
            
            if required and param_name not in params:
                issues.append(f"缺少必需参数: {param_name}")
    
    # 7. 检查是否有affected_edges在顶层（API格式要求）
    if strategy_type in ["VSS", "DHS"]:
        if not has_affected_edges_top_level:
            issues.append("缺少顶层 'affected_edges' 字段（API格式要求）")
    
    return {
        "status": "ok" if not issues else "has_issues",
        "strategy_id": strategy_id,
        "strategy_type": strategy_type,
        "template_id": template_id,
        "issues": issues,
        "warnings": warnings,
        "has_template": "template" in strategy,
        "has_parameters": has_parameters,
        "has_configured_params": has_configured_params,
        "affected_edges_location": "top_level" if has_affected_edges_top_level else ("in_params" if has_affected_edges_in_params else "missing"),
    }


def validate_all_strategies() -> None:
    """验证所有策略实例"""
    strategies_dir = Path("control_data/strategies")
    
    if not strategies_dir.exists():
        logger.error(f"策略目录不存在: {strategies_dir}")
        return
    
    # 加载所有真实数据分析策略
    strategy_files = list(strategies_dir.glob("strategy_real_*.json"))
    
    if not strategy_files:
        logger.warning("未找到真实数据分析策略实例")
        return
    
    logger.info(f"找到 {len(strategy_files)} 个真实数据分析策略实例")
    logger.info("=" * 80)
    
    all_issues = []
    strategies_need_fix = []
    
    for strategy_file in sorted(strategy_files):
        logger.info(f"\n检查: {strategy_file.name}")
        logger.info("-" * 80)
        
        # 加载策略以获取template_id
        try:
            strategy = json.loads(strategy_file.read_text(encoding="utf-8"))
            template_id = strategy.get("template_id", "")
        except Exception as e:
            logger.error(f"无法读取策略文件: {e}")
            continue
        
        # 加载模板
        template = None
        if template_id:
            template = load_template(template_id)
            if template:
                logger.info(f"已加载模板: {template_id}")
            else:
                logger.warning(f"无法加载模板: {template_id}")
        
        # 检查结构
        result = check_strategy_structure(strategy_file, template)
        
        if result["status"] == "error":
            logger.error(f"检查失败: {result.get('error')}")
            all_issues.append((strategy_file.name, result))
            continue
        
        # 显示结果
        logger.info(f"策略ID: {result['strategy_id']}")
        logger.info(f"策略类型: {result['strategy_type']}")
        logger.info(f"模板ID: {result['template_id']}")
        
        if result["issues"]:
            logger.warning(f"发现问题 ({len(result['issues'])} 个):")
            for issue in result["issues"]:
                logger.warning(f"  ❌ {issue}")
            all_issues.append((strategy_file.name, result))
            strategies_need_fix.append(strategy_file)
        else:
            logger.info("✅ 无问题")
        
        if result["warnings"]:
            logger.info(f"提示 ({len(result['warnings'])} 个):")
            for warning in result["warnings"]:
                logger.info(f"  ℹ️  {warning}")
        
        logger.info(f"参数位置: {result['affected_edges_location']}")
        logger.info(f"是否有template字段: {result['has_template']}")
        logger.info(f"参数格式: {'parameters' if result['has_parameters'] else 'configured_params' if result['has_configured_params'] else 'none'}")
    
    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("检查总结")
    logger.info("=" * 80)
    logger.info(f"总策略数: {len(strategy_files)}")
    logger.info(f"有问题: {len(all_issues)}")
    logger.info(f"无问题: {len(strategy_files) - len(all_issues)}")
    
    if strategies_need_fix:
        logger.info(f"\n需要修复的策略 ({len(strategies_need_fix)} 个):")
        for strategy_file in strategies_need_fix:
            logger.info(f"  - {strategy_file.name}")
        logger.info("\n建议运行修复脚本统一格式")


if __name__ == "__main__":
    validate_all_strategies()

