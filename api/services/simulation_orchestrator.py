"""
仿真编排服务 (Simulation Orchestrator)

职责 (Task 1.1 - Week 1 Phase 2):
- 检测仿真来源 (事件场景 / OD提取 / 控制方案)
- 委派给合适的服务执行
- 提供统一的批量仿真接口

架构决策:
- Q1-C: 创建编排层,不修改现有服务
- Q2: 复用 BatchSimulationScheduler (共享层,已验证)
- Q3: 通过元数据版本实现向后兼容
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .base_service import BaseService
from .base_metadata_service import BaseMetadataService
from .simulation_service import SimulationService
from .batch_optimization_service import BatchOptimizationService
from shared.control_tools.batch_simulation_scheduler import BatchSimulationScheduler

logger = logging.getLogger(__name__)


class SimulationOrchestrator(BaseService):
    """
    仿真编排服务 - 统一批量仿真接口

    Design Decision Q1-C: 编排层模式
    - 检测仿真来源
    - 委派给合适的服务
    - 不修改现有服务接口

    Task 1.0 Integration: 使用 BaseMetadataService 进行版本检测
    """

    def __init__(self):
        """初始化编排服务"""
        super().__init__()

        # Task 1.0: 元数据服务 (支持版本检测)
        self.metadata_service = BaseMetadataService(self.cases_dir)

        # 现有服务 (不修改,仅委派)
        self.simulation_service = SimulationService()
        self.batch_optimization_service = BatchOptimizationService()

        # 复用 BatchSimulationScheduler (Q2: 复用经过验证的基础设施)
        self.batch_scheduler = BatchSimulationScheduler(
            base_dir=str(self.cases_dir),
            completion_callback=self._on_batch_completed
        )

    async def batch_start_simulations(
        self,
        simulation_ids: List[str],
        case_id: str,
        parallel_workers: int = 4,
        auto_run_analysis: bool = True,
        analysis_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        启动多个仿真 (统一接口)

        Args:
            simulation_ids: 仿真ID列表
            case_id: 案例ID
            parallel_workers: 并发工作线程数 (2-16)
            auto_run_analysis: 完成后自动运行分析
            analysis_types: 分析类型列表 (default: ["summary", "edgedata"])

        Returns:
            批量执行响应,包含 batch_id 和状态

        Process:
            1. 检测仿真来源 (Q3: 向后兼容)
            2. 委派给合适的服务
            3. 返回统一响应

        Design: PRINCIPLE-INTEGRATION-002 (工作流隔离)
        """
        if not simulation_ids:
            raise ValueError("仿真ID列表不能为空")

        if not case_id:
            raise ValueError("案例ID不能为空")

        # 默认分析类型
        if analysis_types is None:
            analysis_types = ["summary", "edgedata"]

        logger.info(f"批量启动仿真: {len(simulation_ids)} 个仿真, 并发数: {parallel_workers}, 案例: {case_id}")

        # Step 1: 检测仿真来源 (Task 1.0: 使用元数据服务)
        sim_source = self._detect_simulation_source(case_id, simulation_ids[0])
        logger.info(f"检测到仿真来源: {sim_source}")

        # Step 2: 委派给合适的服务
        if sim_source == "event-scenario":
            return await self._batch_start_event_scenarios(
                simulation_ids, case_id, parallel_workers, auto_run_analysis, analysis_types
            )
        elif sim_source == "control-plan":
            # 现有控制方案工作流 (不修改)
            logger.info("委派给 BatchOptimizationService")
            # 注意: BatchOptimizationService 使用不同的接口
            # 这里仅返回信息,实际调用在其他位置
            return {
                "source": "control-plan",
                "message": "Use BatchOptimizationService.start_batch() instead",
                "simulation_ids": simulation_ids,
                "case_id": case_id
            }
        else:
            # OD提取仿真 - 顺序执行 (现有工作流)
            return await self._batch_start_od_simulations(simulation_ids, case_id)

    def _detect_simulation_source(self, case_id: str, simulation_id: str) -> str:
        """
        检测仿真来源 (Q3: 向后兼容)

        Task 1.0 Integration: 使用 BaseMetadataService 的检测方法

        Args:
            case_id: 案例ID
            simulation_id: 仿真ID

        Returns:
            "event-scenario" | "control-plan" | "od-extraction"

        Implementation:
            - 使用 BaseMetadataService.get_simulation_source_type()
            - 检查元数据版本
            - 检测 source_scenario 字段
            - 检测 plan_id 字段
            - 空安全,不抛出异常
        """
        try:
            # 尝试从指定案例加载仿真元数据
            sim_metadata_path = (
                self.cases_dir / case_id / "simulations" / simulation_id / "simulation_metadata.json"
            )

            if not sim_metadata_path.exists():
                # 如果指定路径不存在,尝试搜索
                sim_metadata_path = self._find_simulation_metadata(simulation_id)

            if not sim_metadata_path:
                logger.warning(f"未找到仿真元数据: {case_id}/{simulation_id}, 默认为 OD 提取")
                return "od-extraction"

            # Task 1.0: 使用 BaseMetadataService 的安全加载方法
            metadata = self.metadata_service.load_metadata_safely(sim_metadata_path)

            # Task 1.0: 使用 BaseMetadataService 的来源检测方法
            source_type = self.metadata_service.get_simulation_source_type(metadata)

            logger.info(f"仿真来源检测: {case_id}/{simulation_id} → {source_type}")
            return source_type

        except Exception as e:
            logger.error(f"检测仿真来源失败: {case_id}/{simulation_id}, 错误: {e}")
            return "od-extraction"

    def _find_simulation_metadata(self, simulation_id: str) -> Optional[Path]:
        """
        查找仿真元数据文件

        Args:
            simulation_id: 仿真ID

        Returns:
            元数据文件路径,如果未找到则返回 None
        """
        # 搜索所有案例目录
        if not self.cases_dir.exists():
            return None

        for case_dir in self.cases_dir.iterdir():
            if not case_dir.is_dir():
                continue

            # 标准仿真路径
            sim_path = case_dir / "simulations" / simulation_id / "simulation_metadata.json"
            if sim_path.exists():
                return sim_path

            # 控制方案批量仿真路径
            plan_opti_dir = case_dir / "simulations" / "plan_opti"
            if plan_opti_dir.exists():
                for batch_dir in plan_opti_dir.iterdir():
                    for plan_dir in batch_dir.iterdir():
                        for sim_dir in plan_dir.iterdir():
                            metadata_path = sim_dir / "simulation_metadata.json"
                            if metadata_path.exists():
                                metadata = self.load_metadata(metadata_path)
                                if metadata.get("simulation_id") == simulation_id:
                                    return metadata_path

        return None

    async def _batch_start_event_scenarios(
        self,
        simulation_ids: List[str],
        case_id: str,
        parallel_workers: int,
        auto_run_analysis: bool,
        analysis_types: List[str]
    ) -> Dict[str, Any]:
        """
        批量启动事件场景仿真 (Q2: 复用 BatchSimulationScheduler)

        Args:
            simulation_ids: 仿真ID列表
            case_id: 案例ID
            parallel_workers: 并发数
            auto_run_analysis: 自动运行分析
            analysis_types: 分析类型列表

        Returns:
            批量执行响应

        Design: 复用现有基础设施,不重新实现
        """
        logger.info(f"启动事件场景仿真批次: {len(simulation_ids)} 个仿真, 案例: {case_id}")

        # 生成批次ID
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # TODO: 将事件场景结构转换为批量格式
        # TODO: 调用 BatchSimulationScheduler
        # 当前返回占位响应
        return {
            "batch_id": batch_id,
            "case_id": case_id,
            "simulation_ids": simulation_ids,
            "total_simulations": len(simulation_ids),
            "source": "event-scenario",
            "parallel_workers": parallel_workers,
            "auto_run_analysis": auto_run_analysis,
            "analysis_types": analysis_types,
            "status": "queued",
            "created_at": datetime.now().isoformat()
        }

    async def _batch_start_od_simulations(
        self,
        simulation_ids: List[str],
        case_id: str
    ) -> Dict[str, Any]:
        """
        批量启动 OD 提取仿真 (现有工作流)

        Args:
            simulation_ids: 仿真ID列表
            case_id: 案例ID

        Returns:
            批量执行响应

        Note: OD 提取仿真通常顺序执行,保持现有行为
        """
        logger.info(f"启动 OD 提取仿真: {len(simulation_ids)} 个仿真 (顺序执行), 案例: {case_id}")

        batch_id = f"batch_od_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # TODO: 调用 SimulationService.start_simulation() 顺序执行
        return {
            "batch_id": batch_id,
            "case_id": case_id,
            "simulation_ids": simulation_ids,
            "total_simulations": len(simulation_ids),
            "source": "od-extraction",
            "parallel_workers": 1,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "note": "OD simulations will be executed sequentially"
        }

    def _on_batch_completed(self, batch_id: str, results: Dict[str, Any]):
        """
        批次完成回调

        Args:
            batch_id: 批次ID
            results: 批次结果

        Design: 预留用于自动触发分析
        """
        logger.info(f"批次完成: {batch_id}, 结果: {results}")
        # TODO: 如果 auto_run_analysis=True, 触发 AnalysisOrchestrationService

    async def get_batch_execution_status(self, batch_id: str) -> Dict[str, Any]:
        """
        获取批次执行状态

        Args:
            batch_id: 批次ID

        Returns:
            批次状态信息

        TODO: 实现实时状态查询
        """
        logger.info(f"查询批次状态: {batch_id}")

        return {
            "batch_id": batch_id,
            "status": "unknown",
            "message": "Status tracking not yet implemented",
            "total": 0,
            "completed": 0,
            "failed": 0,
            "in_progress": 0,
            "queued": 0
        }


# 全局单例实例
_simulation_orchestrator_instance: Optional[SimulationOrchestrator] = None


def get_simulation_orchestrator() -> SimulationOrchestrator:
    """
    获取 SimulationOrchestrator 单例实例

    Returns:
        SimulationOrchestrator 单例实例

    Note:
        Task 1.1 Phase 2 Week 1
        使用工厂函数模式实现服务定位器
    """
    global _simulation_orchestrator_instance

    if _simulation_orchestrator_instance is None:
        _simulation_orchestrator_instance = SimulationOrchestrator()
        logger.info("初始化 SimulationOrchestrator 单例实例")

    return _simulation_orchestrator_instance
