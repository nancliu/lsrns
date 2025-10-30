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

# Phase 2b 样式映射 - 中等频率样式 (2-4 次出现)
PHASE_2B_REPLACEMENTS = {
    # 出现 4 次
    'width: 100%; padding: 5px;': 'w-full p-5',
    'text-align: center; color: #7f8c8d;': 'text-center-hint',

    # 出现 3 次
    'padding: 8px; text-align: left; color: #2c3e50; font-weight: 600; font-size: 0.9rem;': 'table-cell-bold',
    'width: 100%; border-collapse: collapse;': 'table-full',
    'text-align: center; color: #7f8c8d; padding: 40px 20px;': 'text-center-large',
    'padding: 8px; text-align: center;': 'table-cell-center',
    'padding: 8px 20px; font-size: 0.95rem;': 'p-8 px-12 font-95',
    'padding: 3px 0;': 'py-1',
    'font-size: 0.85rem; color: #7f8c8d;': 'text-xs text-secondary',
    'display: none;': 'hidden',
    'background: #f5f5f5; border-bottom: 1px solid #ddd;': 'table-row-alt',

    # 出现 2 次
    'width: 100%; padding: 6px; border: 1px solid #ddd; border-radius: 3px; box-sizing: border-box;': 'input-field-standard',
    'text-align: center; color: #e74c3c;': 'text-center-error',
    'padding: 8px; text-align: left; color: #2c3e50; font-weight: 600;': 'table-cell-bold-short',
    'padding: 8px; color: #7f8c8d; font-size: 0.9rem;': 'secondary-text-padded',
    'padding: 6px 14px; background: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; cursor: pointer; font-size: 1rem;': 'btn-secondary-large',
    'padding: 6px 12px; background: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; cursor: pointer;': 'btn-secondary',
    'padding: 6px 12px; background: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; color: #bdc3c7; cursor: not-allowed;': 'btn-secondary-disabled',
    'padding: 3px 0; color: #2c3e50;': 'py-1 text-primary',
    'padding: 25px;': 'p-25',
    'padding: 10px; text-align: left; font-weight: 500;': 'table-cell-medium',
    'padding: 10px; text-align: center; width: 70px; font-size: 12px;': 'table-cell-fixed-center',
    'margin-bottom: 15px; color: #2c3e50;': 'mb-15 text-primary',
    'margin: 5px 0; color: #2c3e50; font-weight: 500;': 'text-primary-medium',
    'margin: 5px 0; color: #2c3e50; font-family: monospace;': 'text-primary-mono',
    'margin: 0; color: #2c3e50;': 'm-0 text-primary',
    'flex: 1;': 'flex-1',
    'display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); z-index: 1000; justify-content: center; align-items: center;': 'modal-overlay',
    'display: grid; grid-template-columns: 1fr 1fr; gap: 15px;': 'grid-2col',
    'display: grid; grid-template-columns: 1fr 1fr; gap: 15px; font-size: 0.9rem;': 'grid-2col-small',
    'display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 20px; border-bottom: 2px solid #e9ecef;': 'flex-row-between',
    'display: flex; gap: 10px; align-items: flex-start;': 'flex-start',
    'background: white; border-radius: 8px; max-width: 900px; width: 90%; max-height: 90vh; overflow-y: auto; box-shadow: 0 10px 40px rgba(0,0,0,0.3);': 'modal-content-container',
    'background: #f8f9fa; padding: 15px; border-radius: 6px;': 'container-background',
    'background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 12px;': 'btn-error',
}

