"""
系统配置工具

提供从 config/system_config.json 读取配置的功能
"""

import json
import os
import logging
import multiprocessing
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _get_cpu_count() -> int:
    """
    获取CPU数量

    优先级（从高到低）：
    1. 环境变量 NUMBER_OF_PROCESSORS (Windows)
    2. multiprocessing.cpu_count()

    Returns:
        int: CPU核心数
    """
    # 优先级1: Windows环境变量 NUMBER_OF_PROCESSORS
    if cpu_str := os.getenv("NUMBER_OF_PROCESSORS"):
        try:
            cpu_count = int(cpu_str)
            if cpu_count > 0:
                logger.debug(f"Using CPU count from NUMBER_OF_PROCESSORS: {cpu_count}")
                return cpu_count
        except ValueError:
            logger.warning(f"Invalid NUMBER_OF_PROCESSORS value: {cpu_str}")

    # 优先级2: Python multiprocessing.cpu_count()
    try:
        cpu_count = multiprocessing.cpu_count()
        logger.debug(f"Using CPU count from multiprocessing.cpu_count(): {cpu_count}")
        return cpu_count
    except NotImplementedError:
        logger.warning("multiprocessing.cpu_count() not available, defaulting to 4")
        return 4


def get_parallel_workers() -> int:
    """
    获取默认的并行仿真工作线程数

    类似于 get_max_concurrent_simulations()，但用于事件场景批量仿真
    优先级逻辑与控制方案批量仿真保持一致

    优先级（从高到低）：
    1. 配置文件 config/system_config.json 中的 batch_simulation.parallel_workers
    2. 配置文件 config/system_config.json 中的 concurrent_simulations_ratio (基于CPU计算)
    3. 默认值：4

    约束：最小值2，最大值64（对应API定义）

    Returns:
        int: 推荐的并行工作线程数
    """
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "system_config.json"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                batch_config = config.get("batch_simulation", {})

                # 优先级1: 专门的 parallel_workers 配置
                if "parallel_workers" in batch_config:
                    workers = int(batch_config["parallel_workers"])
                    if 2 <= workers <= 64:
                        logger.info(f"Using parallel_workers={workers} from config file")
                        return workers
                    else:
                        logger.warning(f"Invalid parallel_workers={workers}, must be in [2, 64]")

                # 优先级2: 从 concurrent_simulations_ratio 计算
                ratio = batch_config.get("concurrent_simulations_ratio")
                if ratio is not None:
                    try:
                        ratio = float(ratio)
                        cpu_count = _get_cpu_count()
                        workers = int(cpu_count * ratio)
                        workers = max(2, min(64, workers))  # 约束在 [2, 64] 范围内
                        logger.info(
                            f"Calculated parallel_workers={workers} from "
                            f"concurrent_simulations_ratio={ratio} ({cpu_count} CPUs)"
                        )
                        return workers
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse concurrent_simulations_ratio: {e}")

    except (json.JSONDecodeError, OSError, KeyError) as e:
        logger.warning(f"Failed to load parallel_workers config: {e}")

    # 默认值
    logger.info("Using default parallel_workers=4")
    return 4


def get_parallel_workers_with_default(requested_workers: Optional[int] = None) -> int:
    """
    获取并行工作线程数，支持请求值和默认值的结合

    Args:
        requested_workers: 用户请求的工作线程数（可选）。
                          如果为None，使用配置文件中的默认值

    Returns:
        int: 最终使用的并行工作线程数
    """
    # 如果用户有请求值，检查其有效性
    if requested_workers is not None:
        if 2 <= requested_workers <= 64:
            logger.info(f"Using requested parallel_workers={requested_workers}")
            return requested_workers
        else:
            logger.warning(
                f"Requested parallel_workers={requested_workers} out of range [2, 64], "
                f"falling back to config default"
            )

    # 否则使用配置默认值
    return get_parallel_workers()
