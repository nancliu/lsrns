#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
比较TAZ_4.add.xml和TAZ_5.add.xml的区别
"""

import xml.etree.ElementTree as ET
from collections import defaultdict

def load_taz_data(filename):
    """加载TAZ文件数据"""
    print(f"📍 加载 {filename}...")
    try:
        tree = ET.parse(filename)
        root = tree.getroot()
        
        taz_data = {}
        taz_directions = {}
        
        for taz in root.findall("taz"):
            taz_id = taz.get("id")
            taz_name = taz.get("name", "")
            
            sources = taz.findall("tazSource")
            sinks = taz.findall("tazSink")
            
            # 确定方向
            if len(sources) > 0 and len(sinks) == 0:
                direction = "source"
            elif len(sinks) > 0 and len(sources) == 0:
                direction = "sink"
            elif len(sources) > 0 and len(sinks) > 0:
                direction = "both"
            else:
                direction = "none"
            
            taz_data[taz_id] = {
                'name': taz_name,
                'direction': direction,
                'sources': [s.get("id") for s in sources],
                'sinks': [s.get("id") for s in sinks]
            }
            taz_directions[taz_id] = direction
        
        print(f"✅ 加载完成: {len(taz_data)}个TAZ")
        return taz_data, taz_directions
        
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        return {}, {}

def analyze_taz_differences(taz4_data, taz5_data):
    """分析TAZ文件的差异"""
    print("\n" + "=" * 80)
    print("🔍 TAZ文件差异分析")
    print("=" * 80)
    
    taz4_ids = set(taz4_data.keys())
    taz5_ids = set(taz5_data.keys())
    
    # 基本统计
    print(f"📊 基本统计:")
    print(f"  TAZ_4.add.xml: {len(taz4_ids)}个TAZ")
    print(f"  TAZ_5.add.xml: {len(taz5_ids)}个TAZ")
    print(f"  差异: {len(taz5_ids) - len(taz4_ids):+d}个TAZ")
    
    # 新增的TAZ
    new_tazs = taz5_ids - taz4_ids
    print(f"\n✅ 新增TAZ: {len(new_tazs)}个")
    if new_tazs:
        print("  新增TAZ列表:")
        for i, taz_id in enumerate(sorted(new_tazs), 1):
            taz_info = taz5_data[taz_id]
            print(f"    {i:2d}. {taz_id}")
            print(f"        名称: {taz_info['name']}")
            print(f"        方向: {taz_info['direction']}")
    
    # 删除的TAZ
    removed_tazs = taz4_ids - taz5_ids
    print(f"\n❌ 删除TAZ: {len(removed_tazs)}个")
    if removed_tazs:
        print("  删除TAZ列表:")
        for i, taz_id in enumerate(sorted(removed_tazs), 1):
            taz_info = taz4_data[taz_id]
            print(f"    {i:2d}. {taz_id}")
            print(f"        名称: {taz_info['name']}")
            print(f"        方向: {taz_info['direction']}")
    
    # 共同的TAZ
    common_tazs = taz4_ids & taz5_ids
    print(f"\n🔄 共同TAZ: {len(common_tazs)}个")
    
    # 检查共同TAZ的变化
    changed_tazs = []
    for taz_id in common_tazs:
        taz4_info = taz4_data[taz_id]
        taz5_info = taz5_data[taz_id]
        
        changes = []
        if taz4_info['name'] != taz5_info['name']:
            changes.append(f"名称: {taz4_info['name']} -> {taz5_info['name']}")
        
        if taz4_info['direction'] != taz5_info['direction']:
            changes.append(f"方向: {taz4_info['direction']} -> {taz5_info['direction']}")
        
        if changes:
            changed_tazs.append((taz_id, changes))
    
    print(f"\n🔄 修改TAZ: {len(changed_tazs)}个")
    if changed_tazs:
        print("  修改TAZ列表:")
        for i, (taz_id, changes) in enumerate(changed_tazs, 1):
            print(f"    {i:2d}. {taz_id}")
            for change in changes:
                print(f"        {change}")
    
    # 返回分析结果
    return new_tazs, removed_tazs, changed_tazs

def analyze_direction_distribution(taz4_data, taz5_data):
    """分析方向分布的变化"""
    print("\n" + "=" * 80)
    print("📊 方向分布分析")
    print("=" * 80)
    
    def count_directions(taz_data):
        directions = defaultdict(int)
        for taz_info in taz_data.values():
            directions[taz_info['direction']] += 1
        return directions
    
    taz4_directions = count_directions(taz4_data)
    taz5_directions = count_directions(taz5_data)
    
    print("TAZ_4 vs TAZ_5 方向分布:")
    all_directions = set(taz4_directions.keys()) | set(taz5_directions.keys())
    
    for direction in sorted(all_directions):
        count4 = taz4_directions.get(direction, 0)
        count5 = taz5_directions.get(direction, 0)
        diff = count5 - count4
        print(f"  {direction:8s}: {count4:3d} → {count5:3d} ({diff:+3d})")

def analyze_new_taz_patterns(new_tazs, taz5_data):
    """分析新增TAZ的模式"""
    if not new_tazs:
        return
    
    print("\n" + "=" * 80)
    print("🔍 新增TAZ模式分析")
    print("=" * 80)
    
    # 按前缀分组
    prefixes = defaultdict(list)
    directions = defaultdict(int)
    
    for taz_id in new_tazs:
        taz_info = taz5_data[taz_id]
        
        # 分析前缀
        if taz_id.startswith('G42015100100'):
            prefixes['G42015100100 (成都收费站)'].append(taz_id)
        elif taz_id.startswith('G42015100200'):
            prefixes['G42015100200 (成都收费站)'].append(taz_id)
        elif taz_id.startswith('G'):
            prefixes['其他G开头'].append(taz_id)
        elif taz_id.startswith('S'):
            prefixes['S开头 (省道)'].append(taz_id)
        else:
            prefixes['其他'].append(taz_id)
        
        # 统计方向
        directions[taz_info['direction']] += 1
    
    print("📋 新增TAZ按前缀分组:")
    for prefix, taz_list in prefixes.items():
        print(f"  {prefix}: {len(taz_list)}个")
        for taz_id in sorted(taz_list)[:5]:  # 只显示前5个
            taz_info = taz5_data[taz_id]
            print(f"    - {taz_id} ({taz_info['direction']}) {taz_info['name']}")
        if len(taz_list) > 5:
            print(f"    ... 还有{len(taz_list)-5}个")
    
    print(f"\n📊 新增TAZ方向分布:")
    for direction, count in sorted(directions.items()):
        percentage = (count / len(new_tazs)) * 100
        print(f"  {direction}: {count}个 ({percentage:.1f}%)")

def check_problematic_tazs(new_tazs, taz5_data):
    """检查是否包含之前分析中的问题TAZ"""
    print("\n" + "=" * 80)
    print("🔍 问题TAZ检查")
    print("=" * 80)
    
    # 之前分析中发现的高频无效TAZ
    problematic_tazs = {
        'G420151001001010010': '高频违规起点',
        'G420151001001020010': '高频违规终点', 
        'G420151002000310010': '高频违规起点+终点'
    }
    
    found_fixes = []
    for taz_id, issue in problematic_tazs.items():
        if taz_id in new_tazs:
            taz_info = taz5_data[taz_id]
            found_fixes.append((taz_id, issue, taz_info))
    
    if found_fixes:
        print("✅ 发现问题TAZ的修复:")
        for taz_id, issue, taz_info in found_fixes:
            print(f"  {taz_id}")
            print(f"    问题: {issue}")
            print(f"    配置: {taz_info['direction']} - {taz_info['name']}")
            print(f"    Sources: {taz_info['sources']}")
            print(f"    Sinks: {taz_info['sinks']}")
    else:
        print("❌ 未发现之前分析中的问题TAZ")
    
    return found_fixes

def main():
    """主函数"""
    print("🔍 TAZ_4 vs TAZ_5 差异分析")
    print("=" * 80)
    
    # 使用正确的路径加载文件
    import os
    
    # 获取当前脚本目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取项目根目录
    project_root = os.path.dirname(current_dir)
    # 构建TAZ文件的绝对路径
    taz4_path = os.path.join(project_root, 'sim_scripts', 'TAZ_4.add.xml')
    taz5_path = os.path.join(project_root, 'sim_scripts', 'TAZ_5.add.xml')
    
    print(f"尝试加载文件:")
    print(f"TAZ_4路径: {taz4_path}")
    print(f"TAZ_5路径: {taz5_path}")
    
    # 加载两个文件
    taz4_data, taz4_directions = load_taz_data(taz4_path)
    taz5_data, taz5_directions = load_taz_data(taz5_path)
    
    if not taz4_data or not taz5_data:
        print("❌ 无法加载TAZ文件，退出分析")
        return
    
    # 分析差异
    new_tazs, removed_tazs, changed_tazs = analyze_taz_differences(taz4_data, taz5_data)
    
    # 分析方向分布
    analyze_direction_distribution(taz4_data, taz5_data)
    
    # 分析新增TAZ模式
    analyze_new_taz_patterns(new_tazs, taz5_data)
    
    # 检查问题TAZ
    found_fixes = check_problematic_tazs(new_tazs, taz5_data)
    
    # 总结
    print("\n" + "=" * 80)
    print("📋 分析总结")
    print("=" * 80)
    
    print(f"✅ TAZ_5相比TAZ_4的改进:")
    print(f"  - 新增了{len(new_tazs)}个TAZ")
    if removed_tazs:
        print(f"  - 删除了{len(removed_tazs)}个TAZ")
    if changed_tazs:
        print(f"  - 修改了{len(changed_tazs)}个TAZ")
    if found_fixes:
        print(f"  - 修复了{len(found_fixes)}个问题TAZ")
    
    print(f"\n🎯 预期效果:")
    if len(new_tazs) > 0:
        print(f"  - 数据保留率可能从79.4%提升到更高")
        print(f"  - TAZ覆盖率从92个提升到{len(taz5_data)}个")
        if found_fixes:
            print(f"  - 解决了之前{len(found_fixes)}个高频违规TAZ的问题")
    
    print("\n🎯 分析完成!")

if __name__ == "__main__":
    main()
