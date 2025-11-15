"""
Edge Impact Aggregator - 边缘影响聚合器

功能: 从事件和管控策略中提取受影响的edge列表，用于生成edgeData配置
作者: Claude Code
日期: 2025-01-15
版本: 1.0.0

主要功能:
1. 从事件位置提取影响边缘 (event impact edges)
2. 从管控策略提取受控边缘 (strategy impact edges)
3. 合并和去重边缘列表
4. 验证边缘ID是否存在于路网中
"""

import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class EdgeImpactAggregator:
    """
    边缘影响聚合器 - 从事件和管控策略中聚合受影响的edge列表
    """

    def __init__(self, network_file: Optional[str] = None):
        """
        初始化聚合器

        Args:
            network_file: SUMO路网文件路径（可选，用于验证）
        """
        self.network_file = network_file
        self._network_edges_cache: Optional[Set[str]] = None

    def aggregate_event_impact_edges(
        self,
        event_location: Dict[str, any],
        method: str = "radius_2_hops"
    ) -> List[str]:
        """
        从事件位置提取影响边缘

        Args:
            event_location: 事件位置信息，包含edge_id, junction_id等
            method: 提取方法
                - "primary_only": 仅主要边缘
                - "radius_1_hop": 主要边缘 + 反向 + 邻接
                - "radius_2_hops": 主要边缘 + 反向 + 邻接 + 溢出区域（推荐）
                - "full_junction": 整个交叉口的所有边缘

        Returns:
            影响边缘ID列表
        """
        edges = []
        primary_edge = event_location.get('edge_id')

        if not primary_edge or primary_edge == '未知':
            logger.warning("事件位置缺少edge_id，无法提取影响边缘")
            return edges

        # Method 1: Primary edge only
        edges.append(primary_edge)

        if method == "primary_only":
            return edges

        # Method 2: Try to add reverse direction (候选边，需要后续验证）
        # ⚠️ 注意：反向边可能不存在于路网中，后续 validate_edges 会过滤无效的边
        reverse_edge = self._get_reverse_edge(primary_edge)
        if reverse_edge:
            edges.append(reverse_edge)
            logger.debug(f"Added reverse edge candidate: {reverse_edge} (will be validated against network)")

        if method == "radius_1_hop":
            # TODO: 实现邻接边缘提取（需要路网拓扑信息）
            logger.info(f"radius_1_hop方法: 当前返回主边缘+可能的反向边，邻接边缘提取待实现")
            return edges

        if method == "radius_2_hops":
            # TODO: 实现2跳溢出区域提取（需要路网拓扑信息）
            logger.info(f"radius_2_hops方法: 当前返回主边缘+可能的反向边，2跳溢出边缘提取待实现")
            return edges

        if method == "full_junction":
            junction_id = event_location.get('junction_id')
            if junction_id and junction_id != '未知':
                # TODO: 实现交叉口所有边缘提取（需要解析路网文件）
                logger.info(f"full_junction方法: 交叉口边缘提取待实现，junction_id={junction_id}")
            return edges

        return edges

    def aggregate_strategy_impact_edges(
        self,
        strategies_config: List[Dict[str, any]]
    ) -> Dict[str, List[str]]:
        """
        从管控策略配置中提取受控边缘

        Args:
            strategies_config: 策略配置列表，每个策略包含strategy_type和parameters

        Returns:
            字典，key为策略类型，value为受控边缘列表
            例如: {
                "VSS": ["3000", "3001", "3002", ...],
                "TEC": ["3100", "3101"],
                "DHS": ["3200", "3201"]
            }
        """
        strategy_edges = {}

        for strategy_config in strategies_config:
            strategy_type = strategy_config.get('strategy_type', 'UNKNOWN')
            parameters = strategy_config.get('parameters', {})

            if strategy_type == 'VSS' or strategy_type == '可变限速标志':
                edges = self._extract_vss_edges(parameters)
                if edges:
                    strategy_edges['VSS'] = edges

            elif strategy_type == 'TEC' or strategy_type == '收费站管控':
                edges = self._extract_tec_edges(parameters)
                if edges:
                    strategy_edges['TEC'] = edges

            elif strategy_type == 'DHS' or strategy_type == '动态硬路肩':
                edges = self._extract_dhs_edges(parameters)
                if edges:
                    strategy_edges['DHS'] = edges

            else:
                logger.warning(f"未知的策略类型: {strategy_type}")

        return strategy_edges

    def merge_edge_impacts(
        self,
        event_edges: List[str],
        strategy_edges: Dict[str, List[str]]
    ) -> Dict[str, any]:
        """
        合并事件边缘和策略边缘，去重并生成统计信息

        Args:
            event_edges: 事件影响边缘列表
            strategy_edges: 策略影响边缘字典 {strategy_type: [edge_ids]}

        Returns:
            合并结果字典，包含:
            - merged_edges: 合并后的边缘列表（去重）
            - source_breakdown: 来源分解统计
            - total_count: 总边缘数
        """
        all_edges_set = set(event_edges)

        # 统计来源
        source_breakdown = {
            'event': len(event_edges),
            'strategies': {}
        }

        # 合并策略边缘
        for strategy_type, edges in strategy_edges.items():
            all_edges_set.update(edges)
            source_breakdown['strategies'][strategy_type] = len(edges)

        merged_edges = sorted(list(all_edges_set))

        return {
            'merged_edges': merged_edges,
            'source_breakdown': source_breakdown,
            'total_count': len(merged_edges),
            'event_count': len(event_edges),
            'strategy_count': sum(len(edges) for edges in strategy_edges.values())
        }

    def validate_edges(
        self,
        edge_ids: List[str]
    ) -> Dict[str, any]:
        """
        验证边缘ID是否存在于路网中

        Args:
            edge_ids: 要验证的边缘ID列表

        Returns:
            验证结果字典，包含:
            - valid_edges: 有效的边缘列表
            - invalid_edges: 无效的边缘列表
            - validation_rate: 验证通过率
        """
        if not self.network_file:
            logger.warning("未提供路网文件，跳过边缘验证")
            return {
                'valid_edges': edge_ids,
                'invalid_edges': [],
                'validation_rate': 1.0,
                'validated': False
            }

        # 加载路网边缘（带缓存）
        network_edges = self._load_network_edges()

        if not network_edges:
            logger.warning("无法加载路网边缘，跳过验证")
            return {
                'valid_edges': edge_ids,
                'invalid_edges': [],
                'validation_rate': 1.0,
                'validated': False
            }

        # 验证每个边缘
        valid_edges = []
        invalid_edges = []

        for edge_id in edge_ids:
            if edge_id in network_edges:
                valid_edges.append(edge_id)
            else:
                invalid_edges.append(edge_id)
                logger.warning(f"边缘ID不存在于路网中: {edge_id}")

        validation_rate = len(valid_edges) / len(edge_ids) if edge_ids else 1.0

        return {
            'valid_edges': valid_edges,
            'invalid_edges': invalid_edges,
            'validation_rate': validation_rate,
            'validated': True
        }

    # ========== 私有辅助方法 ==========

    def _get_reverse_edge(self, edge_id: str) -> Optional[str]:
        """
        获取反向边缘ID

        SUMO约定: 反向边缘通过添加或移除前缀"-"表示
        例如: "3026" <-> "-3026"

        Args:
            edge_id: 原始边缘ID

        Returns:
            反向边缘ID，如果无法确定则返回None
        """
        if edge_id.startswith('-'):
            return edge_id[1:]
        else:
            return f"-{edge_id}"

    def _extract_vss_edges(self, parameters: Dict[str, any]) -> List[str]:
        """
        从VSS策略参数中提取受控边缘

        VSS策略可能包含:
        - edge_range: [start_edge, end_edge]
        - edge_list: [edge1, edge2, ...]
        - edge_pattern: "3000-3050"

        Args:
            parameters: VSS策略参数

        Returns:
            受控边缘列表
        """
        edges = []

        # 方法1: 直接的边缘列表
        if 'edge_list' in parameters:
            edges.extend(parameters['edge_list'])

        # 方法2: 边缘范围
        elif 'edge_range' in parameters:
            edge_range = parameters['edge_range']
            if isinstance(edge_range, list) and len(edge_range) == 2:
                try:
                    start = int(edge_range[0])
                    end = int(edge_range[1])
                    edges = [str(i) for i in range(start, end + 1)]
                except ValueError:
                    logger.warning(f"VSS edge_range格式错误: {edge_range}")

        # 方法3: 模式字符串 "3000-3050"
        elif 'edge_pattern' in parameters:
            pattern = parameters['edge_pattern']
            if '-' in pattern:
                try:
                    parts = pattern.split('-')
                    start = int(parts[0])
                    end = int(parts[1])
                    edges = [str(i) for i in range(start, end + 1)]
                except ValueError:
                    logger.warning(f"VSS edge_pattern格式错误: {pattern}")

        return edges

    def _extract_tec_edges(self, parameters: Dict[str, any]) -> List[str]:
        """
        从TEC策略参数中提取受控边缘

        TEC策略通常包含:
        - entrance_edges: 收费站入口边缘列表
        - control_edges: 额外的受控边缘

        Args:
            parameters: TEC策略参数

        Returns:
            受控边缘列表
        """
        edges = []

        # 收费站入口边缘
        if 'entrance_edges' in parameters:
            edges.extend(parameters['entrance_edges'])

        # 额外的受控边缘
        if 'control_edges' in parameters:
            edges.extend(parameters['control_edges'])

        # 单个entrance_edge（向后兼容）
        if 'entrance_edge' in parameters:
            edges.append(parameters['entrance_edge'])

        return edges

    def _extract_dhs_edges(self, parameters: Dict[str, any]) -> List[str]:
        """
        从DHS策略参数中提取受控边缘

        DHS策略通常包含:
        - shoulder_lanes: 硬路肩车道列表，格式为 "edge_id_lane_index"
        - main_edges: 主线边缘列表

        Args:
            parameters: DHS策略参数

        Returns:
            受控边缘列表（从lane ID中提取edge ID）
        """
        edges_set = set()

        # 从shoulder_lanes中提取edge ID
        if 'shoulder_lanes' in parameters:
            shoulder_lanes = parameters['shoulder_lanes']
            if isinstance(shoulder_lanes, list):
                for lane_id in shoulder_lanes:
                    # 格式: "edge_id_lane_index" 例如 "3200_1"
                    if isinstance(lane_id, str) and '_' in lane_id:
                        edge_id = lane_id.rsplit('_', 1)[0]
                        edges_set.add(edge_id)

        # 主线边缘
        if 'main_edges' in parameters:
            edges_set.update(parameters['main_edges'])

        return list(edges_set)

    def _load_network_edges(self) -> Set[str]:
        """
        从SUMO路网文件中加载所有边缘ID（带缓存）

        Returns:
            边缘ID集合
        """
        # 使用缓存
        if self._network_edges_cache is not None:
            return self._network_edges_cache

        edges = set()

        if not self.network_file:
            return edges

        network_path = Path(self.network_file)
        if not network_path.exists():
            logger.error(f"路网文件不存在: {self.network_file}")
            return edges

        try:
            tree = ET.parse(self.network_file)
            root = tree.getroot()

            # 提取所有<edge>元素的id属性
            for edge_elem in root.findall('.//edge'):
                edge_id = edge_elem.get('id')
                if edge_id:
                    edges.add(edge_id)

            logger.info(f"从路网文件加载了 {len(edges)} 个边缘ID")

            # 缓存结果
            self._network_edges_cache = edges

        except ET.ParseError as e:
            logger.error(f"解析路网文件失败: {e}")
        except Exception as e:
            logger.error(f"加载路网文件失败: {e}")

        return edges


