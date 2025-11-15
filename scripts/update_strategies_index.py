"""
更新策略索引，添加新创建的策略实例
"""

import json
import socket
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

STRATEGIES_DIR = Path("control_data/strategies")
TEMPLATES_DIR = Path("templates/control_strategies")


def load_template_name(template_id: str) -> str:
    """从模板文件加载 template_name"""
    for template_file in TEMPLATES_DIR.rglob("*.json"):
        if template_file.name == "templates_index.json":
            continue
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
                if template_data.get("template_id") == template_id:
                    return template_data.get("template_name", template_id)
        except Exception:
            continue
    return template_id.replace("_", " ").title()


def calculate_edges_count(strategy: Dict[str, Any]) -> int:
    """计算策略影响的边数"""
    strategy_type = strategy.get("strategy_type", "")
    parameters = strategy.get("parameters", {})
    
    if strategy_type == "TEC":
        entrance_edges = parameters.get("entrance_edges", [])
        return len(entrance_edges) if isinstance(entrance_edges, list) else 0
    else:
        affected_edges = parameters.get("affected_edges", [])
        return len(affected_edges) if isinstance(affected_edges, list) else 0


def update_strategies_index():
    """更新策略索引"""
    index_file = STRATEGIES_DIR / "strategies_index.json"
    
    # 读取现有索引
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        existing_ids = {s["strategy_id"] for s in index.get("strategies", [])}
    else:
        index = {"strategies": [], "total_count": 0}
        existing_ids = set()
    
    # 扫描所有策略文件
    strategy_files = list(STRATEGIES_DIR.glob("strat_*.json")) + list(
        STRATEGIES_DIR.glob("strategy_*.json")
    )
    
    added_count = 0
    updated_count = 0
    
    for strategy_file in strategy_files:
        try:
            with open(strategy_file, 'r', encoding='utf-8') as f:
                strategy = json.load(f)
            
            strategy_id = strategy.get("strategy_id")
            if not strategy_id:
                continue
            
            # 获取模板名称
            template_id = strategy.get("template_id", "")
            template_name = strategy.get("template_name", "")
            if not template_name and template_id:
                template_name = load_template_name(template_id)
            
            # 计算边数
            edges_count = calculate_edges_count(strategy)
            
            # 获取时间戳
            if "metadata" in strategy:
                created_at = strategy["metadata"].get("created_at", "")
                updated_at = strategy["metadata"].get("updated_at", "")
            else:
                created_at = strategy.get("created_at", "")
                updated_at = strategy.get("updated_at", "")
            
            entry = {
                "strategy_id": strategy_id,
                "strategy_name": strategy.get("strategy_name", ""),
                "strategy_type": strategy.get("strategy_type", ""),
                "template_id": template_id,
                "template_name": template_name,
                "edges_count": edges_count,
                "created_at": created_at,
                "updated_at": updated_at,
                "file_path": f"control_data/strategies/{strategy_file.name}",
            }
            
            # 检查是否已存在
            existing_idx = next(
                (i for i, s in enumerate(index["strategies"]) if s["strategy_id"] == strategy_id),
                None
            )
            
            if existing_idx is not None:
                # 更新现有条目
                index["strategies"][existing_idx] = entry
                updated_count += 1
            else:
                # 添加新条目
                index["strategies"].append(entry)
                added_count += 1
            
        except Exception as e:
            print(f"⚠️  处理策略文件失败 {strategy_file.name}: {e}")
            continue
    
    # 按更新时间排序
    index["strategies"].sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    
    # 更新总数和时间戳
    index["total_count"] = len(index["strategies"])
    index["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    # 保存索引
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 索引更新完成")
    print(f"   - 新增策略: {added_count} 个")
    print(f"   - 更新策略: {updated_count} 个")
    print(f"   - 总策略数: {index['total_count']} 个")


if __name__ == "__main__":
    print("开始更新策略索引...")
    print("=" * 60)
    update_strategies_index()






