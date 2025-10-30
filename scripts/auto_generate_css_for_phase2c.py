#!/usr/bin/env python3
"""
自动生成 Phase 2c CSS 类
为所有仅出现一次的内联样式创建对应的 CSS 类
"""

import re
from pathlib import Path
from collections import defaultdict

def extract_styles(html_path):
    """提取所有 style 属性及其出现频率"""
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()

    style_regex = r'style="([^"]*)"'
    matches = re.findall(style_regex, html)

    style_dict = defaultdict(int)
    for style_value in matches:
        style_dict[style_value] += 1

    return style_dict

def generate_css_class_name(style_text, index):
    """为样式生成有意义的类名"""
    # 简化 CSS 属性以创建类名
    style_text = style_text.strip()

    # 移除分号和空格
    parts = [p.strip() for p in style_text.split(';') if p.strip()]

    # 提取关键特性
    if 'position' in style_text:
        return f'position-custom-{index}'
    elif 'grid' in style_text:
        return f'grid-custom-{index}'
    elif 'flex' in style_text:
        return f'flex-custom-{index}'
    elif 'background' in style_text:
        return f'bg-custom-{index}'
    elif 'color' in style_text:
        return f'text-custom-{index}'
    elif 'padding' in style_text and 'margin' in style_text:
        return f'spacing-custom-{index}'
    elif 'padding' in style_text:
        return f'padding-custom-{index}'
    elif 'margin' in style_text:
        return f'margin-custom-{index}'
    else:
        return f'style-custom-{index}'

def generate_phase2c_css():
    """生成 Phase 2c 的 CSS"""
    html_path = r'D:\projects\OD_SIM\frontend\control\templates.html'

    style_dict = extract_styles(html_path)

    # 只获取出现 1 次的样式
    single_occurrence = {k: v for k, v in style_dict.items() if v == 1}

    # 按字母顺序排序
    sorted_styles = sorted(single_occurrence.keys())

    css_rules = []
    mappings = {}

    print(f"总计 {len(sorted_styles)} 个仅出现一次的样式\n")
    print("生成 CSS 规则...\n")

    for idx, style_text in enumerate(sorted_styles, 1):
        class_name = generate_css_class_name(style_text, idx)

        # 转换 style 属性为 CSS 规则
        css_properties = style_text.rstrip(';').split(';')
        css_rule = f".{class_name} {{\n"

        for prop in css_properties:
            prop = prop.strip()
            if prop:
                css_rule += f"    {prop};\n"

        css_rule += "}\n"

        css_rules.append(css_rule)
        mappings[style_text] = class_name

        if idx <= 10 or idx % 20 == 0:
            preview = style_text[:60] + '...' if len(style_text) > 60 else style_text
            print(f"{idx:3d}. {class_name:25s} ← {preview}")

    return '\n'.join(css_rules), mappings

if __name__ == '__main__':
    css_output, mappings = generate_phase2c_css()

    # 保存 mappings 为 Python 字典
    output_dict_code = "PHASE_2C_REPLACEMENTS = {\n"
    for style, class_name in sorted(mappings.items(), key=lambda x: x[1]):
        output_dict_code += f"    '{style}': '{class_name}',\n"
    output_dict_code += "}\n"

    # 保存到文件
    import os
    temp_dir = os.path.expanduser('~/.tmp')
    os.makedirs(temp_dir, exist_ok=True)

    mappings_path = os.path.join(temp_dir, 'phase2c_mappings.py')
    css_path = os.path.join(temp_dir, 'phase2c_styles.css')

    with open(mappings_path, 'w', encoding='utf-8') as f:
        f.write(output_dict_code)

    with open(css_path, 'w', encoding='utf-8') as f:
        f.write("/* Phase 2c 自动生成的 CSS 类 */\n\n")
        f.write(css_output)

    print(f"\n✅ 生成完成！")
    print(f"CSS 规则保存至: {css_path}")
    print(f"映射字典保存至: {mappings_path}")
