#!/usr/bin/env python3
"""验证VSS策略是否包含索引0的lane"""

import sys
from pathlib import Path
from xml.etree.ElementTree import parse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

xml_file = project_root / "control_data" / "plans" / "plan_vss_dhs_evening_composite" / "control.add.xml"

tree = parse(str(xml_file))
root = tree.getroot()
vss = root.find(".//variableSpeedSign")

lanes = vss.get("lanes", "").split()
lane_0_list = [l for l in lanes if l.endswith("_0")]

print(f"VSS策略: {vss.get('id')}")
print(f"总lanes数量: {len(lanes)}")
print(f"包含索引0的lanes: {len(lane_0_list)}")
print(f"\n前10个lanes: {lanes[:10]}")
print(f"\n包含索引0的lanes示例: {lane_0_list[:10]}")

if len(lane_0_list) > 0:
    print("\n✅ VSS策略已包含索引0的lanes")
else:
    print("\n❌ VSS策略未包含索引0的lanes")











