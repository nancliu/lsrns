#!/usr/bin/env python3
"""
更新所有已有cases的EdgeData决策规则（P2 v1 → P2 v2）

P2 v1: edge_count >= 10 AND validation_rate >= 0.5
P2 v2: edge_count > 0 (只要有验证通过的边就启用)

该脚本遍历所有case，根据新规则重新判断should_enable
"""

import json
from pathlib import Path

def update_edgedata_rule(metadata_file: Path) -> dict:
    """
    根据P2 v2规则更新metadata中的EdgeData配置

    返回: {'case_id': ..., 'changed': True/False, 'old_should_enable': ..., 'new_should_enable': ...}
    """
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    case_id = metadata.get('case_id', 'unknown')

    # 如果没有edgedata_config，则跳过
    if 'edgedata_config' not in metadata:
        return {'case_id': case_id, 'changed': False, 'reason': 'No edgedata_config'}

    edgedata = metadata['edgedata_config']
    edge_count = edgedata.get('edge_count', 0)
    validation_rate = edgedata.get('validation_rate', 0)
    old_should_enable = edgedata.get('should_enable', False)

    # 应用P2 v2规则：只要有验证通过的边就启用
    new_should_enable = edge_count > 0

    # 如果决策没有变化，则无需更新
    if old_should_enable == new_should_enable:
        return {
            'case_id': case_id,
            'changed': False,
            'reason': f'No change (edge_count={edge_count}, should_enable={new_should_enable})'
        }

    # 更新决策和说明
    if new_should_enable:
        edgedata['should_enable'] = True
        edgedata['decision_reason'] = f'Have verified edges ({edge_count}), enable output for analysis'
        edgedata['decision_action'] = f'✅ 启用edgedata输出 ({edge_count}条已验证的边, 验证率{validation_rate:.1%})'
    else:
        edgedata['should_enable'] = False
        edgedata['decision_reason'] = 'No verified edges found in network'
        edgedata['decision_action'] = '❌ 禁用edgedata输出 (无验证通过的边，无法生成有价值的分析)'

    # 保存更新
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return {
        'case_id': case_id,
        'changed': True,
        'edge_count': edge_count,
        'validation_rate': f'{validation_rate:.1%}',
        'old_should_enable': old_should_enable,
        'new_should_enable': new_should_enable
    }

def main():
    """主函数"""
    cases_dir = Path('cases')

    if not cases_dir.exists():
        print(f'❌ Cases目录不存在: {cases_dir}')
        return

    # 找到所有case的metadata.json文件
    metadata_files = sorted(cases_dir.glob('*/metadata.json'))

    print(f'发现 {len(metadata_files)} 个case\n')
    print('=' * 80)

    changed_count = 0
    unchanged_count = 0

    for metadata_file in metadata_files:
        result = update_edgedata_rule(metadata_file)

        if result['changed']:
            changed_count += 1
            print(f"✅ {result['case_id']}")
            print(f"   边数: {result['edge_count']}, 验证率: {result['validation_rate']}")
            print(f"   {result['old_should_enable']} → {result['new_should_enable']}")
            print()
        else:
            unchanged_count += 1
            print(f"⊘ {result['case_id']}: {result['reason']}")

    print('=' * 80)
    print(f'\n统计结果:')
    print(f'  已更新: {changed_count} 个case')
    print(f'  无需更新: {unchanged_count} 个case')
    print(f'\n✓ EdgeData规则更新完成 (P2 v1 → P2 v2)')

if __name__ == '__main__':
    main()
