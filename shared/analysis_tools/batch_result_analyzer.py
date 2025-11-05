"""
批量仿真结果分析器 (Phase 2: T2.1-T2.3)

职责：
- 比较baseline和test方案的summary.xml结果
- 计算性能改进率（时间、流量、拥堵等）
- 生成结果对比表
"""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import statistics

logger = logging.getLogger(__name__)


class BatchResultAnalyzer:
    """批量仿真结果分析器"""

    def __init__(self):
        """初始化结果分析器"""
        self.baseline_results = {}
        self.test_results = {}
        self.improvement_rates = {}

    def analyze_batch_results(
        self,
        batch_dir: Path,
        plan_ids: List[str],
        baseline_plan_id: str = "baseline_plan"
    ) -> Dict[str, Any]:
        """
        分析批量仿真结果 (T2.1: 结果比较逻辑)

        Args:
            batch_dir: 批次目录路径
            plan_ids: 方案ID列表
            baseline_plan_id: 基准方案ID

        Returns:
            Dict: 分析结果，包含对比指标和改进率

        说明：
        - 从每个方案目录读取summary.xml
        - 提取关键指标（运行步数、流量、拥堵等）
        - 与baseline方案比较，计算改进率
        """
        logger.info(f"Analyzing batch results from {batch_dir}")

        results = {
            "batch_dir": str(batch_dir),
            "analyzed_at": datetime.now().isoformat(),
            "baseline_plan_id": baseline_plan_id,
            "plan_results": {},
            "comparison_summary": {},
            "improvement_rates": {}
        }

        # 1. 加载baseline方案结果
        if baseline_plan_id in plan_ids:
            plan_dir = batch_dir / baseline_plan_id
            baseline_metrics = self._extract_aggregated_metrics(plan_dir, baseline_plan_id)
            if baseline_metrics:
                results["plan_results"][baseline_plan_id] = {
                    "type": "baseline",
                    "metrics": baseline_metrics
                }
                self.baseline_results = baseline_metrics
                logger.info(f"Loaded baseline metrics: {baseline_metrics}")
            else:
                logger.warning(f"Could not extract metrics for baseline plan: {baseline_plan_id}")

        # 2. 加载test方案结果并计算改进率
        for plan_id in plan_ids:
            if plan_id == baseline_plan_id:
                continue

            plan_dir = batch_dir / plan_id
            test_metrics = self._extract_aggregated_metrics(plan_dir, plan_id)
            if test_metrics:
                results["plan_results"][plan_id] = {
                    "type": "test",
                    "metrics": test_metrics
                }
                self.test_results[plan_id] = test_metrics

                # 3. 计算改进率 (T2.2: 改进率计算)
                if self.baseline_results:
                    improvement_rate = self._calculate_improvement_rate(
                        baseline_metrics=self.baseline_results,
                        test_metrics=test_metrics
                    )
                    results["improvement_rates"][plan_id] = improvement_rate
                    self.improvement_rates[plan_id] = improvement_rate
                    logger.info(f"Improvement rates for {plan_id}: {improvement_rate}")
            else:
                logger.warning(f"Could not extract metrics for plan {plan_id}: {plan_dir}")

        # 4. 生成对比总结 (T2.3: 对比表生成)
        results["comparison_summary"] = self._generate_comparison_summary()

        return results

    def _extract_aggregated_metrics(self, plan_dir: Path, plan_id: str) -> Dict[str, Any]:
        """
        从计划目录中聚合多个种子的指标

        目录结构：
        plan_dir/
          ├── sim_66/summary.xml
          ├── sim_67/summary.xml
          └── sim_68/summary.xml

        Args:
            plan_dir: 计划目录路径
            plan_id: 计划ID

        Returns:
            Dict: 聚合后的指标数据（使用平均值）
        """
        sim_dirs = sorted([d for d in plan_dir.iterdir() if d.is_dir() and d.name.startswith('sim_')])

        if not sim_dirs:
            logger.warning(f"No simulation directories found in {plan_dir}")
            return {}

        all_metrics = []

        for sim_dir in sim_dirs:
            summary_path = sim_dir / "summary.xml"
            if summary_path.exists():
                metrics = self._extract_summary_metrics(summary_path)
                if metrics:
                    all_metrics.append(metrics)
                    logger.debug(f"Loaded metrics from {summary_path}")
            else:
                logger.warning(f"Summary.xml not found: {summary_path}")

        if not all_metrics:
            logger.warning(f"No metrics extracted for plan {plan_id}")
            return {}

        # 聚合指标：对所有种子的值进行平均
        aggregated = self._aggregate_metrics_list(all_metrics, plan_id)
        aggregated['num_seeds'] = len(all_metrics)
        aggregated['seed_metrics'] = all_metrics  # 保存原始数据用于可靠性计算

        logger.info(f"Aggregated metrics for {plan_id} from {len(all_metrics)} seeds: {aggregated}")
        return aggregated

    def _aggregate_metrics_list(self, metrics_list: List[Dict[str, Any]], plan_id: str) -> Dict[str, Any]:
        """
        聚合多个种子的指标（使用平均值）

        Args:
            metrics_list: 指标字典列表
            plan_id: 计划ID

        Returns:
            Dict: 聚合后的指标
        """
        if not metrics_list:
            return {}

        aggregated = {}

        # 获取所有指标的键
        all_keys = set()
        for metrics in metrics_list:
            all_keys.update(metrics.keys())

        # 对每个指标计算平均值
        for key in all_keys:
            values = []
            for metrics in metrics_list:
                if key in metrics:
                    try:
                        values.append(float(metrics[key]))
                    except (ValueError, TypeError):
                        pass

            if values:
                aggregated[key] = round(statistics.mean(values), 2)
                logger.debug(f"Plan {plan_id}: {key} = {aggregated[key]} (from {len(values)} seeds)")

        return aggregated

    def _extract_summary_metrics(self, summary_path: Path) -> Dict[str, Any]:
        """
        从summary.xml提取关键指标

        关键指标：
        - step: 仿真步数（影响模拟时间）
        - loaded: 加载的车辆数
        - inserted: 插入的车辆数
        - ended: 完成的车辆数
        - running: 当前运行车辆数
        - waiting: 等待车辆数
        - teleports: 传送次数（拥堵指标）
        - collisions: 碰撞次数
        - avgSpeed: 平均速度（核心性能指标）

        Args:
            summary_path: summary.xml文件路径

        Returns:
            Dict: 提取的指标数据
        """
        metrics = {}

        try:
            tree = ET.parse(summary_path)
            root = tree.getroot()

            # 解析timestep元素，提取最后一步的数据
            timesteps = root.findall("timestep")
            if timesteps:
                last_step = timesteps[-1]
                metrics["step"] = int(last_step.get("time", 0))

                # 从最后一步提取vehicle信息
                vehicle = last_step.find("vehicleSummary")
                if vehicle is not None:
                    metrics["loaded"] = int(vehicle.get("loaded", 0))
                    metrics["inserted"] = int(vehicle.get("inserted", 0))
                    metrics["ended"] = int(vehicle.get("ended", 0))
                    metrics["running"] = int(vehicle.get("running", 0))
                    metrics["waiting"] = int(vehicle.get("waiting", 0))
                    metrics["teleports"] = int(vehicle.get("teleports", 0))
                    metrics["collisions"] = int(vehicle.get("collisions", 0))

                    # 计算平均速度
                    if metrics["ended"] > 0:
                        # 需要从tripinfo.xml精确计算，这里用代理方法
                        metrics["avgSpeed"] = vehicle.get("avgSpeed", None)
                        if metrics["avgSpeed"] is not None:
                            metrics["avgSpeed"] = float(metrics["avgSpeed"])
                    else:
                        metrics["avgSpeed"] = 0.0

            logger.debug(f"Extracted metrics from {summary_path}: {metrics}")

        except Exception as e:
            logger.error(f"Error parsing {summary_path}: {e}")
            metrics = {}

        return metrics

    def _calculate_improvement_rate(
        self,
        baseline_metrics: Dict[str, Any],
        test_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        计算test方案相对baseline的改进率 (T2.2: 改进率计算)

        改进率 = (baseline_value - test_value) / baseline_value * 100%

        正改进（越小越好的指标）：
        - waiting: 等待时间（提高）
        - teleports: 传送次数（减少拥堵）
        - collisions: 碰撞次数（安全性）

        负改进（越大越好的指标）：
        - avgSpeed: 平均速度（加速）

        Args:
            baseline_metrics: 基准方案指标
            test_metrics: 测试方案指标

        Returns:
            Dict: 包含各项改进率的字典，>0表示改进，<0表示恶化
        """
        improvement = {}

        # 关键指标对
        metric_pairs = {
            # (指标名, 方向)
            # 方向: "lower_better" = True (越小越好), False (越大越好)
            "waiting": ("waiting", True),
            "teleports": ("teleports", True),
            "collisions": ("collisions", True),
            "avgSpeed": ("avgSpeed", False),
            "running": ("running", True),  # 车辆仍在网中（越少越好？实际取决于目标）
        }

        for metric_key, (metric_name, lower_is_better) in metric_pairs.items():
            baseline_val = baseline_metrics.get(metric_name)
            test_val = test_metrics.get(metric_name)

            if baseline_val is None or test_val is None:
                improvement[metric_key] = None
                continue

            try:
                baseline_val = float(baseline_val)
                test_val = float(test_val)

                if baseline_val == 0:
                    # 基准值为0，无法计算比率，使用绝对差值
                    if lower_is_better:
                        improvement[metric_key] = min(test_val, baseline_val) == baseline_val
                    else:
                        improvement[metric_key] = test_val > baseline_val
                else:
                    # 标准改进率计算
                    if lower_is_better:
                        # 基准值减少了多少
                        rate = (baseline_val - test_val) / baseline_val * 100
                    else:
                        # 基准值增加了多少
                        rate = (test_val - baseline_val) / baseline_val * 100

                    improvement[metric_key] = round(rate, 2)

            except (ValueError, TypeError) as e:
                logger.warning(f"Cannot calculate improvement for {metric_key}: {e}")
                improvement[metric_key] = None

        return improvement

    def _generate_comparison_summary(self) -> Dict[str, Any]:
        """
        生成对比总结 (T2.3: 对比表生成)

        生成可用于结果表的结构化数据

        Returns:
            Dict: 对比总结，包含行标题和所有方案的值
        """
        if not self.baseline_results:
            logger.warning("Baseline results not available for comparison summary")
            return {}

        summary = {
            "columns": ["指标", "基准方案", "单位"],
            "rows": [],
            "metrics_definitions": {
                "step": "仿真步数",
                "loaded": "已加载车辆数",
                "inserted": "已插入车辆数",
                "ended": "已完成车辆数",
                "running": "当前运行车数",
                "waiting": "等待车数",
                "teleports": "传送次数（拥堵指标）",
                "collisions": "碰撞次数",
                "avgSpeed": "平均速度（m/s）",
            }
        }

        # 添加测试方案列
        for plan_id in self.test_results.keys():
            summary["columns"].append(f"{plan_id}")
            summary["columns"].append(f"改进率%")

        # 添加行数据
        metrics_to_compare = ["step", "ended", "running", "waiting", "teleports", "collisions", "avgSpeed"]

        for metric in metrics_to_compare:
            if metric not in self.baseline_results:
                continue

            row = {
                "metric": metric,
                "metric_name": summary["metrics_definitions"].get(metric, metric),
                "baseline_value": self.baseline_results.get(metric),
                "unit": self._get_metric_unit(metric),
                "test_values": {}
            }

            # 添加各测试方案的值和改进率
            for plan_id, improvement_rate in self.improvement_rates.items():
                test_val = self.test_results.get(plan_id, {}).get(metric)
                row["test_values"][plan_id] = {
                    "value": test_val,
                    "improvement_rate": improvement_rate.get(metric) if improvement_rate else None
                }

            summary["rows"].append(row)

        return summary

    def _get_metric_unit(self, metric: str) -> str:
        """获取指标单位"""
        units = {
            "step": "s",
            "loaded": "辆",
            "inserted": "辆",
            "ended": "辆",
            "running": "辆",
            "waiting": "辆",
            "teleports": "次",
            "collisions": "次",
            "avgSpeed": "m/s",
        }
        return units.get(metric, "")

    def get_improvement_rates(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """获取特定方案的改进率"""
        return self.improvement_rates.get(plan_id)

    def get_all_results(self) -> Dict[str, Any]:
        """获取所有分析结果"""
        return {
            "baseline_results": self.baseline_results,
            "test_results": self.test_results,
            "improvement_rates": self.improvement_rates
        }


# 便利函数
def analyze_batch(
    batch_dir: str,
    plan_ids: List[str],
    baseline_plan_id: str = "baseline_plan"
) -> Dict[str, Any]:
    """
    便利函数：创建分析器并分析批次结果

    Args:
        batch_dir: 批次目录
        plan_ids: 方案ID列表
        baseline_plan_id: 基准方案ID

    Returns:
        Dict: 分析结果
    """
    analyzer = BatchResultAnalyzer()
    return analyzer.analyze_batch_results(
        batch_dir=Path(batch_dir),
        plan_ids=plan_ids,
        baseline_plan_id=baseline_plan_id
    )
