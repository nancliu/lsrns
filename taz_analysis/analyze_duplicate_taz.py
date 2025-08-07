#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
分析TAZ_5.add.xml中的重复TAZ ID
输出每个重复ID的详细信息，包括名称、source和sink状态
"""

import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict, Counter

def analyze_duplicate_taz(taz_file):
    """分析TAZ文件中的重复定义"""
    print(f"正在分析TAZ文件: {taz_file}")
    
    try:
        tree = ET.parse(taz_file)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ 解析TAZ文件失败: {e}")
        return False
    
    # 统计TAZ ID出现次数
    taz_id_counts = Counter()
    for taz in root.findall(".//taz"):
        taz_id = taz.get('id', '')
        if taz_id:
            taz_id_counts[taz_id] += 1
    
    # 找出重复的TAZ ID
    duplicate_ids = [taz_id for taz_id, count in taz_id_counts.items() if count > 1]
    print(f"发现{len(duplicate_ids)}个重复的TAZ ID")
    
    if not duplicate_ids:
        print("✅ 没有发现重复的TAZ ID")
        return True
    
    # 收集每个重复ID的详细信息
    duplicate_info = defaultdict(list)
    for taz_id in duplicate_ids:
        for taz in root.findall(f".//taz[@id='{taz_id}']"):
            taz_name = taz.get('name', '')
            has_source = len(taz.findall("./tazSource")) > 0
            has_sink = len(taz.findall("./tazSink")) > 0
            
            # 收集source和sink的ID
            source_ids = [src.get('id', '') for src in taz.findall("./tazSource")]
            sink_ids = [sink.get('id', '') for sink in taz.findall("./tazSink")]
            
            duplicate_info[taz_id].append({
                'name': taz_name,
                'has_source': has_source,
                'has_sink': has_sink,
                'source_ids': source_ids,
                'sink_ids': sink_ids
            })
    
    # 输出重复ID的详细信息
    print("\n=== 重复TAZ ID详细信息 ===")
    for taz_id, instances in duplicate_info.items():
        print(f"\nTAZ ID: {taz_id} (共{len(instances)}个实例)")
        for i, instance in enumerate(instances):
            print(f"  实例 #{i+1}:")
            print(f"    名称: {instance['name']}")
            print(f"    有source: {instance['has_source']}")
            print(f"    有sink: {instance['has_sink']}")
            print(f"    Source IDs: {', '.join(instance['source_ids']) if instance['source_ids'] else '无'}")
            print(f"    Sink IDs: {', '.join(instance['sink_ids']) if instance['sink_ids'] else '无'}")
    
    # 输出重复ID列表
    print("\n=== 重复TAZ ID列表 ===")
    for taz_id in duplicate_ids:
        print(taz_id)
    
    return True

def main():
    """主函数"""
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # 设置默认文件路径
    taz_file = os.path.join(project_root, 'sim_scripts', 'TAZ_5.add.xml')
    
    # 检查文件是否存在
    if not os.path.exists(taz_file):
        print(f"❌ TAZ文件不存在: {taz_file}")
        return False
    
    # 分析重复的TAZ定义
    success = analyze_duplicate_taz(taz_file)
    
    if success:
        print("\n✅ TAZ文件分析完成")
        return True
    else:
        print("\n❌ TAZ文件分析失败")
        return False

if __name__ == "__main__":
    main() 