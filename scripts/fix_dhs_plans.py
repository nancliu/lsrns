#!/usr/bin/env python3
"""修复DHS方案的XML生成问题"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.control_tools.plan_file_manager import regenerate_plan_xml

# 找到所有DHS方案
dhs_plans = [
    "plan_dhs_morning_peak_severe",
    "plan_dhs_evening_peak_severe",
]

print("修复DHS方案XML生成...")
print("=" * 60)

for plan_id in dhs_plans:
    try:
        result = regenerate_plan_xml(plan_id)
        status = "✅" if result.get("regenerated") else "⚠️"
        print(f"{status} {plan_id}: XML已重新生成")
        if result.get("validation"):
            print(f"   验证状态: {'通过' if result['validation'].get('is_valid') else '失败'}")
    except Exception as e:
        print(f"❌ {plan_id}: 生成失败 - {e}")

print("=" * 60)
print("完成!")
