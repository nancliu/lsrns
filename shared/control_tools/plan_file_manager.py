"""
方案文件管理器

职责：
- 管理方案文件的创建、读取、更新、删除
- 维护方案索引 (plans_index.json)
- 处理方案目录结构
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger(__name__)

# 常量定义
PLANS_BASE_DIR = Path("control_data/plans")
BASELINE_PLAN_ID = "baseline_plan"
PLANS_INDEX_FILE = "plans_index.json"


def _generate_plan_id() -> str:
    """
    生成方案ID

    格式: plan_YYYYMMDD_HHMMSS_xxxxx

    Returns:
        str: 方案ID
    """
    from random import randint
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = f"{randint(10000, 99999):05d}"
    return f"plan_{timestamp}_{random_suffix}"


def _get_plan_dir(plan_id: str) -> Path:
    """获取方案目录路径"""
    return PLANS_BASE_DIR / plan_id


def _ensure_plans_base_dir() -> None:
    """确保方案基础目录存在"""
    PLANS_BASE_DIR.mkdir(parents=True, exist_ok=True)


def _load_plans_index() -> Dict[str, Any]:
    """
    加载方案索引

    Returns:
        Dict: 索引数据，格式: {"plans": []}
    """
    _ensure_plans_base_dir()
    index_file = PLANS_BASE_DIR / PLANS_INDEX_FILE

    if not index_file.exists():
        return {"plans": []}

    try:
        with open(index_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载方案索引失败: {e}")
        return {"plans": []}


def _save_plans_index(index_data: Dict[str, Any]) -> None:
    """
    保存方案索引

    Args:
        index_data: 索引数据
    """
    _ensure_plans_base_dir()
    index_file = PLANS_BASE_DIR / PLANS_INDEX_FILE

    try:
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        logger.info(f"方案索引已保存: {index_file}")
    except Exception as e:
        logger.error(f"保存方案索引失败: {e}")
        raise


def create_plan(plan_data: Dict[str, Any]) -> str:
    """
    创建方案

    Args:
        plan_data: 方案数据字典

    Returns:
        str: 方案ID

    Raises:
        ValueError: 参数验证失败
        IOError: 文件操作失败
    """
    # 验证必填字段
    if "plan_name" not in plan_data:
        raise ValueError("缺少必填字段: plan_name")

    # 生成方案ID
    plan_id = _generate_plan_id()
    plan_dir = _get_plan_dir(plan_id)

    try:
        # 创建方案目录
        plan_dir.mkdir(parents=True, exist_ok=True)

        # 准备元数据
        now = datetime.now().isoformat()
        metadata = {
            "plan_id": plan_id,
            "plan_name": plan_data["plan_name"],
            "description": plan_data.get("description"),
            "strategy_ids": plan_data.get("strategy_ids", []),
            "tags": plan_data.get("tags", []),
            "target_scenario": plan_data.get("target_scenario"),
            "expected_effects": plan_data.get("expected_effects"),
            "additional_file_path": f"control_data/plans/{plan_id}/control.add.xml",
            "created_at": now,
            "updated_at": now,
        }

        # 保存元数据
        metadata_file = plan_dir / "plan_metadata.json"
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 保存策略引用
        refs_file = plan_dir / "strategy_refs.json"
        with open(refs_file, "w", encoding="utf-8") as f:
            json.dump(metadata["strategy_ids"], f, ensure_ascii=False, indent=2)

        # 更新索引
        index = _load_plans_index()
        index["plans"].append({
            "plan_id": plan_id,
            "plan_name": metadata["plan_name"],
            "is_baseline": plan_id == "baseline_plan",
            "strategy_count": len(metadata["strategy_ids"]),
            "tags": metadata["tags"],
            "created_at": now,
        })
        _save_plans_index(index)

        logger.info(f"方案创建成功: {plan_id}")
        return plan_id

    except Exception as e:
        # 清理失败的目录
        if plan_dir.exists():
            shutil.rmtree(plan_dir, ignore_errors=True)
        logger.error(f"创建方案失败: {e}")
        raise


def get_plan(plan_id: str) -> Dict[str, Any]:
    """
    获取方案详情

    Args:
        plan_id: 方案ID

    Returns:
        Dict: 方案数据

    Raises:
        FileNotFoundError: 方案不存在
    """
    plan_dir = _get_plan_dir(plan_id)
    metadata_file = plan_dir / "plan_metadata.json"

    if not metadata_file.exists():
        raise FileNotFoundError(f"方案不存在: {plan_id}")

    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取方案元数据失败 [{plan_id}]: {e}")
        raise


def update_plan(plan_id: str, updates: Dict[str, Any]) -> None:
    """
    更新方案元数据

    Args:
        plan_id: 方案ID
        updates: 要更新的字段

    Raises:
        FileNotFoundError: 方案不存在
    """
    metadata = get_plan(plan_id)

    # 更新字段
    for key, value in updates.items():
        if value is not None:  # 只更新非None值
            metadata[key] = value

    # 更新时间戳
    metadata["updated_at"] = datetime.now().isoformat()

    # 保存更新
    plan_dir = _get_plan_dir(plan_id)
    metadata_file = plan_dir / "plan_metadata.json"

    try:
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 如果strategy_ids变化，更新strategy_refs.json
        if "strategy_ids" in updates:
            refs_file = plan_dir / "strategy_refs.json"
            with open(refs_file, "w", encoding="utf-8") as f:
                json.dump(metadata["strategy_ids"], f, ensure_ascii=False, indent=2)

        # 更新索引
        index = _load_plans_index()
        for item in index["plans"]:
            if item["plan_id"] == plan_id:
                item["plan_name"] = metadata["plan_name"]
                item["is_baseline"] = len(metadata["strategy_ids"]) == 0
                item["strategy_count"] = len(metadata["strategy_ids"])
                item["tags"] = metadata.get("tags", [])
                break
        _save_plans_index(index)

        logger.info(f"方案更新成功: {plan_id}")

    except Exception as e:
        logger.error(f"更新方案失败 [{plan_id}]: {e}")
        raise


def delete_plan(plan_id: str) -> None:
    """
    删除方案及其文件

    Args:
        plan_id: 方案ID

    Raises:
        ValueError: 尝试删除基准方案
        FileNotFoundError: 方案不存在
    """
    # 防止删除基准方案
    if plan_id == BASELINE_PLAN_ID:
        raise ValueError("不能删除基准方案")

    plan_dir = _get_plan_dir(plan_id)

    if not plan_dir.exists():
        raise FileNotFoundError(f"方案不存在: {plan_id}")

    try:
        # 删除目录
        shutil.rmtree(plan_dir)

        # 更新索引
        index = _load_plans_index()
        index["plans"] = [
            item for item in index["plans"]
            if item["plan_id"] != plan_id
        ]
        _save_plans_index(index)

        logger.info(f"方案删除成功: {plan_id}")

    except Exception as e:
        logger.error(f"删除方案失败 [{plan_id}]: {e}")
        raise


def list_plans(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    列出所有方案（支持过滤）

    Args:
        filters: 过滤条件字典
            - tags: List[str] - 标签过滤（包含任一标签即可）
            - target_scenario: str - 场景过滤（模糊匹配）
            - include_baseline: bool - 是否包含基准方案（默认True）

    Returns:
        List[Dict]: 方案列表
    """
    index = _load_plans_index()
    plans = index.get("plans", [])

    if not filters:
        return plans

    # 应用过滤
    filtered_plans = plans

    # 基准方案过滤
    include_baseline = filters.get("include_baseline", True)
    if not include_baseline:
        filtered_plans = [p for p in filtered_plans if not p.get("is_baseline", False)]

    # 标签过滤
    if "tags" in filters and filters["tags"]:
        filter_tags = set(filters["tags"])
        filtered_plans = [
            p for p in filtered_plans
            if filter_tags & set(p.get("tags", []))
        ]

    # 场景过滤（需要加载完整元数据）
    if "target_scenario" in filters and filters["target_scenario"]:
        scenario_keyword = filters["target_scenario"].lower()
        result = []
        for p in filtered_plans:
            try:
                metadata = get_plan(p["plan_id"])
                target = metadata.get("target_scenario", "")
                if target and scenario_keyword in target.lower():
                    result.append(p)
            except Exception:
                continue
        filtered_plans = result

    return filtered_plans


