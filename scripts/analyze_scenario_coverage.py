"""
分析场景生成覆盖率和管控数据提取情况

检查：
1. CSV中总共有多少事件
2. 有多少事件有管控数据
3. 当前生成了多少场景
4. 管控数据是否正确提取
"""

import pandas as pd
import json
from pathlib import Path

def analyze_event_coverage():
    """分析事件覆盖率"""

    # 1. 读取CSV事件数据
    csv_path = Path("events/all_extracted_events.csv")
    df = pd.read_csv(csv_path)

    print("=" * 80)
    print("📊 事件数据分析")
    print("=" * 80)
    print(f"\n总事件数: {len(df)}")

    # 2. 按事件类型统计
    print("\n事件类型分布:")
    event_type_counts = df['类型'].value_counts()
    for event_type, count in event_type_counts.items():
        print(f"  {event_type}: {count}")

    # 3. 统计有管控数据的事件
    has_control_start = df['管控开始时间'].notna()
    has_control_station = df['管控收费站'].notna()
    has_control = has_control_start & has_control_station

    print(f"\n有管控数据的事件: {has_control.sum()} / {len(df)} ({has_control.sum()/len(df)*100:.1f}%)")

    # 按事件类型统计有管控数据的事件
    print("\n各事件类型的管控数据覆盖:")
    for event_type in df['类型'].unique():
        type_mask = df['类型'] == event_type
        type_control = has_control & type_mask
        print(f"  {event_type}: {type_control.sum()} / {type_mask.sum()} ({type_control.sum()/type_mask.sum()*100:.1f}%)")

    # 4. 统计数据完整性（用于生成场景）
    print("\n" + "=" * 80)
    print("📋 数据完整性分析（用于场景生成）")
    print("=" * 80)

    # 必需字段
    has_edge_id = df['edge_id'].notna()
    has_junction_id = df['junction_id'].notna()
    has_start_time = df['开始时间'].notna()
    has_end_time = df['结束时间'].notna()
    has_lane_occupation = df['占用车道情况'].notna()

    # 基本完整性（不含车道占用，因为交通管制和交通阻塞不需要）
    basic_complete = has_edge_id & has_start_time & has_end_time
    print(f"\n基本数据完整 (edge_id + 时间): {basic_complete.sum()} / {len(df)}")

    # 完整性（含车道占用）
    full_complete = basic_complete & has_lane_occupation
    print(f"完整数据 (+ 车道占用): {full_complete.sum()} / {len(df)}")

    # 交通管制特殊要求（需要管控数据）
    road_control_mask = df['类型'] == '交通管制'
    road_control_complete = road_control_mask & has_control & has_edge_id & has_start_time & has_end_time
    print(f"交通管制数据完整 (需要管控数据): {road_control_complete.sum()} / {road_control_mask.sum()}")

    # 交通阻塞特殊要求（不需要车道占用）
    congestion_mask = df['类型'] == '交通阻塞'
    congestion_complete = congestion_mask & basic_complete
    print(f"交通阻塞数据完整 (不需要车道占用): {congestion_complete.sum()} / {congestion_mask.sum()}")

    # 5. 读取生成的场景索引
    print("\n" + "=" * 80)
    print("🎯 场景生成情况")
    print("=" * 80)

    scenario_index_path = Path("output/scenarios/scenario_index.json")
    if scenario_index_path.exists():
        with open(scenario_index_path, 'r', encoding='utf-8') as f:
            scenario_index = json.load(f)

        metadata = scenario_index['metadata']
        print(f"\n生成的场景总数: {metadata['total_scenarios']}")
        print(f"基于事件数: {metadata['total_events']}")
        print(f"成功: {metadata['success_count']}")
        print(f"失败: {metadata['failed_count']}")

        print("\n按事件类型:")
        for event_type, count in metadata['stats_by_event_type'].items():
            print(f"  {event_type}: {count} 场景")

        print("\n按控制策略:")
        for strategy, count in metadata['stats_by_strategy'].items():
            print(f"  {strategy}: {count} 场景")

        # 6. 检查管控数据提取情况
        print("\n" + "=" * 80)
        print("🔍 管控数据提取验证")
        print("=" * 80)

        # 随机抽取几个场景检查管控数据
        scenarios = scenario_index['scenarios']

        # 统计使用CSV管控数据的场景
        csv_control_count = 0
        event_activated_count = 0

        for scenario in scenarios[:10]:  # 检查前10个场景
            event_id = scenario['event_id']
            strategy = scenario['strategy']

            # 读取control_strategy_config.json
            config_path = Path(scenario['files']['control_strategy_config'])
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    control_config = json.load(f)

                # 检查是否使用CSV控制数据
                params = control_config.get('parameters', {})
                if 'csv_control' in params and params['csv_control']:
                    csv_control_count += 1
                    print(f"\n✅ Event {event_id} ({strategy}): 使用CSV管控数据")
                    if 'toll_station_ids' in params:
                        print(f"   收费站: {params['toll_station_ids']}")
                    if 'control_range' in params:
                        print(f"   管控范围: {params['control_range']}")
                else:
                    event_activated_count += 1
                    print(f"\n⚠️  Event {event_id} ({strategy}): 事件激活模式（无CSV管控数据）")

        print(f"\n前10个场景中:")
        print(f"  使用CSV管控数据: {csv_control_count}")
        print(f"  事件激活模式: {event_activated_count}")

    else:
        print("\n⚠️  未找到scenario_index.json，尚未生成场景")

    # 7. 生成建议
    print("\n" + "=" * 80)
    print("💡 建议")
    print("=" * 80)

    potential_events = basic_complete.sum()
    current_events = 18 if scenario_index_path.exists() else 0

    print(f"\n当前生成: {current_events} 个事件的场景")
    print(f"潜在可用: {potential_events} 个事件 (有基本数据)")
    print(f"覆盖率: {current_events/potential_events*100:.1f}%")

    if current_events < potential_events:
        print(f"\n🔧 可以增加覆盖率:")
        print(f"   1. 修改 filter_representative_events() 中的 target_count 参数")
        print(f"   2. 当前默认选择 3 events/type × 6 types = 18 events")
        print(f"   3. 可以增加到 {potential_events} 个事件（所有有效事件）")
        print(f"   4. 建议分批生成：先50个，再100个，最后全部")

if __name__ == "__main__":
    analyze_event_coverage()
