"""
Strategy Comparison Service

交通控制策略对比分析服务

职责:
- 提取多个控制策略的仿真结果中的8个交通性能指标
- 生成策略对比数据（最终值）
- 生成时序对比数据
- 将结果存储在 case/analysis 目录中
- 提供API接口返回对比结果

8个交通性能指标:
1. 当前运行车数 (current_vehicles) - lower is better (辆)
2. 平均速度 (avg_speed) - higher is better (km/h)
3. 已载入车数 (loaded_vehicles) - higher is better (辆)
4. 碰撞次数 (collisions) - lower is better (次，交通安全指标)
5. 平均等待时间 (meanWaitingTime) - lower is better (秒，拥堵指标)
6. 已完成车数 (completed_vehicles) - higher is better (辆)
7. 已到达车数 (arrived) - higher is better (辆，成功率指标)
8. 等待车数 (waiting_vehicles) - lower is better (辆)
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

from .base_service import BaseService

logger = logging.getLogger(__name__)


class StrategyComparisonService(BaseService):
    """
    交通控制策略对比分析服务

    负责提取、计算和存储多个控制策略的交通性能指标对比
    """

    # 8个交通性能指标定义
    TRAFFIC_METRICS = {
        'current_vehicles': {
            'label': '当前运行车数',
            'unit': '辆',
            'higher_is_better': False,
            'source': 'summary'
        },
        'avg_speed': {
            'label': '平均速度',
            'unit': 'km/h',
            'higher_is_better': True,
            'source': 'summary'
        },
        'loaded_vehicles': {
            'label': '已载入车数',
            'unit': '辆',
            'higher_is_better': True,
            'source': 'summary'
        },
        'collisions': {
            'label': '碰撞次数',
            'unit': '次',
            'higher_is_better': False,
            'source': 'summary',
            'description': '交通安全指标：越少越好'
        },
        'meanWaitingTime': {
            'label': '平均等待时间',
            'unit': '秒',
            'higher_is_better': False,
            'source': 'summary',
            'description': '交通拥堵指标：越短越好'
        },
        'completed_vehicles': {
            'label': '已完成车数',
            'unit': '辆',
            'higher_is_better': True,
            'source': 'summary'
        },
        'arrived': {
            'label': '已到达车数',
            'unit': '辆',
            'higher_is_better': True,
            'source': 'summary',
            'description': '仿真成功率：越多越好'
        },
        'waiting_vehicles': {
            'label': '等待车数',
            'unit': '辆',
            'higher_is_better': False,
            'source': 'summary'
        }
    }

    def __init__(self):
        """初始化策略对比服务"""
        super().__init__()

    async def generate_strategy_comparison(
        self,
        case_id: str,
        control_strategies: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        生成控制策略对比分析数据

        Args:
            case_id: 案例ID
            control_strategies: 控制策略列表 (None时自动检测)

        Returns:
            Dict: 包含strategy_comparison和timeseries数据

        Raises:
            ValueError: 案例不存在或缺少仿真数据
        """
        logger.info(f"生成策略对比分析: case_id={case_id}")

        case_dir = self.cases_dir / case_id
        if not case_dir.exists():
            raise ValueError(f"Case not found: {case_id}")

        # 检测可用的控制策略和仿真
        simulations = self._detect_simulations(case_dir, control_strategies)
        if not simulations:
            raise ValueError(f"No simulations found for case: {case_id}")

        # 为每个策略收集指标
        strategy_comparison = {}
        timeseries_data = {}

        for strategy, sim_dirs in simulations.items():
            # 聚合该策略的所有仿真指标
            strategy_metrics = self._aggregate_strategy_metrics(sim_dirs)
            strategy_comparison[strategy] = strategy_metrics

            # 收集时序数据
            timeseries_data[strategy] = self._extract_timeseries_data(sim_dirs)

        # 保存结果到analysis目录
        analysis_dir = case_dir / "analysis"
        analysis_dir.mkdir(parents=True, exist_ok=True)

        # 保存最终值对比
        comparison_file = analysis_dir / "strategy_comparison.json"
        with open(comparison_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'case_id': case_id,
                'strategy_comparison': strategy_comparison
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"策略对比结果已保存: {comparison_file}")

        # 保存时序数据
        timeseries_file = analysis_dir / "strategy_timeseries.json"
        with open(timeseries_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'case_id': case_id,
                'timeseries': timeseries_data
            }, f, indent=2, ensure_ascii=False)
        logger.info(f"时序数据已保存: {timeseries_file}")

        return {
            'strategy_comparison': strategy_comparison,
            'timeseries': timeseries_data,
            'strategies': list(strategy_comparison.keys()),
            'metrics': self.TRAFFIC_METRICS
        }

    def _detect_simulations(
        self,
        case_dir: Path,
        control_strategies: Optional[List[str]] = None
    ) -> Dict[str, List[Path]]:
        """
        检测案例下的仿真目录，按控制策略分组

        Args:
            case_dir: 案例目录
            control_strategies: 指定的策略列表

        Returns:
            Dict: {strategy: [sim_dirs]}
        """
        simulations_dir = case_dir / "simulations"
        if not simulations_dir.exists():
            return {}

        simulations = {}

        for sim_dir in simulations_dir.iterdir():
            if not sim_dir.is_dir():
                continue

            # 从仿真目录名提取控制策略
            # 预期格式: sim_scenario_<id>_<strategy>
            strategy = self._extract_strategy_from_dirname(sim_dir.name)

            if control_strategies and strategy not in control_strategies:
                continue

            if strategy not in simulations:
                simulations[strategy] = []
            simulations[strategy].append(sim_dir)

        return simulations

    def _extract_strategy_from_dirname(self, dirname: str) -> str:
        """
        从仿真目录名提取控制策略

        预期格式: sim_scenario_<scenario_id>_<strategy>
        如: sim_scenario_10754_no_control, sim_scenario_10754_tec

        策略可能包含下划线（如no_control），所以要找到sim_scenario之后的最后一个_分隔部分
        """
        if not dirname.startswith('sim_scenario_'):
            return 'UNKNOWN'

        # 移除前缀 'sim_scenario_'
        remainder = dirname[len('sim_scenario_'):]

        # 找到第一个_，它分隔scenario_id和strategy
        first_underscore = remainder.find('_')

        if first_underscore == -1:
            # 没有找到_，整个remainder是strategy
            return remainder.upper()

        # scenario_id后面的所有内容都是strategy（可能包含_）
        # 例如: 6120705_no_control -> strategy是no_control
        strategy = remainder[first_underscore + 1:]
        return strategy.upper()  # e.g., NO_CONTROL, TEC, VSS, DHS

    def _aggregate_strategy_metrics(
        self,
        sim_dirs: List[Path]
    ) -> Dict[str, Any]:
        """
        聚合一个控制策略的所有仿真指标

        Args:
            sim_dirs: 该策略的仿真目录列表

        Returns:
            Dict: 聚合后的指标
        """
        aggregated = {}

        # 收集所有仿真的指标数据（动态收集，不预先定义）
        metric_values = {}

        for sim_dir in sim_dirs:
            # 从该仿真提取指标
            metrics = self._extract_simulation_metrics(sim_dir)

            for metric_key, value in metrics.items():
                if value is not None:
                    if metric_key not in metric_values:
                        metric_values[metric_key] = []
                    metric_values[metric_key].append(value)

        # 计算聚合值（平均值）
        for metric_key, values in metric_values.items():
            if values:
                # 所有指标都取平均值
                aggregated[metric_key] = sum(values) / len(values)
            else:
                aggregated[metric_key] = None

        return aggregated

    def _extract_simulation_metrics(self, sim_dir: Path) -> Dict[str, Any]:
        """
        从单个仿真目录提取8个交通性能指标

        Args:
            sim_dir: 仿真目录

        Returns:
            Dict: 8个指标的值
        """
        metrics = {metric_key: None for metric_key in self.TRAFFIC_METRICS.keys()}

        # 1. 从summary.xml提取: 所有指标都从最后一个step提取
        summary_file = sim_dir / "summary.xml"
        if summary_file.exists():
            try:
                summary_metrics = self._extract_from_summary(summary_file)
                metrics.update(summary_metrics)
            except Exception as e:
                logger.warning(f"Failed to read summary.xml from {sim_dir}: {e}")

        # 2. 从edgedata提取: chain_frequency, transmission_frequency
        # (这些需要从SUMO的edgedata输出中计算)
        edgedata_dir = sim_dir / "edgedata"
        if edgedata_dir.exists():
            try:
                edgedata_metrics = self._extract_from_edgedata(edgedata_dir)
                metrics.update(edgedata_metrics)
            except Exception as e:
                logger.warning(f"Failed to extract edgedata metrics from {sim_dir}: {e}")

        return metrics

    def _extract_from_summary(self, summary_file: Path) -> Dict[str, Any]:
        """
        从SUMO的summary.xml文件提取所有8个交通性能指标
        从最后一个step（仿真结束时的状态）提取

        指标来源（均来自summary.xml最后一个step属性）:
        - current_vehicles: running - 当前运行车数
        - avg_speed: meanSpeed - 平均速度（需转换m/s→km/h）
        - loaded_vehicles: loaded - 已载入车数
        - collisions: collisions - 碰撞次数（安全指标）
        - meanWaitingTime: meanWaitingTime - 平均等待时间（拥堵指标）
        - completed_vehicles: ended - 已完成车数
        - arrived: arrived - 已到达车数（成功率指标）
        - waiting_vehicles: waiting - 等待车数
        """
        metrics = {
            'current_vehicles': None,
            'avg_speed': None,
            'loaded_vehicles': None,
            'collisions': None,
            'meanWaitingTime': None,
            'completed_vehicles': None,
            'arrived': None,
            'waiting_vehicles': None
        }

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(summary_file)
            root = tree.getroot()

            # 遍历所有step，保存最后一个（最终仿真状态）
            last_step = None
            for step in root.findall('step'):
                last_step = step

            # 从最后一个step提取所有指标
            if last_step is not None:
                # 1. 车辆数据 - 直接来自summary.xml属性
                metrics['current_vehicles'] = int(last_step.get('running', 0))
                metrics['loaded_vehicles'] = int(last_step.get('loaded', 0))
                metrics['waiting_vehicles'] = int(last_step.get('waiting', 0))
                metrics['completed_vehicles'] = int(last_step.get('ended', 0))
                metrics['arrived'] = int(last_step.get('arrived', 0))

                # 2. 平均速度 - m/s转换为km/h
                avg_speed_str = last_step.get('meanSpeed', '0')
                try:
                    avg_speed = float(avg_speed_str) * 3.6  # m/s to km/h
                    metrics['avg_speed'] = avg_speed
                except:
                    metrics['avg_speed'] = 0.0

                # 3. 安全指标 - 碰撞次数
                try:
                    metrics['collisions'] = int(last_step.get('collisions', 0))
                except:
                    metrics['collisions'] = 0

                # 4. 拥堵指标 - 平均等待时间
                try:
                    metrics['meanWaitingTime'] = float(last_step.get('meanWaitingTime', 0))
                except:
                    metrics['meanWaitingTime'] = 0.0

        except Exception as e:
            logger.warning(f"Error parsing summary.xml: {e}")

        return {k: v for k, v in metrics.items() if v is not None}

    def _extract_from_edgedata(self, edgedata_dir: Path) -> Dict[str, Any]:
        """
        从edgedata目录提取指标

        注意: 在Plan A实现中，我们改用summary.xml中的指标:
        - collisions (取代chain_frequency)
        - meanWaitingTime (取代transmission_frequency)

        edgedata指标extraction已弃用，返回空字典
        """
        # 返回空字典 - edgedata指标不再使用
        # Plan A的8个指标完全来自summary.xml
        return {}

    def _extract_timeseries_data(
        self,
        sim_dirs: List[Path]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        从仿真提取完整时序数据

        数据来源优先级：
        1. summary.xml - SUMO输出的每个时间步数据（完整）
        2. progress.json - 最后一个进度检查点（作为备选）

        Args:
            sim_dirs: 仿真目录列表

        Returns:
            Dict: 各策略各指标的时序数据
        """
        timeseries = {metric_key: [] for metric_key in self.TRAFFIC_METRICS.keys()}

        # 聚合所有仿真的时序数据
        all_timeseries = {metric_key: [] for metric_key in self.TRAFFIC_METRICS.keys()}

        for sim_dir in sim_dirs:
            # 优先从summary.xml提取完整时序数据
            summary_file = sim_dir / "summary.xml"
            if summary_file.exists():
                try:
                    summary_timeseries = self._extract_timeseries_from_summary(summary_file)
                    # 聚合时序数据
                    for metric_key, values in summary_timeseries.items():
                        all_timeseries[metric_key].extend(values)
                    continue
                except Exception as e:
                    logger.warning(f"Failed to extract timeseries from summary.xml: {e}")

            # 备选：从progress.json提取最终状态
            progress_file = sim_dir / "progress.json"
            if progress_file.exists():
                try:
                    with open(progress_file, 'r', encoding='utf-8') as f:
                        progress_data = json.load(f)
                        timestamp = progress_data.get('updated_at')

                        all_timeseries['current_vehicles'].append({
                            'time': float(progress_data.get('percent', 0)),
                            'timestamp': timestamp,
                            'value': progress_data.get('running_vehicles', 0)
                        })
                        all_timeseries['loaded_vehicles'].append({
                            'time': float(progress_data.get('percent', 0)),
                            'timestamp': timestamp,
                            'value': progress_data.get('loaded_vehicles', 0)
                        })
                        all_timeseries['waiting_vehicles'].append({
                            'time': float(progress_data.get('percent', 0)),
                            'timestamp': timestamp,
                            'value': progress_data.get('waiting_vehicles', 0)
                        })
                except Exception as e:
                    logger.warning(f"Failed to extract timeseries from progress.json: {e}")

        # 按时间排序每个指标的数据
        for metric_key in all_timeseries.keys():
            # 去重并按时间排序
            seen_times = set()
            unique_data = []
            for point in sorted(all_timeseries[metric_key], key=lambda x: x.get('time', 0)):
                time_key = point.get('time')
                if time_key not in seen_times:
                    seen_times.add(time_key)
                    unique_data.append(point)

            timeseries[metric_key] = unique_data

        return timeseries

    def _extract_timeseries_from_summary(
        self,
        summary_file: Path
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        从SUMO的summary.xml文件提取时序数据

        Args:
            summary_file: summary.xml文件路径

        Returns:
            Dict: 时序数据，每个指标包含时间序列
        """
        timeseries = {metric_key: [] for metric_key in self.TRAFFIC_METRICS.keys()}

        try:
            import xml.etree.ElementTree as ET
            tree = ET.parse(summary_file)
            root = tree.getroot()

            # 遍历每个时间步
            for step in root.findall('step'):
                time = float(step.get('time', 0))
                running = int(step.get('running', 0))
                ended = int(step.get('ended', 0))
                waiting = int(step.get('waiting', 0))
                loaded = int(step.get('loaded', 0))

                # 提取速度数据
                avg_speed_str = step.get('meanSpeed', '0')
                try:
                    avg_speed = float(avg_speed_str) * 3.6  # m/s to km/h
                except:
                    avg_speed = 0.0

                # 添加时序数据点
                timeseries['current_vehicles'].append({
                    'time': time,
                    'timestamp': f"{time:.1f}s",
                    'value': running
                })

                timeseries['avg_speed'].append({
                    'time': time,
                    'timestamp': f"{time:.1f}s",
                    'value': round(avg_speed, 2)
                })

                timeseries['loaded_vehicles'].append({
                    'time': time,
                    'timestamp': f"{time:.1f}s",
                    'value': loaded
                })

                timeseries['waiting_vehicles'].append({
                    'time': time,
                    'timestamp': f"{time:.1f}s",
                    'value': waiting
                })

                # 累积值
                timeseries['completed_vehicles'].append({
                    'time': time,
                    'timestamp': f"{time:.1f}s",
                    'value': ended
                })

        except Exception as e:
            logger.warning(f"Error extracting timeseries from summary.xml: {e}")

        return timeseries

    async def load_comparison_from_file(
        self,
        case_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        从保存的JSON文件加载策略对比数据

        Args:
            case_id: 案例ID

        Returns:
            Dict: 策略对比数据，或None如果文件不存在
        """
        comparison_file = self.cases_dir / case_id / "analysis" / "strategy_comparison.json"

        if not comparison_file.exists():
            logger.warning(f"Strategy comparison file not found: {comparison_file}")
            return None

        try:
            with open(comparison_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('strategy_comparison', {})
        except Exception as e:
            logger.error(f"Error loading strategy comparison: {e}")
            return None

    async def load_timeseries_from_file(
        self,
        case_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        从保存的JSON文件加载时序数据

        Args:
            case_id: 案例ID

        Returns:
            Dict: 时序数据，或None如果文件不存在
        """
        timeseries_file = self.cases_dir / case_id / "analysis" / "strategy_timeseries.json"

        if not timeseries_file.exists():
            logger.warning(f"Strategy timeseries file not found: {timeseries_file}")
            return None

        try:
            with open(timeseries_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('timeseries', {})
        except Exception as e:
            logger.error(f"Error loading strategy timeseries: {e}")
            return None
