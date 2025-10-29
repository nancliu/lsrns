"""
快速方案生成脚本 - 基于模板快速创建Plan变体

用途: 在完整自动化实现之前，快速生成可用的Plan方案供批量优化开发使用

使用方法:
    python scripts/quick_plan_generator.py --pattern morning_peak --strategy VSS
    python scripts/quick_plan_generator.py --pattern evening_peak --strategy DHS
    python scripts/quick_plan_generator.py --pattern allday --strategy "VSS+DHS+TEC"

版本: v0.1
日期: 2025-10-27
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 配置定义
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONGESTION_PATTERNS = {
    'morning_peak_severe': {
        'display_name': '早高峰严重拥堵',
        'description': '工作日早高峰时段（6:00-10:00）出现的严重拥堵',
        'time_window': '6:00-10:00',
        'severity_threshold': '平均速度 < 30 km/h，持续时长 ≥ 2小时',
        'characteristics': {'speed': '<30km/h', 'duration': '2-4h'},
        'applicable_road_types': ['城市快速路', '高速公路主线']
    },
    'evening_peak_severe': {
        'display_name': '晚高峰严重拥堵',
        'description': '工作日晚高峰时段（16:00-20:00）出现的严重拥堵',
        'time_window': '16:00-20:00',
        'severity_threshold': '平均速度 < 30 km/h，持续时长 ≥ 2小时',
        'characteristics': {'speed': '<30km/h', 'duration': '2-4h'},
        'applicable_road_types': ['城市快速路', '高速公路主线']
    },
    'evening_peak_high_flow': {
        'display_name': '晚高峰高流量拥堵',
        'description': '工作日晚高峰时段（16:00-20:00）出现的高流量拥堵',
        'time_window': '16:00-20:00',
        'severity_threshold': '平均速度 < 20 km/h，流量 > 300 veh/hr，持续时长 ≥ 3小时',
        'characteristics': {'speed': '<20km/h', 'flow': '>300veh/hr', 'duration': '3-6h'},
        'applicable_road_types': ['城市快速路', '高速公路主线'],
        'infrastructure_requirements': ['路段长度 ≥ 3 km', '应急车道宽度 ≥ 3.0 m']
    },
    'allday_persistent_severe': {
        'display_name': '全天持续拥堵',
        'description': '工作日全天持续拥堵（拥堵持续时长>6小时）',
        'time_window': '全天（6:00-20:00拥堵持续>6小时）',
        'severity_threshold': '平均速度 < 20 km/h，持续时长 > 6小时，入口流量 > 主线容量80%',
        'characteristics': {'speed': '<20km/h', 'duration': '>6h', 'entrance_overflow': True},
        'applicable_road_types': ['高速公路主线'],
        'infrastructure_requirements': ['主线路段长度 ≥ 5 km', '应急车道宽度 ≥ 3.0 m', '上游具备入口匝道', '具备实时监控系统']
    }
}

STRATEGY_COMBINATIONS = {
    'VSS': {
        'display_name': 'VSS可变限速',
        'strategy_types': ['VSS'],
        'complexity': '简单',
        'reference_strategies': ['strategy_real_vss_g4202_001'],
        'expected_effects': {
            'speed_improvement': '预期速度提升100-200%（具体改善幅度取决于初始拥堵严重程度）',
            'implementation_difficulty': '简单（单策略，快速部署）'
        }
    },
    'DHS': {
        'display_name': 'DHS应急车道开放',
        'strategy_types': ['DHS'],
        'complexity': '简单',
        'reference_strategies': ['strategy_real_dhs_g4202_001'],
        'expected_effects': {
            'speed_improvement': '预期速度提升80-150%',
            'capacity_increase': '通行能力提升30-35%（3车道→4车道）',
            'implementation_difficulty': '简单（单策略，需确认应急车道条件）'
        },
        'infrastructure_requirements': ['应急车道宽度 ≥ 3.0 m', '路段长度 ≥ 3 km']
    },
    'TEC': {
        'display_name': 'TEC入口流量控制',
        'strategy_types': ['TEC'],
        'complexity': '简单',
        'reference_strategies': ['strategy_real_tec_g5_001'],
        'expected_effects': {
            'entrance_flow_control': '入口流量削减50-70%',
            'speed_improvement': '预期速度提升50-120%',
            'implementation_difficulty': '简单（单策略，需确认入口控制点）'
        },
        'infrastructure_requirements': ['上游具备入口匝道']
    },
    'VSS+DHS': {
        'display_name': 'VSS+DHS复合管控',
        'strategy_types': ['VSS', 'DHS'],
        'complexity': '中等',
        'reference_strategies': ['strategy_real_vss_g4202_002', 'strategy_real_dhs_g4202_002'],
        'coordination': {
            'activation_sequence': {
                'phase1': 'VSS先激活（提前1小时预警限速80 km/h）',
                'phase2': 'VSS严格限速+DHS同步开放（50 km/h+应急车道）',
                'phase3': 'VSS恢复+DHS关闭'
            },
            'parameter_coupling': {
                'vss_dhs_coupling': 'DHS开放后，VSS限速可适当提高10 km/h'
            }
        },
        'expected_effects': {
            'speed_improvement': '预期速度提升200-300%',
            'capacity_increase': '通行能力提升30-35%（3车道→4车道）',
            'implementation_difficulty': '中等（双策略协同，需时序配合）'
        },
        'infrastructure_requirements': ['路段长度 ≥ 3 km', '应急车道宽度 ≥ 3.0 m']
    },
    'VSS+TEC': {
        'display_name': 'VSS+TEC复合管控',
        'strategy_types': ['VSS', 'TEC'],
        'complexity': '中等',
        'reference_strategies': ['strategy_real_vss_g5_001', 'strategy_real_tec_g5_001'],
        'coordination': {
            'activation_sequence': {
                'phase1': 'TEC先激活入口限流',
                'phase2': 'VSS配合限速控制主线流速',
                'phase3': '协同解除'
            },
            'parameter_coupling': {
                'tec_vss_coupling': 'TEC限流值应使主线流量保持在VSS限速下的安全容量范围内'
            }
        },
        'expected_effects': {
            'speed_improvement': '预期速度提升150-250%',
            'entrance_flow_control': '入口流量削减50-70%',
            'implementation_difficulty': '中等（双策略协同，需参数耦合）'
        },
        'infrastructure_requirements': ['上游具备入口匝道']
    },
    'VSS+DHS+TEC': {
        'display_name': 'VSS+DHS+TEC三策略立体管控',
        'strategy_types': ['VSS', 'DHS', 'TEC'],
        'complexity': '高',
        'reference_strategies': ['strategy_real_vss_g5_001', 'strategy_real_dhs_g5_002', 'strategy_real_tec_g5_001'],
        'coordination': {
            'overall_strategy': '三层防御：上游控源（TEC） → 中游稳流（VSS） → 下游扩容（DHS）',
            'spatial_layers': {
                'upstream_layer': {'control_type': 'TEC入口流量控制', 'function': '源头控制进入主线的车辆数量'},
                'midstream_layer': {'control_type': 'VSS可变限速', 'function': '稳定交通流，防止速度波动'},
                'downstream_layer': {'control_type': 'DHS应急车道开放', 'function': '增加通行能力，疏导车辆'}
            },
            'time_coordination': {
                'morning_peak': {'6:00-7:00': 'TEC开始限流，VSS预警限速', '7:00-10:00': 'TEC严格限流，VSS严格限速，DHS开放', '10:00+': '所有策略逐步恢复'},
                'evening_peak': {'16:00-17:00': 'TEC开始限流，VSS预警，DHS准备', '17:00-20:00': '三策略全激活', '20:00+': '所有策略解除'}
            },
            'parameter_coupling': {
                'tec_vss_coupling': 'TEC限流值应使主线流量保持在VSS限速下的安全容量范围内',
                'vss_dhs_coupling': 'DHS开放后，VSS限速应适当提高10-15 km/h'
            }
        },
        'expected_effects': {
            'speed_improvement': '预期速度提升150-250%',
            'capacity_increase': '主线通行能力提升30-35%',
            'entrance_flow_control': '入口流量削减50-70%',
            'congestion_duration_reduction': '拥堵持续时长减少50-70%',
            'implementation_difficulty': '高（三策略协同，需精细化管理）'
        },
        'infrastructure_requirements': ['主线路段长度 ≥ 5 km', '应急车道宽度 ≥ 3.0 m', '上游具备入口匝道', '具备实时监控系统']
    }
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Plan生成器
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class QuickPlanGenerator:
    """快速Plan生成器（基于模板）"""

    def __init__(self, output_dir: str = "control_data/plans"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_plan(self, pattern_key: str, strategy_combo_key: str) -> Dict:
        """
        生成Plan方案

        Args:
            pattern_key: 拥堵模式键（如 'morning_peak_severe'）
            strategy_combo_key: 策略组合键（如 'VSS' 或 'VSS+DHS'）

        Returns:
            plan_metadata: 生成的Plan元数据
        """
        pattern = CONGESTION_PATTERNS.get(pattern_key)
        strategy_combo = STRATEGY_COMBINATIONS.get(strategy_combo_key)

        if not pattern:
            raise ValueError(f"Unknown pattern: {pattern_key}")
        if not strategy_combo:
            raise ValueError(f"Unknown strategy combination: {strategy_combo_key}")

        # 验证适用性
        self._validate_compatibility(pattern, strategy_combo)

        # 生成Plan ID
        strategy_id_part = strategy_combo_key.lower().replace('+', '_')
        plan_id = f"plan_{strategy_id_part}_{pattern_key}"

        # 生成Plan名称
        plan_name = f"{pattern['display_name']}{strategy_combo['display_name']}方案"

        # 生成描述
        description = f"针对{pattern['description']}，采用{strategy_combo['display_name']}管控。"

        # 构建标签
        tags = ['P0', pattern_key.split('_')[0] + '高峰']
        tags.append(strategy_combo['complexity'] + '策略')
        tags.extend(strategy_combo['strategy_types'])

        # 构建Plan元数据
        now = datetime.now().isoformat()
        plan_metadata = {
            'plan_id': plan_id,
            'plan_name': plan_name,
            'is_baseline': False,
            'description': description,
            'strategy_ids': strategy_combo['reference_strategies'],
            'tags': tags,
            'complexity_level': strategy_combo['complexity'],
            'target_scenario': f"{pattern['time_window']}，{pattern['severity_threshold']}",
            'applicable_conditions': {
                'congestion_pattern': pattern['description'],
                'time_window': pattern['time_window'],
                'severity_threshold': pattern['severity_threshold'],
                'road_types': pattern['applicable_road_types']
            },
            'expected_effects': strategy_combo['expected_effects'],
            'validation_records': [],
            'additional_file_path': f'control_data/plans/{plan_id}/control.add.xml',
            'created_at': now,
            'updated_at': now,
            'generation_method': 'quick_template_based'
        }

        # 添加基础设施要求（如果有）
        if 'infrastructure_requirements' in pattern:
            plan_metadata['applicable_conditions']['infrastructure_requirements'] = pattern['infrastructure_requirements']
        elif 'infrastructure_requirements' in strategy_combo:
            plan_metadata['applicable_conditions']['infrastructure_requirements'] = strategy_combo['infrastructure_requirements']

        # 添加策略协同信息（如果是多策略）
        if 'coordination' in strategy_combo:
            plan_metadata['strategy_coordination'] = strategy_combo['coordination']
            plan_metadata['strategy_coordination']['complexity_level'] = strategy_combo['complexity']

        return plan_metadata

    def _validate_compatibility(self, pattern: Dict, strategy_combo: Dict):
        """验证模式与策略组合的兼容性"""
        # 检查基础设施要求
        pattern_infra = set(pattern.get('infrastructure_requirements', []))
        combo_infra = set(strategy_combo.get('infrastructure_requirements', []))

        if combo_infra and not combo_infra.issubset(pattern_infra | set(pattern.get('applicable_road_types', []))):
            print(f"⚠️  警告: 策略组合需要的基础设施可能不满足: {combo_infra - pattern_infra}")

        # 检查拥堵严重程度与策略复杂度的匹配
        if 'severe' in pattern and strategy_combo['complexity'] == '高':
            # 严重拥堵可能不需要高复杂度策略（除非是持续拥堵）
            if 'persistent' not in pattern:
                print(f"⚠️  提示: 简单严重拥堵可能不需要高复杂度策略组合")

    def save_plan(self, plan_metadata: Dict) -> Path:
        """保存Plan到文件系统"""
        plan_id = plan_metadata['plan_id']
        plan_dir = self.output_dir / plan_id
        plan_dir.mkdir(parents=True, exist_ok=True)

        # 保存plan_metadata.json
        metadata_file = plan_dir / 'plan_metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(plan_metadata, f, ensure_ascii=False, indent=2)

        # 保存strategy_refs.json
        strategy_refs_file = plan_dir / 'strategy_refs.json'
        with open(strategy_refs_file, 'w', encoding='utf-8') as f:
            json.dump(plan_metadata['strategy_ids'], f, ensure_ascii=False, indent=2)

        # 生成control.add.xml占位符
        # 注意：实际的XML内容应该通过API的generate_additional端点生成
        # 这里创建一个基本的占位符，确保文件存在
        xml_file = plan_dir / 'control.add.xml'
        if not xml_file.exists():
            xml_content = self._generate_placeholder_xml(plan_metadata)
            with open(xml_file, 'w', encoding='utf-8') as f:
                f.write(xml_content)

        print(f"✅ Plan已保存: {plan_dir}")
        return plan_dir

    def _generate_placeholder_xml(self, plan_metadata: Dict) -> str:
        """生成占位符XML文件"""
        strategy_count = len(plan_metadata.get('strategy_ids', []))

        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<additional xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.dlr.de/xsd/additional_file.xsd">
    <!--
        Plan: {plan_metadata['plan_id']}
        Name: {plan_metadata['plan_name']}
        Strategies: {strategy_count}
        Generated: {plan_metadata.get('created_at', 'N/A')}

        NOTE: This is a placeholder file.
        Actual control configurations should be generated by applying strategies.
        Use the API endpoint POST /api/v1/control/plans/{plan_metadata['plan_id']}/generate_additional
        to generate the full configuration based on referenced strategies.
    -->

    <!-- Strategy IDs referenced: {', '.join(plan_metadata.get('strategy_ids', []))} -->

</additional>
"""
        return xml_content

    def update_plans_index(self):
        """更新plans_index.json"""
        index_file = self.output_dir / 'plans_index.json'

        # 扫描所有Plan目录
        plans = []
        for plan_dir in sorted(self.output_dir.iterdir()):
            if not plan_dir.is_dir():
                continue

            metadata_file = plan_dir / 'plan_metadata.json'
            if not metadata_file.exists():
                continue

            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 提取索引信息
            plan_index_entry = {
                'plan_id': metadata['plan_id'],
                'plan_name': metadata['plan_name'],
                'is_baseline': metadata.get('is_baseline', False),
                'strategy_count': len(metadata.get('strategy_ids', [])),
                'tags': metadata.get('tags', []),
                'complexity_level': metadata.get('complexity_level'),
                'target_scenario': metadata.get('target_scenario'),
                'created_at': metadata.get('created_at')
            }
            plans.append(plan_index_entry)

        # 保存索引
        index_data = {
            'plans': plans,
            'total': len(plans),
            'last_updated': datetime.now().isoformat()
        }

        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        print(f"✅ Plans索引已更新: {index_file} (共{len(plans)}个Plan)")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 批量生成
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def generate_all_recommended_plans():
    """生成所有推荐的Plan组合"""
    generator = QuickPlanGenerator()

    recommended_combinations = [
        # 早高峰方案
        ('morning_peak_severe', 'VSS'),
        ('morning_peak_severe', 'DHS'),
        ('morning_peak_severe', 'TEC'),
        ('morning_peak_severe', 'VSS+DHS'),
        ('morning_peak_severe', 'VSS+TEC'),

        # 晚高峰方案
        ('evening_peak_severe', 'VSS'),
        ('evening_peak_severe', 'DHS'),
        ('evening_peak_severe', 'TEC'),
        ('evening_peak_high_flow', 'VSS+DHS'),
        ('evening_peak_high_flow', 'VSS+TEC'),

        # 全天方案
        ('allday_persistent_severe', 'VSS+DHS+TEC'),
    ]

    generated_plans = []

    print("=" * 80)
    print("开始批量生成Plan方案...")
    print("=" * 80)

    for pattern_key, strategy_key in recommended_combinations:
        try:
            print(f"\n📋 生成: {pattern_key} + {strategy_key}")
            plan_metadata = generator.generate_plan(pattern_key, strategy_key)
            plan_dir = generator.save_plan(plan_metadata)
            generated_plans.append(plan_metadata['plan_id'])
        except Exception as e:
            print(f"❌ 生成失败: {e}")

    # 更新索引
    print("\n" + "=" * 80)
    generator.update_plans_index()
    print("=" * 80)

    print(f"\n✅ 批量生成完成! 共生成 {len(generated_plans)} 个Plan:")
    for plan_id in generated_plans:
        print(f"   - {plan_id}")

    return generated_plans


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 命令行接口
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='快速生成Plan方案')
    parser.add_argument('--pattern', type=str, help='拥堵模式 (morning_peak_severe, evening_peak_high_flow, etc.)')
    parser.add_argument('--strategy', type=str, help='策略组合 (VSS, DHS, TEC, VSS+DHS, etc.)')
    parser.add_argument('--batch', action='store_true', help='批量生成所有推荐组合')
    parser.add_argument('--list-patterns', action='store_true', help='列出所有可用的拥堵模式')
    parser.add_argument('--list-strategies', action='store_true', help='列出所有可用的策略组合')

    args = parser.parse_args()

    # 列出模式
    if args.list_patterns:
        print("\n可用的拥堵模式:")
        print("=" * 80)
        for key, pattern in CONGESTION_PATTERNS.items():
            print(f"  {key:30s} - {pattern['display_name']}")
            print(f"    时间窗口: {pattern['time_window']}")
            print(f"    阈值: {pattern['severity_threshold']}")
            print()
        exit(0)

    # 列出策略
    if args.list_strategies:
        print("\n可用的策略组合:")
        print("=" * 80)
        for key, combo in STRATEGY_COMBINATIONS.items():
            print(f"  {key:15s} - {combo['display_name']} (复杂度: {combo['complexity']})")
            print(f"    策略类型: {', '.join(combo['strategy_types'])}")
            print()
        exit(0)

    # 批量生成
    if args.batch:
        generate_all_recommended_plans()
        exit(0)

    # 单个生成
    if args.pattern and args.strategy:
        generator = QuickPlanGenerator()
        plan_metadata = generator.generate_plan(args.pattern, args.strategy)
        generator.save_plan(plan_metadata)
        generator.update_plans_index()
        exit(0)

    # 默认：批量生成
    print("未指定参数，执行批量生成...\n")
    generate_all_recommended_plans()