def get_plan_strategies(plan_id: str) -> List[Dict[str, Any]]:
    """
    获取方案包含的策略实例列表

    Args:
        plan_id: 方案ID

    Returns:
        List[Dict]: 策略实例数据列表

    Raises:
        FileNotFoundError: 方案不存在
    """
    from shared.control_tools.strategy_file_manager import load_strategy

    metadata = get_plan(plan_id)
    strategy_ids = metadata.get("strategy_ids", [])

    strategies = []
    for sid in strategy_ids:
        try:
            strategy = load_strategy(sid)
            strategies.append(strategy)
        except FileNotFoundError:
            logger.warning(f"策略不存在，已跳过: {sid}")
        except Exception as e:
            logger.error(f"加载策略失败 [{sid}]: {e}")

    return strategies


def regenerate_plan_xml(plan_id: str) -> None:
    """
    重新生成方案的control.add.xml

    Args:
        plan_id: 方案ID

    Raises:
        FileNotFoundError: 方案不存在
    """
    from shared.control_tools.additional_generator import generate_plan_additional

    metadata = get_plan(plan_id)
    strategies = get_plan_strategies(plan_id)

    # 生成XML
    xml_content = generate_plan_additional(
        plan_id=plan_id,
        plan_name=metadata["plan_name"],
        strategies=strategies
    )

    # 保存XML
    plan_dir = _get_plan_dir(plan_id)
    xml_file = plan_dir / "control.add.xml"

    try:
        with open(xml_file, "w", encoding="utf-8") as f:
            f.write(xml_content)
        logger.info(f"方案XML重新生成成功: {plan_id}")
    except Exception as e:
        logger.error(f"保存方案XML失败 [{plan_id}]: {e}")
        raise


