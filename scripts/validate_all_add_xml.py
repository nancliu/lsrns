#!/usr/bin/env python3
"""验证所有方案的.add.xml是否符合SUMO仿真要求"""

import sys
import json
from pathlib import Path
from xml.etree.ElementTree import parse as parse_xml
from xml.dom import minidom

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.control_tools.xml_validator import validate_xml_string

# 所有方案
plans = [
    "baseline_plan",
    "plan_dhs_morning_peak_severe",
    "plan_tec_evening_peak_severe",
    "plan_tec_morning_peak_severe",
    "plan_vss_dhs_evening_composite",
    "plan_vss_dhs_evening_peak_high_flow",
    "plan_vss_dhs_morning_peak_severe",
    "plan_vss_dhs_tec_allday_complex",
    "plan_vss_dhs_tec_allday_persistent_severe",
    "plan_vss_evening_peak_severe",
    "plan_vss_morning_peak_severe",
    "plan_vss_morning_peak_simple",
    "plan_vss_tec_evening_peak_high_flow",
    "plan_vss_tec_morning_peak_severe",
]

print("=" * 100)
print("SUMO仿真兼容性验证 - 所有方案.add.xml检查")
print("=" * 100)

stats = {
    "total": 0,
    "valid": 0,
    "invalid": 0,
    "warnings": 0,
    "errors": 0,
    "strategy_types": {"VSS": 0, "DHS": 0, "TEC": 0, "unknown": 0},
}

