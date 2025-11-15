"""
迁移事件场景 XML 文件格式

将旧的 closedLane 格式转换为 SUMO 1.24+ 兼容的 rerouter 格式

旧格式:
    <closedLane id="accident_10762" edge="-7016" lanes="-7016_1"
                disallow="all" begin="1800" end="9098"/>

新格式:
    <rerouter id="accident_10762" edges="-7016">
        <interval begin="1800" end="9098">
            <closingLaneReroute id="-7016_1" disallow="all"/>
        </interval>
    </rerouter>

使用方法:
    python scripts/migrate_event_xml_format.py --dry-run  # 测试模式（不修改文件）
    python scripts/migrate_event_xml_format.py            # 执行迁移
"""

import re
import argparse
from pathlib import Path
from typing import List, Tuple
import xml.etree.ElementTree as ET


def parse_closedlane_element(line: str) -> dict:
    """
    解析 closedLane 元素的属性

    Args:
        line: 包含 closedLane 元素的行

    Returns:
        属性字典，包括 id, edge, lanes, disallow, begin, end
    """
    attrs = {}

    # 提取属性
    patterns = {
        'id': r'id="([^"]+)"',
        'edge': r'edge="([^"]+)"',
        'lanes': r'lanes="([^"]+)"',
        'disallow': r'disallow="([^"]+)"',
        'begin': r'begin="([^"]+)"',
        'end': r'end="([^"]+)"'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, line)
        if match:
            attrs[key] = match.group(1)

    return attrs


def convert_to_rerouter(attrs: dict) -> List[str]:
    """
    将 closedLane 属性转换为 rerouter XML 行

    Args:
        attrs: closedLane 属性字典

    Returns:
        新格式的 XML 行列表
    """
    lines = []

    # 构建 rerouter 元素
    rerouter_id = attrs.get('id', 'unknown')
    edge = attrs.get('edge', 'unknown')
    begin = attrs.get('begin', '0')
    end = attrs.get('end', '0')
    disallow = attrs.get('disallow', 'all')
    lanes = attrs.get('lanes', '').split()

    lines.append(f'    <rerouter id="{rerouter_id}" edges="{edge}">')
    lines.append(f'        <interval begin="{begin}" end="{end}">')

    # 为每个车道添加 closingLaneReroute
    for lane_id in lanes:
        lines.append(f'            <closingLaneReroute id="{lane_id}" disallow="{disallow}"/>')

    lines.append('        </interval>')
    lines.append('    </rerouter>')

    return lines


def migrate_xml_file(file_path: Path, dry_run: bool = False) -> Tuple[bool, str]:
    """
    迁移单个 XML 文件

    Args:
        file_path: XML 文件路径
        dry_run: 如果为 True，不修改文件

    Returns:
        (是否修改, 状态消息)
    """
    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 检查是否包含 closedLane
        has_closedlane = any('<closedLane' in line for line in lines)

        if not has_closedlane:
            return False, "No closedLane elements found"

        # 转换内容
        new_lines = []
        i = 0
        modified = False

        while i < len(lines):
            line = lines[i]

            if '<closedLane' in line:
                # 解析 closedLane 元素
                attrs = parse_closedlane_element(line)

                # 转换为 rerouter 格式
                rerouter_lines = convert_to_rerouter(attrs)

                # 添加注释说明
                new_lines.append('    <!-- Converted from closedLane to rerouter format -->\n')
                new_lines.extend([l + '\n' for l in rerouter_lines])
                new_lines.append('\n')

                modified = True
            else:
                new_lines.append(line)

            i += 1

        # 如果不是干运行，写入文件
        if modified and not dry_run:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True, "Migrated successfully"
        elif modified:
            return True, "Would be migrated (dry-run)"
        else:
            return False, "No changes needed"

    except Exception as e:
        return False, f"Error: {str(e)}"


def find_event_xml_files() -> List[Path]:
    """
    查找所有需要迁移的事件场景 XML 文件

    Returns:
        XML 文件路径列表
    """
    files = []

    # 查找 output/scenarios 下的文件
    scenarios_dir = Path('output/scenarios')
    if scenarios_dir.exists():
        files.extend(scenarios_dir.rglob('scenario_*.add.xml'))

    # 查找 cases 下的文件
    cases_dir = Path('cases')
    if cases_dir.exists():
        for case_dir in cases_dir.glob('case_*'):
            # 查找案例配置目录和仿真目录下的文件
            files.extend(case_dir.rglob('scenario_*.add.xml'))

    return sorted(files)


def main():
    parser = argparse.ArgumentParser(
        description='Migrate event scenario XML files from closedLane to rerouter format'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - show what would be changed without modifying files'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Migrate a specific file instead of all files'
    )

    args = parser.parse_args()

    print("=" * 80)
    print("事件场景 XML 格式迁移工具")
    print("closedLane → rerouter (SUMO 1.24+ 兼容)")
    print("=" * 80)
    print()

    if args.dry_run:
        print("⚠️  DRY-RUN 模式：将显示需要修改的文件，但不会实际修改")
        print()

    # 获取文件列表
    if args.file:
        files = [Path(args.file)]
    else:
        files = find_event_xml_files()

    print(f"找到 {len(files)} 个事件场景 XML 文件")
    print()

    # 迁移统计
    migrated_count = 0
    skipped_count = 0
    error_count = 0

    # 处理每个文件
    for file_path in files:
        modified, message = migrate_xml_file(file_path, dry_run=args.dry_run)

        if modified:
            migrated_count += 1
            status = "🔄" if args.dry_run else "✓"
            try:
                rel_path = file_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = file_path
            print(f"{status} {rel_path}")
            if args.dry_run:
                print(f"   → {message}")
        elif "Error" in message:
            error_count += 1
            try:
                rel_path = file_path.relative_to(Path.cwd())
            except ValueError:
                rel_path = file_path
            print(f"✗ {rel_path}")
            print(f"   → {message}")
        else:
            skipped_count += 1

    # 显示统计
    print()
    print("=" * 80)
    print("迁移完成")
    print("=" * 80)
    print(f"需要迁移: {migrated_count}")
    print(f"已是新格式: {skipped_count}")
    print(f"错误: {error_count}")
    print()

    if args.dry_run and migrated_count > 0:
        print("⚠️  这是 DRY-RUN 模式，文件尚未修改")
        print("运行不带 --dry-run 参数来执行实际迁移:")
        print(f"    python {Path(__file__).name}")
        print()


if __name__ == '__main__':
    main()
