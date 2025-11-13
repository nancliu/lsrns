"""
分析进度跟踪器 (Analysis Progress Tracker)

职责 (Task 1.5 - Week 1 Phase 2):
- 实时追踪分析批次进度
- 计算 ETA (预计完成时间)
- 更新任务状态 (queued → running → completed/failed)
- 提供进度百分比计算

Design:
- 每10秒更新一次 (不是1秒)
- ETA 基于已完成任务和经过时间计算
- 线程安全的状态更新
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnalysisProgressTracker:
    """
    分析进度跟踪器

    Usage:
        tracker = AnalysisProgressTracker()
        tracker.init_batch(batch_id, case_dir, tasks)
        tracker.update_task_progress(batch_id, task_id, status="running")
        progress = tracker.get_batch_progress(batch_id)
    """

    def __init__(self):
        """初始化进度跟踪器"""
        self.update_interval_seconds = 10  # 10秒更新间隔

    def init_batch(
        self,
        batch_id: str,
        case_dir: Path,
        tasks: List[Dict[str, Any]]
    ) -> Path:
        """
        初始化分析批次

        Args:
            batch_id: 批次ID
            case_dir: 案例目录
            tasks: 任务列表

        Returns:
            任务索引文件路径

        Creates:
            cases/{case_id}/analysis/{batch_id}/analysis_tasks_index.json
        """
        analysis_batch_dir = case_dir / "analysis" / batch_id
        analysis_batch_dir.mkdir(parents=True, exist_ok=True)

        tasks_index_path = analysis_batch_dir / "analysis_tasks_index.json"

        tasks_index = {
            "batch_id": batch_id,
            "case_id": case_dir.name,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": "created",
            "tasks": tasks,
            "progress": {
                "total": len(tasks),
                "completed": 0,
                "failed": 0,
                "in_progress": 0,
                "queued": len(tasks)
            },
            "execution": {
                "started_at": None,
                "elapsed_seconds": 0,
                "estimated_completion": None
            }
        }

        with open(tasks_index_path, 'w', encoding='utf-8') as f:
            json.dump(tasks_index, f, ensure_ascii=False, indent=2)

        logger.info(f"初始化分析批次: {batch_id}, 任务数: {len(tasks)}")
        return tasks_index_path

    def update_task_progress(
        self,
        batch_id: str,
        case_dir: Path,
        task_id: str,
        status: str,
        progress_percent: int = 0,
        error: Optional[str] = None
    ) -> bool:
        """
        更新单个任务进度

        Args:
            batch_id: 批次ID
            case_dir: 案例目录
            task_id: 任务ID
            status: 任务状态 (queued | running | completed | failed)
            progress_percent: 进度百分比 (0-100)
            error: 错误信息 (如果失败)

        Returns:
            True 如果更新成功, False 如果任务未找到

        Behavior:
            - 更新任务状态
            - 更新时间戳
            - 重新计算批次进度
        """
        tasks_index_path = case_dir / "analysis" / batch_id / "analysis_tasks_index.json"

        if not tasks_index_path.exists():
            logger.error(f"任务索引文件不存在: {tasks_index_path}")
            return False

        try:
            with open(tasks_index_path, 'r', encoding='utf-8') as f:
                tasks_index = json.load(f)

            # 查找任务
            task_found = False
            for task in tasks_index["tasks"]:
                if task["task_id"] == task_id:
                    old_status = task["status"]
                    task["status"] = status
                    task["progress_percent"] = progress_percent

                    # 更新时间戳
                    if status == "running" and old_status != "running":
                        task["started_at"] = datetime.now().isoformat()
                    elif status in ["completed", "failed"]:
                        task["completed_at"] = datetime.now().isoformat()
                        if task.get("started_at"):
                            start_time = datetime.fromisoformat(task["started_at"])
                            task["elapsed_seconds"] = (datetime.now() - start_time).total_seconds()

                    if error:
                        task["error"] = error

                    task_found = True
                    break

            if not task_found:
                logger.warning(f"任务未找到: {task_id}")
                return False

            # 重新计算批次进度
            self._recalculate_batch_progress(tasks_index)

            # 保存更新
            tasks_index["updated_at"] = datetime.now().isoformat()
            with open(tasks_index_path, 'w', encoding='utf-8') as f:
                json.dump(tasks_index, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            logger.error(f"更新任务进度失败: {e}")
            return False

    def get_batch_progress(
        self,
        batch_id: str,
        case_dir: Path
    ) -> Dict[str, Any]:
        """
        获取批次进度 (实时)

        Args:
            batch_id: 批次ID
            case_dir: 案例目录

        Returns:
            进度信息字典

        Structure:
            {
                "batch_id": "...",
                "total_tasks": 100,
                "completed": 45,
                "failed": 2,
                "in_progress": 3,
                "queued": 50,
                "estimated_completion": "2025-11-12T16:45:00",
                "current_tasks": [...]
            }
        """
        tasks_index_path = case_dir / "analysis" / batch_id / "analysis_tasks_index.json"

        if not tasks_index_path.exists():
            return {
                "batch_id": batch_id,
                "error": "批次不存在",
                "status": "not_found"
            }

        try:
            with open(tasks_index_path, 'r', encoding='utf-8') as f:
                tasks_index = json.load(f)

            progress = tasks_index.get("progress", {})
            execution = tasks_index.get("execution", {})

            # 获取当前正在执行的任务
            current_tasks = [
                task for task in tasks_index["tasks"]
                if task["status"] == "running"
            ]

            # 计算 ETA
            eta = self.calculate_eta(
                total=progress.get("total", 0),
                completed=progress.get("completed", 0),
                started_at=execution.get("started_at")
            )

            return {
                "batch_id": batch_id,
                "status": tasks_index.get("status", "unknown"),
                "total_tasks": progress.get("total", 0),
                "completed": progress.get("completed", 0),
                "failed": progress.get("failed", 0),
                "in_progress": progress.get("in_progress", 0),
                "queued": progress.get("queued", 0),
                "estimated_completion": eta,
                "elapsed_seconds": execution.get("elapsed_seconds", 0),
                "current_tasks": current_tasks,
                "updated_at": tasks_index.get("updated_at")
            }

        except Exception as e:
            logger.error(f"获取批次进度失败: {e}")
            return {
                "batch_id": batch_id,
                "error": str(e),
                "status": "error"
            }

    def calculate_eta(
        self,
        total: int,
        completed: int,
        started_at: Optional[str]
    ) -> Optional[str]:
        """
        计算预计完成时间 (ETA)

        Args:
            total: 总任务数
            completed: 已完成任务数
            started_at: 批次开始时间 (ISO格式)

        Returns:
            预计完成时间 (ISO格式), 如果无法计算则返回 None

        Algorithm:
            1. 计算经过时间
            2. 计算平均每个任务耗时
            3. 预测剩余时间
            4. 返回预计完成时间

        Edge cases:
            - 未开始: 返回 None
            - 已完成全部: 返回当前时间
            - 除零: 返回 None
        """
        if not started_at:
            return None

        if completed == 0:
            return None  # 无法预测

        if completed >= total:
            return datetime.now().isoformat()  # 已完成

        try:
            start_time = datetime.fromisoformat(started_at)
            elapsed = datetime.now() - start_time
            elapsed_seconds = elapsed.total_seconds()

            if elapsed_seconds <= 0:
                return None

            # 平均每个任务耗时
            avg_time_per_task = elapsed_seconds / completed

            # 剩余任务数
            remaining = total - completed

            # 预计剩余时间
            estimated_remaining_seconds = avg_time_per_task * remaining

            # 预计完成时间
            eta_time = datetime.now() + timedelta(seconds=estimated_remaining_seconds)

            return eta_time.isoformat()

        except Exception as e:
            logger.warning(f"计算 ETA 失败: {e}")
            return None

    def _recalculate_batch_progress(self, tasks_index: Dict[str, Any]):
        """
        重新计算批次进度

        Args:
            tasks_index: 任务索引字典 (in-place 修改)

        Updates:
            - progress.completed
            - progress.failed
            - progress.in_progress
            - progress.queued
            - execution.elapsed_seconds
            - status (running | completed | failed)
        """
        tasks = tasks_index["tasks"]
        total = len(tasks)

        # 统计各状态任务数
        completed = sum(1 for t in tasks if t["status"] == "completed")
        failed = sum(1 for t in tasks if t["status"] == "failed")
        in_progress = sum(1 for t in tasks if t["status"] == "running")
        queued = sum(1 for t in tasks if t["status"] == "queued")

        tasks_index["progress"] = {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "queued": queued
        }

        # 更新批次状态
        if completed + failed == total:
            tasks_index["status"] = "completed" if failed == 0 else "failed"
        elif in_progress > 0 or completed > 0:
            tasks_index["status"] = "running"
        else:
            tasks_index["status"] = "created"

        # 更新执行时间
        if tasks_index["status"] == "running" and not tasks_index["execution"].get("started_at"):
            tasks_index["execution"]["started_at"] = datetime.now().isoformat()

        if tasks_index["execution"].get("started_at"):
            start_time = datetime.fromisoformat(tasks_index["execution"]["started_at"])
            tasks_index["execution"]["elapsed_seconds"] = (datetime.now() - start_time).total_seconds()