for plan_id in plans:
    plan_dir = Path("control_data/plans") / plan_id
    xml_file = plan_dir / "control.add.xml"

    if not xml_file.exists():
        print(f"\n❌ {plan_id}: XML文件不存在")
        stats["invalid"] += 1
        continue

    stats["total"] += 1

    try:
        # 读取XML文件
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        # 使用xml_validator验证
        validation_result = validate_xml_string(xml_content)

        # 解析XML获取统计信息
        tree = parse_xml(str(xml_file))
        root = tree.getroot()

        # 统计策略类型
        vss_count = len(root.findall(".//variableSpeedSign"))
        dhs_count = len(root.findall(".//rerouter"))
        tec_count = len(root.findall(".//calibrator"))

        if vss_count > 0:
            stats["strategy_types"]["VSS"] += vss_count
        if dhs_count > 0:
            stats["strategy_types"]["DHS"] += dhs_count
        if tec_count > 0:
            stats["strategy_types"]["TEC"] += tec_count

        # 显示验证结果（XMLValidationResult是对象，不是字典）
        is_valid = validation_result.is_valid
        warnings = validation_result.warnings
        errors = validation_result.errors

        status_icon = "✅" if is_valid else "⚠️"
        print(f"\n{status_icon} {plan_id}")
        print(f"   XML格式: {'合法' if is_valid else '非法'}")
        print(f"   策略统计: VSS={vss_count}, DHS={dhs_count}, TEC={tec_count}")
        print(f"   文件大小: {xml_file.stat().st_size} bytes")

        # 显示详细信息
        if vss_count > 0:
            print(f"\n   【VSS策略详情】")
            for vss in root.findall(".//variableSpeedSign"):
                vss_id = vss.get('id', 'unknown')
                edges = vss.get('edges', '')[:60]
                steps = len(vss.findall('step'))
                print(f"     - ID: {vss_id}")
                print(f"       Edges: {edges}...")
                print(f"       时间步数: {steps}")

                # 检查step时间和速度
                for i, step in enumerate(vss.findall('step')):
                    time = step.get('time')
                    speed = step.get('speed')
                    if speed and speed != '-1':
                        speed_kmh = float(speed) * 3.6 if speed else 0
                        print(f"       Step {i+1}: 时间={time}s, 速度={speed}m/s ({speed_kmh:.1f}km/h)")
                    else:
                        print(f"       Step {i+1}: 时间={time}s, 速度=默认（复位）")

        if dhs_count > 0:
            print(f"\n   【DHS策略详情】")
            for rerouter in root.findall(".//rerouter"):
                rerouter_id = rerouter.get('id', 'unknown')
                edges = rerouter.get('edges', '')[:60]
                intervals = len(rerouter.findall('interval'))
                print(f"     - ID: {rerouter_id}")
                print(f"       Edges: {edges}...")
                print(f"       时间区间数: {intervals}")

                # 检查每个interval
                for i, interval in enumerate(rerouter.findall('interval')):
                    begin = interval.get('begin')
                    end = interval.get('end')
                    closing = interval.find('closingLaneReroute')

                    if closing is not None:
                        lane_id = closing.get('id')
                        allow = closing.get('allow', '')
                        status = "关闭" if allow == '' else "部分开放"
                        print(f"       区间{i+1}: {begin}s-{end}s | Lane {lane_id} | {status}")
                    else:
                        print(f"       区间{i+1}: {begin}s-{end}s | 开放")

        if tec_count > 0:
            print(f"\n   【TEC策略详情】")
            for calibrator in root.findall(".//calibrator"):
                cal_id = calibrator.get('id', 'unknown')
                edge = calibrator.get('edge', 'unknown')
                flows = len(calibrator.findall('flow'))
                print(f"     - ID: {cal_id}")
                print(f"       Edge: {edge}")
                print(f"       流量时段数: {flows}")

                # 检查每个flow
                for i, flow in enumerate(calibrator.findall('flow')):
                    begin = flow.get('begin')
                    end = flow.get('end')
                    vph = flow.get('vehsPerHour', 'N/A')
                    speed = flow.get('speed', 'N/A')
                    print(f"       流量{i+1}: {begin}s-{end}s | {vph}veh/h | {speed}m/s")

        # 显示警告和错误
        if warnings:
            stats["warnings"] += len(warnings)
            print(f"\n   ⚠️ 警告 ({len(warnings)}):")
            for warning in warnings[:3]:  # 只显示前3个
                print(f"      - {warning}")
            if len(warnings) > 3:
                print(f"      ... 还有 {len(warnings)-3} 个警告")

        if errors:
            stats["errors"] += len(errors)
            print(f"\n   ❌ 错误 ({len(errors)}):")
            for error in errors[:3]:  # 只显示前3个
                print(f"      - {error}")
            if len(errors) > 3:
                print(f"      ... 还有 {len(errors)-3} 个错误")

        if is_valid:
            stats["valid"] += 1
            print(f"\n   ✅ SUMO兼容性: 通过")
        else:
            stats["invalid"] += 1
            print(f"\n   ❌ SUMO兼容性: 需要修复")

    except Exception as e:
        stats["invalid"] += 1
        print(f"\n❌ {plan_id}: 处理失败")
        print(f"   错误: {str(e)}")

# 打印汇总统计
print("\n" + "=" * 100)
print("【验证汇总统计】")
print("=" * 100)
print(f"总方案数: {stats['total']}")
print(f"✅ 有效方案: {stats['valid']}")
print(f"❌ 无效方案: {stats['invalid']}")
print(f"\n策略统计:")
print(f"  VSS (可变限速): {stats['strategy_types']['VSS']}")
print(f"  DHS (应急车道): {stats['strategy_types']['DHS']}")
print(f"  TEC (收费站管控): {stats['strategy_types']['TEC']}")
print(f"\n问题汇总:")
print(f"  总警告数: {stats['warnings']}")
print(f"  总错误数: {stats['errors']}")

if stats["errors"] == 0 and stats["invalid"] == 0:
    print("\n✅ 所有方案都符合SUMO仿真要求！")
elif stats["invalid"] == 0:
    print(f"\n⚠️ 所有方案都能被SUMO加载，但有 {stats['warnings']} 个警告需要检查")
else:
    print(f"\n❌ 有 {stats['invalid']} 个方案存在问题，需要修复")

print("=" * 100)
