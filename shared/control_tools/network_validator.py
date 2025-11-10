"""
Network Edge Validator for Control Plans
验证控制方案中的edge引用是否有效
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import json
from typing import Set, Dict, List, Tuple


class NetworkValidator:
    """验证控制方案的网络引用"""

    def __init__(self, network_file: str):
        """
        初始化网络验证器
        Args:
            network_file: SUMO网络文件路径
        """
        self.network_file = Path(network_file)
        self.valid_edges: Set[str] = set()
        self.edge_info: Dict[str, Dict] = {}
        self.load_network()

    def load_network(self):
        """加载并解析SUMO网络文件"""
        print(f"Loading network file: {self.network_file}")

        try:
            tree = ET.parse(self.network_file)
            root = tree.getroot()

            # 提取所有edge信息
            edges = root.findall('.//edge')
            print(f"Found {len(edges)} edges in network file")

            for edge in edges:
                edge_id = edge.get('id')
                if edge_id:
                    self.valid_edges.add(edge_id)
                    # 存储edge的额外信息
                    self.edge_info[edge_id] = {
                        'from': edge.get('from'),
                        'to': edge.get('to'),
                        'lanes': len(edge.findall('lane')),
                        'lane_ids': [lane.get('id') for lane in edge.findall('lane')]
                    }

            print(f"Loaded {len(self.valid_edges)} valid edge IDs")

        except Exception as e:
            print(f"Error loading network file: {e}")
            raise

    def validate_edges(self, edge_list: List[str]) -> Tuple[List[str], List[str]]:
        """
        验证edge列表
        Args:
            edge_list: 待验证的edge ID列表
        Returns:
            (valid_edges, invalid_edges)
        """
        valid = []
        invalid = []

        for edge in edge_list:
            if edge in self.valid_edges:
                valid.append(edge)
            else:
                invalid.append(edge)

        return valid, invalid

    def validate_plan(self, plan_path: str) -> Dict:
        """
        验证单个方案的网络引用
        Args:
            plan_path: 方案目录路径
        Returns:
            验证结果
        """
        plan_path = Path(plan_path)
        metadata_file = plan_path / "plan_metadata.json"

        if not metadata_file.exists():
            return {'error': f"Metadata file not found: {metadata_file}"}

        with open(metadata_file, 'r', encoding='utf-8') as f:
            plan_data = json.load(f)

        result = {
            'plan_id': plan_data['plan_id'],
            'strategies': [],
            'total_edges': 0,
            'valid_edges': 0,
            'invalid_edges': 0,
            'validation_status': 'PASS'
        }

        # 验证每个策略的edges
        for strategy in plan_data.get('strategies', []):
            strategy_result = {
                'strategy_id': strategy.get('strategy_id'),
                'strategy_type': strategy.get('strategy_type'),
                'edges': [],
                'valid': [],
                'invalid': []
            }

            # 根据策略类型获取edges
            if strategy['strategy_type'] == 'VSS':
                edges = strategy.get('parameters', {}).get('affected_edges', [])
            elif strategy['strategy_type'] == 'TEC':
                edges = strategy.get('parameters', {}).get('control_points', [])
            elif strategy['strategy_type'] == 'DHS':
                edges = strategy.get('parameters', {}).get('affected_edges', [])
            else:
                edges = []

            strategy_result['edges'] = edges
            valid, invalid = self.validate_edges(edges)
            strategy_result['valid'] = valid
            strategy_result['invalid'] = invalid

            result['strategies'].append(strategy_result)
            result['total_edges'] += len(edges)
            result['valid_edges'] += len(valid)
            result['invalid_edges'] += len(invalid)

        if result['invalid_edges'] > 0:
            result['validation_status'] = 'FAIL'

        return result

    def validate_all_morning_peak_plans(self) -> Dict:
        """验证所有早高峰方案"""
        plans_dir = Path("control_data/plans")
        results = {
            'network_file': str(self.network_file),
            'total_edges_in_network': len(self.valid_edges),
            'plans': [],
            'summary': {
                'total_plans': 0,
                'passed': 0,
                'failed': 0,
                'total_edge_references': 0,
                'valid_references': 0,
                'invalid_references': 0
            }
        }

        # 查找所有早高峰方案
        morning_peak_plans = list(plans_dir.glob("plan_morning_peak_g4202_*/"))
        print(f"\nValidating {len(morning_peak_plans)} morning peak plans...")

        for plan_dir in morning_peak_plans:
            plan_result = self.validate_plan(plan_dir)
            results['plans'].append(plan_result)

            # 更新汇总
            results['summary']['total_plans'] += 1
            if plan_result.get('validation_status') == 'PASS':
                results['summary']['passed'] += 1
            else:
                results['summary']['failed'] += 1

            results['summary']['total_edge_references'] += plan_result.get('total_edges', 0)
            results['summary']['valid_references'] += plan_result.get('valid_edges', 0)
            results['summary']['invalid_references'] += plan_result.get('invalid_edges', 0)

            # 打印进度
            status = "✓" if plan_result.get('validation_status') == 'PASS' else "✗"
            invalid_count = plan_result.get('invalid_edges', 0)
            print(f"{status} {plan_result['plan_id']}: {invalid_count} invalid edges")

        return results

    def fix_invalid_edges(self, invalid_edges: List[str]) -> Dict[str, str]:
        """
        尝试修复无效的edge引用
        Args:
            invalid_edges: 无效的edge列表
        Returns:
            映射字典 {invalid_edge: suggested_valid_edge}
        """
        fixes = {}

        for invalid_edge in invalid_edges:
            # 尝试找到相似的有效edge
            # 策略1: 去掉负号（如果是反向edge）
            if invalid_edge.startswith('-'):
                positive_edge = invalid_edge[1:]
                if positive_edge in self.valid_edges:
                    fixes[invalid_edge] = positive_edge
                    continue

            # 策略2: 添加负号（尝试反向）
            negative_edge = f"-{invalid_edge}"
            if negative_edge in self.valid_edges:
                fixes[invalid_edge] = negative_edge
                continue

            # 策略3: 查找相似的edge（去掉小数部分）
            base_edge = invalid_edge.split('.')[0]
            if base_edge in self.valid_edges:
                fixes[invalid_edge] = base_edge
            elif f"-{base_edge}" in self.valid_edges:
                fixes[invalid_edge] = f"-{base_edge}"

            # 如果还找不到，查找数字相近的edge
            if invalid_edge not in fixes:
                try:
                    # 提取数字部分
                    import re
                    numbers = re.findall(r'\d+', invalid_edge)
                    if numbers:
                        main_number = numbers[0]
                        # 查找包含这个数字的edge
                        candidates = [e for e in self.valid_edges if main_number in e]
                        if candidates:
                            # 选择最相似的
                            fixes[invalid_edge] = candidates[0]
                except:
                    pass

        return fixes

    def generate_validation_report(self, output_file: str = "network_validation_report.json"):
        """生成验证报告"""
        results = self.validate_all_morning_peak_plans()

        # 收集所有无效的edges
        all_invalid_edges = set()
        for plan in results['plans']:
            for strategy in plan['strategies']:
                all_invalid_edges.update(strategy.get('invalid', []))

        # 尝试修复
        if all_invalid_edges:
            fixes = self.fix_invalid_edges(list(all_invalid_edges))
            results['suggested_fixes'] = fixes
            print(f"\nSuggested fixes for {len(fixes)} invalid edges")

        # 保存报告
        output_path = Path("control_data/plans") / output_file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\nValidation report saved to: {output_path}")
        print(f"\nSummary:")
        print(f"  Total plans: {results['summary']['total_plans']}")
        print(f"  Passed: {results['summary']['passed']}")
        print(f"  Failed: {results['summary']['failed']}")
        print(f"  Total edge references: {results['summary']['total_edge_references']}")
        print(f"  Valid references: {results['summary']['valid_references']}")
        print(f"  Invalid references: {results['summary']['invalid_references']}")

        return results


def main():
    """主函数"""
    # 使用指定的网络文件
    network_file = "templates/network_files/sichuan202508v7.net.xml"

    print("=" * 60)
    print("Network Edge Validation for Morning Peak Plans")
    print("=" * 60)

    validator = NetworkValidator(network_file)
    results = validator.generate_validation_report()

    # 如果有无效的edges，显示修复建议
    if 'suggested_fixes' in results and results['suggested_fixes']:
        print("\n" + "=" * 60)
        print("Suggested Edge Fixes:")
        print("-" * 60)
        for invalid, valid in results['suggested_fixes'].items():
            print(f"  {invalid} -> {valid}")

    return results


if __name__ == "__main__":
    results = main()