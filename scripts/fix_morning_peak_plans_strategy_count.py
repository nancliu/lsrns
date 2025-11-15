"""
修复早高峰方案的 strategy_count 字段

从 strategies 数组中提取 strategy_id，添加 strategy_ids 字段，
并更新 plans_index.json 中的 strategy_count
"""

import json
from pathlib import Path
from typing import List, Dict, Any

PLANS_BASE_DIR = Path("control_data/plans")
PLANS_INDEX_FILE = PLANS_BASE_DIR / "plans_index.json"


def extract_strategy_ids(plan_metadata: Dict[str, Any]) -> List[str]:
    """从 plan_metadata 中提取 strategy_ids"""
    strategy_ids = []
    
    # 如果已经有 strategy_ids 字段，直接返回
    if "strategy_ids" in plan_metadata and plan_metadata["strategy_ids"]:
        return plan_metadata["strategy_ids"]
    
    # 从 strategies 数组中提取 strategy_id
    if "strategies" in plan_metadata:
        for strategy in plan_metadata["strategies"]:
            if isinstance(strategy, dict) and "strategy_id" in strategy:
                strategy_ids.append(strategy["strategy_id"])
    
    return strategy_ids


def fix_plan(plan_id: str) -> bool:
    """修复单个方案的 strategy_ids 和 strategy_count"""
    plan_dir = PLANS_BASE_DIR / plan_id
    
    if not plan_dir.exists():
        print(f"⚠️  方案目录不存在: {plan_id}")
        return False
    
    metadata_file = plan_dir / "plan_metadata.json"
    if not metadata_file.exists():
        print(f"⚠️  元数据文件不存在: {plan_id}")
        return False
    
    try:
        # 读取方案元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            plan_metadata = json.load(f)
        
        # 提取 strategy_ids
        strategy_ids = extract_strategy_ids(plan_metadata)
        
        if not strategy_ids:
            print(f"⚠️  方案 {plan_id} 没有策略")
            return False
        
        # 更新 plan_metadata.json
        plan_metadata["strategy_ids"] = strategy_ids
        
        # 保存更新后的元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(plan_metadata, f, ensure_ascii=False, indent=2)
        
        # 创建或更新 strategy_refs.json
        refs_file = plan_dir / "strategy_refs.json"
        with open(refs_file, 'w', encoding='utf-8') as f:
            json.dump(strategy_ids, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 修复方案: {plan_id} (strategy_count: {len(strategy_ids)})")
        return True
        
    except Exception as e:
        print(f"❌ 修复方案失败 {plan_id}: {e}")
        return False


def update_plans_index():
    """更新 plans_index.json 中的 strategy_count"""
    if not PLANS_INDEX_FILE.exists():
        print(f"⚠️  索引文件不存在: {PLANS_INDEX_FILE}")
        return
    
    try:
        # 读取索引文件
        with open(PLANS_INDEX_FILE, 'r', encoding='utf-8') as f:
            index_data = json.load(f)
        
        updated_count = 0
        
        # 更新每个早高峰方案的 strategy_count
        for plan_entry in index_data.get("plans", []):
            plan_id = plan_entry.get("plan_id", "")
            
            # 只处理早高峰方案
            if not plan_id.startswith("plan_morning_peak_g4202_"):
                continue
            
            # 读取方案元数据获取 strategy_ids
            plan_dir = PLANS_BASE_DIR / plan_id
            metadata_file = plan_dir / "plan_metadata.json"
            
            if not metadata_file.exists():
                continue
            
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    plan_metadata = json.load(f)
                
                # 提取 strategy_ids
                strategy_ids = extract_strategy_ids(plan_metadata)
                strategy_count = len(strategy_ids)
                
                # 更新索引条目
                plan_entry["strategy_count"] = strategy_count
                
                # 确保其他必要字段存在
                if "is_baseline" not in plan_entry:
                    plan_entry["is_baseline"] = False
                
                updated_count += 1
                print(f"✅ 更新索引: {plan_id} (strategy_count: {strategy_count})")
                
            except Exception as e:
                print(f"⚠️  读取方案元数据失败 {plan_id}: {e}")
                continue
        
        # 保存更新后的索引
        with open(PLANS_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 索引文件已更新，共更新 {updated_count} 个方案")
        
    except Exception as e:
        print(f"❌ 更新索引文件失败: {e}")


def main():
    """主函数"""
    print("开始修复早高峰方案的 strategy_count 字段...")
    print("-" * 60)
    
    # 1. 修复每个方案的 strategy_ids
    print("\n步骤 1: 修复方案元数据...")
    plan_dirs = [d for d in PLANS_BASE_DIR.iterdir() 
                 if d.is_dir() and d.name.startswith("plan_morning_peak_g4202_")]
    
    fixed_count = 0
    for plan_dir in sorted(plan_dirs):
        if fix_plan(plan_dir.name):
            fixed_count += 1
    
    print(f"\n✅ 共修复 {fixed_count} 个方案的元数据")
    
    # 2. 更新 plans_index.json
    print("\n步骤 2: 更新 plans_index.json...")
    update_plans_index()
    
    print("\n" + "=" * 60)
    print("✅ 修复完成！")


if __name__ == "__main__":
    main()






