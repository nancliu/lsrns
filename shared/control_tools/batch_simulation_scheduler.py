"""
批量仿真调度器

负责管理多方案×多随机种子的并行仿真任务执行
"""

import os
import json
import asyncio
import multiprocessing
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


def get_max_concurrent_simulations() -> int:
    """
    计算最大并发仿真数

    优先级：
    1. 环境变量 MAX_CONCURRENT_SIMULATIONS
    2. CPU线程数 * 0.75
    3. 最小值4，最大值80

    Returns:
        int: 最大并发仿真数
    """
    if env_value := os.getenv("MAX_CONCURRENT_SIMULATIONS"):
        try:
            value = int(env_value)
            return max(4, min(80, value))
        except ValueError:
            logger.warning(f"Invalid MAX_CONCURRENT_SIMULATIONS value: {env_value}")

    cpu_count = multiprocessing.cpu_count()
    concurrent = int(cpu_count * 0.75)
    result = max(4, min(80, concurrent))

    logger.info(f"Dynamic concurrency: {cpu_count} CPUs * 0.75 = {concurrent}, using {result}")
    return result


@dataclass
class BatchTask:
    """批量仿真任务数据类"""
    task_id: str
    plan_id: str
    plan_name: str
    seed: int
    status: str = "pending"  # pending, running, completed, failed
    simulation_id: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'BatchTask':
        """从字典创建"""
        return cls(**data)


