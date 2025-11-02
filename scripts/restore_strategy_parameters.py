"""
恢复策略实例中丢失的参数

根据模板要求和备份文件中的具体数值，补回在修复过程中遗失的参数。
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 项目根目录
project_root = Path(__file__).parent.parent
strategies_dir = project_root / "control_data" / "strategies"
templates_dir = project_root / "templates" / "control_strategies"


def load_template(template_id: str) -> Optional[Dict[str, Any]]:
    """加载策略模板"""
    # 根据template_id推断路径
    if template_id.startswith("vss_"):
        template_path = templates_dir / "variable_speed_sign" / f"{template_id}.json"
    elif template_id.startswith("dhs_"):
        template_path = templates_dir / "dynamic_hard_shoulder" / f"{template_id}.json"
    elif template_id.startswith("tec_"):
        template_path = templates_dir / "toll_entrance_control" / f"{template_id}.json"
    else:
        logger.warning(f"无法推断模板路径: {template_id}")
        return None
    
    if not template_path.exists():
        logger.warning(f"模板文件不存在: {template_path}")
        return None
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载模板失败 {template_path}: {e}")
        return None


def get_required_parameters(template: Dict[str, Any]) -> List[str]:
    """从模板中提取必需参数名列表"""
    required_params = []
    parameters_schema = template.get("parameters_schema", [])
    
    for param_def in parameters_schema:
        param_name = param_def.get("parameter_name")
        required = param_def.get("required", False)
        
        # affected_edges和entrance_edges已经在parameters中，跳过
        if param_name in ["affected_edges", "entrance_edges"]:
            continue
        
        if required:
            required_params.append(param_name)
    
    return required_params


def get_parameter_name_mapping() -> Dict[str, List[str]]:
    """
    返回参数名称映射关系（处理历史变更带来的名称差异）
    
    返回: {标准名称: [可能的旧名称列表]}
    """
    return {
        "speed_steps": ["speed_steps"],  # 无变化
        "intervals": ["intervals"],  # DHS无变化
        "flow_intervals": ["flow_intervals"],  # TEC无变化
        "entrance_edges": ["entrance_edges", "entrance_edge"],  # 单复数差异
        "affected_edges": ["affected_edges"],  # 无变化
    }


def restore_parameters_from_backup(
    strategy: Dict[str, Any],
    backup_file: Path,
    template: Dict[str, Any]
) -> Dict[str, Any]:
    """
    从备份文件中恢复丢失的参数（优先从备份文件恢复）
    
    策略：
    1. 优先从备份文件的parameters/configured_params中获取（处理名称差异）
    2. 如果备份文件中没有，从模板的default_value获取
    3. 合并所有备份中的非edges参数
    """
    # 加载备份文件
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_strategy = json.load(f)
    except Exception as e:
        logger.error(f"加载备份文件失败 {backup_file}: {e}")
        return strategy.get("parameters", {})
    
    # 获取备份文件中的parameters（可能在不同位置或不同名称）
    backup_params = {}
    if "parameters" in backup_strategy:
        backup_params = backup_strategy["parameters"].copy()
    elif "configured_params" in backup_strategy:
        backup_params = backup_strategy["configured_params"].copy()
    
    # 获取当前parameters（已包含edges）
    current_params = strategy.get("parameters", {}).copy()
    
    # 获取参数名称映射
    name_mapping = get_parameter_name_mapping()
    
    # 获取模板要求的必需参数
    required_params = get_required_parameters(template) if template else []
    
    # 策略：先恢复所有备份中的参数（不仅仅是必需参数，因为可能还有其他参数）
    restored_params = {}
    restored_count = 0
    
    # 1. 优先从备份中恢复所有参数（处理名称差异）
    for standard_name, possible_names in name_mapping.items():
        # 如果当前已有且不为空，跳过
        if standard_name in current_params and current_params.get(standard_name):
            continue
        
        # 尝试从备份中查找（包括可能的旧名称）
        found = False
        for old_name in possible_names:
            if old_name in backup_params and backup_params[old_name]:
                # 处理单复数转换（entrance_edge -> entrance_edges）
                if old_name == "entrance_edge" and standard_name == "entrance_edges":
                    value = backup_params[old_name]
                    restored_params[standard_name] = [value] if isinstance(value, str) else value
                else:
                    restored_params[standard_name] = backup_params[old_name]
                
                found = True
                restored_count += 1
                value_desc = len(restored_params[standard_name]) if isinstance(restored_params[standard_name], list) else 1
                logger.info(f"  从备份恢复参数 {standard_name} (原名称: {old_name}): {value_desc} 项")
                break
        
        # 如果没有找到，且是必需参数，尝试从模板default_value获取
        if not found and standard_name in required_params:
            param_def = next(
                (p for p in template.get("parameters_schema", []) 
                 if p.get("parameter_name") == standard_name),
                None
            ) if template else None
            
            if param_def and "default_value" in param_def:
                restored_params[standard_name] = param_def["default_value"]
                restored_count += 1
                logger.info(f"  使用模板默认值恢复参数 {standard_name}")
    
    # 2. 恢复备份中其他非edges的参数（可能不是必需参数，但有实际值）
    for param_name, param_value in backup_params.items():
        # 跳过edges相关参数（已经在current_params中）
        if param_name in ["affected_edges", "entrance_edges", "entrance_edge"]:
            continue
        
        # 如果当前没有这个参数，且备份中有值，则恢复
        if param_name not in current_params or not current_params.get(param_name):
            if param_value:  # 只恢复有值的参数
                restored_params[param_name] = param_value
                restored_count += 1
                value_desc = len(param_value) if isinstance(param_value, list) else 1
                logger.info(f"  从备份恢复额外参数 {param_name}: {value_desc} 项")
    
    # 合并恢复的参数到当前参数
    current_params.update(restored_params)
    
    if restored_count > 0:
        logger.info(f"  ✅ 恢复了 {restored_count} 个参数")
    else:
        logger.info(f"  ℹ️  无需恢复参数（已完整）")
    
    return current_params


def restore_timestamps(
    strategy: Dict[str, Any],
    backup_file: Path
) -> Dict[str, Any]:
    """
    从备份文件中恢复创建时间和更新时间
    
    可能位置：
    1. metadata.created_at / metadata.updated_at
    2. 顶层 created_at / updated_at
    
    如果备份文件中没有，使用默认时间：2025-10-28T08:00:00Z
    """
    # 默认时间戳（2025年10月28日8点整）
    DEFAULT_TIMESTAMP = "2025-10-28T08:00:00Z"
    
    try:
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_strategy = json.load(f)
    except Exception as e:
        logger.error(f"加载备份文件失败 {backup_file}: {e}")
        backup_strategy = {}
    
    # 获取备份中的时间戳
    backup_created_at = None
    backup_updated_at = None
    
    # 优先从metadata获取
    if "metadata" in backup_strategy:
        backup_metadata = backup_strategy["metadata"]
        backup_created_at = backup_metadata.get("created_at")
        backup_updated_at = backup_metadata.get("updated_at")
    
    # 如果metadata中没有，尝试从顶层获取
    if not backup_created_at or not backup_created_at.strip():
        backup_created_at = backup_strategy.get("created_at")
    if not backup_updated_at or not backup_updated_at.strip():
        backup_updated_at = backup_strategy.get("updated_at")
    
    # 恢复时间戳
    updated = False
    
    # 确保metadata存在
    if "metadata" not in strategy:
        strategy["metadata"] = {}
    
    current_created_at = strategy["metadata"].get("created_at", "")
    current_updated_at = strategy["metadata"].get("updated_at", "")
    
    # 恢复created_at（优先使用备份中的值，如果为空则使用默认时间）
    if not current_created_at or not current_created_at.strip():
        if backup_created_at and backup_created_at.strip():
            strategy["metadata"]["created_at"] = backup_created_at
            logger.info(f"  恢复创建时间: {backup_created_at}")
        else:
            strategy["metadata"]["created_at"] = DEFAULT_TIMESTAMP
            logger.info(f"  补充默认创建时间: {DEFAULT_TIMESTAMP}")
        updated = True
    
    # 恢复updated_at（优先使用备份中的值，如果为空则使用默认时间）
    if not current_updated_at or not current_updated_at.strip():
        if backup_updated_at and backup_updated_at.strip():
            strategy["metadata"]["updated_at"] = backup_updated_at
            logger.info(f"  恢复更新时间: {backup_updated_at}")
        else:
            strategy["metadata"]["updated_at"] = DEFAULT_TIMESTAMP
            logger.info(f"  补充默认更新时间: {DEFAULT_TIMESTAMP}")
        updated = True
    
    if updated:
        logger.info(f"  ✅ 时间戳已处理")
    else:
        logger.info(f"  ℹ️  时间戳无需更新")
    
    return strategy


def restore_strategy_file(strategy_file: Path, backup: bool = True) -> bool:
    """恢复单个策略文件的参数"""
    logger.info(f"\n处理: {strategy_file.name}")
    
    # 加载当前策略
    try:
        with open(strategy_file, 'r', encoding='utf-8') as f:
            strategy = json.load(f)
    except Exception as e:
        logger.error(f"加载策略文件失败: {e}")
        return False
    
    # 查找备份文件（优先查找更早的备份）
    backup_file = None
    # 尝试按优先级查找备份文件
    backup_candidates = [
        strategy_file.with_suffix('.json.backup2'),  # 更早的备份
        strategy_file.with_suffix('.json.backup'),   # 最近的备份
    ]
    
    # 也尝试查找所有匹配的备份文件
    all_backups = list(strategy_file.parent.glob(f"{strategy_file.stem}*.backup*"))
    all_backups.sort(key=lambda p: p.name)  # 按文件名排序（.backup2优先于.backup）
    
    for candidate in backup_candidates + all_backups:
        if candidate.exists():
            backup_file = candidate
            logger.info(f"使用备份文件: {backup_file.name}")
            break
    
    if not backup_file or not backup_file.exists():
        logger.error(f"未找到任何备份文件")
        return False
    
    # 加载模板
    template_id = strategy.get("template_id", "")
    template = load_template(template_id)
    if not template:
        logger.warning(f"无法加载模板 {template_id}，将仅从备份恢复")
    
    # 恢复参数（优先从备份文件）
    if backup_file.exists():
        restored_params = restore_parameters_from_backup(strategy, backup_file, template)
        
        # 更新策略参数
        strategy["parameters"] = restored_params
        
        # 恢复时间戳
        strategy = restore_timestamps(strategy, backup_file)
        
        # 创建新备份（如果需要）
        if backup:
            new_backup = strategy_file.with_suffix('.json.backup2')
            try:
                with open(new_backup, 'w', encoding='utf-8') as f:
                    json.dump(strategy, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logger.warning(f"创建新备份失败: {e}")
        
        # 保存修复后的策略
        try:
            with open(strategy_file, 'w', encoding='utf-8') as f:
                json.dump(strategy, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 修复完成: {strategy_file.name}")
            return True
        except Exception as e:
            logger.error(f"保存策略文件失败: {e}")
            return False
    else:
        logger.warning(f"备份文件不存在，无法恢复")
        return False


def main():
    """主函数"""
    logger.info("=" * 80)
    logger.info("恢复策略实例参数")
    logger.info("=" * 80)
    
    # 查找所有真实数据策略实例
    strategy_files = list(strategies_dir.glob("strategy_real_*.json"))
    
    logger.info(f"找到 {len(strategy_files)} 个策略实例需要检查")
    logger.info("=" * 80)
    
    success_count = 0
    fail_count = 0
    
    for strategy_file in sorted(strategy_files):
        if restore_strategy_file(strategy_file, backup=True):
            success_count += 1
        else:
            fail_count += 1
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("恢复总结")
    logger.info("=" * 80)
    logger.info(f"总策略数: {len(strategy_files)}")
    logger.info(f"成功: {success_count}")
    logger.info(f"失败: {fail_count}")
    logger.info("")
    logger.info("建议验证恢复结果:")
    logger.info("  python scripts/validate_strategy_parameters.py")


if __name__ == "__main__":
    main()

