#!/usr/bin/env python3
"""检查所有DHS方案的lane ID格式是否正确"""

import sys
from pathlib import Path
from xml.etree.ElementTree import parse
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

dhs_plans = [
    "plan_dhs_morning_peak_severe",
    "plan_vss_dhs_evening_composite",
    "plan_vss_dhs_evening_peak_high_flow",
    "plan_vss_dhs_morning_peak_severe",
    "plan_vss_dhs_tec_allday_complex",
    "plan_vss_dhs_tec_allday_persistent_severe",
]

print("检查所有DHS方案的lane ID格式...")
print("=" * 80)

all_ok = True
total_checked = 0
total_fixed = 0

for plan_id in dhs_plans:
    xml_file = project_root / "control_data" / "plans" / plan_id / "control.add.xml"
    
    if not xml_file.exists():
        print(f"\n⚠️  {plan_id}: XML文件不存在")
        continue
    
    try:
        tree = parse(str(xml_file))
        root = tree.getroot()
        rerouters = root.findall('.//rerouter')
        
        print(f"\n{plan_id}:")
        print(f"  找到 {len(rerouters)} 个DHS rerouter")
        
        plan_ok = True
        for rerouter in rerouters:
            strategy_id = rerouter.get('id', 'unknown')
            intervals = rerouter.findall('interval')
            
            print(f"  策略: {strategy_id} ({len(intervals)} 个interval)")
            
            for i, interval in enumerate(intervals):
                closings = interval.findall('closingLaneReroute')
                
                if not closings:
                    continue
                
                lane_ids = [c.get('id') for c in closings]
                
                # 检查格式：应该是 edge_id_lane_index 格式（例如 -9292_0）
                bad_ids = []
                for lid in lane_ids:
                    # 匹配格式：可选的负号，数字（可能包含小数点），下划线，数字
                    if not re.match(r'^-?\d+(\.\d+)?_\d+$', lid):
                        bad_ids.append(lid)
                
                if bad_ids:
                    plan_ok = False
                    all_ok = False
                    print(f"    ❌ 区间 {i+1}: 发现错误格式的lane ID: {bad_ids}")
                else:
                    print(f"    ✅ 区间 {i+1}: {len(closings)} 个closingLaneReroute，格式正确（示例: {lane_ids[0]}）")
        
        if plan_ok:
            total_checked += 1
        else:
            total_fixed += 1
            
    except Exception as e:
        print(f"  ❌ 检查失败: {e}")
        all_ok = False

print("\n" + "=" * 80)
if all_ok:
    print(f"✅ 所有 {len(dhs_plans)} 个DHS方案已完成修正！")
    print(f"   - 已检查: {total_checked}")
else:
    print(f"❌ 发现 {total_fixed} 个方案需要修正")