# Phase 2c 样式映射 - 低频样式 (1 次出现) - 仅纯 CSS，不含动态表达式
PHASE_2C_REPLACEMENTS = {
    # 背景和边框样式
    'background: #e74c3c; color: white; border: none; padding: 4px 8px; border-radius: 3px; cursor: pointer;': 'btn-error-compact',
    'background: #ebf5fb; border-left: 4px solid #3498db; padding: 15px; margin-bottom: 20px; border-radius: 4px; display: none;': 'alert-info-hidden',
    'background: #ecf0f1; border-bottom: 1px solid #bdc3c7;': 'toolbar-bg',
    'display: none; background: #f8f9fa; padding: 10px; border-radius: 4px; margin-bottom: 10px;': 'hint-hidden',
    'display: none; background: #fff3cd; border-left: 4px solid #ffc107; padding: 10px; margin-bottom: 10px; border-radius: 4px;': 'warning-hidden',
    'background: #f8f9fa;': 'bg-light-gray',
    'margin-top: 10px; padding: 10px; background: white; border-radius: 4px; font-size: 0.9rem;': 'card-small',
    'background: #f8f9fa; border-bottom: 2px solid #e9ecef;': 'divider-gray',
    'padding: 10px 20px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.95rem; margin-right: 10px;': 'btn-primary-md',
    'padding: 10px 20px; background: #95a5a6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.95rem;': 'btn-secondary-md',
    'background: #f8f9fa; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; margin-top: 20px;': 'card-outlined',
    'padding: 2px 8px; background: #ecf0f1; border-radius: 4px; font-size: 0.8rem; color: #7f8c8d; font-family: monospace;': 'tag-code',
    'padding: 4px 10px; margin: 0 2px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem;': 'btn-small-blue',
    'padding: 4px 10px; margin: 0 2px; background: #9b59b6; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem;': 'btn-small-purple',
    'padding: 4px 10px; margin: 0 2px; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem;': 'btn-small-red',
    'padding: 4px 10px; margin: 0 2px; background: #f39c12; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem;': 'btn-small-orange',
    'background: #f8f9fa; padding: 20px; border-radius: 6px; margin-bottom: 15px;': 'container-light-large',
    'padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; background: white; cursor: pointer;': 'input-button-compact',
    'padding: 8px 16px; background: #3498db; color: white; border: none; border-radius: 4px; cursor: pointer;': 'btn-primary-sm',
    'background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);': 'card-shadowed',
    'background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; display: flex; gap: 15px; align-items: center; flex-wrap: wrap;': 'card-flex-center',

    # Flex 和 Grid 布局
    'white-space: nowrap; align-self: flex-start;': 'nowrap-flex-start',
    'display: flex; gap: 10px; margin-bottom: 15px; align-items: center;': 'flex-row-gap',
    'display: flex; justify-content: space-between; align-items: center;': 'flex-row-between',
    'display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;': 'flex-row-between-start',
    'flex: 1; min-width: 250px;': 'flex-auto-min',
    'margin-top: 15px; justify-content: flex-start;': 'flex-start-top',
    'margin-top: 20px; display: flex; justify-content: center; align-items: center; gap: 10px;': 'flex-center-gap',
    'display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 15px;': 'grid-4col',
    'display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;': 'grid-2col-gap',
    'display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 15px;': 'grid-4col-gap',
    'grid-column: 1 / -1;': 'grid-full-width',
    'text-align: center; color: #7f8c8d; grid-column: 1 / -1;': 'grid-center-full',

    # 边距样式
    'margin-bottom: 25px;': 'mb-25',
    'margin-left: 10px;': 'ml-10',
    'margin-left: 15px; font-size: 0.85rem;': 'ml-15-sm',
    'margin-left: 20px;': 'ml-20',
    'margin-right: 10px; font-weight: 600;': 'mr-10-bold',
    'margin-right: 8px;': 'mr-8',
    'margin-top: 15px;': 'mt-15',
    'margin-top: 20px; text-align: right;': 'mt-20-right',
    'margin-top: 30px;': 'mt-30',

    # 填充和尺寸样式
    'width: 100%; padding: 4px; border: 1px solid #ddd; border-radius: 3px; font-size: 12px; min-height: 60px; box-sizing: border-box;': 'textarea-full',
    'width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 0.95rem;': 'input-field-md',
    'padding: 10px; text-align: center; width: 80px;': 'cell-fixed-80',
    'padding: 12px;': 'p-12',
    'padding: 12px; text-align: center;': 'p-12-center',
    'padding: 3px 0; border-bottom: 1px solid #f0f0f0;': 'py-xs-border',
    'padding: 3px 0; width: 120px;': 'py-xs-w120',
    'padding: 5px 15px; font-size: 0.9rem;': 'px-15-sm',
    'padding: 6px 15px; font-size: 0.9rem;': 'px-15-sm2',
    'padding: 8px; min-width: 100px;': 'p-8-minw100',

    # 位置样式
    'background: #ecf0f1; border-bottom: 1px solid #bdc3c7; position: sticky; top: 0;': 'sticky-header',
    'position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0; cursor: default;': 'overlay-full-0',
    'position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 1; cursor: default; pointer-events: none;': 'overlay-full-1',

    # 文本样式
    'white-space: nowrap;': 'nowrap',
    'border-bottom: 1px solid #e9ecef;': 'border-bottom-light',
    'display: inline-block;': 'inline-block',
    'display: none; width: 100%; border-collapse: collapse;': 'table-full-hidden',
    'font-size: 1.2rem;': 'font-lg',
    'max-height: 300px; overflow-y: auto; border: 1px solid #e9ecef; border-radius: 4px;': 'scroll-container-300',
    'max-height: 400px; overflow-y: auto;': 'scroll-container-400',
    'overflow-x: auto;': 'overflow-x-auto',
    'width: 100%; font-size: 0.9rem; color: #7f8c8d;': 'text-full-sm-gray',
    'color: #2c3e50;': 'text-dark',
    'color: #2c3e50; font-size: 1rem;': 'text-dark-md',
    'color: #2c3e50; margin-bottom: 15px; font-size: 1.1rem;': 'heading-dark-lg',
    'color: #3498db; font-size: 1.2rem;': 'text-blue-lg',
    'color: #7f8c8d;': 'text-gray',
    'color: #95a5a6; font-size: 0.85rem; margin-left: 5px;': 'text-light-xs',
    'color: #e74c3c;': 'text-red',
    'color: #e74c3c; font-weight: bold; margin-left: 5px;': 'text-red-bold-ml',
    'font-size: 0.85rem; color: #7f8c8d; margin-left: 10px;': 'text-xs-gray-ml',
    'font-size: 1.1rem; color: #2c3e50; margin-left: 10px;': 'text-md-dark-ml',
    'margin-bottom: 10px; color: #2c3e50;': 'mb-10-dark',
    'margin-left: auto; font-size: 0.9rem; color: #7f8c8d;': 'ml-auto-sm-gray',
    'margin: 5px 0; color: #2c3e50; line-height: 1.6;': 'my-5-dark-leading',
    'padding: 12px; color: #2c3e50; font-weight: 500;': 'p-12-dark-medium',
    'padding: 12px; color: #7f8c8d;': 'p-12-gray',
    'padding: 12px; color: #7f8c8d; font-size: 0.9rem;': 'p-12-gray-sm',
    'padding: 12px; color: #7f8c8d; text-align: center;': 'p-12-gray-center',
    'padding: 12px; text-align: center; font-weight: 600; color: #2c3e50;': 'p-12-center-bold-dark',
    'padding: 3px 0; font-family: monospace; color: #2c3e50;': 'py-xs-code-dark',
    'padding: 3px 0; font-family: monospace; color: #2c3e50; word-break: break-all;': 'py-xs-code-dark-break',
    'padding: 8px; color: #2c3e50; font-size: 0.9rem;': 'p-8-dark-sm',
    'padding: 8px; color: #2c3e50; font-weight: 500;': 'p-8-dark-medium',
    'padding: 8px; color: #7f8c8d; font-family: monospace; font-size: 0.9rem;': 'p-8-gray-code-sm',
    'padding: 8px; color: #7f8c8d; font-family: monospace; word-break: break-all;': 'p-8-gray-code-break',
    'text-align: center; color: #e74c3c; padding: 40px 20px;': 'text-center-red-lg',
    'text-align: center; padding: 30px; color: #7f8c8d;': 'text-center-gray-pad',

    # 其他复合样式
    'border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; margin-bottom: 20px;': 'bordered-card',
    'margin-left: 10px; padding: 3px 10px; border-radius: 10px; font-size: 0.85rem;': 'badge-compact',
    'padding: 5px 15px; font-size: 0.9rem; margin-left: 10px;': 'px-15-sm-ml',
}


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
