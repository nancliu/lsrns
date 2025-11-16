#!/usr/bin/env python3
"""
场景索引生成脚本

该脚本扫描 output/scenarios 目录，从每个场景的 event_description.json 中
提取完整的场景信息，生成 scenario_index.json 文件。

使用方法:
    python generate_scenario_index.py [output_dir]

    output_dir: output/scenarios 目录的路径，默认为 ../output/scenarios
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 事件类型映射（根据目录前缀）
EVENT_TYPE_MAPPING = {
    '01_accident': '交通事故',
    '02_congestion': '交通拥堵',
    '03_road_control': '道路管制',
    '05_breakdown': '车辆故障',
    '06_weather': '恶劣天气',
    '07_flowsurge': '流量激增',
    '99_07_flowsurge': '流量激增'
}

# 策略名称规范化映射
STRATEGY_NORMALIZATION = {
    'no_control': 'NO_CONTROL',
    'tec': 'TEC',
    'vss': 'VSS',
    'dhs': 'DHS'
}

# event_type清理规则
EVENT_TYPE_CLEANUP = {
    '交通管制': '道路管制',
    '交通阻塞': '交通拥堵',
    '流量激增': '流量激增工况'
}


def normalize_strategy(strategy_str):
    """规范化策略名称"""
    strategy_lower = strategy_str.lower()
    return STRATEGY_NORMALIZATION.get(strategy_lower, strategy_str.upper())


def cleanup_event_type(event_type_str):
    """清理event_type，确保命名一致"""
    return EVENT_TYPE_CLEANUP.get(event_type_str, event_type_str)


def extract_scenario_data(scenario_dir, event_type_from_dir):
    """
    从场景目录中提取完整数据

    Args:
        scenario_dir: 场景目录的Path对象
        event_type_from_dir: 从目录结构推断的event_type

    Returns:
        tuple: (scenario_data_dict, success_flag, error_message)
    """
    # 解析目录名获取event_id和strategy
    # 处理形如 scenario_10754_no_control 的目录名
    name = scenario_dir.name.replace('scenario_', '')

    # 检查已知的策略后缀
    strategy = 'UNKNOWN'
    event_id = name

    for strategy_suffix in ['no_control', 'dhs', 'tec', 'vss']:
        if name.endswith('_' + strategy_suffix):
            event_id = name[:-len('_' + strategy_suffix)]
            strategy = normalize_strategy(strategy_suffix)
            break
    else:
        # 如果没有找到已知后缀，使用最后的部分
        parts = name.rsplit('_', 1)
        if len(parts) > 1:
            event_id = parts[0]
            strategy = normalize_strategy(parts[1])

    # 初始化默认值
    location = {
        "road": "",
        "direction": "",
        "mileage": "",
        "junction_id": "",
        "edge_id": ""
    }
    time_info = {
        "start_time": "2025-01-01 00:00:00",
        "end_time": "2025-01-01 01:00:00",
        "duration_hours": 1
    }
    event_desc = ""
    event_type = event_type_from_dir

    # 尝试从event_description.json读取详细信息
    event_desc_file = scenario_dir / 'event_description.json'
    error_msg = None

    if event_desc_file.exists():
        try:
            with open(event_desc_file, 'r', encoding='utf-8') as f:
                event_data = json.load(f)

                # 提取location信息
                if 'location' in event_data and isinstance(event_data['location'], dict):
                    location = event_data['location']

                # 提取time信息
                if 'time' in event_data and isinstance(event_data['time'], dict):
                    time_info = event_data['time']

                # 提取事件描述
                if 'event_description' in event_data:
                    event_desc = event_data['event_description']

                # 从event_description.json读取event_type（如果存在）
                if 'event_type' in event_data:
                    event_type = cleanup_event_type(event_data['event_type'])
        except json.JSONDecodeError as e:
            error_msg = f"JSON格式错误: {e}"
        except Exception as e:
            error_msg = f"读取错误: {e}"
    else:
        error_msg = "event_description.json not found"

    # 构建场景对象
    scenario_obj = {
        "event_id": event_id,
        "event_type": event_type,
        "strategy": strategy,
        "event_description": event_desc,
        "location": location,
        "time": time_info,
        "files": {
            "scenario_dir": scenario_dir.name,
            "add_xml": "",
            "event_description": "event_description.json",
            "traffic_config": "traffic_input_config.json",
            "control_config": "control_strategy_config.json"
        },
        "created_cases": [],
        "case_count": 0
    }

    return scenario_obj, error_msg is None, error_msg


def generate_scenario_index(output_scenarios_dir, output_file=None):
    """
    生成场景索引文件

    Args:
        output_scenarios_dir: output/scenarios 目录的路径
        output_file: 输出文件路径，默认为 {output_scenarios_dir}/scenario_index.json

    Returns:
        dict: 生成结果统计信息
    """
    base_dir = Path(output_scenarios_dir)

    if not base_dir.exists():
        raise ValueError(f"输出目录不存在: {base_dir}")

    if output_file is None:
        output_file = base_dir / "scenario_index.json"
    else:
        output_file = Path(output_file)

    scenarios = []
    event_type_count = defaultdict(int)
    errors = []

    # 遍历每个事件类型目录
    for event_dir in sorted(base_dir.iterdir()):
        if not event_dir.is_dir():
            continue

        # 检查是否为事件类型目录
        if not any(event_dir.name.startswith(prefix) for prefix in EVENT_TYPE_MAPPING.keys()):
            continue

        event_type = EVENT_TYPE_MAPPING.get(event_dir.name, event_dir.name)

        # 遍历该事件类型下的所有scenario目录
        for scenario_dir in sorted(event_dir.iterdir()):
            if not (scenario_dir.is_dir() and scenario_dir.name.startswith('scenario_')):
                continue

            # 跳过测试场景
            if 'TEST' in scenario_dir.name:
                continue

            # 提取场景数据
            scenario_obj, success, error_msg = extract_scenario_data(scenario_dir, event_type)
            scenarios.append(scenario_obj)
            event_type_count[scenario_obj['event_type']] += 1

            if not success:
                errors.append((scenario_dir.name, error_msg))

    # 创建索引
    index_data = {
        "timestamp": datetime.now().isoformat(),
        "total_scenarios": len(scenarios),
        "scenarios": scenarios
    }

    # 保存文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    return {
        'success': True,
        'total_scenarios': len(scenarios),
        'event_types': dict(event_type_count),
        'output_file': str(output_file),
        'file_size_kb': output_file.stat().st_size / 1024,
        'errors': errors
    }


def main():
    """命令行入口"""
    # 获取输出目录
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    else:
        # 默认相对于脚本的路径
        script_dir = Path(__file__).parent
        output_dir = script_dir.parent / "output" / "scenarios"

    try:
        print(f"正在生成场景索引...")
        print(f"输出目录: {output_dir}\n")

        result = generate_scenario_index(output_dir)

        print(f"✓ 场景索引生成成功")
        print(f"✓ 总场景数: {result['total_scenarios']}")
        print(f"✓ 输出文件: {result['output_file']}")
        print(f"✓ 文件大小: {result['file_size_kb']:.1f} KB\n")

        print("事件类型统计:")
        for event_type in sorted(result['event_types'].keys()):
            count = result['event_types'][event_type]
            print(f"  {event_type}: {count}")

        if result['errors']:
            print(f"\n⚠️  出现 {len(result['errors'])} 个错误:")
            for scenario_name, error in result['errors'][:5]:
                print(f"  - {scenario_name}: {error}")
            if len(result['errors']) > 5:
                print(f"  ... 还有 {len(result['errors']) - 5} 个")
        else:
            print(f"\n✓ 所有场景都已成功处理")

        return 0

    except Exception as e:
        print(f"✗ 错误: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
