#!/usr/bin/env python3
"""
内联样式替换脚本 - Phase 2a
将 templates.html 中的内联 style 属性替换为 CSS 类

用法:
    python replace_inline_styles.py --phase 2a --dry-run
    python replace_inline_styles.py --phase 2a --apply
"""

import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple

# ==================== Phase 2a 样式映射 ====================
# 格式: 原样式 -> 替换类

PHASE_2A_REPLACEMENTS = {
    # 高频样式 (出现 10 次)
    'padding: 8px;': 'p-8',
    'padding: 14px 12px; text-align: left; font-weight: 600; font-size: 0.85rem; white-space: nowrap;': 'table-cell-head',
    'padding: 10px;': 'p-10',
    'display: block; margin-bottom: 5px; font-weight: 600;': 'label-text',

    # 高频样式 (出现 9 次)
    'margin: 5px 0; color: #7f8c8d; font-size: 0.9rem;': 'hint-text-small',
    'margin: 5px 0; color: #2c3e50;': 'info-text',

    # 高频样式 (出现 8 次)
    'padding: 10px; text-align: left; font-size: 12px;': 'table-cell-basic',

    # 高频样式 (出现 7 次)
    'width: 100%; padding: 8px;': 'w-full p-8',
    'width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px; box-sizing: border-box;': 'input-field',
    'color: #2c3e50; margin-top: 0;': 'text-primary mt-0',

    # 高频样式 (出现 5 次)
    'padding: 12px; text-align: left; font-weight: 600; color: #2c3e50;': 'table-cell-head-data',
    'margin: 5px 0; color: #7f8c8d;': 'hint-text',
    'background: #f8f9fa; padding: 15px; border-radius: 6px; margin-bottom: 20px;': 'container-light',
}

# Phase 2b 和 2c 的样式映射 (待定义)
PHASE_2B_REPLACEMENTS = {}
PHASE_2C_REPLACEMENTS = {}


class StyleReplacer:
    """处理内联样式替换的类"""

    def __init__(self, html_path: str, phase: str = '2a'):
        self.html_path = Path(html_path)
        self.phase = phase
        self.replacements = self._get_replacements()
        self.original_content = None
        self.modified_content = None
        self.stats = {
            'total_replacements': 0,
            'styles_replaced': {},
            'html_lines_removed': 0
        }

    def _get_replacements(self) -> Dict[str, str]:
        """获取当前阶段的替换映射"""
        if self.phase == '2a':
            return PHASE_2A_REPLACEMENTS
        elif self.phase == '2b':
            return PHASE_2B_REPLACEMENTS
        elif self.phase == '2c':
            return PHASE_2C_REPLACEMENTS
        else:
            raise ValueError(f"Unknown phase: {self.phase}")

    def load_html(self) -> bool:
        """加载 HTML 文件"""
        try:
            with open(self.html_path, 'r', encoding='utf-8') as f:
                self.original_content = f.read()
            return True
        except Exception as e:
            print(f"❌ 无法读取 HTML 文件: {e}")
            return False

    def replace_styles(self) -> bool:
        """替换内联样式"""
        if self.original_content is None:
            print("❌ 请先加载 HTML 文件")
            return False

        self.modified_content = self.original_content

        for original_style, replacement_class in self.replacements.items():
            # 创建完整的 style="..." 模式
            style_pattern = f'style="{re.escape(original_style)}"'
            style_replacement = f'class="{replacement_class}"'

            # 计算替换数
            matches = len(re.findall(style_pattern, self.modified_content))

            if matches > 0:
                # 执行替换
                self.modified_content = self.modified_content.replace(
                    f'style="{original_style}"',
                    f'class="{replacement_class}"'
                )

                self.stats['total_replacements'] += matches
                self.stats['styles_replaced'][original_style[:50]] = {
                    'count': matches,
                    'new_class': replacement_class
                }
                print(f"✅ 替换 {matches:2d} 个: {replacement_class:20s} ← {original_style[:50]}")

        # 计算行数差异
        original_lines = len(self.original_content.split('\n'))
        modified_lines = len(self.modified_content.split('\n'))
        self.stats['html_lines_removed'] = original_lines - modified_lines

        return True

    def preview_changes(self, max_lines: int = 20) -> None:
        """预览变更"""
        if self.modified_content is None:
            print("❌ 请先执行替换")
            return

        print("\n" + "="*80)
        print("📊 替换统计")
        print("="*80)
        print(f"总替换数: {self.stats['total_replacements']} 个 style 属性")
        print(f"HTML 行数变化: {self.stats['html_lines_removed']} 行")

        print("\n📋 替换详情:")
        for style, info in list(self.stats['styles_replaced'].items())[:max_lines]:
            print(f"  • {info['count']:2d}x → {info['new_class']}")

    def save_html(self, output_path: str = None) -> bool:
        """保存修改后的 HTML"""
        if self.modified_content is None:
            print("❌ 请先执行替换")
            return False

        save_path = Path(output_path) if output_path else self.html_path

        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(self.modified_content)
            print(f"✅ 文件已保存: {save_path}")
            return True
        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='内联样式替换脚本 - Phase 2a/2b/2c'
    )
    parser.add_argument(
        '--phase',
        choices=['2a', '2b', '2c'],
        default='2a',
        help='执行阶段 (默认: 2a)'
    )
    parser.add_argument(
        '--html',
        default=r'D:\projects\OD_SIM\frontend\control\templates.html',
        help='HTML 文件路径'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='仅预览，不保存'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='执行替换并保存'
    )

    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("请指定 --dry-run 或 --apply")
        sys.exit(1)

    print(f"\n🔄 Phase {args.phase} - 开始处理\n")

    # 创建替换器
    replacer = StyleReplacer(args.html, phase=args.phase)

    # 加载 HTML
    if not replacer.load_html():
        sys.exit(1)

    # 执行替换
    if not replacer.replace_styles():
        sys.exit(1)

    # 预览
    replacer.preview_changes()

    # 保存
    if args.apply:
        print(f"\n💾 保存修改...\n")
        if replacer.save_html():
            print("✅ Phase {args.phase} 完成！")
        else:
            sys.exit(1)
    else:
        print(f"\n⚠️  --dry-run 模式，未保存文件")
        print(f"要应用更改，请运行: python replace_inline_styles.py --phase {args.phase} --apply")


if __name__ == '__main__':
    main()
