"""
修复策略实例结构，统一为API格式

将所有真实数据分析策略实例转换为与API创建策略实例一致的格式：
1. 添加template字段
2. 将configured_params转换为parameters
3. 提取affected_edges到顶层
4. 将顶层metadata字段转换为嵌套metadata对象
5. 保留其他字段（description, tags, data_source等）
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_template(template_id: str) -> Optional[Dict[str, Any]]:
    """加载模板定义"""
    template_dirs = [
        Path("templates/control_strategies"),
        Path("control_data/templates"),
    ]
    
    for base_dir in template_dirs:
        if not base_dir.exists():
            continue
            
        for pattern in [
            f"{template_id}.json",
            f"**/{template_id}.json"
        ]:
            for path in base_dir.glob(pattern):
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except Exception as e:
                    logger.debug(f"无法加载模板 {path}: {e}")
                    continue
    
    return None


def convert_strategy_to_api_format(strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    将真实数据分析策略格式转换为API格式
    
    转换规则：
    1. configured_params -> parameters
    2. 提取affected_edges到顶层
    3. 顶层metadata字段 -> metadata对象
    4. 添加template字段
    5. 保留其他字段（description, tags, data_source等）
    """
    template_id = strategy.get("template_id", "")
    strategy_type = strategy.get("strategy_type", "")
    
    # 加载模板
    template = load_template(template_id)
    if not template:
        logger.warning(f"无法加载模板 {template_id}，将不添加template字段")
    
    # 1. 提取configured_params作为parameters（严格格式：edges保留在parameters中）
    configured_params = strategy.get("configured_params", {})
    parameters = configured_params.copy()
    
    # 2. 确保affected_edges在parameters中（VSS/DHS）
    if strategy_type in ["VSS", "DHS"]:
        # 确保affected_edges在parameters中（不从parameters移除）
        if "affected_edges" not in parameters:
            # 如果parameters中没有，尝试从顶层获取（向后兼容迁移）
            if "affected_edges" in strategy:
                parameters["affected_edges"] = strategy["affected_edges"]
            else:
                logger.warning(f"Strategy {strategy.get('strategy_id')} missing affected_edges")
    
    # 3. 处理TEC的entrance_edges（确保在parameters中）
    if strategy_type == "TEC":
        # entrance_edges必须在parameters中
        if "entrance_edge" in parameters:
            # 单个入口转换为数组
            entrance_edge = parameters.pop("entrance_edge")
            parameters["entrance_edges"] = [entrance_edge] if entrance_edge else []
        elif "entrance_edges" not in parameters:
            # 如果parameters中没有，尝试从顶层affected_edges获取（向后兼容迁移）
            if "affected_edges" in strategy:
                parameters["entrance_edges"] = strategy["affected_edges"]
            else:
                logger.warning(f"Strategy {strategy.get('strategy_id')} missing entrance_edges")
    
    # 4. 构建metadata对象
    metadata = {
        "created_at": strategy.get("created_at", ""),
        "updated_at": strategy.get("updated_at", strategy.get("created_at", "")),
        "created_by": strategy.get("created_by", "system"),
        "version": strategy.get("version", 1),
    }
    
    # 5. 构建新的策略结构（严格格式：edges只在parameters中）
    new_strategy = {
        "strategy_id": strategy["strategy_id"],
        "strategy_name": strategy["strategy_name"],
        "template_id": template_id,
        "template_name": strategy.get("template_name", template.get("template_name", "") if template else ""),
        "strategy_type": strategy_type,
        "parameters": parameters,  # edges已包含在parameters中
        # 不再设置顶层affected_edges（严格格式）
        "metadata": metadata,
    }
    
    # 6. 保留其他可选字段
    optional_fields = ["description", "tags", "data_source", "status", "referenced_by"]
    for field in optional_fields:
        if field in strategy:
            new_strategy[field] = strategy[field]
    
    # 7. 添加template字段（方案生成需要）
    if template:
        new_strategy["template"] = template
    
    # 8. 确保移除顶层affected_edges字段（严格格式）
    # 注意：不在这里删除，而是在构建时就不包含它
    # 但为了安全，确保旧文件中的顶层字段不影响新格式
    
    return new_strategy


def fix_strategy_file(strategy_file: Path, backup: bool = True) -> bool:
    """
    修复单个策略文件
    
    Args:
        strategy_file: 策略文件路径
        backup: 是否创建备份
    
    Returns:
        True if success
    """
    try:
        # 读取原始策略
        strategy = json.loads(strategy_file.read_text(encoding="utf-8"))
        
        # 创建备份
        if backup:
            backup_path = strategy_file.with_suffix(".json.backup")
            backup_path.write_text(json.dumps(strategy, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info(f"已创建备份: {backup_path.name}")
        
        # 转换格式
        new_strategy = convert_strategy_to_api_format(strategy)
        
        # 保存新格式
        strategy_file.write_text(
            json.dumps(new_strategy, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        logger.info(f"✅ 修复完成: {strategy_file.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 修复失败 {strategy_file.name}: {e}", exc_info=True)
        return False


def fix_all_strategies(backup: bool = True) -> None:
    """修复所有策略实例"""
    strategies_dir = Path("control_data/strategies")
    
    if not strategies_dir.exists():
        logger.error(f"策略目录不存在: {strategies_dir}")
        return
    
    # 查找所有真实数据分析策略
    strategy_files = list(strategies_dir.glob("strategy_real_*.json"))
    
    if not strategy_files:
        logger.warning("未找到真实数据分析策略实例")
        return
    
    logger.info(f"找到 {len(strategy_files)} 个策略实例需要修复")
    logger.info("=" * 80)
    
    success_count = 0
    failed_count = 0
    
    for strategy_file in sorted(strategy_files):
        logger.info(f"\n处理: {strategy_file.name}")
        if fix_strategy_file(strategy_file, backup=backup):
            success_count += 1
        else:
            failed_count += 1
    
    # 总结
    logger.info("\n" + "=" * 80)
    logger.info("修复总结")
    logger.info("=" * 80)
    logger.info(f"总策略数: {len(strategy_files)}")
    logger.info(f"成功: {success_count}")
    logger.info(f"失败: {failed_count}")
    
    if success_count > 0:
        logger.info("\n建议运行验证脚本确认修复结果")
        logger.info("python scripts/validate_strategy_parameters.py")


if __name__ == "__main__":
    import sys
    
    backup = "--no-backup" not in sys.argv
    if not backup:
        logger.warning("⚠️  未启用备份模式，原始文件将被直接修改")
        response = input("确认继续？(yes/no): ")
        if response.lower() != "yes":
            logger.info("已取消")
            sys.exit(0)
    
    fix_all_strategies(backup=backup)

