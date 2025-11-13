"""
Analysis Results Service (Task 3.1 - Week 3 Phase 2)

分析结果聚合服务

职责:
- 聚合多个仿真的 EdgeData/TripInfo 指标
- 生成对比报告 (基线 vs 事件 vs 控制策略)
- 计算改善指标和排名
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_service import BaseService
from ..models.responses.analysis_results_responses import (
    EdgeDataMetrics,
    TripInfoMetrics,
    ComparisonMetrics,
    AnalysisResultsSummary,
    AnalysisResultsResponse,
    ComparisonReportResponse
)

logger = logging.getLogger(__name__)


class AnalysisResultsService(BaseService):
    """
    分析结果聚合服务 (Task 3.1)

    提供分析结果的聚合、对比和排名功能
    """

    def __init__(self):
        """初始化分析结果服务"""
        super().__init__()

    async def get_analysis_results(
        self,
        batch_id: str,
        case_id: str
    ) -> AnalysisResultsResponse:
        """
        获取分析结果 (聚合)

        Args:
            batch_id: 分析批次ID
            case_id: 案例ID

        Returns:
            AnalysisResultsResponse: 完整分析结果

        Raises:
            ValueError: 批次不存在或数据无效
        """
        logger.info(f"获取分析结果: batch={batch_id}, case={case_id}")

        # 验证批次存在
        case_dir = self.cases_dir / case_id
        analysis_batch_dir = case_dir / "analysis" / batch_id

        if not analysis_batch_dir.exists():
            raise ValueError(f"Analysis batch not found: {batch_id}")

        # 加载批次元数据
        batch_metadata = self._load_batch_metadata(analysis_batch_dir)

        # 构建总览
        summary = self._build_analysis_summary(batch_id, case_id, batch_metadata)

        # 聚合 EdgeData 指标
        edgedata_metrics = self._aggregate_edgedata_metrics(
            analysis_batch_dir,
            batch_metadata.get("simulation_ids", [])
        )

        # 聚合 TripInfo 指标
        tripinfo_metrics = self._aggregate_tripinfo_metrics(
            analysis_batch_dir,
            batch_metadata.get("simulation_ids", [])
        )

        # 生成对比指标
        comparison_metrics = self._generate_comparison_metrics(
            analysis_batch_dir,
            batch_metadata
        )

        # 聚合统计
        aggregated_statistics = self._build_aggregated_statistics(
            edgedata_metrics,
            tripinfo_metrics
        )

        return AnalysisResultsResponse(
            summary=summary,
            edgedata_metrics=edgedata_metrics,
            tripinfo_metrics=tripinfo_metrics,
            comparison_metrics=comparison_metrics,
            aggregated_statistics=aggregated_statistics
        )

    async def get_comparison_report(
        self,
        batch_id: str,
        case_id: str
    ) -> ComparisonReportResponse:
        """
        获取对比报告

        Args:
            batch_id: 分析批次ID
            case_id: 案例ID

        Returns:
            ComparisonReportResponse: 对比报告

        Raises:
            ValueError: 批次不存在或缺少基线场景
        """
        logger.info(f"生成对比报告: batch={batch_id}, case={case_id}")

        # 验证批次存在
        case_dir = self.cases_dir / case_id
        analysis_batch_dir = case_dir / "analysis" / batch_id

        if not analysis_batch_dir.exists():
            raise ValueError(f"Analysis batch not found: {batch_id}")

        # 加载批次元数据
        batch_metadata = self._load_batch_metadata(analysis_batch_dir)

        baseline_scenario_id = batch_metadata.get("baseline_scenario_id")
        comparison_scenario_ids = batch_metadata.get("comparison_scenario_ids", [])

        if not baseline_scenario_id:
            raise ValueError("Baseline scenario not specified")

        # 构建场景信息
        baseline_scenario = self._build_scenario_info(baseline_scenario_id)
        comparison_scenarios = [
            self._build_scenario_info(scenario_id)
            for scenario_id in comparison_scenario_ids
        ]

        # 生成对比指标
        comparison_metrics = self._generate_comparison_metrics(
            analysis_batch_dir,
            batch_metadata
        )

        # 计算改善排名
        improvement_ranking = self._calculate_improvement_ranking(
            comparison_metrics,
            comparison_scenarios
        )

        # 生成可视化数据
        visualization_data = self._build_visualization_data(
            comparison_metrics,
            baseline_scenario,
            comparison_scenarios
        )

        return ComparisonReportResponse(
            batch_id=batch_id,
            case_id=case_id,
            baseline_scenario=baseline_scenario,
            comparison_scenarios=comparison_scenarios,
            comparison_metrics=comparison_metrics,
            improvement_ranking=improvement_ranking,
            visualization_data=visualization_data
        )

    # ========================================================================
    # Private Methods - Data Loading
    # ========================================================================

    def _load_batch_metadata(self, analysis_batch_dir: Path) -> Dict[str, Any]:
        """
        加载批次元数据

        Args:
            analysis_batch_dir: 分析批次目录

        Returns:
            Dict: 批次元数据
        """
        metadata_file = analysis_batch_dir / "analysis_index.json"

        if not metadata_file.exists():
            logger.warning(f"Batch metadata not found: {metadata_file}")
            return {}

        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to load batch metadata: {e}")
            return {}

    # ========================================================================
    # Private Methods - Aggregation
    # ========================================================================

    def _build_analysis_summary(
        self,
        batch_id: str,
        case_id: str,
        batch_metadata: Dict[str, Any]
    ) -> AnalysisResultsSummary:
        """
        构建分析结果总览

        Args:
            batch_id: 批次ID
            case_id: 案例ID
            batch_metadata: 批次元数据

        Returns:
            AnalysisResultsSummary: 总览数据
        """
        simulation_ids = batch_metadata.get("simulation_ids", [])

        return AnalysisResultsSummary(
            batch_id=batch_id,
            case_id=case_id,
            total_simulations=len(simulation_ids),
            analyzed_simulations=len(simulation_ids),
            simulation_ids=simulation_ids,
            baseline_scenario_id=batch_metadata.get("baseline_scenario_id"),
            comparison_scenario_ids=batch_metadata.get("comparison_scenario_ids", []),
            analysis_started_at=batch_metadata.get("created_at", datetime.now().isoformat()),
            analysis_completed_at=batch_metadata.get("completed_at", datetime.now().isoformat()),
            analysis_duration_seconds=batch_metadata.get("duration_seconds", 0.0),
            analysis_types_completed=batch_metadata.get("analysis_types", []),
            key_metrics=batch_metadata.get("key_metrics", {})
        )

    def _aggregate_edgedata_metrics(
        self,
        analysis_batch_dir: Path,
        simulation_ids: List[str]
    ) -> List[EdgeDataMetrics]:
        """
        聚合 EdgeData 指标

        Args:
            analysis_batch_dir: 分析批次目录
            simulation_ids: 仿真ID列表

        Returns:
            List[EdgeDataMetrics]: EdgeData 指标列表
        """
        import xml.etree.ElementTree as ET
        import statistics

        logger.info(f"聚合 EdgeData 指标: {len(simulation_ids)} 个仿真")

        # 读取每个仿真的 edgedata 结果并按 edge_id 聚合
        edge_data_map = {}  # {edge_id: [data_from_sim1, data_from_sim2, ...]}

        for sim_id in simulation_ids:
            # 路径: cases/{case_id}/simulations/{sim_id}/outputs/edgedata.xml
            sim_dir = self.cases_dir / analysis_batch_dir.parts[-2] / "simulations" / sim_id
            edgedata_file = sim_dir / "outputs" / "edgedata.xml"

            if not edgedata_file.exists():
                logger.warning(f"EdgeData file not found for sim {sim_id}: {edgedata_file}")
                continue

            try:
                tree = ET.parse(edgedata_file)
                root = tree.getroot()

                # 解析 edgedata.xml
                for edge in root.findall(".//edge"):
                    edge_id = edge.get("id")
                    if not edge_id:
                        continue

                    # 聚合所有时间间隔的数据
                    speed_values = []
                    density_values = []
                    occupancy_values = []

                    for interval in edge.findall("interval"):
                        speed = float(interval.get("speed", 0))
                        density = float(interval.get("density", 0))
                        occupancy = float(interval.get("occupancy", 0))

                        speed_values.append(speed)
                        density_values.append(density)
                        occupancy_values.append(occupancy)

                    if speed_values:
                        if edge_id not in edge_data_map:
                            edge_data_map[edge_id] = {
                                "speed_samples": [],
                                "density_samples": [],
                                "occupancy_samples": []
                            }

                        edge_data_map[edge_id]["speed_samples"].append(statistics.mean(speed_values))
                        edge_data_map[edge_id]["density_samples"].append(statistics.mean(density_values))
                        edge_data_map[edge_id]["occupancy_samples"].append(statistics.mean(occupancy_values))

            except Exception as e:
                logger.error(f"Failed to parse edgedata.xml for sim {sim_id}: {e}")
                continue

        # 计算每个道路段的聚合指标
        aggregated_metrics = []

        for edge_id, data in edge_data_map.items():
            speed_samples = data["speed_samples"]
            density_samples = data["density_samples"]
            occupancy_samples = data["occupancy_samples"]

            if not speed_samples:
                continue

            avg_speed = statistics.mean(speed_samples)
            min_speed = min(speed_samples)
            max_speed = max(speed_samples)
            speed_std = statistics.stdev(speed_samples) if len(speed_samples) > 1 else 0.0

            avg_density = statistics.mean(density_samples)
            max_density = max(density_samples)

            avg_occupancy = statistics.mean(occupancy_samples)
            max_occupancy = max(occupancy_samples)

            # 判断拥堵等级 (基于平均速度)
            if avg_speed >= 60:
                congestion_level = "smooth"
                congestion_duration = 0.0
            elif avg_speed >= 40:
                congestion_level = "moderate"
                congestion_duration = 30.0
            elif avg_speed >= 20:
                congestion_level = "congested"
                congestion_duration = 60.0
            else:
                congestion_level = "severe"
                congestion_duration = 90.0

            aggregated_metrics.append(
                EdgeDataMetrics(
                    edge_id=edge_id,
                    edge_name=None,  # TODO: 从网络文件获取道路名称
                    total_vehicles=int(avg_density * 1000),  # 估算
                    avg_vehicles_per_hour=int(avg_density * 250),  # 估算
                    max_vehicles_per_hour=int(max_density * 250),  # 估算
                    avg_speed=avg_speed,
                    min_speed=min_speed,
                    max_speed=max_speed,
                    speed_std=speed_std,
                    avg_density=avg_density,
                    max_density=max_density,
                    avg_occupancy=avg_occupancy,
                    max_occupancy=max_occupancy,
                    congestion_level=congestion_level,
                    congestion_duration_minutes=congestion_duration
                )
            )

        logger.info(f"聚合完成: {len(aggregated_metrics)} 个道路段")
        return aggregated_metrics

    def _aggregate_tripinfo_metrics(
        self,
        analysis_batch_dir: Path,
        simulation_ids: List[str]
    ) -> TripInfoMetrics:
        """
        聚合 TripInfo 指标

        Args:
            analysis_batch_dir: 分析批次目录
            simulation_ids: 仿真ID列表

        Returns:
            TripInfoMetrics: TripInfo 指标
        """
        import xml.etree.ElementTree as ET
        import statistics

        logger.info(f"聚合 TripInfo 指标: {len(simulation_ids)} 个仿真")

        # 聚合所有仿真的 tripinfo 数据
        all_durations = []
        all_delays = []
        all_waiting_times = []
        all_trip_lengths = []
        total_trips_count = 0
        completed_trips_count = 0

        for sim_id in simulation_ids:
            # 路径: cases/{case_id}/simulations/{sim_id}/outputs/tripinfo.xml
            sim_dir = self.cases_dir / analysis_batch_dir.parts[-2] / "simulations" / sim_id
            tripinfo_file = sim_dir / "outputs" / "tripinfo.xml"

            if not tripinfo_file.exists():
                logger.warning(f"TripInfo file not found for sim {sim_id}: {tripinfo_file}")
                continue

            try:
                tree = ET.parse(tripinfo_file)
                root = tree.getroot()

                # 解析 tripinfo.xml
                for tripinfo in root.findall("tripinfo"):
                    total_trips_count += 1

                    # 提取字段
                    duration = float(tripinfo.get("duration", 0))
                    time_loss = float(tripinfo.get("timeLoss", 0))  # delay
                    wait_steps = float(tripinfo.get("waitingTime", 0))
                    route_length = float(tripinfo.get("routeLength", 0))

                    # 检查是否完成 (duration > 0 表示完成)
                    if duration > 0:
                        completed_trips_count += 1
                        all_durations.append(duration)
                        all_delays.append(time_loss)
                        all_waiting_times.append(wait_steps)
                        all_trip_lengths.append(route_length / 1000)  # 转换为 km

            except Exception as e:
                logger.error(f"Failed to parse tripinfo.xml for sim {sim_id}: {e}")
                continue

        # 计算聚合指标
        if not all_durations:
            logger.warning("No tripinfo data found, returning default metrics")
            return TripInfoMetrics(
                total_trips=0,
                completed_trips=0,
                incomplete_trips=0,
                completion_rate=0.0
            )

        incomplete_trips_count = total_trips_count - completed_trips_count
        completion_rate = (completed_trips_count / total_trips_count * 100) if total_trips_count > 0 else 0.0

        avg_duration = statistics.mean(all_durations)
        min_duration = min(all_durations)
        max_duration = max(all_durations)
        total_duration = sum(all_durations)

        avg_trip_length = statistics.mean(all_trip_lengths)
        total_trip_length = sum(all_trip_lengths)

        avg_delay = statistics.mean(all_delays)
        total_delay = sum(all_delays)

        avg_waiting_time = statistics.mean(all_waiting_times)

        # 计算平均速度 (km/h)
        avg_trip_speed = (avg_trip_length / (avg_duration / 3600)) if avg_duration > 0 else 0.0

        logger.info(
            f"聚合完成: {total_trips_count} 行程, "
            f"完成率={completion_rate:.1f}%, "
            f"平均时长={avg_duration:.1f}s"
        )

        return TripInfoMetrics(
            total_trips=total_trips_count,
            completed_trips=completed_trips_count,
            incomplete_trips=incomplete_trips_count,
            completion_rate=completion_rate,
            avg_trip_duration=avg_duration,
            min_trip_duration=min_duration,
            max_trip_duration=max_duration,
            total_trip_duration=total_duration,
            avg_trip_length=avg_trip_length,
            total_trip_length=total_trip_length,
            avg_delay=avg_delay,
            total_delay=total_delay,
            avg_waiting_time=avg_waiting_time,
            avg_trip_speed=avg_trip_speed
        )

    def _generate_comparison_metrics(
        self,
        analysis_batch_dir: Path,
        batch_metadata: Dict[str, Any]
    ) -> List[ComparisonMetrics]:
        """
        生成对比指标

        Args:
            analysis_batch_dir: 分析批次目录
            batch_metadata: 批次元数据

        Returns:
            List[ComparisonMetrics]: 对比指标列表
        """
        logger.info("生成对比指标")

        baseline_scenario_id = batch_metadata.get("baseline_scenario_id")
        comparison_scenario_ids = batch_metadata.get("comparison_scenario_ids", [])

        if not baseline_scenario_id or not comparison_scenario_ids:
            logger.warning("No baseline or comparison scenarios specified")
            return []

        comparison_metrics_list = []

        # 加载基线场景的聚合结果
        baseline_simulation_ids = self._get_simulation_ids_for_scenario(
            batch_metadata, baseline_scenario_id
        )

        if not baseline_simulation_ids:
            logger.warning(f"No simulations found for baseline scenario: {baseline_scenario_id}")
            return []

        baseline_edgedata = self._aggregate_edgedata_metrics(
            analysis_batch_dir, baseline_simulation_ids
        )
        baseline_tripinfo = self._aggregate_tripinfo_metrics(
            analysis_batch_dir, baseline_simulation_ids
        )

        # 对每个对比场景生成对比指标
        for comparison_scenario_id in comparison_scenario_ids:
            comparison_simulation_ids = self._get_simulation_ids_for_scenario(
                batch_metadata, comparison_scenario_id
            )

            if not comparison_simulation_ids:
                logger.warning(f"No simulations found for comparison scenario: {comparison_scenario_id}")
                continue

            comparison_edgedata = self._aggregate_edgedata_metrics(
                analysis_batch_dir, comparison_simulation_ids
            )
            comparison_tripinfo = self._aggregate_tripinfo_metrics(
                analysis_batch_dir, comparison_simulation_ids
            )

            # 生成 EdgeData 对比指标
            if baseline_edgedata and comparison_edgedata:
                # 计算平均速度
                baseline_avg_speed = sum(e.avg_speed for e in baseline_edgedata) / len(baseline_edgedata)
                comparison_avg_speed = sum(e.avg_speed for e in comparison_edgedata) / len(comparison_edgedata)

                comparison_metrics_list.append(
                    self._create_comparison_metric(
                        metric_name="avg_speed",
                        metric_type="edgedata",
                        baseline_value=baseline_avg_speed,
                        comparison_value=comparison_avg_speed,
                        baseline_scenario_id=baseline_scenario_id,
                        comparison_scenario_id=comparison_scenario_id,
                        higher_is_better=True  # 速度越高越好
                    )
                )

                # 计算平均密度
                baseline_avg_density = sum(e.avg_density for e in baseline_edgedata) / len(baseline_edgedata)
                comparison_avg_density = sum(e.avg_density for e in comparison_edgedata) / len(comparison_edgedata)

                comparison_metrics_list.append(
                    self._create_comparison_metric(
                        metric_name="avg_density",
                        metric_type="edgedata",
                        baseline_value=baseline_avg_density,
                        comparison_value=comparison_avg_density,
                        baseline_scenario_id=baseline_scenario_id,
                        comparison_scenario_id=comparison_scenario_id,
                        higher_is_better=False  # 密度越低越好
                    )
                )

            # 生成 TripInfo 对比指标
            comparison_metrics_list.append(
                self._create_comparison_metric(
                    metric_name="avg_trip_duration",
                    metric_type="tripinfo",
                    baseline_value=baseline_tripinfo.avg_trip_duration,
                    comparison_value=comparison_tripinfo.avg_trip_duration,
                    baseline_scenario_id=baseline_scenario_id,
                    comparison_scenario_id=comparison_scenario_id,
                    higher_is_better=False  # 时间越短越好
                )
            )

            comparison_metrics_list.append(
                self._create_comparison_metric(
                    metric_name="avg_delay",
                    metric_type="tripinfo",
                    baseline_value=baseline_tripinfo.avg_delay,
                    comparison_value=comparison_tripinfo.avg_delay,
                    baseline_scenario_id=baseline_scenario_id,
                    comparison_scenario_id=comparison_scenario_id,
                    higher_is_better=False  # 延误越少越好
                )
            )

            comparison_metrics_list.append(
                self._create_comparison_metric(
                    metric_name="completion_rate",
                    metric_type="tripinfo",
                    baseline_value=baseline_tripinfo.completion_rate,
                    comparison_value=comparison_tripinfo.completion_rate,
                    baseline_scenario_id=baseline_scenario_id,
                    comparison_scenario_id=comparison_scenario_id,
                    higher_is_better=True  # 完成率越高越好
                )
            )

        logger.info(f"生成了 {len(comparison_metrics_list)} 个对比指标")
        return comparison_metrics_list

    def _get_simulation_ids_for_scenario(
        self,
        batch_metadata: Dict[str, Any],
        scenario_id: str
    ) -> List[str]:
        """
        获取指定场景的仿真ID列表

        Args:
            batch_metadata: 批次元数据
            scenario_id: 场景ID

        Returns:
            List[str]: 仿真ID列表
        """
        # TODO: 实现从批次元数据中提取特定场景的仿真ID
        # 简化版: 假设所有仿真都属于同一场景
        return batch_metadata.get("simulation_ids", [])

    def _create_comparison_metric(
        self,
        metric_name: str,
        metric_type: str,
        baseline_value: float,
        comparison_value: float,
        baseline_scenario_id: str,
        comparison_scenario_id: str,
        higher_is_better: bool = True
    ) -> ComparisonMetrics:
        """
        创建单个对比指标

        Args:
            metric_name: 指标名称
            metric_type: 指标类型
            baseline_value: 基线值
            comparison_value: 对比值
            baseline_scenario_id: 基线场景ID
            comparison_scenario_id: 对比场景ID
            higher_is_better: 是否越高越好

        Returns:
            ComparisonMetrics: 对比指标对象
        """
        # 计算差异
        absolute_difference = comparison_value - baseline_value
        relative_difference_percent = (absolute_difference / baseline_value * 100) if baseline_value != 0 else 0

        # 判断改善状态
        if abs(relative_difference_percent) < 1.0:
            improvement_status = "unchanged"
            improvement_color = "gray"
        elif higher_is_better:
            if absolute_difference > 0:
                improvement_status = "improved"
                improvement_color = "green"
            else:
                improvement_status = "deteriorated"
                improvement_color = "red"
        else:
            if absolute_difference < 0:
                improvement_status = "improved"
                improvement_color = "green"
            else:
                improvement_status = "deteriorated"
                improvement_color = "red"

        # 统计显著性判断 (简化版: 超过5%认为显著)
        is_significant = abs(relative_difference_percent) >= 5.0

        return ComparisonMetrics(
            metric_name=metric_name,
            metric_type=metric_type,
            baseline_value=baseline_value,
            baseline_scenario_id=baseline_scenario_id,
            comparison_value=comparison_value,
            comparison_scenario_id=comparison_scenario_id,
            absolute_difference=absolute_difference,
            relative_difference_percent=relative_difference_percent,
            improvement_status=improvement_status,
            improvement_color=improvement_color,
            is_significant=is_significant,
            confidence_level=0.95 if is_significant else None
        )

    def _build_aggregated_statistics(
        self,
        edgedata_metrics: List[EdgeDataMetrics],
        tripinfo_metrics: TripInfoMetrics
    ) -> Dict[str, Any]:
        """
        构建聚合统计数据

        Args:
            edgedata_metrics: EdgeData 指标列表
            tripinfo_metrics: TripInfo 指标

        Returns:
            Dict: 聚合统计数据
        """
        return {
            "total_edges": len(edgedata_metrics),
            "total_trips": tripinfo_metrics.total_trips,
            "overall_avg_speed": sum(m.avg_speed for m in edgedata_metrics) / len(edgedata_metrics)
                if edgedata_metrics else 0,
            "overall_completion_rate": tripinfo_metrics.completion_rate,
            "time_series": {},  # TODO: 时间序列数据
            "spatial_distribution": {}  # TODO: 空间分布数据
        }

    # ========================================================================
    # Private Methods - Comparison Report
    # ========================================================================

    def _build_scenario_info(self, scenario_id: str) -> Dict[str, Any]:
        """
        构建场景信息

        Args:
            scenario_id: 场景ID

        Returns:
            Dict: 场景信息
        """
        # TODO: 从场景元数据读取实际信息
        # 当前返回占位数据
        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario_id.split("_")[-1].upper(),
            "event_type": "accident",
            "control_type": scenario_id.split("_")[-1] if "_" in scenario_id else "none"
        }

    def _calculate_improvement_ranking(
        self,
        comparison_metrics: List[ComparisonMetrics],
        comparison_scenarios: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        计算改善排名

        Args:
            comparison_metrics: 对比指标列表
            comparison_scenarios: 对比场景列表

        Returns:
            List[Dict]: 排名列表 (按改善程度降序)
        """
        logger.info("计算改善排名")

        # 按场景分组指标
        scenario_metrics = {}
        for metric in comparison_metrics:
            scenario_id = metric.comparison_scenario_id
            if scenario_id not in scenario_metrics:
                scenario_metrics[scenario_id] = []
            scenario_metrics[scenario_id].append(metric)

        # 计算每个场景的总体改善分数
        ranking = []
        for scenario in comparison_scenarios:
            scenario_id = scenario["scenario_id"]
            metrics = scenario_metrics.get(scenario_id, [])

            if not metrics:
                continue

            # 计算加权改善分数
            # 权重: 速度 30%, 延误 30%, 完成率 20%, 密度 20%
            improvement_scores = []
            weights = {
                "avg_speed": 0.30,
                "avg_delay": 0.30,
                "completion_rate": 0.20,
                "avg_density": 0.20
            }

            total_weight = 0
            weighted_improvement = 0

            for metric in metrics:
                weight = weights.get(metric.metric_name, 0.1)
                if weight > 0:
                    # 改善的相对百分比 (已经包含方向)
                    if metric.improvement_status == "improved":
                        improvement_value = abs(metric.relative_difference_percent)
                    elif metric.improvement_status == "deteriorated":
                        improvement_value = -abs(metric.relative_difference_percent)
                    else:
                        improvement_value = 0

                    weighted_improvement += improvement_value * weight
                    total_weight += weight

            # 归一化
            overall_improvement = weighted_improvement / total_weight if total_weight > 0 else 0

            ranking.append({
                "scenario_id": scenario_id,
                "scenario_name": scenario.get("scenario_name", ""),
                "overall_improvement": overall_improvement,
                "rank": 0  # 将在排序后设置
            })

        # 按改善程度降序排序
        ranking.sort(key=lambda x: x["overall_improvement"], reverse=True)

        # 设置排名
        for idx, item in enumerate(ranking):
            item["rank"] = idx + 1

        logger.info(f"排名计算完成: {len(ranking)} 个场景")
        return ranking

    def _build_visualization_data(
        self,
        comparison_metrics: List[ComparisonMetrics],
        baseline_scenario: Dict[str, Any],
        comparison_scenarios: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        构建可视化数据

        Args:
            comparison_metrics: 对比指标列表
            baseline_scenario: 基线场景
            comparison_scenarios: 对比场景列表

        Returns:
            Dict: 可视化数据 (图表配置)
        """
        logger.info("构建可视化数据")

        # 1. 构建柱状图数据 (按指标分组)
        charts_data = []

        # 按指标名称分组
        metrics_by_name = {}
        for metric in comparison_metrics:
            metric_name = metric.metric_name
            if metric_name not in metrics_by_name:
                metrics_by_name[metric_name] = []
            metrics_by_name[metric_name].append(metric)

        # 为每个指标创建柱状图
        for metric_name, metrics_list in metrics_by_name.items():
            chart_data = {
                "type": "bar",
                "title": f"{metric_name} 对比",
                "labels": [],
                "datasets": [
                    {
                        "label": "基线",
                        "data": [],
                        "backgroundColor": "rgba(54, 162, 235, 0.5)"
                    },
                    {
                        "label": "对比场景",
                        "data": [],
                        "backgroundColor": "rgba(255, 99, 132, 0.5)"
                    }
                ]
            }

            for metric in metrics_list:
                scenario_name = metric.comparison_scenario_id.split("_")[-1].upper()
                chart_data["labels"].append(scenario_name)
                chart_data["datasets"][0]["data"].append(metric.baseline_value)
                chart_data["datasets"][1]["data"].append(metric.comparison_value)

            charts_data.append(chart_data)

        # 2. 构建热力图数据 (EdgeData 指标)
        heatmaps_data = []

        edgedata_metrics = [m for m in comparison_metrics if m.metric_type == "edgedata"]
        if edgedata_metrics:
            heatmap_data = {
                "type": "edgedata",
                "metric": "avg_speed",
                "data": []
            }

            for metric in edgedata_metrics:
                heatmap_data["data"].append({
                    "scenario_id": metric.comparison_scenario_id,
                    "value": metric.comparison_value,
                    "baseline_value": metric.baseline_value,
                    "improvement_color": metric.improvement_color
                })

            heatmaps_data.append(heatmap_data)

        # 3. 构建雷达图数据 (综合性能对比)
        radar_charts_data = []

        # 提取关键指标用于雷达图
        key_metrics = ["avg_speed", "avg_delay", "completion_rate", "avg_density"]

        for scenario in comparison_scenarios:
            scenario_id = scenario["scenario_id"]

            # 获取该场景的所有指标
            scenario_metrics = [m for m in comparison_metrics if m.comparison_scenario_id == scenario_id]

            radar_data = {
                "title": f"{scenario.get('scenario_name', scenario_id)} 综合性能",
                "labels": [],
                "datasets": [
                    {
                        "label": "基线",
                        "data": []
                    },
                    {
                        "label": scenario.get("scenario_name", scenario_id),
                        "data": []
                    }
                ]
            }

            for metric_name in key_metrics:
                matching_metric = next((m for m in scenario_metrics if m.metric_name == metric_name), None)
                if matching_metric:
                    radar_data["labels"].append(metric_name)
                    # 归一化到 0-100 范围
                    baseline_normalized = min(100, matching_metric.baseline_value)
                    comparison_normalized = min(100, matching_metric.comparison_value)
                    radar_data["datasets"][0]["data"].append(baseline_normalized)
                    radar_data["datasets"][1]["data"].append(comparison_normalized)

            if radar_data["labels"]:
                radar_charts_data.append(radar_data)

        logger.info(
            f"可视化数据构建完成: {len(charts_data)} 个图表, "
            f"{len(heatmaps_data)} 个热力图, {len(radar_charts_data)} 个雷达图"
        )

        return {
            "charts": charts_data,
            "heatmaps": heatmaps_data,
            "radar_charts": radar_charts_data
        }