# ========== 便捷函数 ==========

def aggregate_edgedata_edges(
    event_location: Dict[str, any],
    strategies_config: List[Dict[str, any]],
    network_file: Optional[str] = None,
    event_method: str = "radius_2_hops"
) -> Dict[str, any]:
    """
    便捷函数: 聚合事件和策略的edgeData边缘列表

    Args:
        event_location: 事件位置信息
        strategies_config: 策略配置列表
        network_file: 路网文件路径（用于验证）
        event_method: 事件边缘提取方法

    Returns:
        聚合结果字典，包含merged_edges, source_breakdown, validation等
    """
    aggregator = EdgeImpactAggregator(network_file=network_file)

    # 1. 提取事件边缘
    event_edges = aggregator.aggregate_event_impact_edges(
        event_location=event_location,
        method=event_method
    )

    # 2. 提取策略边缘
    strategy_edges = aggregator.aggregate_strategy_impact_edges(
        strategies_config=strategies_config
    )

    # 3. 合并边缘
    merge_result = aggregator.merge_edge_impacts(
        event_edges=event_edges,
        strategy_edges=strategy_edges
    )

    # 4. 验证边缘（如果提供了路网文件）
    validation_result = aggregator.validate_edges(
        edge_ids=merge_result['merged_edges']
    )

    # 5. 合并结果
    return {
        **merge_result,
        'validation': validation_result
    }
