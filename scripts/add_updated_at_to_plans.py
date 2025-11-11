"""
为所有早高峰方案添加 updated_at 字段
"""

import json
from pathlib import Path
from datetime import datetime

PLANS_BASE_DIR = Path("control_data/plans")


def add_updated_at_to_plan(plan_id: str) -> bool:
    """为单个方案添加 updated_at 字段"""
    plan_dir = PLANS_BASE_DIR / plan_id
    
    if not plan_dir.exists():
        return False
    
    metadata_file = plan_dir / "plan_metadata.json"
    if not metadata_file.exists():
        return False
    
    try:
        # 读取方案元数据
        with open(metadata_file, 'r', encoding='utf-8') as f:
            plan_metadata = json.load(f)
        
        # 如果已经有 updated_at，跳过
        if "updated_at" in plan_metadata and plan_metadata["updated_at"]:
            return False
        
        # 添加 updated_at（使用 created_at 的值）
        plan_metadata["updated_at"] = plan_metadata.get("created_at", datetime.now().isoformat())
        
        # 保存更新后的元数据
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(plan_metadata, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 更新方案: {plan_id}")
        return True
        
    except Exception as e:
        print(f"❌ 更新方案失败 {plan_id}: {e}")
        return False


def main():
    """主函数"""
    print("开始为早高峰方案添加 updated_at 字段...")
    print("=" * 60)
    
    # 查找所有早高峰方案
    plan_dirs = [d for d in PLANS_BASE_DIR.iterdir() 
                 if d.is_dir() and d.name.startswith("plan_morning_peak_g4202_")]
    
    updated_count = 0
    for plan_dir in sorted(plan_dirs):
        if add_updated_at_to_plan(plan_dir.name):
            updated_count += 1
    
    print("\n" + "=" * 60)
    print(f"✅ 完成！共更新 {updated_count} 个方案")


if __name__ == "__main__":
    main()



