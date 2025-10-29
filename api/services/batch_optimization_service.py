"""
批量优化仿真服务

职责：
- 批量仿真批次的创建和管理
- 协调batch_simulation_scheduler执行
- 结果汇总和统计分析
- 与plan_service和simulation_service集成
"""

import logging
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import xml.etree.ElementTree as ET

from shared.control_tools.batch_simulation_scheduler import BatchSimulationScheduler
from shared.control_tools import plan_file_manager

logger = logging.getLogger(__name__)

# 配置路径
CASES_BASE_DIR = "cases"
PLANS_BASE_DIR = "control_data/plans"
BASELINE_PLAN_ID = "baseline_plan"


class BatchOptimizationService:
    """批量优化仿真服务"""

    def __init__(self):
        """初始化服务"""
        self.cases_base_dir = CASES_BASE_DIR
        self.plans_base_dir = PLANS_BASE_DIR
        self.scheduler = BatchSimulationScheduler(base_dir=CASES_BASE_DIR)

    def create_batch(
        self,
        case_id: str,
        plan_ids: List[str],
        num_seeds: int = 3,
        base_seed: int = 66,
        simulation_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        创建批量仿真批次

        Args:
            case_id: 案例ID
            plan_ids: 方案ID列表（必须包含baseline_plan）
            num_seeds: 每个方案的随机种子数量
            base_seed: 起始随机种子值
            simulation_config: 仿真配置参数（可选）

        Returns:
            Dict: 批次创建响应数据

        Raises:
            ValueError: 验证失败
            FileNotFoundError: 案例或方案不存在
        """
        logger.info(f"Creating batch for case {case_id} with {len(plan_ids)} plans")

        # 1. 验证case_id存在
        case_dir = Path(self.cases_base_dir) / case_id
        if not case_dir.exists():
            raise FileNotFoundError(f"案例不存在: {case_id}")

        # 2. 验证所有plan_ids存在
        plan_names = {}
        for plan_id in plan_ids:
            try:
                plan_metadata = plan_file_manager.get_plan(plan_id)
                plan_names[plan_id] = plan_metadata["plan_name"]
            except FileNotFoundError:
                raise FileNotFoundError(f"方案不存在: {plan_id}")

        # 3. 确保包含baseline_plan
        if BASELINE_PLAN_ID not in plan_ids:
            logger.warning(f"Baseline plan not in list, adding it automatically")
            plan_ids.insert(0, BASELINE_PLAN_ID)
            plan_names[BASELINE_PLAN_ID] = "基准方案（无管控）"

        # 4. 创建批次
        batch_id, batch_dir = self.scheduler.create_batch(
            case_id=case_id,
            plan_ids=plan_ids,
            plan_names=plan_names,
            num_seeds=num_seeds,
            base_seed=base_seed,
        )

        # 5. 保存仿真配置（如果提供）
        if simulation_config:
            config_path = batch_dir / "simulation_config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(simulation_config, f, ensure_ascii=False, indent=2)

        # 6. 构建响应
        total_tasks = len(plan_ids) * num_seeds

        response = {
            "batch_id": batch_id,
            "case_id": case_id,
            "plan_ids": plan_ids,
            "total_tasks": total_tasks,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

        logger.info(
            f"Batch {batch_id} created: {len(plan_ids)} plans × {num_seeds} seeds = {total_tasks} tasks"
        )

        return response

    async def start_batch(
        self, case_id: str, batch_id: str, simulation_service  # Type hint would be circular
    ) -> Dict[str, Any]:
        """
        启动批量仿真（异步）

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            simulation_service: 仿真服务实例

        Returns:
            Dict: 批次启动响应数据

        Raises:
            FileNotFoundError: 批次不存在
        """
        logger.info(f"Starting batch {batch_id}")

        # 验证批次存在
        batch_dir = Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / batch_id
        if not batch_dir.exists():
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        # 启动批量仿真（异步执行）
        asyncio.create_task(
            self.scheduler.start_batch(
                case_id=case_id, batch_id=batch_id, simulation_service=simulation_service
            )
        )

        response = {
            "batch_id": batch_id,
            "status": "running",
            "started_at": datetime.now().isoformat(),
        }

        logger.info(f"Batch {batch_id} started")

        return response

    def get_batch_progress(self, case_id: str, batch_id: str) -> Dict[str, Any]:
        """
        获取批次进度

        Args:
            case_id: 案例ID
            batch_id: 批次ID

        Returns:
            Dict: 批次进度数据

        Raises:
            FileNotFoundError: 批次不存在
        """
        try:
            progress_data = self.scheduler.get_batch_progress(case_id, batch_id)

            # 添加预计完成时间
            from shared.control_tools.batch_simulation_scheduler import BatchTask

            tasks = [BatchTask.from_dict(t) for t in progress_data["tasks"]]
            estimated_completion = self.scheduler._calculate_estimated_completion(tasks)

            response = {**progress_data, "estimated_completion": estimated_completion}

            return response

        except FileNotFoundError as e:
            raise FileNotFoundError(f"批次不存在: {batch_id}") from e

    def get_batch_results(
        self, case_id: str, batch_id: str, include_time_series: bool = False
    ) -> Dict[str, Any]:
        """
        获取批次结果汇总

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            include_time_series: 是否包含时序数据（在网车辆峰值曲线等）

        Returns:
            Dict: 批次结果数据

        Raises:
            FileNotFoundError: 批次不存在
            ValueError: 批次未完成
        """
        logger.info(
            f"Getting results for batch {batch_id}, " f"include_time_series={include_time_series}"
        )

        # 获取批次进度
        progress_data = self.scheduler.get_batch_progress(case_id, batch_id)

        # 检查批次是否完成
        if progress_data["status"] not in ["completed", "failed"]:
            raise ValueError(f"批次尚未完成，当前状态: {progress_data['status']}")

        # 读取批次元数据
        batch_dir = Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / batch_id
        metadata_path = batch_dir / "batch_metadata.json"

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # 按方案分组任务
        from shared.control_tools.batch_simulation_scheduler import BatchTask

        tasks = [BatchTask.from_dict(t) for t in progress_data["tasks"]]

        plan_tasks = {}
        for task in tasks:
            if task.plan_id not in plan_tasks:
                plan_tasks[task.plan_id] = []
            plan_tasks[task.plan_id].append(task)

        # 为每个方案提取结果和统计
        plan_results = []

        for plan_id, plan_task_list in plan_tasks.items():
            # 获取方案名称
            try:
                plan_metadata = plan_file_manager.get_plan(plan_id)
                plan_name = plan_metadata["plan_name"]
            except:
                plan_name = plan_id

            # 提取每次仿真的指标
            simulations = []
            for task in plan_task_list:
                if task.status == "completed" and task.simulation_id:
                    # 提取仿真指标
                    metrics = self._extract_simulation_metrics(
                        case_id=case_id, batch_id=batch_id, plan_id=plan_id, task=task
                    )
                    if metrics:
                        simulations.append(metrics)

            # 计算聚合统计
            aggregated_metrics = self._calculate_aggregated_metrics(simulations)

            plan_result = {
                "plan_id": plan_id,
                "plan_name": plan_name,
                "simulations": simulations,
                "aggregated_metrics": aggregated_metrics,
            }

            # 如果需要时序数据，提取并聚合
            if include_time_series:
                time_series = self._extract_and_aggregate_time_series(
                    case_id=case_id, batch_id=batch_id, plan_id=plan_id, tasks=plan_task_list
                )
                if time_series:
                    plan_result["time_series"] = time_series

            plan_results.append(plan_result)

        # 构建响应
        response = {
            "batch_id": batch_id,
            "status": progress_data["status"],
            "plan_results": plan_results,
            "created_at": metadata.get("created_at"),
            "completed_at": metadata.get("completed_at"),
        }

        logger.info(f"Results for batch {batch_id}: {len(plan_results)} plans")

        return response

    def _extract_simulation_metrics(
        self, case_id: str, batch_id: str, plan_id: str, task
    ) -> Optional[Dict[str, Any]]:
        """
        从仿真结果文件中提取性能指标

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            plan_id: 方案ID
            task: 任务对象

        Returns:
            Optional[Dict]: 仿真指标，如果无法提取则返回None
        """
        try:
            sim_dir = (
                Path(self.cases_base_dir)
                / case_id
                / "simulations"
                / "plan_opti"
                / batch_id
                / plan_id
                / f"sim_{task.seed}"
            )

            metrics = {"seed": task.seed, "simulation_id": task.simulation_id}

            # 尝试从summary.xml提取指标
            summary_file = sim_dir / "summary.xml"
            if summary_file.exists():
                summary_metrics = self._parse_summary_xml(summary_file)
                metrics.update(summary_metrics)

            # 尝试从tripinfo.xml提取指标
            tripinfo_file = sim_dir / "tripinfo.xml"
            if tripinfo_file.exists():
                tripinfo_metrics = self._parse_tripinfo_xml(tripinfo_file)
                metrics.update(tripinfo_metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to extract metrics for task {task.task_id}: {e}")
            return None

    def _parse_summary_xml(self, file_path: Path) -> Dict[str, Any]:
        """
        解析summary.xml文件提取指标

        Args:
            file_path: summary.xml文件路径

        Returns:
            Dict: 提取的指标
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # 提取基础统计
            step_elem = root.find("step[@time]")
            if step_elem is not None:
                return {
                    "total_vehicles": int(step_elem.get("loaded", 0)),
                    "avg_speed": float(step_elem.get("meanSpeed", 0.0)),
                }

            return {}

        except Exception as e:
            logger.warning(f"Failed to parse summary.xml: {e}")
            return {}

    def _parse_tripinfo_xml(self, file_path: Path) -> Dict[str, Any]:
        """
        解析tripinfo.xml文件提取指标

        Args:
            file_path: tripinfo.xml文件路径

        Returns:
            Dict: 提取的指标
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # 提取所有tripinfo
            tripinfos = root.findall("tripinfo")

            if not tripinfos:
                return {}

            total_duration = 0.0
            total_delay = 0.0
            count = len(tripinfos)

            for trip in tripinfos:
                total_duration += float(trip.get("duration", 0.0))
                total_delay += float(trip.get("timeLoss", 0.0))

            return {
                "avg_travel_time": total_duration / count if count > 0 else 0.0,
                "total_delay": total_delay,
            }

        except Exception as e:
            logger.warning(f"Failed to parse tripinfo.xml: {e}")
            return {}

    def _calculate_aggregated_metrics(
        self, simulations: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, float]]:
        """
        计算聚合统计指标

        Args:
            simulations: 仿真结果列表

        Returns:
            Dict: 聚合指标（按指标名称分组）
        """
        if not simulations:
            return {}

        # 提取所有可用的指标名称（排除seed和simulation_id）
        metric_names = set()
        for sim in simulations:
            for key in sim.keys():
                if key not in ["seed", "simulation_id"] and isinstance(sim[key], (int, float)):
                    metric_names.add(key)

        # 计算每个指标的统计
        aggregated = {}

        for metric_name in metric_names:
            values = [
                sim[metric_name]
                for sim in simulations
                if metric_name in sim and sim[metric_name] is not None
            ]

            if values:
                import statistics

                aggregated[metric_name] = {
                    "mean": statistics.mean(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0.0,
                    "min": min(values),
                    "max": max(values),
                }

        return aggregated

    def _extract_and_aggregate_time_series(
        self, case_id: str, batch_id: str, plan_id: str, tasks: List[Any]
    ) -> Optional[Dict[str, Any]]:
        """
        提取并聚合方案的时序数据

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            plan_id: 方案ID
            tasks: 任务列表

        Returns:
            Dict: 时序数据（包含time_points和各指标的mean/std/min/max）
            None: 无法提取时序数据
        """
        try:
            # 提取每个仿真的时序数据
            all_time_series = []

            for task in tasks:
                if task.status == "completed" and task.simulation_id:
                    ts_data = self._extract_time_series_from_summary(
                        case_id=case_id, batch_id=batch_id, plan_id=plan_id, seed=task.seed
                    )
                    if ts_data:
                        all_time_series.append(ts_data)

            if not all_time_series:
                logger.warning(f"No time series data found for plan {plan_id}")
                return None

            # 聚合多次仿真的时序数据
            aggregated_ts = self._aggregate_time_series(all_time_series)

            return aggregated_ts

        except Exception as e:
            logger.error(f"Failed to extract time series for plan {plan_id}: {e}")
            return None

    def _extract_time_series_from_summary(
        self, case_id: str, batch_id: str, plan_id: str, seed: int
    ) -> Optional[Dict[str, List]]:
        """
        从单个仿真的summary.xml提取时序数据

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            plan_id: 方案ID
            seed: 随机种子

        Returns:
            Dict: 时序数据 {time: [...], running: [...], loaded: [...], ...}
            None: 文件不存在或解析失败
        """
        try:
            # 构建summary.xml路径
            sim_dir = (
                Path(self.cases_base_dir)
                / case_id
                / "simulations"
                / "plan_opti"
                / batch_id
                / plan_id
                / f"sim_{seed}"
            )
            summary_file = sim_dir / "summary.xml"

            if not summary_file.exists():
                logger.warning(f"Summary file not found: {summary_file}")
                return None

            # 解析XML
            tree = ET.parse(summary_file)
            root = tree.getroot()

            # 提取所有step元素
            steps = root.findall("step")

            if not steps:
                logger.warning(f"No steps found in {summary_file}")
                return None

            # 初始化数据列表
            time_data = []
            running_data = []
            loaded_data = []
            ended_data = []
            mean_speed_data = []

            # 提取每个时间步的数据
            for step in steps:
                time_val = float(step.get("time", 0.0))
                running_val = int(step.get("running", 0))
                loaded_val = int(step.get("loaded", 0))
                ended_val = int(step.get("ended", 0))
                speed_val = float(step.get("meanSpeed", 0.0))

                time_data.append(time_val)
                running_data.append(running_val)
                loaded_data.append(loaded_val)
                ended_data.append(ended_val)
                mean_speed_data.append(speed_val)

            logger.debug(f"Extracted {len(time_data)} time points from " f"{plan_id}/sim_{seed}")

            return {
                "time": time_data,
                "running": running_data,
                "loaded": loaded_data,
                "ended": ended_data,
                "mean_speed": mean_speed_data,
            }

        except Exception as e:
            logger.error(
                f"Failed to extract time series from summary.xml " f"({plan_id}/sim_{seed}): {e}"
            )
            return None

    def _aggregate_time_series(self, all_time_series: List[Dict[str, List]]) -> Dict[str, Any]:
        """
        聚合多次仿真的时序数据

        Args:
            all_time_series: 所有仿真的时序数据列表

        Returns:
            Dict: 聚合后的时序数据
        """
        import numpy as np

        if not all_time_series:
            return {}

        # 假设所有仿真的时间点相同（或取第一个作为参考）
        time_points = all_time_series[0]["time"]

        # 对每个指标计算mean/std/min/max
        metrics = ["running", "loaded", "ended", "mean_speed"]
        aggregated = {"time_points": time_points}

        for metric in metrics:
            # 收集所有仿真的该指标数据
            metric_data = []
            for ts in all_time_series:
                if metric in ts and len(ts[metric]) == len(time_points):
                    metric_data.append(ts[metric])

            if metric_data:
                # 转换为numpy数组方便计算
                data_array = np.array(metric_data)  # shape: (num_sims, num_time_points)

                aggregated[metric] = {
                    "mean": data_array.mean(axis=0).tolist(),
                    "std": data_array.std(axis=0).tolist(),
                    "min": data_array.min(axis=0).tolist(),
                    "max": data_array.max(axis=0).tolist(),
                }

        return aggregated

    def cancel_batch(self, case_id: str, batch_id: str) -> Dict[str, Any]:
        """
        取消批量仿真

        Args:
            case_id: 案例ID
            batch_id: 批次ID

        Returns:
            Dict: 取消响应数据

        Raises:
            FileNotFoundError: 批次不存在
        """
        logger.info(f"Cancelling batch {batch_id}")

        try:
            self.scheduler.cancel_batch(case_id, batch_id)

            response = {
                "batch_id": batch_id,
                "status": "cancelled",
                "cancelled_at": datetime.now().isoformat(),
            }

            logger.info(f"Batch {batch_id} cancelled")

            return response

        except FileNotFoundError as e:
            raise FileNotFoundError(f"批次不存在: {batch_id}") from e

    def delete_batch(self, case_id: str, batch_id: str) -> Dict[str, Any]:
        """
        删除批量仿真批次

        Args:
            case_id: 案例ID
            batch_id: 批次ID

        Returns:
            Dict: 删除响应数据

        Raises:
            FileNotFoundError: 批次不存在
        """
        logger.info(f"Deleting batch {batch_id}")

        batch_dir = Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / batch_id

        if not batch_dir.exists():
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        # 删除批次目录
        import shutil

        shutil.rmtree(batch_dir)

        response = {"batch_id": batch_id, "deleted": True, "deleted_at": datetime.now().isoformat()}

        logger.info(f"Batch {batch_id} deleted")

        return response


# 单例服务实例
batch_optimization_service = BatchOptimizationService()


# 导出服务函数（用于路由层调用）
def create_batch_service(
    case_id: str,
    plan_ids: List[str],
    num_seeds: int = 3,
    base_seed: int = 66,
    simulation_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """创建批量仿真批次服务函数"""
    return batch_optimization_service.create_batch(
        case_id=case_id,
        plan_ids=plan_ids,
        num_seeds=num_seeds,
        base_seed=base_seed,
        simulation_config=simulation_config,
    )


async def start_batch_service(case_id: str, batch_id: str, simulation_service) -> Dict[str, Any]:
    """启动批量仿真服务函数"""
    return await batch_optimization_service.start_batch(
        case_id=case_id, batch_id=batch_id, simulation_service=simulation_service
    )


def get_batch_progress_service(case_id: str, batch_id: str) -> Dict[str, Any]:
    """获取批次进度服务函数"""
    return batch_optimization_service.get_batch_progress(case_id, batch_id)


def get_batch_results_service(case_id: str, batch_id: str) -> Dict[str, Any]:
    """获取批次结果服务函数"""
    return batch_optimization_service.get_batch_results(case_id, batch_id)


def cancel_batch_service(case_id: str, batch_id: str) -> Dict[str, Any]:
    """取消批量仿真服务函数"""
    return batch_optimization_service.cancel_batch(case_id, batch_id)


def delete_batch_service(case_id: str, batch_id: str) -> Dict[str, Any]:
    """删除批量仿真服务函数"""
    return batch_optimization_service.delete_batch(case_id, batch_id)