class BatchSimulationScheduler:
    """批量仿真调度器"""

    def __init__(self, base_dir: str = "cases"):
        """
        初始化调度器

        Args:
            base_dir: 案例基础目录路径
        """
        self.base_dir = Path(base_dir)
        self.running_tasks: Dict[str, asyncio.Task] = {}  # task_id -> asyncio.Task
        self.semaphore: Optional[asyncio.Semaphore] = None

    def create_batch(
        self,
        case_id: str,
        plan_ids: List[str],
        plan_names: Dict[str, str],
        num_seeds: int = 3,
        base_seed: int = 66
    ) -> Tuple[str, Path]:
        """
        创建批量仿真批次

        Args:
            case_id: 案例ID
            plan_ids: 方案ID列表
            plan_names: 方案ID到名称的映射
            num_seeds: 每个方案的随机种子数量
            base_seed: 起始随机种子值

        Returns:
            (batch_id, batch_dir_path): 批次ID和批次目录路径
        """
        # 生成batch_id (格式: batch_YYYYMMDD_HHMMSS)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_id = f"batch_{timestamp}"

        # 创建批次目录
        batch_dir = self.base_dir / case_id / "simulations" / "plan_opti" / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        # 生成任务列表 (plans × seeds)
        tasks = []
        task_counter = 1

        for plan_id in plan_ids:
            plan_name = plan_names.get(plan_id, plan_id)

            for i in range(num_seeds):
                seed = base_seed + i
                task = BatchTask(
                    task_id=f"task_{task_counter:03d}",
                    plan_id=plan_id,
                    plan_name=plan_name,
                    seed=seed
                )
                tasks.append(task)
                task_counter += 1

        # 保存batch_metadata.json
        batch_metadata = {
            "batch_id": batch_id,
            "case_id": case_id,
            "plan_ids": plan_ids,
            "num_seeds": num_seeds,
            "base_seed": base_seed,
            "total_tasks": len(tasks),
            "status": "pending",
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None
        }

        metadata_path = batch_dir / "batch_metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(batch_metadata, f, ensure_ascii=False, indent=2)

        # 初始化batch_progress.json
        progress_data = {
            "batch_id": batch_id,
            "status": "pending",
            "progress": 0.0,
            "total_tasks": len(tasks),
            "completed_tasks": 0,
            "failed_tasks": 0,
            "running_tasks": 0,
            "tasks": [task.to_dict() for task in tasks],
            "updated_at": datetime.now().isoformat()
        }

        progress_path = batch_dir / "batch_progress.json"
        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Created batch {batch_id}: {len(plan_ids)} plans × {num_seeds} seeds = {len(tasks)} tasks"
        )

        return batch_id, batch_dir

    def get_batch_progress(self, case_id: str, batch_id: str) -> Dict:
        """
        获取批次进度

        Args:
            case_id: 案例ID
            batch_id: 批次ID

        Returns:
            dict: 批次进度数据
        """
        progress_path = (
            self.base_dir / case_id / "simulations" / "plan_opti" / batch_id / "batch_progress.json"
        )

        if not progress_path.exists():
            raise FileNotFoundError(f"Batch progress file not found: {progress_path}")

        with open(progress_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _update_batch_progress(
        self,
        case_id: str,
        batch_id: str,
        tasks: List[BatchTask],
        status: str
    ) -> None:
        """
        更新批次进度文件

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            tasks: 任务列表
            status: 批次状态
        """
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == "completed")
        failed = sum(1 for t in tasks if t.status == "failed")
        running = sum(1 for t in tasks if t.status == "running")

        progress = completed / total if total > 0 else 0.0

        progress_data = {
            "batch_id": batch_id,
            "status": status,
            "progress": progress,
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "running_tasks": running,
            "tasks": [task.to_dict() for task in tasks],
            "updated_at": datetime.now().isoformat()
        }

        progress_path = (
            self.base_dir / case_id / "simulations" / "plan_opti" / batch_id / "batch_progress.json"
        )

        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)

    async def start_batch(
        self,
        case_id: str,
        batch_id: str,
        simulation_service  # Type hint would be circular, use duck typing
    ) -> None:
        """
        启动批量仿真（异步执行）

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            simulation_service: 仿真服务实例（用于调用prepare/start）
        """
        # 读取批次进度
        progress_data = self.get_batch_progress(case_id, batch_id)
        tasks = [BatchTask.from_dict(t) for t in progress_data["tasks"]]

        # 更新批次状态为running
        batch_dir = self.base_dir / case_id / "simulations" / "plan_opti" / batch_id
        metadata_path = batch_dir / "batch_metadata.json"

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        metadata["status"] = "running"
        metadata["started_at"] = datetime.now().isoformat()

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 初始化并发控制
        max_concurrent = get_max_concurrent_simulations()
        self.semaphore = asyncio.Semaphore(max_concurrent)

        logger.info(f"Starting batch {batch_id} with max {max_concurrent} concurrent tasks")

        # 创建所有任务的协程
        async_tasks = []
        for task in tasks:
            if task.status == "pending":
                async_task = self._run_task(
                    case_id=case_id,
                    batch_id=batch_id,
                    task=task,
                    tasks_list=tasks,
                    simulation_service=simulation_service
                )
                async_tasks.append(async_task)

        # 并行执行所有任务
        if async_tasks:
            await asyncio.gather(*async_tasks, return_exceptions=True)

        # 更新批次最终状态
        all_completed = all(t.status in ["completed", "failed"] for t in tasks)
        any_failed = any(t.status == "failed" for t in tasks)

        if all_completed:
            final_status = "failed" if any_failed else "completed"
            metadata["status"] = final_status
            metadata["completed_at"] = datetime.now().isoformat()

            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            self._update_batch_progress(case_id, batch_id, tasks, final_status)

            logger.info(f"Batch {batch_id} {final_status}: {len(tasks)} tasks processed")

    async def _run_task(
        self,
        case_id: str,
        batch_id: str,
        task: BatchTask,
        tasks_list: List[BatchTask],
        simulation_service
    ) -> None:
        """
        运行单个仿真任务（带并发控制）

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            task: 任务对象
            tasks_list: 所有任务列表（用于更新进度）
            simulation_service: 仿真服务实例
        """
        async with self.semaphore:  # 并发控制
            try:
                # 更新任务状态为running
                task.status = "running"
                task.started_at = datetime.now().isoformat()
                self._update_batch_progress(case_id, batch_id, tasks_list, "running")

                logger.info(f"Starting task {task.task_id}: {task.plan_name} (seed={task.seed})")

                # 创建仿真目录
                sim_dir = (
                    self.base_dir / case_id / "simulations" / "plan_opti" / batch_id /
                    task.plan_id / f"sim_{task.seed}"
                )
                sim_dir.mkdir(parents=True, exist_ok=True)

                # TODO: 实际调用simulation_service的prepare和start方法
                # 这里需要等待Task 2.6完成集成
                # 暂时模拟成功
                await asyncio.sleep(0.5)  # 模拟仿真耗时

                # 更新任务状态为completed
                task.status = "completed"
                task.completed_at = datetime.now().isoformat()
                task.simulation_id = f"sim_{batch_id}_{task.task_id}"

                logger.info(f"Completed task {task.task_id}")

            except Exception as e:
                # 更新任务状态为failed
                task.status = "failed"
                task.completed_at = datetime.now().isoformat()
                task.error = str(e)

                logger.error(f"Failed task {task.task_id}: {e}", exc_info=True)

            finally:
                # 更新进度
                self._update_batch_progress(case_id, batch_id, tasks_list, "running")

    def cancel_batch(self, case_id: str, batch_id: str) -> None:
        """
        取消批量仿真（取消所有pending任务）

        Args:
            case_id: 案例ID
            batch_id: 批次ID
        """
        progress_data = self.get_batch_progress(case_id, batch_id)
        tasks = [BatchTask.from_dict(t) for t in progress_data["tasks"]]

        # 取消所有pending任务
        cancelled_count = 0
        for task in tasks:
            if task.status == "pending":
                task.status = "failed"
                task.error = "Cancelled by user"
                cancelled_count += 1

        # 更新批次状态
        batch_dir = self.base_dir / case_id / "simulations" / "plan_opti" / batch_id
        metadata_path = batch_dir / "batch_metadata.json"

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        metadata["status"] = "failed"
        metadata["completed_at"] = datetime.now().isoformat()

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        self._update_batch_progress(case_id, batch_id, tasks, "failed")

        logger.info(f"Cancelled batch {batch_id}: {cancelled_count} tasks cancelled")

    def _calculate_estimated_completion(
        self,
        tasks: List[BatchTask],
        avg_task_duration_seconds: float = 300.0
    ) -> Optional[str]:
        """
        计算预计完成时间

        Args:
            tasks: 任务列表
            avg_task_duration_seconds: 平均任务耗时（秒）

        Returns:
            Optional[str]: ISO格式的预计完成时间，如果无法计算则返回None
        """
        pending_count = sum(1 for t in tasks if t.status == "pending")
        running_count = sum(1 for t in tasks if t.status == "running")

        if pending_count == 0 and running_count == 0:
            return None

        # 粗略估算：(pending + running) * avg_duration / max_concurrent
        max_concurrent = get_max_concurrent_simulations()
        remaining_tasks = pending_count + running_count
        estimated_seconds = (remaining_tasks * avg_task_duration_seconds) / max_concurrent

        estimated_time = datetime.now().timestamp() + estimated_seconds
        return datetime.fromtimestamp(estimated_time).isoformat()
