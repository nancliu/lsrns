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

        if method == "radius_1_hop":
            # TODO: 实现邻接边缘提取（需要路网拓扑信息）
            logger.info(f"radius_1_hop方法: 当前仅返回主边缘，邻接边缘提取待实现")
            return edges

        if method == "radius_2_hops":
            # TODO: 实现2跳溢出区域提取（需要路网拓扑信息）
            logger.info(f"radius_2_hops方法: 当前仅返回主边缘，2跳溢出边缘提取待实现")
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

        VSS策略参数格式（v0.9.0+）:
        - affected_edges: [edge1, edge2, ...] 直接的边缘列表（推荐）
        - edge_list: [edge1, edge2, ...] 旧版本的边缘列表

        向后兼容旧格式:
        - edge_range: [start_edge, end_edge] 边缘范围
        - edge_pattern: "3000-3050" 模式字符串

        Args:
            parameters: VSS策略参数

        Returns:
            受控边缘列表
        """
        edges = []

        # 优先使用新格式：affected_edges （直接的边缘列表）
        if 'affected_edges' in parameters:
            affected_edges = parameters['affected_edges']
            if isinstance(affected_edges, list):
                edges.extend(affected_edges)
                logger.debug(f"VSS: 从affected_edges提取 {len(edges)} 条可变限速边缘")

        # 旧格式: 直接的边缘列表
        elif 'edge_list' in parameters:
            edge_list = parameters['edge_list']
            if isinstance(edge_list, list):
                edges.extend(edge_list)
                logger.debug(f"VSS: 从edge_list提取 {len(edges)} 条可变限速边缘")

        # 旧格式: 边缘范围
        elif 'edge_range' in parameters:
            edge_range = parameters['edge_range']
            if isinstance(edge_range, list) and len(edge_range) == 2:
                try:
                    start = int(edge_range[0])
                    end = int(edge_range[1])
                    edges = [str(i) for i in range(start, end + 1)]
                    logger.debug(f"VSS: 从edge_range提取 {len(edges)} 条可变限速边缘")
                except ValueError:
                    logger.warning(f"VSS edge_range格式错误: {edge_range}")

        # 旧格式: 模式字符串 "3000-3050"
        elif 'edge_pattern' in parameters:
            pattern = parameters['edge_pattern']
            if isinstance(pattern, str) and '-' in pattern:
                try:
                    parts = pattern.split('-')
                    start = int(parts[0])
                    end = int(parts[1])
                    edges = [str(i) for i in range(start, end + 1)]
                    logger.debug(f"VSS: 从edge_pattern提取 {len(edges)} 条可变限速边缘")
                except ValueError:
                    logger.warning(f"VSS edge_pattern格式错误: {pattern}")

        if edges:
            logger.info(f"VSS策略: 聚合了 {len(edges)} 条可变限速边缘 - {edges[:3]}...")
        else:
            logger.warning(f"VSS策略: 未能从参数中提取可变限速边缘")

        return edges

    def _extract_tec_edges(self, parameters: Dict[str, any]) -> List[str]:
        """
        从TEC策略参数中提取受控边缘

        TEC策略参数格式（v0.9.0+）:
        - entrance_edges: 收费站入口边缘列表
        - affected_edges: 所有受影响的边缘列表（推荐）

        向后兼容旧格式:
        - control_edges: 额外的受控边缘
        - entrance_edge: 单个入口边缘

        Args:
            parameters: TEC策略参数

        Returns:
            受控边缘列表
        """
        edges_set = set()

        # 优先使用新格式：affected_edges （所有受影响的边）
        if 'affected_edges' in parameters:
            affected_edges = parameters['affected_edges']
            if isinstance(affected_edges, list):
                edges_set.update(affected_edges)
                logger.debug(f"TEC: 从affected_edges提取 {len(edges_set)} 条收费管控边缘")

        # 收费站入口边缘
        if 'entrance_edges' in parameters:
            entrance_edges = parameters['entrance_edges']
            if isinstance(entrance_edges, list):
                edges_set.update(entrance_edges)
                logger.debug(f"TEC: 从entrance_edges提取 {len(entrance_edges)} 条入口边缘")

        # 额外的受控边缘
        if 'control_edges' in parameters:
            control_edges = parameters['control_edges']
            if isinstance(control_edges, list):
                edges_set.update(control_edges)
                logger.debug(f"TEC: 从control_edges提取 {len(control_edges)} 条额外受控边缘")

        # 单个entrance_edge（向后兼容）
        if 'entrance_edge' in parameters:
            entrance_edge = parameters['entrance_edge']
            if isinstance(entrance_edge, str) and entrance_edge:
                edges_set.add(entrance_edge)

        if edges_set:
            logger.info(f"TEC策略: 聚合了 {len(edges_set)} 条收费管控边缘 - {list(edges_set)[:3]}...")
        else:
            logger.warning(f"TEC策略: 未能从参数中提取收费管控边缘")

        return list(edges_set)

    def _extract_dhs_edges(self, parameters: Dict[str, any]) -> List[str]:
        """
        从DHS策略参数中提取受控边缘

        DHS策略参数格式（v0.9.0+）:
        - shoulder_segments: 应急车道edge ID列表 ["edge1", "edge2", ...]
        - affected_lanes: 应急车道车道ID列表，格式为 "edge_id_lane_index" ["-12680_0", ...]
        - activation_schedule: 激活时间表配置

        向后兼容旧格式:
        - shoulder_lanes: 硬路肩车道列表，格式为 "edge_id_lane_index"
        - main_edges: 主线边缘列表

        Args:
            parameters: DHS策略参数

        Returns:
            受控边缘列表（从lane ID或segments中提取edge ID）
        """
        edges_set = set()

        # 优先使用新格式：shoulder_segments (edge ID直接列表)
        if 'shoulder_segments' in parameters:
            shoulder_segments = parameters['shoulder_segments']
            if isinstance(shoulder_segments, list):
                for edge_id in shoulder_segments:
                    if isinstance(edge_id, str) and edge_id.strip():
                        edges_set.add(edge_id.strip())
                logger.debug(f"DHS: 从shoulder_segments提取 {len(edges_set)} 条应急车道边缘")

        # 新格式: affected_lanes (从lane ID中提取edge ID)
        if 'affected_lanes' in parameters:
            affected_lanes = parameters['affected_lanes']
            if isinstance(affected_lanes, list):
                for lane_id in affected_lanes:
                    # 格式: "edge_id_lane_index" 例如 "-12680_0"
                    if isinstance(lane_id, str) and '_' in lane_id:
                        edge_id = lane_id.rsplit('_', 1)[0]
                        edges_set.add(edge_id)
                logger.debug(f"DHS: 从affected_lanes提取 {len(edges_set)} 条应急车道边缘")

        # 向后兼容旧格式：shoulder_lanes
        if 'shoulder_lanes' in parameters and len(edges_set) == 0:
            shoulder_lanes = parameters['shoulder_lanes']
            if isinstance(shoulder_lanes, list):
                for lane_id in shoulder_lanes:
                    # 格式: "edge_id_lane_index" 例如 "3200_1"
                    if isinstance(lane_id, str) and '_' in lane_id:
                        edge_id = lane_id.rsplit('_', 1)[0]
                        edges_set.add(edge_id)

        # 主线边缘
        if 'main_edges' in parameters:
            main_edges = parameters['main_edges']
            if isinstance(main_edges, list):
                edges_set.update(main_edges)

        if edges_set:
            logger.info(f"DHS策略: 聚合了 {len(edges_set)} 条应急车道边缘 - {list(edges_set)[:3]}...")
        else:
            logger.warning(f"DHS策略: 未能从参数中提取应急车道边缘")

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
