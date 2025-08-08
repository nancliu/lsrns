#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
处理TAZ_5.add.xml中的重复TAZ定义
根据taz_validation_results.csv中的数据来决定保留哪个TAZ定义
确保处理后的TAZ ID是唯一的，即使存在完全相同的TAZ数据也只保留一个
"""

import os
import sys
import csv
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from collections import defaultdict, Counter

def prettify(elem):
    """返回格式化的XML字符串"""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def load_validation_results(csv_file):
    """加载验证结果CSV文件"""
    print(f"正在加载验证结果: {csv_file}")
    validation_data = {}
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                taz_id = row.get('taz_id_in_xml', '').strip()
                if taz_id:
                    # 保存整行数据以便后续参考
                    validation_data[taz_id] = row
    except Exception as e:
        print(f"❌ 加载验证结果失败: {e}")
        return {}
    
    print(f"✅ 成功加载验证结果: {len(validation_data)}条记录")
    return validation_data

def fix_duplicate_taz(taz_file, validation_file, output_file=None):
    """修复TAZ文件中的重复定义"""
    # 如果没有指定输出文件，则默认为原文件名加上_fixed后缀
    if not output_file:
        base_name, ext = os.path.splitext(taz_file)
        output_file = f"{base_name}_fixed{ext}"
    
    # 加载验证结果
    validation_data = load_validation_results(validation_file)
    if not validation_data:
        print("❌ 没有加载到验证数据，无法继续")
        return False
    
    # 解析TAZ文件
    print(f"正在解析TAZ文件: {taz_file}")
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
    
    # 创建一个新的根元素
    new_root = ET.Element("tazs")
    
    # 记录已处理的TAZ ID
    processed_ids = set()
    
    # 处理每个TAZ元素
    for taz in root.findall(".//taz"):
        taz_id = taz.get('id', '')
        
        # 如果TAZ ID已经处理过，则跳过
        if taz_id in processed_ids:
            continue
        
        # 如果是重复的TAZ ID，需要选择一个保留
        if taz_id in duplicate_ids:
            # 收集所有具有相同ID的TAZ元素
            same_id_tazs = []
            for t in root.findall(f".//taz[@id='{taz_id}']"):
                same_id_tazs.append(t)
            
            print(f"处理重复的TAZ ID: {taz_id}，共有{len(same_id_tazs)}个实例")
            
            # 选择要保留的TAZ
            # 优先选择在验证结果中有记录且验证通过的TAZ
            selected_taz = None
            for t in same_id_tazs:
                taz_name = t.get('name', '')
                has_source = len(t.findall("./tazSource")) > 0
                has_sink = len(t.findall("./tazSink")) > 0
                
                # 检查是否与验证结果匹配
                if taz_id in validation_data:
                    validation_row = validation_data[taz_id]
                    validation_has_source = validation_row.get('has_source', '').lower() == 'yes'
                    validation_has_sink = validation_row.get('has_sink', '').lower() == 'yes'
                    
                    # 如果source和sink状态匹配验证结果，则选择此TAZ
                    if (has_source == validation_has_source) and (has_sink == validation_has_sink):
                        selected_taz = t
                        print(f"  选择与验证结果匹配的TAZ: {taz_name}")
                        break
            
            # 如果没有找到匹配的，选择第一个
            if selected_taz is None and same_id_tazs:
                selected_taz = same_id_tazs[0]
                print(f"  未找到匹配的TAZ，选择第一个: {selected_taz.get('name', '')}")
            
            # 将选中的TAZ添加到新的根元素
            if selected_taz is not None:
                new_taz = ET.SubElement(new_root, "taz")
                for key, value in selected_taz.attrib.items():
                    new_taz.set(key, value)
                
                # 复制子元素
                for child in selected_taz:
                    ET.SubElement(new_taz, child.tag, child.attrib)
        else:
            # 非重复TAZ，直接添加
            new_taz = ET.SubElement(new_root, "taz")
            for key, value in taz.attrib.items():
                new_taz.set(key, value)
            
            # 复制子元素
            for child in taz:
                ET.SubElement(new_taz, child.tag, child.attrib)
        
        # 标记为已处理
        processed_ids.add(taz_id)
    
    # 检查是否所有TAZ ID都已处理
    unprocessed_ids = set(taz_id_counts.keys()) - processed_ids
    if unprocessed_ids:
        print(f"警告: 有{len(unprocessed_ids)}个TAZ ID未处理")
        for taz_id in unprocessed_ids:
            print(f"  未处理的TAZ ID: {taz_id}")
    
    # 保存修复后的TAZ文件
    print(f"正在保存修复后的TAZ文件: {output_file}")
    try:
        # 添加XML声明
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('<?xml version="1.0" encoding="utf-8"?>\n')
            f.write(ET.tostring(new_root, encoding='unicode'))
        
        print(f"✅ 成功保存修复后的TAZ文件")
        
        # 验证修复后的文件中TAZ ID是否唯一
        verify_tree = ET.parse(output_file)
        verify_root = verify_tree.getroot()
        verify_ids = [taz.get('id', '') for taz in verify_root.findall(".//taz")]
        verify_id_counts = Counter(verify_ids)
        duplicate_after_fix = [taz_id for taz_id, count in verify_id_counts.items() if count > 1]
        
        if duplicate_after_fix:
            print(f"❌ 修复后的文件中仍有{len(duplicate_after_fix)}个重复的TAZ ID")
            for taz_id in duplicate_after_fix:
                print(f"  重复的TAZ ID: {taz_id}")
            return False
        else:
            print(f"✅ 验证通过: 修复后的文件中所有TAZ ID都是唯一的")
            return True
    except Exception as e:
        print(f"❌ 保存TAZ文件失败: {e}")
        return False

def update_dll_script(script_file, old_taz_file="TAZ_5.add.xml", new_taz_file="TAZ_5_fixed.add.xml"):
    """更新脚本中的TAZ文件引用"""
    print(f"正在更新脚本文件: {script_file}")
    
    try:
        # 读取脚本文件
        with open(script_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换TAZ文件引用
        updated_content = content.replace(f'"{old_taz_file}"', f'"{new_taz_file}"')
        updated_content = updated_content.replace(f"'{old_taz_file}'", f"'{new_taz_file}'")
        
        # 计算替换次数
        replacement_count = content.count(f'"{old_taz_file}"') + content.count(f"'{old_taz_file}'")
        
        # 保存更新后的脚本文件
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        print(f"✅ 成功更新脚本文件，共替换了{replacement_count}处TAZ文件引用")
        return True
    except Exception as e:
        print(f"❌ 更新脚本文件失败: {e}")
        return False

def main():
    """主函数"""
    # 获取项目根目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    # 设置默认文件路径
    taz_file = os.path.join(project_root, 'sim_scripts', 'TAZ_5.add.xml')
    validation_file = os.path.join(current_dir, 'taz_validation_results.csv')
    output_file = os.path.join(project_root, 'sim_scripts', 'TAZ_5_fixed.add.xml')
    script_file = os.path.join(project_root, 'sim_scripts', 'DLLtest2025_6_3.py')
    
    # 检查文件是否存在
    if not os.path.exists(taz_file):
        print(f"❌ TAZ文件不存在: {taz_file}")
        return False
    
    if not os.path.exists(validation_file):
        print(f"❌ 验证结果文件不存在: {validation_file}")
        return False
    
    # 修复重复的TAZ定义
    success = fix_duplicate_taz(taz_file, validation_file, output_file)
    
    if success:
        print(f"✅ TAZ文件修复完成，结果保存在: {output_file}")
        
        # 更新DLLtest2025_6_3.py中的TAZ文件引用
        if os.path.exists(script_file):
            if update_dll_script(script_file):
                print(f"✅ 已更新{script_file}中的TAZ文件引用")
            else:
                print(f"❌ 更新{script_file}中的TAZ文件引用失败")
        else:
            print(f"❌ 脚本文件不存在: {script_file}")
        
        return True
    else:
        print("❌ TAZ文件修复失败")
        return False

if __name__ == "__main__":
    main() 