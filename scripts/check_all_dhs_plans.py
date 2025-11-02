#!/usr/bin/env python3
"""检查所有包含DHS策略的方案的XML生成结果"""

import sys
import json
from pathlib import Path
from xml.etree.ElementTree import parse as parse_xml

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.control_tools.plan_file_manager import regenerate_plan_xml

# 包含DHS的所有方案
dhs_plans = [
    "plan_dhs_morning_peak_severe",
    "plan_vss_dhs_evening_composite",
    "plan_vss_dhs_evening_peak_high_flow",
    "plan_vss_dhs_morning_peak_severe",
    "plan_vss_dhs_tec_allday_complex",
    "plan_vss_dhs_tec_allday_persistent_severe",
]

print("检查和重新生成所有DHS方案XML...")
print("=" * 80)

for plan_id in dhs_plans:
    try:
        # 重新生成XML
        result = regenerate_plan_xml(plan_id)
        
        # 检查XML内容
        plan_dir = Path("control_data/plans") / plan_id
        xml_file = plan_dir / "control.add.xml"
        
        if xml_file.exists():
            # 解析XML
            tree = parse_xml(str(xml_file))
            root = tree.getroot()
            
            # 统计DHS策略
            dhs_count = len(root.findall(".//rerouter"))
            rerouters = root.findall(".//rerouter")
            
            print(f"\n✅ {plan_id}")
            print(f"   XML验证: {'通过' if result.get('validation', {}).get('is_valid') else '失败'}")
            print(f"   DHS策略数: {dhs_count}")
            
            # 显示每个DHS策略的时间区间和allow设置
            for rerouter in rerouters:
                rerouter_id = rerouter.get('id', 'unknown')
                edges = rerouter.get('edges', '')[:50] + "..." if len(rerouter.get('edges', '')) > 50 else rerouter.get('edges', '')
                
                print(f"\n   策略: {rerouter_id}")
                print(f"   受影响edge: {edges}")
                
                intervals = rerouter.findall('interval')
                print(f"   时间区间数: {len(intervals)}")
                
                for i, interval in enumerate(intervals):
                    begin = interval.get('begin')
                    end = interval.get('end')
                    
                    # 转换为小时
                    begin_h = int(begin) // 3600 if begin else 0
                    end_h = int(end) // 3600 if end else 0
                    
                    closing = interval.find('closingLaneReroute')
                    if closing is not None:
                        lane_id = closing.get('id', 'unknown')
                        allow = closing.get('allow', 'unknown')
                        
                        status = "开放" if allow else "关闭"
                        allow_display = allow if allow else "(无)"
                        
                        print(f"     区间{i+1}: {begin_h:02d}:00-{end_h:02d}:00 | Lane {lane_id} | {status} | allow='{allow_display}'")
        else:
            print(f"⚠️  {plan_id}: XML文件不存在")
            
    except Exception as e:
        print(f"❌ {plan_id}: 处理失败 - {e}")

print("\n" + "=" * 80)
print("检查完成!")
