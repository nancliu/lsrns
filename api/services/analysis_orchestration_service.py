"""
分析编排服务 (Analysis Orchestration Service)

职责 (Task 1.2 - Week 1 Phase 2):
- 为事件场景仿真创建分析批次
- 复用 SummaryAnalyzer 和 EdgeDataAnalyzer (共享层)
- 提供实时进度跟踪
- 存储带场景溯源的分析结果

架构决策:
- Q8: 不使用 OD 分析服务 (accuracy/mechanism/performance/edgedata_service)
- Q9: 不修改现有服务 - 创建适配层
- 复用: SummaryAnalyzer, EdgeDataAnalyzer (shared/analysis_tools/)
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from .base_service import BaseService
from shared.analysis_tools.batch_result_analyzer import BatchResultAnalyzer

logger = logging.getLogger(__name__)


class AnalysisOrchestrationService(BaseService):
    """
    分析编排服务 - 适配层

    Design Decision Q9-A: 不修改现有分析服务
    - 创建适配层复用批量分析工具
    - 转换事件场景结构为批量格式
    - 存储带场景溯源的结果
    """

    def __init__(self):
        """初始化分析编排服务"""
        super().__init__()

        # 复用共享层分析器 (Q9: 不修改,仅复用)
        self.batch_result_analyzer = BatchResultAnalyzer()

    async def create_analysis_batch(
        self,
        simulation_ids: List[str],
        case_id: str,
        baseline_scenario_id: str,
        comparison_scenario_id: Optional[str] = None,
        analysis_focus: List[str] = None,
        parallel_workers: int = 4
    ) -> Dict[str, Any]:
        """
        创建分析批次 (事件场景仿真)

        Args:
            simulation_ids: 仿真ID列表
            case_id: 案例ID
            baseline_scenario_id: 基线场景ID (用于对比)
            comparison_scenario_id: 对比场景ID (可选)
            analysis_focus: 分析类型列表 (默认: ["summary", "edgedata"])
            parallel_workers: 并发工作线程数 (2-8)

        Returns:
            分析批次响应,包含 batch_id 和任务队列

        Process:
            1. 验证所有仿真ID存在且已完成
            2. 创建分析元数据
            3. 队列分析任务
            4. 返回 batch_id 用于进度跟踪
            5. 后台启动执行器

        Design: 适配器模式 (Q8, Q9)
        """
        if not simulation_ids:
            raise ValueError("仿真ID列表不能为空")

        if analysis_focus is None:
            analysis_focus = ["summary", "edgedata"]  # 默认分析类型

        logger.info(
            f"创建分析批次: 案例={case_id}, "
            f"仿真数={len(simulation_ids)}, "
            f"分析类型={analysis_focus}"
        )

        # Step 1: 验证仿真
        valid_simulations = self._validate_simulations(simulation_ids, case_id)
        if not valid_simulations:
            raise ValueError("没有找到有效的已完成仿真")

        # Step 2: 生成批次ID
        batch_id = f"analysis_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Step 3: 创建分析元数据
        case_dir = self.cases_dir / case_id
        analysis_batch_dir = case_dir / "analysis" / batch_id
        self.ensure_directory(analysis_batch_dir)

        metadata = self._create_analysis_batch_metadata(
            batch_id=batch_id,
            case_id=case_id,
            simulation_ids=valid_simulations,
            baseline_scenario_id=baseline_scenario_id,
            comparison_scenario_id=comparison_scenario_id,
            analysis_focus=analysis_focus,
            parallel_workers=parallel_workers
        )

        # Step 4: 保存元数据
        metadata_path = analysis_batch_dir / "analysis_metadata.json"
        self.save_metadata(metadata_path, metadata)

        # Step 5: 创建任务队列
        tasks = self._create_task_queue(
            simulation_ids=valid_simulations,
            analysis_focus=analysis_focus
        )

        # Step 6: 保存任务队列
        tasks_path = analysis_batch_dir / "analysis_tasks_index.json"
        self._save_tasks_index(tasks_path, batch_id, case_id, tasks)

        logger.info(f"分析批次已创建: {batch_id}, 任务数: {len(tasks)}")

        return {
            "batch_id": batch_id,
            "case_id": case_id,
            "total_tasks": len(tasks),
            "simulation_ids": valid_simulations,
            "analysis_focus": analysis_focus,
            "status": "created",
            "created_at": datetime.now().isoformat()
        }

    async def get_analysis_progress(self, batch_id: str) -> Dict[str, Any]:
        """
        获取分析批次进度 (实时监控)

        Args:
            batch_id: 分析批次ID

        Returns:
            进度信息字典

        Real-time updates (每10秒):
            - total_tasks: 总任务数
            - completed: 已完成
            - failed: 失败
            - in_progress: 进行中
            - queued: 等待中
            - estimated_completion: 预计完成时间
            - current_tasks: 当前任务列表

        TODO: 实现实时进度跟踪
        """
        logger.info(f"查询分析进度: {batch_id}")

        # TODO: 从 analysis_tasks_index.json 读取任务状态
        return {
            "batch_id": batch_id,
            "total_tasks": 0,
            "completed": 0,
            "failed": 0,
            "in_progress": 0,
            "queued": 0,
            "estimated_completion": None,
            "current_tasks": [],
            "status": "unknown",
            "message": "Progress tracking not yet implemented"
        }

    async def cancel_analysis_batch(self, batch_id: str) -> Dict[str, Any]:
        """
        取消分析批次 (优雅停止)

        Args:
            batch_id: 批次ID

        Returns:
            取消结果

        Behavior:
            - 允许进行中的任务完成
            - 停止队列新任务
            - 更新批次状态为 "cancelled"
        """
        logger.info(f"取消分析批次: {batch_id}")

        return {
            "batch_id": batch_id,
            "status": "cancelled",
            "message": "Batch cancellation not yet implemented"
        }

    def _validate_simulations(
        self,
        simulation_ids: List[str],
        case_id: str
    ) -> List[str]:
        """
        验证仿真是否存在且已完成

        Args:
            simulation_ids: 仿真ID列表
            case_id: 案例ID

        Returns:
            有效的仿真ID列表
        """
        valid_simulations = []
        case_dir = self.cases_dir / case_id

        for sim_id in simulation_ids:
            sim_dir = case_dir / "simulations" / sim_id
            if not sim_dir.exists():
                logger.warning(f"仿真目录不存在: {sim_id}")
                continue

            # 检查仿真是否完成 (存在 summary.xml)
            summary_file = sim_dir / "outputs" / "summary.xml"
            if not summary_file.exists():
                logger.warning(f"仿真未完成 (缺少 summary.xml): {sim_id}")
                continue

            valid_simulations.append(sim_id)

        logger.info(f"验证结果: {len(valid_simulations)}/{len(simulation_ids)} 个仿真有效")
        return valid_simulations

    def _create_analysis_batch_metadata(
        self,
        batch_id: str,
        case_id: str,
        simulation_ids: List[str],
        baseline_scenario_id: str,
        comparison_scenario_id: Optional[str],
        analysis_focus: List[str],
        parallel_workers: int
    ) -> Dict[str, Any]:
        """
        创建分析批次元数据 (Level 3: Analysis Metadata)

        Design: AD-12 三级元数据追踪
        """
        # 从第一个仿真获取 source_scenario (如果存在)
        source_scenario = self._get_source_scenario_from_simulation(
            simulation_ids[0], case_id
        )

        return {
            "metadata_version": "2.0",
            "analysis_batch_id": batch_id,
            "case_id": case_id,
            "simulation_ids": simulation_ids,
            "created_at": datetime.now().isoformat(),

            # 场景溯源 (AD-12: 完整可追溯链)
            "source_scenario": source_scenario,
            "baseline_scenario_id": baseline_scenario_id,
            "comparison_scenario_id": comparison_scenario_id,

            # 分析配置
            "analysis_config": {
                "analysis_types": analysis_focus,
                "parallel_workers": parallel_workers
            },

            # 执行状态
            "execution": {
                "status": "created",
                "started_at": None,
                "completed_at": None,
                "elapsed_seconds": None
            },

            # 结果汇总 (分析完成后填充)
            "results_summary": {}
        }

    def _get_source_scenario_from_simulation(
        self,
        simulation_id: str,
        case_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        从仿真元数据获取 source_scenario

        Args:
            simulation_id: 仿真ID
            case_id: 案例ID

        Returns:
            source_scenario 字典,如果不存在则返回 None
        """
        try:
            case_dir = self.cases_dir / case_id
            sim_metadata_path = case_dir / "simulations" / simulation_id / "simulation_metadata.json"

            if not sim_metadata_path.exists():
                return None

            metadata = self.load_metadata(sim_metadata_path)
            return metadata.get("source_scenario")

        except Exception as e:
            logger.warning(f"无法获取 source_scenario: {e}")
            return None

    def _create_task_queue(
        self,
        simulation_ids: List[str],
        analysis_focus: List[str]
    ) -> List[Dict[str, Any]]:
        """
        创建分析任务队列

        Args:
            simulation_ids: 仿真ID列表
            analysis_focus: 分析类型列表

        Returns:
            任务列表

        Task structure:
            - task_id: 唯一任务ID
            - simulation_id: 仿真ID
            - analysis_type: 分析类型
            - status: queued | running | completed | failed
            - progress_percent: 0-100
        """
        tasks = []
        task_counter = 1

        for sim_id in simulation_ids:
            for analysis_type in analysis_focus:
                task = {
                    "task_id": f"task_{task_counter:04d}",
                    "simulation_id": sim_id,
                    "analysis_type": analysis_type,
                    "status": "queued",
                    "progress_percent": 0,
                    "started_at": None,
                    "completed_at": None,
                    "elapsed_seconds": None,
                    "error": None
                }
                tasks.append(task)
                task_counter += 1

        return tasks

    def _save_tasks_index(
        self,
        tasks_path: Path,
        batch_id: str,
        case_id: str,
        tasks: List[Dict[str, Any]]
    ):
        """
        保存任务索引文件

        Args:
            tasks_path: 任务索引文件路径
            batch_id: 批次ID
            case_id: 案例ID
            tasks: 任务列表
        """
        tasks_index = {
            "batch_id": batch_id,
            "case_id": case_id,
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
            }
        }

        self.save_metadata(tasks_path, tasks_index)

    # ===== Adapter Methods (Q9: 转换事件场景结构为批量格式) =====

    def _convert_to_batch_format(
        self,
        simulation_ids: List[str],
        case_id: str
    ) -> Dict[str, Any]:
        """
        将事件场景仿真结构转换为批量分析格式

        Args:
            simulation_ids: 仿真ID列表
            case_id: 案例ID

        Returns:
            批量格式配置

        Design: 适配器模式 (Q9)
        - 转换目录结构
        - 准备分析器输入
        - 不修改 SummaryAnalyzer/EdgeDataAnalyzer
        """
        # TODO: 实现格式转换
        return {
            "case_id": case_id,
            "simulation_ids": simulation_ids,
            "format": "batch"
        }
