"""
为早高峰方案创建缺失的策略实例文件

从方案的 strategies 数组中提取策略数据，创建策略实例文件
"""

import json
import socket
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

PLANS_BASE_DIR = Path("control_data/plans")
STRATEGIES_DIR = Path("control_data/strategies")
TEMPLATES_DIR = Path("templates/control_strategies")


def load_template_name(template_id: str) -> str:
    """从模板文件加载 template_name"""
    # 尝试查找模板文件
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
    
    # 如果找不到，使用默认名称
    return template_id.replace("_", " ").title()


def create_strategy_instance(strategy_data: Dict[str, Any]) -> bool:
    """创建策略实例文件"""
    strategy_id = strategy_data.get("strategy_id")
    if not strategy_id:
        return False
    
    strategy_file = STRATEGIES_DIR / f"{strategy_id}.json"
    
    # 如果文件已存在，跳过
    if strategy_file.exists():
        print(f"  ⏭️  策略实例已存在: {strategy_id}")
        return True
    
    # 构建完整的策略实例数据
    template_id = strategy_data.get("template_id", "")
    template_name = strategy_data.get("template_name", "")
    
    if not template_name:
        template_name = load_template_name(template_id)
    
    current_time = datetime.now(timezone.utc).isoformat()
    created_by = socket.gethostname() if socket.gethostname() else "system"
    
    strategy_instance = {
        "strategy_id": strategy_id,
        "strategy_name": strategy_data.get("strategy_name", ""),
        "template_id": template_id,
        "template_name": template_name,
        "strategy_type": strategy_data.get("strategy_type", ""),
        "parameters": strategy_data.get("parameters", {}),
        "metadata": {
            "created_at": current_time,
            "updated_at": current_time,
            "created_by": created_by,
            "version": 1
        }
    }
    
    try:
        # 确保目录存在
        STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
        
        # 保存策略实例文件
        with open(strategy_file, 'w', encoding='utf-8') as f:
            json.dump(strategy_instance, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ 创建策略实例: {strategy_id}")
        return True
        
    except Exception as e:
        print(f"  ❌ 创建策略实例失败 {strategy_id}: {e}")
        return False


def fix_plan_strategies(plan_id: str) -> int:
    """为单个方案创建缺失的策略实例"""
    plan_dir = PLANS_BASE_DIR / plan_id
    
    if not plan_dir.exists():
        print(f"⚠️  方案目录不存在: {plan_id}")
        return 0
    
    metadata_file = plan_dir / "plan_metadata.json"
    if not metadata_file.exists():
        print(f"⚠️  元数据文件不存在: {plan_id}")
        return 0
    
    try:
        # 读取方案元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            plan_metadata = json.load(f)
        
        # 从 strategies 数组中提取策略数据
        strategies = plan_metadata.get("strategies", [])
        
        if not strategies:
            print(f"⚠️  方案 {plan_id} 没有策略")
            return 0
        
        created_count = 0
        print(f"\n处理方案: {plan_id}")
        
        for strategy in strategies:
            if isinstance(strategy, dict) and strategy.get("strategy_id"):
                if create_strategy_instance(strategy):
                    created_count += 1
        
        return created_count
        
    except Exception as e:
        print(f"❌ 处理方案失败 {plan_id}: {e}")
        return 0


def main():
    """主函数"""
    print("开始为早高峰方案创建缺失的策略实例文件...")
    print("=" * 60)
    
    # 查找所有早高峰方案
    plan_dirs = [d for d in PLANS_BASE_DIR.iterdir() 
                 if d.is_dir() and d.name.startswith("plan_morning_peak_g4202_")]
    
    total_created = 0
    
    for plan_dir in sorted(plan_dirs):
        created = fix_plan_strategies(plan_dir.name)
        total_created += created
    
    print("\n" + "=" * 60)
    print(f"✅ 完成！共创建 {total_created} 个策略实例文件")


if __name__ == "__main__":
    main()



