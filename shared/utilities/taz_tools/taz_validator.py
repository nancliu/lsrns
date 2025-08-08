#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
TAZ验证和修复工具

该脚本用于验证TAZ_5_fixed.add.xml文件是否符合taz_to_simnetwork_updated_oppo.csv的要求，
并根据需求修改XML文件。

要求：
- csv文件中point_id与xml文件中taz id相对应，匹配taz数据
- 当csv文件中ori_taz_type列为tazSource时，xml文件中该taz的tazSink字段的id根据opp_point_id选择，
  opp_point_id对应xml文件中的taz id，根据taz id复用该taz的tazSink标签的内容，
  删除xml中原来tazSink标签的内容
- 当csv文件中ori_taz_type列为tazSink时，xml文件中该taz的tazSource字段的id根据opp_point_id选择，
  opp_point_id对应xml文件中的taz id，根据taz id复用该taz的tazSource标签的内容，
  删除xml中原来tazSource标签的内容
"""

import os
import csv
import xml.etree.ElementTree as ET
import re
import sys
from collections import defaultdict

def load_csv_data(csv_file):
    """
    加载CSV文件数据
    
    Args:
        csv_file: CSV文件路径
        
    Returns:
        包含所需信息的字典
    """
    taz_info = {}
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                point_id = row.get('point_id', '')
                ori_taz_type = row.get('ori_taz_type', '')
                opp_point_id = row.get('opp_point_id', '')
                
                # 只处理有ori_taz_type的数据
                if ori_taz_type in ['tazSource', 'tazSink'] and opp_point_id:
                    taz_info[point_id] = {
                        'ori_taz_type': ori_taz_type,
                        'opp_point_id': opp_point_id,
                        'name': row.get('name', '')  # 添加名称信息用于日志
                    }
        
        print(f"从CSV加载了 {len(taz_info)} 个需要处理的TAZ记录")
        return taz_info
    except Exception as e:
        print(f"加载CSV文件时出错: {e}")
        return {}

def parse_xml(xml_file):
    """
    解析XML文件
    
    Args:
        xml_file: XML文件路径
        
    Returns:
        XML树和根元素
    """
    try:
        # 保留原始XML声明和注释
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # 解析XML
        tree = ET.parse(xml_file)
        root = tree.getroot()
        return tree, root, xml_content
    except Exception as e:
        print(f"解析XML文件时出错: {e}")
        return None, None, None

def extract_taz_data(root):
    """
    从XML中提取TAZ数据
    
    Args:
        root: XML根元素
        
    Returns:
        包含TAZ数据的字典
    """
    taz_data = {}
    
    try:
        for taz in root.findall(".//taz"):
            taz_id = taz.get('id')
            taz_name = taz.get('name', '')
            
            # 提取tazSource和tazSink数据
            source_elements = []
            sink_elements = []
            
            for child in taz:
                if child.tag == 'tazSource':
                    source_elements.append(child)
                elif child.tag == 'tazSink':
                    sink_elements.append(child)
            
            taz_data[taz_id] = {
                'element': taz,
                'name': taz_name,
                'source_elements': source_elements,
                'sink_elements': sink_elements
            }
        
        print(f"从XML提取了 {len(taz_data)} 个TAZ记录")
        return taz_data
    except Exception as e:
        print(f"提取TAZ数据时出错: {e}")
        return {}

def validate_and_modify_taz(taz_info, taz_data):
    """
    验证并修改TAZ数据
    
    Args:
        taz_info: CSV中的TAZ信息
        taz_data: XML中的TAZ数据
        
    Returns:
        修改计数、错误计数、错误信息和修改详情
    """
    modifications = 0
    errors = 0
    error_messages = []
    modification_details = []
    
    try:
        for point_id, info in taz_info.items():
            ori_taz_type = info['ori_taz_type']
            opp_point_id = info['opp_point_id']
            taz_name = info.get('name', '')
            
            # 检查point_id和opp_point_id是否都存在于XML中
            if point_id not in taz_data:
                errors += 1
                error_messages.append(f"错误: point_id {point_id} 在XML中不存在")
                continue
                
            if opp_point_id not in taz_data:
                errors += 1
                error_messages.append(f"错误: opp_point_id {opp_point_id} 在XML中不存在")
                continue
            
            # 获取当前TAZ和对应的对立TAZ
            current_taz = taz_data[point_id]
            opposite_taz = taz_data[opp_point_id]
            opp_taz_name = opposite_taz.get('name', '')
            
            # 根据ori_taz_type修改TAZ
            if ori_taz_type == 'tazSource':
                # 当ori_taz_type为tazSource时，需要修改tazSink
                taz_element = current_taz['element']
                
                # 删除原有的tazSink元素
                sink_ids_before = [sink.get('id') for sink in current_taz['sink_elements']]
                for sink in current_taz['sink_elements']:
                    taz_element.remove(sink)
                
                # 复制对立TAZ的tazSink元素
                sink_ids_after = []
                for sink in opposite_taz['sink_elements']:
                    new_sink = ET.Element('tazSink')
                    new_sink.set('id', sink.get('id'))
                    new_sink.set('weight', sink.get('weight'))
                    taz_element.append(new_sink)
                    sink_ids_after.append(sink.get('id'))
                
                modifications += 1
                modification_details.append({
                    'id': point_id,
                    'name': current_taz['name'],
                    'type': 'tazSource',
                    'opp_id': opp_point_id,
                    'opp_name': opposite_taz['name'],
                    'before': sink_ids_before,
                    'after': sink_ids_after
                })
                
            elif ori_taz_type == 'tazSink':
                # 当ori_taz_type为tazSink时，需要修改tazSource
                taz_element = current_taz['element']
                
                # 删除原有的tazSource元素
                source_ids_before = [source.get('id') for source in current_taz['source_elements']]
                for source in current_taz['source_elements']:
                    taz_element.remove(source)
                
                # 复制对立TAZ的tazSource元素
                source_ids_after = []
                for source in opposite_taz['source_elements']:
                    new_source = ET.Element('tazSource')
                    new_source.set('id', source.get('id'))
                    new_source.set('weight', source.get('weight'))
                    taz_element.append(new_source)
                    source_ids_after.append(source.get('id'))
                
                modifications += 1
                modification_details.append({
                    'id': point_id,
                    'name': current_taz['name'],
                    'type': 'tazSink',
                    'opp_id': opp_point_id,
                    'opp_name': opposite_taz['name'],
                    'before': source_ids_before,
                    'after': source_ids_after
                })
        
        return modifications, errors, error_messages, modification_details
    except Exception as e:
        print(f"验证和修改TAZ数据时出错: {e}")
        return 0, 1, [f"处理过程中出错: {str(e)}"], []

def save_xml(tree, xml_file, original_content):
    """
    保存修改后的XML文件
    
    Args:
        tree: 修改后的XML树
        xml_file: 输出XML文件路径
        original_content: 原始XML内容
    """
    try:
        # 获取原始XML声明和注释
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        if original_content.startswith('<?xml'):
            xml_declaration_match = re.match(r'(<\?xml[^>]*\?>)', original_content)
            if xml_declaration_match:
                xml_declaration = xml_declaration_match.group(1)
        
        # 获取注释部分
        comment_match = re.search(r'(<!--.*?-->)', original_content, re.DOTALL)
        comment = comment_match.group(1) if comment_match else ''
        
        # 将树转换为字符串
        tree_str = ET.tostring(tree.getroot(), encoding='utf-8').decode('utf-8')
        
        # 组合最终的XML内容
        final_content = f"{xml_declaration}\n\n{comment}\n\n{tree_str}"
        
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        print(f"修改后的XML文件已保存至: {xml_file}")
        return True
    except Exception as e:
        print(f"保存XML文件时出错: {e}")
        return False

def save_modification_log(modification_details, log_file):
    """
    保存修改日志
    
    Args:
        modification_details: 修改详情列表
        log_file: 日志文件路径
    """
    try:
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("TAZ修改日志\n")
            f.write("=" * 80 + "\n\n")
            
            for i, mod in enumerate(modification_details, 1):
                f.write(f"修改 {i}:\n")
                f.write(f"  TAZ ID: {mod['id']}\n")
                f.write(f"  TAZ名称: {mod['name']}\n")
                f.write(f"  类型: {mod['type']}\n")
                f.write(f"  对应TAZ ID: {mod['opp_id']}\n")
                f.write(f"  对应TAZ名称: {mod['opp_name']}\n")
                
                if mod['type'] == 'tazSource':
                    f.write(f"  修改前tazSink: {', '.join(mod['before'])}\n")
                    f.write(f"  修改后tazSink: {', '.join(mod['after'])}\n")
                else:
                    f.write(f"  修改前tazSource: {', '.join(mod['before'])}\n")
                    f.write(f"  修改后tazSource: {', '.join(mod['after'])}\n")
                
                f.write("\n")
        
        print(f"修改日志已保存至: {log_file}")
        return True
    except Exception as e:
        print(f"保存修改日志时出错: {e}")
        return False

def main():
    """主函数"""
    try:
        # 文件路径
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        
        csv_file = os.path.join(script_dir, 'taz_to_simnetwork_updated_oppo.csv')
        xml_file = os.path.join(project_root, 'sim_scripts', 'TAZ_5_fixed.add.xml')
        output_xml_file = os.path.join(project_root, 'sim_scripts', 'TAZ_5_validated.add.xml')
        log_file = os.path.join(project_root, 'taz_analysis', 'taz_modification_log.txt')
        
        print(f"开始验证TAZ文件: {xml_file}")
        print(f"使用CSV文件: {csv_file}")
        
        # 检查文件是否存在
        if not os.path.exists(csv_file):
            print(f"错误: CSV文件不存在: {csv_file}")
            return
        
        if not os.path.exists(xml_file):
            print(f"错误: XML文件不存在: {xml_file}")
            return
        
        # 加载CSV数据
        taz_info = load_csv_data(csv_file)
        if not taz_info:
            print("错误: 无法加载CSV数据或没有需要处理的记录")
            return
        
        # 解析XML
        tree, root, original_content = parse_xml(xml_file)
        if not tree or not root:
            print("错误: 无法解析XML文件，请检查文件格式")
            return
        
        # 提取TAZ数据
        taz_data = extract_taz_data(root)
        if not taz_data:
            print("错误: 无法从XML提取TAZ数据")
            return
        
        # 验证并修改TAZ
        modifications, errors, error_messages, modification_details = validate_and_modify_taz(taz_info, taz_data)
        
        # 输出结果
        print(f"\n完成验证和修改:")
        print(f"- 修改了 {modifications} 个TAZ")
        print(f"- 发现 {errors} 个错误")
        
        if error_messages:
            print("\n错误信息:")
            for msg in error_messages:
                print(f"  {msg}")
        
        # 保存修改日志
        if modification_details:
            save_modification_log(modification_details, log_file)
        
        # 保存修改后的XML
        if modifications > 0:
            if save_xml(tree, output_xml_file, original_content):
                print(f"\n成功完成! 修改后的XML文件已保存至: {output_xml_file}")
            else:
                print("\n错误: 保存修改后的XML文件失败")
        else:
            print("\n没有进行任何修改，不保存文件")
    
    except Exception as e:
        print(f"程序执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 