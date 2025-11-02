"""
清理测试过程中生成的策略实例

删除所有以 strat_2025 开头的测试策略实例（保留真实数据分析生成的 strategy_real_* 策略）
并重新生成索引文件。
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def cleanup_test_strategies(strategies_dir: str = "control_data/strategies") -> None:
    """
    清理测试生成的策略实例。
    
    Args:
        strategies_dir: 策略存储目录路径
    """
    strategies_path = Path(strategies_dir)
    
    if not strategies_path.exists():
        logger.warning(f"策略目录不存在: {strategies_dir}")
        return
    
    # 查找所有以 strat_2025 开头的策略文件（测试生成的）
    test_strategy_files = list(strategies_path.glob("strat_2025*.json"))
    
    if not test_strategy_files:
        logger.info("未找到测试策略实例")
        return
    
    logger.info(f"找到 {len(test_strategy_files)} 个测试策略实例")
    
    # 显示将要删除的策略
    logger.info("即将删除的测试策略:")
    for file_path in sorted(test_strategy_files):
        try:
            strategy_data = json.loads(file_path.read_text(encoding="utf-8"))
            strategy_name = strategy_data.get("strategy_name", "未知")
            logger.info(f"  - {file_path.name}: {strategy_name}")
        except Exception as e:
            logger.warning(f"  - {file_path.name}: 无法读取文件内容 ({e})")
    
    # 删除测试策略文件
    deleted_count = 0
    failed_count = 0
    
    for file_path in test_strategy_files:
        try:
            file_path.unlink()
            deleted_count += 1
            logger.debug(f"已删除: {file_path.name}")
        except Exception as e:
            logger.error(f"删除失败 {file_path.name}: {e}")
            failed_count += 1
    
    logger.info(f"删除完成: 成功 {deleted_count} 个, 失败 {failed_count} 个")
    
    # 重新生成索引
    logger.info("重新生成索引...")
    try:
        import sys
        
        # 添加项目根目录到 Python 路径
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
        
        from shared.control_tools.strategy_file_manager import regenerate_index
        
        strategies_count = regenerate_index(strategies_dir)
        logger.info(f"索引重新生成完成，剩余 {strategies_count} 个策略实例")
        
        # 显示保留的策略
        index_path = strategies_path / "strategies_index.json"
        if index_path.exists():
            index_data = json.loads(index_path.read_text(encoding="utf-8"))
            strategies = index_data.get("strategies", [])
            logger.info(f"保留的策略实例 ({len(strategies)} 个):")
            for strategy in strategies:
                logger.info(f"  - {strategy['strategy_id']}: {strategy['strategy_name']}")
        
    except Exception as e:
        logger.error(f"重新生成索引失败: {e}", exc_info=True)


if __name__ == "__main__":
    cleanup_test_strategies()