def ensure_baseline_plan_exists() -> None:
    """
    确保全局基准方案存在

    在系统首次启动或安装时创建全局基准方案。
    如果已存在则跳过。
    """
    baseline_path = _get_plan_dir(BASELINE_PLAN_ID)

    if baseline_path.exists():
        logger.info("基准方案已存在，跳过创建")
        return

    try:
        logger.info("创建全局基准方案...")

        # 创建基准方案目录
        baseline_path.mkdir(parents=True, exist_ok=True)

        # 准备基准方案元数据
        now = datetime.now().isoformat()
        baseline_plan = {
            "plan_id": BASELINE_PLAN_ID,
            "plan_name": "基准方案（无管控）",
            "description": "无任何管控措施的基准方案，用于对比评估管控效果",
            "strategy_ids": [],
            "tags": ["基准", "无管控"],
            "target_scenario": "所有场景",
            "expected_effects": {
                "baseline": "提供基准数据用于对比"
            },
            "additional_file_path": f"control_data/plans/{BASELINE_PLAN_ID}/control.add.xml",
            "created_at": now,
            "updated_at": now
        }

        # 保存元数据
        with open(baseline_path / "plan_metadata.json", "w", encoding="utf-8") as f:
            json.dump(baseline_plan, f, ensure_ascii=False, indent=2)

        # 保存空策略引用
        with open(baseline_path / "strategy_refs.json", "w", encoding="utf-8") as f:
            json.dump([], f)

        # 生成空XML
        empty_xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<additional>\n'
            '    <!-- 基准方案：无管控 -->\n'
            '</additional>'
        )
        with open(baseline_path / "control.add.xml", "w", encoding="utf-8") as f:
            f.write(empty_xml)

        # 更新索引
        index = _load_plans_index()
        index["plans"].append({
            "plan_id": BASELINE_PLAN_ID,
            "plan_name": baseline_plan["plan_name"],
            "is_baseline": True,
            "strategy_count": 0,
            "tags": baseline_plan["tags"],
            "created_at": now,
        })
        _save_plans_index(index)

        logger.info("全局基准方案创建成功")

    except Exception as e:
        # 清理失败的目录
        if baseline_path.exists():
            shutil.rmtree(baseline_path, ignore_errors=True)
        logger.error(f"创建基准方案失败: {e}", exc_info=True)
        raise
