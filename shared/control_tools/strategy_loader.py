"""
策略实例加载器

从文件系统加载已保存的策略实例
"""

import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


def load_strategies_index(strategies_dir: Path) -> Dict[str, Any]:
    """
    加载策略索引文件

    Args:
        strategies_dir: 策略目录路径

    Returns:
        索引数据字典，失败时返回空结构
    """
    index_path = strategies_dir / "strategies_index.json"

    try:
        if not index_path.exists():
            logger.warning(f"Strategies index not found: {index_path}")
            return {
                "version": "1.0",
                "total_count": 0,
                "strategies_by_type": {},
                "strategies": []
            }

        with open(index_path, 'r', encoding='utf-8') as f:
            index_data = json.load(f)

        logger.info(
            f"Loaded strategies index: {index_data.get('total_count', 0)} strategies"
        )
        return index_data

    except Exception as e:
        logger.error(f"Error loading strategies index: {e}", exc_info=True)
        return {
            "version": "1.0",
            "total_count": 0,
            "strategies_by_type": {},
            "strategies": []
        }


def load_strategy_detail(strategy_id: str, strategies_dir: Path) -> Optional[Dict[str, Any]]:
    """
    加载单个策略的完整详情

    Args:
        strategy_id: 策略ID
        strategies_dir: 策略目录路径

    Returns:
        策略详情字典，失败时返回None
    """
    strategy_path = strategies_dir / f"{strategy_id}.json"

    try:
        if not strategy_path.exists():
            logger.warning(f"Strategy file not found: {strategy_path}")
            return None

        with open(strategy_path, 'r', encoding='utf-8') as f:
            strategy_data = json.load(f)

        logger.debug(f"Loaded strategy detail: {strategy_id}")
        return strategy_data

    except Exception as e:
        logger.error(f"Error loading strategy {strategy_id}: {e}", exc_info=True)
        return None


def list_all_strategies(
    strategies_dir: Path,
    strategy_type: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    列出所有策略（支持筛选）

    Args:
        strategies_dir: 策略目录路径
        strategy_type: 策略类型筛选 (VSS/DHS/TEC)
        tags: 标签筛选（匹配任一标签即可）
        status: 状态筛选 (active/inactive)

    Returns:
        策略列表（简要信息）
    """
    try:
        # 加载索引
        index_data = load_strategies_index(strategies_dir)
        strategies = index_data.get("strategies", [])

        # 应用筛选
        if strategy_type:
            strategies = [
                s for s in strategies
                if s.get("strategy_type") == strategy_type
            ]

        if status:
            strategies = [
                s for s in strategies
                if s.get("status") == status
            ]

        if tags:
            strategies = [
                s for s in strategies
                if any(tag in s.get("tags", []) for tag in tags)
            ]

        logger.info(
            f"Filtered strategies: {len(strategies)} "
            f"(type={strategy_type}, status={status}, tags={tags})"
        )

        return strategies

    except Exception as e:
        logger.error(f"Error listing strategies: {e}", exc_info=True)
        return []


def get_strategies_summary(strategies_dir: Path) -> Dict[str, Any]:
    """
    获取策略统计摘要

    Args:
        strategies_dir: 策略目录路径

    Returns:
        统计信息字典
    """
    try:
        index_data = load_strategies_index(strategies_dir)

        return {
            "total_count": index_data.get("total_count", 0),
            "strategies_by_type": index_data.get("strategies_by_type", {}),
            "last_updated": index_data.get("last_updated"),
            "version": index_data.get("version", "1.0")
        }

    except Exception as e:
        logger.error(f"Error getting strategies summary: {e}", exc_info=True)
        return {
            "total_count": 0,
            "strategies_by_type": {},
            "last_updated": None,
            "version": "1.0"
        }
