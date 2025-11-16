#!/usr/bin/env python3
"""
根据cases中的metadata.json自动更新scenario_index.json

此脚本遍历所有案例的metadata.json文件，提取其中的场景和案例信息，
然后更新scenario_index.json中对应场景的created_cases字段。

使用方法:
    python sync_scenario_index.py

功能:
    1. 遍历cases目录中的所有metadata.json
    2. 提取case_id, case_name, scenarios等信息
    3. 找到scenario_index.json中对应的场景
    4. 添加/更新created_cases字段
    5. 保存更新后的scenario_index.json
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class ScenarioIndexSyncer:
    """同步scenario_index.json的类"""

    def __init__(self):
        self.cases_dir = Path('cases')
        self.scenario_index_path = Path('output/scenarios/scenario_index.json')
        self.scenario_index_data = {}
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def load_scenario_index(self) -> bool:
        """加载scenario_index.json"""
        if not self.scenario_index_path.exists():
            logger.error(f'❌ scenario_index.json不存在: {self.scenario_index_path}')
            return False

        try:
            with open(self.scenario_index_path, 'r', encoding='utf-8') as f:
                self.scenario_index_data = json.load(f)
            logger.info(f'✓ 加载scenario_index.json: {len(self.scenario_index_data.get("scenarios", []))} 个场景')
            return True
        except Exception as e:
            logger.error(f'❌ 加载scenario_index.json失败: {e}')
            return False

    def get_case_metadata_files(self) -> List[Path]:
        """获取所有case的metadata.json文件"""
        if not self.cases_dir.exists():
            logger.error(f'❌ cases目录不存在: {self.cases_dir}')
            return []

        metadata_files = sorted(self.cases_dir.glob('*/metadata.json'))
        logger.info(f'发现 {len(metadata_files)} 个case的metadata.json')
        return metadata_files

    def load_case_metadata(self, metadata_file: Path) -> Optional[Dict[str, Any]]:
        """加载单个case的metadata.json"""
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f'⚠️ 加载metadata失败 {metadata_file}: {e}')
            return None

    def find_scenario_entry(self, scenario_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        """在scenario_index中查找对应的scenario条目"""
        scenarios = self.scenario_index_data.get('scenarios', [])
        for scenario in scenarios:
            if (scenario.get('files', {}).get('scenario_dir') == scenario_id and
                scenario.get('event_id') == event_id):
                return scenario
        return None

    def update_created_case(self, scenario_entry: Dict[str, Any], case_info: Dict[str, Any]) -> bool:
        """更新scenario中的created_cases"""
        if scenario_entry is None:
            return False

        # 初始化created_cases如果不存在
        if 'created_cases' not in scenario_entry:
            scenario_entry['created_cases'] = []

        created_cases = scenario_entry['created_cases']

        # 检查case是否已存在（避免重复）
        case_id = case_info['case_id']
        for existing_case in created_cases:
            if existing_case.get('case_id') == case_id:
                logger.warning(f'⚠️ case已存在: {case_id}，跳过')
                return False

        # 添加新case信息
        new_case_entry = {
            'case_id': case_info['case_id'],
            'case_name': case_info['case_name'],
            'status': case_info['status'],
            'created_at': case_info['created_at'],
            'source_scenario_id': case_info.get('source_scenario_id')
        }

        created_cases.append(new_case_entry)
        return True

    def process_case_metadata(self, metadata_file: Path) -> bool:
        """处理单个case的metadata.json"""
        case_dir_name = metadata_file.parent.name
        metadata = self.load_case_metadata(metadata_file)

        if metadata is None:
            self.error_count += 1
            return False

        # 检查是否为event_scenario_batch类型
        source_type = metadata.get('source_type', '')
        if source_type != 'event_scenario_batch':
            logger.info(f'⊘ {case_dir_name}: 非event_scenario_batch类型，跳过')
            self.skipped_count += 1
            return False

        case_id = metadata.get('case_id')
        case_name = metadata.get('case_name')
        status = metadata.get('status')
        created_at = metadata.get('created_at')
        event_id = metadata.get('event_scenario', {}).get('event_id')
        scenarios = metadata.get('scenarios', [])

        if not case_id or not event_id or not scenarios:
            logger.warning(f'⚠️ {case_dir_name}: 缺少必要字段')
            self.skipped_count += 1
            return False

        # 为每个scenario添加case信息
        updated_count_for_case = 0
        for scenario_id in scenarios:
            scenario_entry = self.find_scenario_entry(scenario_id, event_id)

            if scenario_entry is None:
                logger.warning(f'⚠️ 未找到scenario: {scenario_id} (event_id={event_id})')
                continue

            case_info = {
                'case_id': case_id,
                'case_name': case_name,
                'status': status,
                'created_at': created_at,
                'source_scenario_id': scenario_id
            }

            if self.update_created_case(scenario_entry, case_info):
                updated_count_for_case += 1
                logger.info(f'✓ 更新scenario: {scenario_id} ← {case_id}')

        if updated_count_for_case > 0:
            self.updated_count += updated_count_for_case
            logger.info(f'✓ case {case_id}: 更新 {updated_count_for_case} 个scenario')
            return True
        else:
            logger.warning(f'⚠️ case {case_id}: 没有更新任何scenario')
            return False

    def save_scenario_index(self) -> bool:
        """保存更新后的scenario_index.json"""
        try:
            # 更新timestamp
            self.scenario_index_data['generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            with open(self.scenario_index_path, 'w', encoding='utf-8') as f:
                json.dump(self.scenario_index_data, f, ensure_ascii=False, indent=2)

            logger.info(f'✓ scenario_index.json已保存')
            return True
        except Exception as e:
            logger.error(f'❌ 保存scenario_index.json失败: {e}')
            return False

    def run(self) -> bool:
        """执行同步"""
        logger.info('='*80)
        logger.info('开始同步scenario_index.json...')
        logger.info('='*80)

        # 1. 加载scenario_index.json
        if not self.load_scenario_index():
            return False

        # 2. 获取所有metadata.json文件
        metadata_files = self.get_case_metadata_files()
        if not metadata_files:
            logger.warning('⚠️ 未找到任何metadata.json文件')
            return False

        # 3. 处理每个metadata.json
        logger.info('')
        logger.info('处理案例metadata.json:')
        logger.info('-'*80)
        for metadata_file in metadata_files:
            self.process_case_metadata(metadata_file)

        # 4. 保存更新后的scenario_index.json
        logger.info('')
        logger.info('='*80)
        if self.save_scenario_index():
            logger.info(f'✓ 同步完成！')
            logger.info(f'  - 更新: {self.updated_count} 个scenario')
            logger.info(f'  - 跳过: {self.skipped_count} 个case')
            logger.info(f'  - 错误: {self.error_count} 个case')
            return True
        else:
            return False


def main():
    """主函数"""
    syncer = ScenarioIndexSyncer()
    success = syncer.run()
    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
