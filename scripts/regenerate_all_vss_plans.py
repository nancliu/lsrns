#!/usr/bin/env python3
"""重新生成所有包含VSS策略的方案XML"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.control_tools.plan_file_manager import regenerate_plan_xml
import json

# 从plans_index.json获取所有方案
with open(project_root / "control_data" / "plans" / "plans_index.json", "r", encoding="utf-8") as f:
    plans_data = json.load(f)

# 找出所有包含VSS的方案
vss_plans = []
for plan in plans_data["plans"]:
    plan_id = plan["plan_id"]
    plan_name = plan.get("plan_name", "").lower()
    tags = [str(t).upper() for t in plan.get("tags", [])]
    
    if plan_id.startswith("plan_vss") or "VSS" in tags or "vss" in plan_name:
        vss_plans.append(plan_id)

print(f"找到 {len(vss_plans)} 个包含VSS策略的方案")
print("=" * 80)

success_count = 0
error_count = 0

for plan_id in vss_plans:
    try:
        print(f"\n重新生成: {plan_id}")
        result = regenerate_plan_xml(plan_id)
        
        if result.get("validation", {}).get("is_valid"):
            print(f"  ✅ 成功，验证通过")
            success_count += 1
        else:
            print(f"  ⚠️  成功，但验证有警告: {result.get('validation', {}).get('warnings', [])}")
            success_count += 1
            
    except Exception as e:
        print(f"  ❌ 失败: {e}")
        error_count += 1

print("\n" + "=" * 80)
print(f"完成！成功: {success_count}, 失败: {error_count}")









