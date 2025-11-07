#!/usr/bin/env python3
"""验证所有VSS方案是否使用lanes属性"""

import sys
from pathlib import Path
from xml.etree.ElementTree import parse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

plans_dir = project_root / "control_data" / "plans"
vss_files = list(plans_dir.glob("plan_vss*/control.add.xml"))

print(f"检查 {len(vss_files)} 个VSS方案文件...\n")
print("=" * 80)

all_ok = True

for xml_file in vss_files:
    plan_name = xml_file.parent.name
    try:
        tree = parse(str(xml_file))
        root = tree.getroot()
        vss_list = root.findall(".//variableSpeedSign")
        
        print(f"\n{plan_name}:")
        print(f"  找到 {len(vss_list)} 个VSS策略")
        
        for vss in vss_list:
            strategy_id = vss.get("id", "unknown")
            has_lanes = "lanes" in vss.attrib
            has_edges = "edges" in vss.attrib
            
            if has_lanes and not has_edges:
                lanes_count = len(vss.get("lanes", "").split())
                print(f"    ✅ 策略 {strategy_id}: 使用lanes属性 ({lanes_count} 个lanes)")
            elif has_edges:
                print(f"    ❌ 策略 {strategy_id}: 仍使用edges属性")
                all_ok = False
            else:
                print(f"    ❌ 策略 {strategy_id}: 缺少lanes属性")
                all_ok = False
                
    except Exception as e:
        print(f"  ❌ 读取失败: {e}")
        all_ok = False

print("\n" + "=" * 80)
if all_ok:
    print("✅ 所有VSS策略都正确使用lanes属性！")
else:
    print("❌ 部分策略需要修正")




