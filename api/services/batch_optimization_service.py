"""
批量优化仿真服务

职责：
- 批量仿真批次的创建和管理
- 协调batch_simulation_scheduler执行
- 结果汇总和统计分析 (Phase 2: BatchResultAnalyzer集成)
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
from shared.analysis_tools.batch_result_analyzer import BatchResultAnalyzer

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
        self.scheduler = BatchSimulationScheduler(
            base_dir=CASES_BASE_DIR,
            completion_callback=self._on_batch_completed
        )

    @staticmethod
    def _output_level_to_config(output_level: str) -> Dict[str, bool]:
        """
        将旧的output_level映射到新的output_config格式
        向后兼容函数（P0-1: 使用新的output_*键名）
        """
        level_map = {
            'minimal': {
                'output_tripinfo': False,
                'output_vehroute': False,
                'output_netstate': False,
                'output_fcd': False,
                'output_emission': False,
                'output_edgedata': False,
            },
            'standard': {
                'output_tripinfo': True,
                'output_vehroute': True,
                'output_netstate': True,
                'output_fcd': True,
                'output_emission': True,
                'output_edgedata': True,
            },
            'full': {
                'output_tripinfo': True,
                'output_vehroute': True,
                'output_netstate': True,
                'output_fcd': True,
                'output_emission': True,
                'output_edgedata': True,
            }
        }
        return level_map.get(output_level, level_map['standard'])

    @staticmethod
    def validate_batch_output_config(batch_dir: Path, config: Dict[str, Any]) -> tuple[bool, str]:
        """
        验证批次输出配置一致性 (Phase 3 T3.3: 配置一致性验证)

        检查批次中所有任务都使用相同的输出配置，防止配置漂移

        Args:
            batch_dir: 批次目录路径
            config: 预期的统一配置 (来自 simulation_config.json)

        Returns:
            tuple: (is_valid: bool, message: str)
                - is_valid=True: 配置一致，消息为成功提示
                - is_valid=False: 配置不一致，消息为错误详情
        """
        try:
            # 检查 simulation_config.json 存在且可解析
            config_file = batch_dir / "simulation_config.json"
            if not config_file.exists():
                return False, f"Batch configuration file missing: {config_file}"

            with open(config_file, 'r', encoding='utf-8') as f:
                stored_config = json.load(f)

            logger.info(f"Validating batch config consistency in {batch_dir}")

            # 验证关键配置字段存在
            required_fields = ['output_tripinfo', 'output_vehroute', 'output_netstate',
                              'output_fcd', 'output_emission', 'output_edgedata']

            for field in required_fields:
                if field not in stored_config:
                    return False, f"Missing required config field: {field}"

            # 验证存储的配置与预期配置匹配
            for field in required_fields:
                if stored_config.get(field) != config.get(field):
                    return False, (
                        f"Configuration mismatch for {field}: "
                        f"expected={config.get(field)}, stored={stored_config.get(field)}"
                    )

            # 检查 simulation_duration 一致性（如果存在）
            if 'simulation_duration' in config:
                stored_duration = stored_config.get('simulation_duration')
                if stored_duration != config['simulation_duration']:
                    return False, (
                        f"Simulation duration mismatch: "
                        f"expected={config['simulation_duration']}, stored={stored_duration}"
                    )

            # 验证种子配置一致性（Phase 5）
            if 'num_seeds' in config:
                stored_seeds = stored_config.get('num_seeds')
                if stored_seeds != config['num_seeds']:
                    return False, f"num_seeds mismatch: expected={config['num_seeds']}, stored={stored_seeds}"

            if 'base_seed' in config:
                stored_base = stored_config.get('base_seed')
                if stored_base != config['base_seed']:
                    return False, f"base_seed mismatch: expected={config['base_seed']}, stored={stored_base}"

            logger.info(f"Batch output config validation PASSED for {batch_dir}")
            return True, "Batch configuration is consistent across all tasks"

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in simulation_config.json: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error validating batch config: {str(e)}"

    def create_batch(
        self,
        case_id: str,
        plan_ids: List[str],
        num_seeds: int = 3,
        base_seed: int = 66,
        output_config: Optional[Dict[str, Any]] = None,
        output_level: Optional[str] = None,
        simulation_config: Optional[Dict[str, Any]] = None,
        simulation_duration: Optional[Dict[str, int]] = None,
        edgedata_use_template_edges: Optional[bool] = False,
    ) -> Dict[str, Any]:
        """
        创建批量仿真批次 (P1-2: 支持simulation_duration) (P2-2: 支持edgedata_use_template_edges)

        Args:
            case_id: 案例ID
            plan_ids: 方案ID列表（必须包含baseline_plan）
            num_seeds: 每个方案的随机种子数量
            base_seed: 起始随机种子值
            output_config: 仿真输出配置 (Phase 1新增)
            output_level: 仿真输出级别（已弃用，保留向后兼容）
            simulation_config: 仿真配置参数（可选）
            simulation_duration: 自定义仿真时长（P1-2新增）
                格式: {hours: int, minutes: int, total_minutes: int}
            edgedata_use_template_edges: EdgeData是否保留模板edges属性（P2-2新增，默认False）

        Returns:
            Dict: 批次创建响应数据

        Raises:
            ValueError: 验证失败
            FileNotFoundError: 案例或方案不存在
        """
        logger.info(f"Creating batch for case {case_id} with {len(plan_ids)} plans")

        # 1. 处理output_config和output_level（优先使用output_config）(P0-2: 扩展output_config支持所有输出参数)
        if output_config is None:
            output_config = self._output_level_to_config(output_level or "standard")
        else:
            # 转换Pydantic模型或dict为标准dict格式
            if hasattr(output_config, 'model_dump'):
                # Pydantic v2 模型
                output_config_dict = output_config.model_dump()
            elif hasattr(output_config, 'dict'):
                # Pydantic v1 模型
                output_config_dict = output_config.dict()
            else:
                # 已经是dict
                output_config_dict = output_config

            # 确保它包含所有必需字段（支持新的output_*键名）
            output_config = {
                'output_tripinfo': output_config_dict.get('output_tripinfo', output_config_dict.get('tripinfo_xml', False)),
                'output_vehroute': output_config_dict.get('output_vehroute', False),
                'output_netstate': output_config_dict.get('output_netstate', False),
                'output_fcd': output_config_dict.get('output_fcd', False),
                'output_emission': output_config_dict.get('output_emission', False),
                'output_edgedata': output_config_dict.get('output_edgedata', output_config_dict.get('edgedata_xml', False))
            }

        logger.info(f"Using output_config: {output_config}")

        # 2. 验证case_id存在
        case_dir = Path(self.cases_base_dir) / case_id
        if not case_dir.exists():
            raise FileNotFoundError(f"案例不存在: {case_id}")

        # 3. 验证所有plan_ids存在
        plan_names = {}
        for plan_id in plan_ids:
            try:
                plan_metadata = plan_file_manager.get_plan(plan_id)
                plan_names[plan_id] = plan_metadata["plan_name"]
            except FileNotFoundError:
                raise FileNotFoundError(f"方案不存在: {plan_id}")

        # 4. 确保包含baseline_plan (Phase 4: 基准方案强制包含)
        if BASELINE_PLAN_ID not in plan_ids:
            logger.warning(f"Baseline plan not in list, adding it automatically")
            plan_ids.insert(0, BASELINE_PLAN_ID)
            plan_names[BASELINE_PLAN_ID] = "基准方案（无管控）"

        # 5. 创建批次
        batch_id, batch_dir = self.scheduler.create_batch(
            case_id=case_id,
            plan_ids=plan_ids,
            plan_names=plan_names,
            num_seeds=num_seeds,
            base_seed=base_seed,
            simulation_duration=simulation_duration,
            output_config=output_config,
            output_level=output_level,
        )

        # 6. 生成统一的仿真配置 (P1-2: 支持simulation_duration) (P0-1: 修复键名映射) (P0-2: 从output_config读取) (P2-2: 支持edgedata_use_template_edges)
        unified_simulation_config = {
            "output_level": output_level,
            "num_seeds": num_seeds,
            "base_seed": base_seed,
            "seed_sequence": list(range(base_seed, base_seed + num_seeds)),
            # 从output_config读取输出参数配置
            "output_tripinfo": output_config.get('output_tripinfo', False),
            "output_vehroute": output_config.get('output_vehroute', False),
            "output_netstate": output_config.get('output_netstate', False),
            "output_fcd": output_config.get('output_fcd', False),
            "output_emission": output_config.get('output_emission', False),
            "output_edgedata": output_config.get('output_edgedata', False),
            "edgedata_use_template_edges": edgedata_use_template_edges,
            "created_at": datetime.now().isoformat()
        }

        # P1-2: 保存simulation_duration到配置中（如果提供）
        if simulation_duration:
            logger.info(f"Adding custom simulation_duration: {simulation_duration}")
            unified_simulation_config['simulation_duration'] = simulation_duration

        # 7. 保存统一的仿真配置到batch目录
        config_path = batch_dir / "simulation_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(unified_simulation_config, f, ensure_ascii=False, indent=2)

        logger.info(f"Unified simulation config saved: {config_path}")

        # 8. 如果提供了额外的simulation_config，合并它
        if simulation_config:
            # 不覆盖关键的输出配置，但允许其他参数
            unified_simulation_config.update(simulation_config)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(unified_simulation_config, f, ensure_ascii=False, indent=2)

        # P0-3: 构造simulation_params (包含所有输出参数) (P1-2: 包含simulation_duration) (P2-2: 包含edgedata_use_template_edges)
        simulation_params = {
            'output_tripinfo': unified_simulation_config.get('output_tripinfo', False),
            'output_vehroute': unified_simulation_config.get('output_vehroute', False),
            'output_netstate': unified_simulation_config.get('output_netstate', False),
            'output_fcd': unified_simulation_config.get('output_fcd', False),
            'output_emission': unified_simulation_config.get('output_emission', False),
            'output_edgedata': unified_simulation_config.get('output_edgedata', False),
            'edgedata_use_template_edges': edgedata_use_template_edges,
        }

        # P1-2: 添加simulation_duration到simulation_params（如果提供）
        if simulation_duration:
            simulation_params['simulation_duration'] = simulation_duration
            logger.info(f"Added simulation_duration to simulation_params: {simulation_duration}")

        # 保存simulation_params到unified_simulation_config中
        unified_simulation_config['simulation_params'] = simulation_params
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(unified_simulation_config, f, ensure_ascii=False, indent=2)

        logger.info(f"Simulation params constructed and saved: {simulation_params}")

        # 8.5. 验证批次输出配置一致性 (Phase 3 T3.3: 配置验证)
        validation_config = {
            'output_tripinfo': unified_simulation_config.get('output_tripinfo', False),
            'output_vehroute': unified_simulation_config.get('output_vehroute', False),
            'output_netstate': unified_simulation_config.get('output_netstate', False),
            'output_fcd': unified_simulation_config.get('output_fcd', False),
            'output_emission': unified_simulation_config.get('output_emission', False),
            'output_edgedata': unified_simulation_config.get('output_edgedata', False),
        }
        if simulation_duration:
            validation_config['simulation_duration'] = simulation_duration
        if 'num_seeds' in unified_simulation_config:
            validation_config['num_seeds'] = unified_simulation_config['num_seeds']
        if 'base_seed' in unified_simulation_config:
            validation_config['base_seed'] = unified_simulation_config['base_seed']

        is_valid, validation_message = self.validate_batch_output_config(batch_dir, validation_config)
        if not is_valid:
            logger.error(f"Batch output config validation FAILED: {validation_message}")
            raise ValueError(f"Batch configuration validation failed: {validation_message}")
        logger.info(f"Batch output config validation PASSED: {validation_message}")

        # 9. 构建响应
        total_tasks = len(plan_ids) * num_seeds

        response = {
            "batch_id": batch_id,
            "case_id": case_id,
            "plan_ids": plan_ids,
            "total_tasks": total_tasks,
            "num_seeds": num_seeds,
            "base_seed": base_seed,
            "output_level": output_level,
            "simulation_duration": simulation_duration,
            "output_config": output_config,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }

        # 10. 更新批次索引 (Phase 3: 包含output_level信息)
        batch_metadata = {
            "batch_id": batch_id,
            "case_id": case_id,
            "plan_ids": plan_ids,
            "total_tasks": total_tasks,
            "num_seeds": num_seeds,
            "base_seed": base_seed,
            "output_level": output_level,  # Phase 3新增
            "output_config": output_config,  # 详细输出配置
            "simulation_duration": simulation_duration,  # P1新增: 仿真时长配置
            "max_concurrent": 1,  # 默认并发数
            "status": "pending",
            "created_at": response["created_at"],
        }
        self._update_batches_index_on_create(case_id, batch_metadata)

        # 批次创建完成日志 - 输出完整的批次信息
        logger.info("=" * 80)
        logger.info("✓ 批次创建成功 (Batch Created Successfully)")
        logger.info("=" * 80)
        logger.info("")
        logger.info("【批次基础信息 (Batch Basic Info)】")
        logger.info(f"  批次ID (Batch ID):           {batch_id}")
        logger.info(f"  案例ID (Case ID):            {case_id}")
        logger.info(f"  批次状态 (Status):            {response['status']}")
        logger.info(f"  创建时间 (Created At):        {response['created_at']}")
        logger.info("")
        logger.info("【方案配置 (Plans Configuration)】")
        logger.info(f"  方案数量 (Number of Plans):   {len(plan_ids)}")
        logger.info(f"  方案ID列表 (Plan IDs):")
        for idx, plan_id in enumerate(plan_ids, 1):
            plan_name = plan_names.get(plan_id, "Unknown")
            logger.info(f"    [{idx}] {plan_id} - {plan_name}")
        logger.info("")
        logger.info("【种子配置 (Seed Configuration - Phase 5)】")
        logger.info(f"  每方案种子数 (num_seeds):    {num_seeds}")
        logger.info(f"  基础种子值 (base_seed):       {base_seed}")
        logger.info(f"  种子序列 (seed_sequence):     {list(range(base_seed, base_seed + num_seeds))}")
        logger.info(f"  总任务数 (Total Tasks):       {total_tasks} ({len(plan_ids)} plans × {num_seeds} seeds)")
        logger.info("")
        logger.info("【输出配置 (Output Configuration - Phase 3)】")
        logger.info(f"  输出级别 (Output Level):      {output_level or 'standard'}")
        logger.info(f"  tripinfo输出 (tripinfo_xml):  {output_config.get('output_tripinfo', False)}")
        logger.info(f"  vehroute输出 (vehroute):      {output_config.get('output_vehroute', False)}")
        logger.info(f"  netstate输出 (netstate):      {output_config.get('output_netstate', False)}")
        logger.info(f"  FCD输出 (fcd):                {output_config.get('output_fcd', False)}")
        logger.info(f"  排放数据输出 (emission):      {output_config.get('output_emission', False)}")
        logger.info(f"  edgedata输出 (edgedata_xml):  {output_config.get('output_edgedata', False)}")
        logger.info(f"  edgedata保留edges属性:        {edgedata_use_template_edges}")
        if simulation_duration:
            logger.info("")
            logger.info("【仿真时长 (Simulation Duration - Phase 1)】")
            logger.info(f"  小时 (Hours):                 {simulation_duration.get('hours', 0)}")
            logger.info(f"  分钟 (Minutes):               {simulation_duration.get('minutes', 0)}")
            logger.info(f"  总时长 (Total Minutes):       {simulation_duration.get('total_minutes', 0)}")
        logger.info("")
        logger.info("【批次目录 (Batch Directory)】")
        logger.info(f"  {batch_dir}")
        logger.info("=" * 80)

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

        # 验证批次输出配置一致性 (Phase 3 T3.3: 执行前验证)
        try:
            config_file = batch_dir / "simulation_config.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    stored_config = json.load(f)

                validation_config = {
                    'output_tripinfo': stored_config.get('output_tripinfo', False),
                    'output_vehroute': stored_config.get('output_vehroute', False),
                    'output_netstate': stored_config.get('output_netstate', False),
                    'output_fcd': stored_config.get('output_fcd', False),
                    'output_emission': stored_config.get('output_emission', False),
                    'output_edgedata': stored_config.get('output_edgedata', False),
                }
                if 'simulation_duration' in stored_config:
                    validation_config['simulation_duration'] = stored_config['simulation_duration']
                if 'num_seeds' in stored_config:
                    validation_config['num_seeds'] = stored_config['num_seeds']
                if 'base_seed' in stored_config:
                    validation_config['base_seed'] = stored_config['base_seed']

                is_valid, validation_message = self.validate_batch_output_config(batch_dir, validation_config)
                if not is_valid:
                    logger.error(f"Pre-execution config validation FAILED: {validation_message}")
                    raise ValueError(f"Batch configuration invalid before execution: {validation_message}")
                logger.info(f"Pre-execution config validation PASSED: {validation_message}")
        except FileNotFoundError as e:
            logger.error(f"Batch config file not found: {e}")
            raise ValueError(f"Batch configuration missing: {str(e)}")

        # 启动批量仿真（异步执行）
        asyncio.create_task(
            self.scheduler.start_batch(
                case_id=case_id, batch_id=batch_id, simulation_service=simulation_service
            )
        )

        # 更新批次索引状态为running
        self._update_batches_index_on_status_change(
            case_id=case_id,
            batch_id=batch_id,
            status="running"
        )

        response = {
            "batch_id": batch_id,
            "status": "running",
            "started_at": datetime.now().isoformat(),
        }

        logger.info(f"Batch {batch_id} started and index updated")

        return response

    def _read_or_update_cache(
        self,
        cache_file_path: Path,
        summary_file_path: Path,
        task_id: str,
        is_completed: bool = False
    ) -> Optional[List[Dict[str, int]]]:
        """
        读取或增量更新JSON缓存文件

        策略（增量缓存）：
        1. 如果缓存存在，尝试读取缓存中最后一个时间点
        2. 从summary.xml中提取新的（比缓存更新）的时间点
        3. 将新数据追加到缓存中
        4. 如果是已完成任务，可选地读取完整summary.xml
        5. 返回增量更新后的完整时序数据

        Args:
            cache_file_path: 缓存JSON文件路径
            summary_file_path: summary.xml文件路径
            task_id: 任务ID（用于日志）
            is_completed: 任务是否已完成

        Returns:
            List[Dict]: 时序数据列表，如果无法更新则返回None
        """
        import time as time_module

        logger.debug(f"[_read_or_update_cache] Task {task_id}: Checking cache at {cache_file_path}")

        # 步骤1：检查并读取缓存文件
        cached_data = []
        last_cached_time = -1

        if cache_file_path.exists():
            try:
                with open(cache_file_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                if cached_data:
                    last_cached_time = cached_data[-1].get('time', -1)
                logger.debug(f"[_read_or_update_cache] Task {task_id}: Loaded cache with {len(cached_data)} points, last_time={last_cached_time}")
            except Exception as e:
                logger.warning(f"[_read_or_update_cache] Task {task_id}: Failed to read cache: {e}")
                cached_data = []
                last_cached_time = -1

        # 步骤2：从summary.xml提取新的数据点
        if summary_file_path.exists():
            try:
                # 对于运行中任务，只读取最后一步（高效）
                # 对于已完成任务，读取完整数据（确保完整性）
                if is_completed:
                    # 已完成：读取完整时序（1次性读取整个文件）
                    new_time_series = self._extract_summary_time_series(summary_file_path)
                    logger.debug(f"[_read_or_update_cache] Task {task_id}: Completed task, read full series: {len(new_time_series)} points")
                else:
                    # 运行中：只读最后一个步（高效）
                    last_step = self._extract_summary_last_step(summary_file_path)
                    new_time_series = [last_step] if last_step else []
                    if new_time_series:
                        logger.debug(f"[_read_or_update_cache] Task {task_id}: Running task, read last step: time={last_step.get('time')}")

                # 步骤3：找出比缓存更新的数据点
                incremental_data = [
                    entry for entry in new_time_series
                    if entry.get('time', -1) > last_cached_time
                ]

                if incremental_data:
                    # 合并缓存和增量数据
                    cached_data.extend(incremental_data)
                    # 去重和排序（以防有重复）
                    unique_data = {}
                    for entry in cached_data:
                        time_key = entry.get('time')
                        if time_key is not None:
                            unique_data[time_key] = entry
                    cached_data = [unique_data[t] for t in sorted(unique_data.keys())]

                    logger.debug(f"[_read_or_update_cache] Task {task_id}: Added {len(incremental_data)} new points, total={len(cached_data)}")

                    # 步骤4：保存更新后的缓存
                    try:
                        cache_file_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(cache_file_path, 'w', encoding='utf-8') as f:
                            json.dump(cached_data, f, ensure_ascii=False)
                        logger.debug(f"[_read_or_update_cache] Task {task_id}: Cache saved with {len(cached_data)} points")
                    except Exception as e:
                        logger.warning(f"[_read_or_update_cache] Task {task_id}: Failed to save cache: {e}")
                        # 缓存保存失败不影响返回数据
                else:
                    logger.debug(f"[_read_or_update_cache] Task {task_id}: No new data points since last_time={last_cached_time}")

            except Exception as e:
                logger.warning(f"[_read_or_update_cache] Task {task_id}: Failed to read summary.xml: {e}")

        # 步骤5：返回缓存数据
        return cached_data if cached_data else None

    def _extract_summary_last_step(self, summary_file_path: Path) -> Optional[Dict[str, Any]]:
        """
        增量解析summary.xml，仅提取最后一个<step>元素

        策略：
        1. 从文件末尾向前读取最后4KB数据（避免读取整个文件，防止并发写入问题）
        2. 正则提取最后一个<step>元素
        3. 解析属性：time, running, loaded, ended
        4. 添加重试机制处理文件锁

        Args:
            summary_file_path: summary.xml文件路径

        Returns:
            Dict: 最后一步的状态数据，如果文件不存在或解析失败则返回None
        """
        import re
        import io

        logger.debug(f"[_extract_summary_last_step] Extracting last step from {summary_file_path}")

        if not summary_file_path.exists():
            logger.debug(f"[_extract_summary_last_step] File does not exist")
            return None

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 使用io.open以处理并发读写，添加重试
                with io.open(str(summary_file_path), 'rb') as f:
                    f.seek(0, 2)  # 移到文件末尾
                    file_size = f.tell()
                    read_size = min(8192, file_size)  # 增加到8KB以防文件较小
                    f.seek(-read_size, 2)
                    tail_content = f.read().decode('utf-8', errors='ignore')

                # 正则提取最后一个<step>元素
                # 匹配格式: <step time="X" running="Y" loaded="Z" ended="W" ... />
                pattern = r'<step\s+([^>]+)/>'
                matches = list(re.finditer(pattern, tail_content))

                if not matches:
                    logger.debug(f"[_extract_summary_last_step] No step elements found in tail")
                    return None

                # 取最后一个匹配
                last_match = matches[-1]
                step_attributes_str = last_match.group(1)

                # 解析属性
                attr_pattern = r'(\w+)="([^"]+)"'
                attributes = dict(re.findall(attr_pattern, step_attributes_str))

                # 提取所需字段（time是float，其他是int）
                parsed_data = {
                    'time': int(float(attributes.get('time', 0))),
                    'running': int(attributes.get('running', 0)),
                    'loaded': int(attributes.get('loaded', 0)),
                    'ended': int(attributes.get('ended', 0)),
                }

                logger.debug(f"[_extract_summary_last_step] Successfully extracted last step: {parsed_data}")
                return parsed_data

            except (IOError, OSError) as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.warning(f"[_extract_summary_last_step] Failed after {max_retries} retries due to file lock: {e}")
                    return None
                logger.debug(f"[_extract_summary_last_step] Retry {retry_count}/{max_retries} due to file access issue: {e}")
                import time
                time.sleep(0.05)  # 等待50ms再重试
            except Exception as e:
                logger.warning(f"[_extract_summary_last_step] Failed to parse summary.xml: {e}")
                return None

    def _extract_simulation_end_time(self, sumocfg_file_path: Path) -> Optional[int]:
        """
        从simulation.sumocfg中提取仿真结束时间

        策略：
        1. 读取simulation.sumocfg文件
        2. 解析XML查找 <time><end value="..."/>
        3. 返回end_time值（单位：秒）

        Args:
            sumocfg_file_path: simulation.sumocfg文件路径

        Returns:
            int: 仿真结束时间（秒），如果无法提取则返回None
        """
        import re
        import io

        logger.debug(f"Extracting end_time from: {sumocfg_file_path}")

        if not sumocfg_file_path.exists():
            logger.debug(f"sumocfg file not found: {sumocfg_file_path}")
            return None

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # 读取整个sumocfg文件（通常很小）
                with io.open(str(sumocfg_file_path), 'rb') as f:
                    content = f.read().decode('utf-8', errors='ignore')

                # 正则匹配: <time>...<end value="600"/>
                pattern = r'<time>\s*(?:<begin[^>]*>\s*)?<end\s+value="([^"]+)"'
                match = re.search(pattern, content)

                if match:
                    end_time_str = match.group(1)
                    try:
                        end_time = int(float(end_time_str))
                        logger.debug(f"Successfully extracted end_time: {end_time} seconds from {sumocfg_file_path.name}")
                        return end_time
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to parse end_time value '{end_time_str}': {e}")
                        return None
                else:
                    logger.debug(f"No <time><end> pattern found in {sumocfg_file_path.name}")
                    return None

            except (IOError, OSError) as e:
                retry_count += 1
                if retry_count >= max_retries:
                    logger.warning(f"Failed to read {sumocfg_file_path.name} after {max_retries} retries: {e}")
                    return None
                logger.debug(f"Retry {retry_count}/{max_retries} for {sumocfg_file_path.name}")
                import time
                time.sleep(0.05)  # 等待50ms再重试
            except Exception as e:
                logger.warning(f"Error extracting end_time: {e}")
                return None

    def _get_simulation_live_status(
        self, case_id: str, batch_id: str, task: Dict[str, Any], total_steps: int = 14400
    ) -> Dict[str, Any]:
        """
        获取运行中仿真的实时状态（从progress.json读取）

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            task: 任务信息字典，包含simulation_id
            total_steps: 仿真总步数（默认4小时=14400秒，将被实际配置覆盖）

        Returns:
            Dict: 实时状态数据
        """
        # 获取simulation_id
        simulation_id = task.get('simulation_id')
        if not simulation_id:
            logger.debug(f"Task {task.get('task_id')} has no simulation_id yet")
            return {
                'current_step': 0,
                'total_steps': total_steps,
                'progress_percent': 0.0,
                'message': '任务尚未分配仿真ID'
            }

        # 定位progress.json文件
        # 批量仿真使用plan_opti目录结构: cases/{case_id}/simulations/plan_opti/{batch_id}/{plan_id}/sim_{seed}/
        plan_id = task.get('plan_id')
        seed = task.get('seed')

        if plan_id and seed:
            # 批量仿真：使用plan_opti路径
            simulation_dir = (
                Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" /
                batch_id / plan_id / f"sim_{seed}"
            )
        else:
            # 单次仿真：使用标准路径（向后兼容）
            simulation_dir = Path(self.cases_base_dir) / case_id / "simulations" / simulation_id

        progress_file = simulation_dir / "progress.json"
        summary_file = simulation_dir / "summary.xml"

        # 尝试从simulation.sumocfg提取实际的仿真结束时间，以替换硬编码的total_steps
        sumocfg_file = simulation_dir / "simulation.sumocfg"
        extracted_end_time = self._extract_simulation_end_time(sumocfg_file)
        if extracted_end_time is not None:
            total_steps = extracted_end_time
            logger.debug(f"[_get_simulation_live_status] Using extracted end_time from simulation.sumocfg: {total_steps} seconds")
        else:
            logger.debug(f"[_get_simulation_live_status] Using default total_steps: {total_steps} seconds")

        # 调试日志
        logger.debug(f"Looking for progress.json at: {progress_file}")
        logger.debug(f"File exists: {progress_file.exists()}")

        # 读取progress.json或从summary.xml获取最后一步数据
        if not progress_file.exists():
            logger.debug(f"progress.json not found at {progress_file}, trying summary.xml")
            # 对于已完成的任务，从summary.xml读取最后一步数据
            last_step = self._extract_summary_last_step(summary_file)
            if last_step:
                logger.debug(f"Found last step in summary.xml: {last_step}")
                return {
                    'current_step': last_step.get('time', total_steps),
                    'total_steps': total_steps,
                    'progress_percent': 100.0,
                    'running_vehicles': last_step.get('running', 0),
                    'ended_vehicles': last_step.get('ended', 0),
                    'loaded_vehicles': last_step.get('loaded', 0)
                }
            else:
                return {
                    'current_step': 0,
                    'total_steps': total_steps,
                    'progress_percent': 0.0,
                    'message': '仿真正在初始化...'
                }

        try:
            import json
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)

            logger.debug(f"Read progress.json: {progress_data}")

            # 提取summary数据（如果存在）
            summary = progress_data.get('summary', {})
            if not summary:
                # 如果progress.json中没有summary数据，尝试从summary.xml提取最后一步数据
                logger.debug(f"No summary in progress.json, trying summary.xml")
                last_step = self._extract_summary_last_step(summary_file)
                if last_step:
                    logger.debug(f"Found last step in summary.xml: {last_step}")
                    return {
                        'current_step': last_step.get('time', total_steps),
                        'total_steps': total_steps,
                        'progress_percent': 100.0 if progress_data.get('percent', 0) >= 100 else progress_data.get('percent', 0.0),
                        'running_vehicles': last_step.get('running', 0),
                        'ended_vehicles': last_step.get('ended', 0),
                        'loaded_vehicles': last_step.get('loaded', 0)
                    }
                else:
                    # 最后的备选方案：只返回基础进度
                    return {
                        'current_step': 0,
                        'total_steps': total_steps,
                        'progress_percent': progress_data.get('percent', 0.0),
                        'message': progress_data.get('message', '运行中...')
                    }

            current_step = summary.get('current_step', 0)
            progress_percent = (current_step / total_steps) * 100 if total_steps > 0 else 0

            # 估算任务剩余时间
            estimated_remaining_seconds = None
            if 'started_at' in task and current_step > 0:
                try:
                    from datetime import datetime
                    started_at = datetime.fromisoformat(task['started_at'])
                    elapsed_seconds = (datetime.now() - started_at).total_seconds()
                    avg_step_duration = elapsed_seconds / current_step if current_step > 0 else 1.0
                    remaining_steps = total_steps - current_step
                    estimated_remaining_seconds = int(remaining_steps * avg_step_duration)
                except Exception:
                    pass

            # 确保 end_time 被正确设置为实际的 total_steps（已经过 summary.xml 动态提取或默认值）
            # 这个值是由调用处传入，或在本函数内从 summary.xml 提取的
            actual_end_time = total_steps

            result = {
                'current_step': current_step,
                'total_steps': actual_end_time,  # 实际的仿真结束时间（秒）
                'end_time': actual_end_time,     # 供前端使用，仿真结束时间（秒）
                'current_time': current_step,    # 当前仿真时间（秒）
                'progress_percent': round(progress_percent, 2),
                'running_vehicles': summary.get('running_vehicles', 0),
                'ended_vehicles': summary.get('ended_vehicles', 0),
                'loaded_vehicles': summary.get('loaded_vehicles', 0)
            }

            if estimated_remaining_seconds is not None:
                result['estimated_remaining_seconds'] = estimated_remaining_seconds

            return result

        except Exception as e:
            logger.warning(f"Failed to read progress.json at {progress_file}: {e}")
            return {
                'current_step': 0,
                'total_steps': total_steps,
                'progress_percent': 0.0,
                'message': '读取进度失败'
            }

    def _extract_summary_time_series(self, summary_file_path: Path) -> List[Dict[str, int]]:
        """
        提取summary.xml的完整时序数据

        Args:
            summary_file_path: summary.xml文件路径

        Returns:
            List[Dict]: 时序数据列表，每个元素包含 {time, running, loaded, ended}
        """
        import re
        import xml.etree.ElementTree as ET
        import io

        logger.debug(f"[_extract_summary_time_series] Starting extraction from {summary_file_path}")

        if not summary_file_path.exists():
            logger.debug(f"[_extract_summary_time_series] File does not exist: {summary_file_path}")
            return []

        try:
            # 使用io.open并指定编码，处理并发读写问题
            # 添加超时和重试机制
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                try:
                    # 以只读模式打开文件，防止被写入锁定
                    with io.open(str(summary_file_path), 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    # 使用fromstring而不是parse，避免文件锁
                    root = ET.fromstring(content)
                    break
                except (ET.ParseError, IOError) as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.warning(f"[_extract_summary_time_series] Failed after {max_retries} retries: {e}")
                        raise
                    logger.debug(f"[_extract_summary_time_series] Retry {retry_count}/{max_retries} due to: {e}")
                    import time
                    time.sleep(0.1)  # 等待100ms再重试

            time_series = []
            for step_elem in root.findall('.//step'):
                try:
                    time_series.append({
                        'time': int(float(step_elem.get('time', 0))),
                        'running': int(step_elem.get('running', 0)),
                        'loaded': int(step_elem.get('loaded', 0)),
                        'ended': int(step_elem.get('ended', 0))
                    })
                except Exception as e:
                    logger.debug(f"[_extract_summary_time_series] Skipped malformed entry: {e}")
                    continue

            logger.debug(f"[_extract_summary_time_series] Successfully extracted {len(time_series)} time points")
            return time_series

        except Exception as e:
            logger.warning(f"[_extract_summary_time_series] Failed to extract time series from {summary_file_path}: {e}", exc_info=True)
            return []

    def _aggregate_live_time_series(
        self, tasks: List[Dict[str, Any]], case_id: str, batch_id: str
    ) -> Dict[str, Any]:
        """
        汇总所有任务（运行中或已完成）的时序数据，生成动态曲线数据

        【数据源说明】CRITICAL - Data Source Documentation
        ==========================================
        此聚合使用 ONLY `live_curve_cache.json` 从已完成或运行中的任务
        This is the SINGLE SOURCE OF TRUTH for all time series vehicle count data
        Both runtime and completion charts use the same data source (per-task cache files)

        数据来源:
        - ✅ ALWAYS: live_curve_cache.json (per-task cache files)
        - ❌ NEVER: progress.json (only contains summary metrics, NOT time series)

        【任务选择策略】
        - 当所有任务完成时：汇总所有已完成任务（包括超过并发限制的所有任务，如22个任务）
        - 当批次运行中时：汇总所有运行中任务（保持实时性）

        【时间点对齐策略】
        - 使用并集（union）而非交集（intersection）来对齐时间点
        - 对于缺失的时间点，使用最近邻插值（取小于等于该时间点的最大值）
        - 这样可以确保即使多个任务（如22个）时间点不完全对齐，也能正确汇总所有任务的车辆数

        【增量缓存优化】
        优先级：
        1. 运行中任务 → 使用增量缓存（只读最后一步）→ 7倍性能提升
        2. 已完成任务 → 读取完整summary.xml（一次性）→ 确保完整性
        3. 如果没有数据 → 返回空

        数据流：
        - 运行中: summary.xml(尾部) → live_curve_cache.json(追加) → 曲线渲染 ✓ 实时性
        - 已完成: summary.xml(完整) → live_curve_cache.json(替换) → 曲线渲染 ✓ 完整性
        - Both use SAME cache file format and aggregation logic

        Args:
            tasks: 任务列表
            case_id: 案例ID
            batch_id: 批次ID

        Returns:
            Dict: {
                'time_points': [0, 1, 2, ...],
                'total_running': [320, 350, ...],  # 所有任务同一时刻车辆数之和
                'task_count': N,  # 参与汇总的任务数
                'last_update': '2025-10-29T10:25:00',
                'data_source': 'incremental_cache'  # 数据源标记
            }
        """
        from datetime import datetime
        from collections import defaultdict

        # 策略：当所有任务完成时，汇总所有已完成任务；否则汇总运行中任务
        running_tasks = [t for t in tasks if t.get('status') == 'running']
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        
        # 如果所有任务都已完成（无运行中任务），汇总所有已完成任务
        # 这样可以包含所有超过并发限制的任务（比如22个任务）
        if not running_tasks and completed_tasks:
            # 批次已完成：汇总所有已完成任务
            data_source_tasks = completed_tasks
            is_live = False
            logger.debug(f"[_aggregate_live_time_series] Batch completed: aggregating ALL {len(completed_tasks)} completed tasks")
        elif running_tasks:
            # 批次运行中：汇总运行中任务（保持实时性）
            data_source_tasks = running_tasks
            is_live = True
            logger.debug(f"[_aggregate_live_time_series] Batch running: aggregating {len(running_tasks)} running tasks")
        else:
            # 无运行中或已完成任务
            data_source_tasks = []
            is_live = False

        logger.debug(f"[_aggregate_live_time_series] Running tasks: {len(running_tasks)}, Completed: {len(completed_tasks)}")
        logger.debug(f"[_aggregate_live_time_series] Using {'running' if is_live else 'completed'} tasks for time series (count: {len(data_source_tasks)})")

        if not data_source_tasks:
            logger.debug(f"[_aggregate_live_time_series] No running or completed tasks, returning empty")
            return {
                'time_points': [],
                'total_running': [],
                'task_count': 0,
                'last_update': datetime.now().isoformat(),
                'data_source': 'empty'
            }

        # 【数据对齐策略】收集每个任务的时序数据，使用并集对齐（包含所有任务的所有时间点）
        # 对于缺失的时间点使用最近邻插值，确保即使多个任务（如22个）时间点不完全对齐也能正确汇总
        task_time_series_map = {}  # {task_id: {time: running_count}}

        for task in data_source_tasks:
            simulation_id = task.get('simulation_id')
            plan_id = task.get('plan_id')
            seed = task.get('seed')
            task_id = task.get('task_id', 'unknown')
            task_status = task.get('status')

            # 定位summary.xml和cache.json（支持plan_opti路径）
            if plan_id and seed:
                # 批量仿真：使用plan_opti路径
                simulation_dir = (
                    Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" /
                    batch_id / plan_id / f"sim_{seed}"
                )
            elif simulation_id:
                # 单次仿真：使用标准路径（向后兼容）
                simulation_dir = Path(self.cases_base_dir) / case_id / "simulations" / simulation_id
            else:
                logger.debug(f"[_aggregate_live_time_series] Task {task_id} has no simulation_id or plan_id/seed")
                continue

            summary_file = simulation_dir / "summary.xml"
            cache_file = simulation_dir / "live_curve_cache.json"  # 缓存文件 - SINGLE SOURCE OF TRUTH

            logger.debug(f"[_aggregate_live_time_series] Task {task_id}: summary={summary_file.exists()}, cache={cache_file.exists()}")
            logger.debug(f"[_aggregate_live_time_series] Data Source: Reading from cache file: {cache_file}")

            # 【增量缓存策略】使用缓存读取（性能优化）
            # CRITICAL: This is the ONLY source of time series data
            # Data flows: summary.xml → live_curve_cache.json → API response → chart
            is_completed = (task_status == 'completed')
            time_series = self._read_or_update_cache(
                cache_file_path=cache_file,
                summary_file_path=summary_file,
                task_id=task_id,
                is_completed=is_completed
            )

            logger.debug(f"[_aggregate_live_time_series] Task {task_id}: Extracted {len(time_series) if time_series else 0} data points from live_curve_cache.json")
            if time_series:
                logger.debug(f"[_aggregate_live_time_series] Task {task_id}: Time range: {time_series[0].get('time', 0)} - {time_series[-1].get('time', 0)} seconds")

                # 将此任务的时序数据转换为字典格式
                task_data = {}
                for entry in time_series:
                    time_step = entry.get('time', 0)
                    running_vehicles = entry.get('running', 0)
                    task_data[time_step] = running_vehicles

                task_time_series_map[task_id] = task_data

        # 【时间点对齐策略】使用并集而非交集，对缺失时间点进行插值
        # 这样可以确保即使多个任务（如22个）的时间点不完全对齐，也能正确汇总
        if not task_time_series_map:
            logger.debug(f"[_aggregate_live_time_series] No task data available")
            all_time_points = set()
        else:
            # 获取所有任务的时间点集合的并集（而非交集）
            time_point_sets = [set(task_data.keys()) for task_data in task_time_series_map.values()]
            all_time_points = set.union(*time_point_sets) if time_point_sets else set()

            logger.debug(f"[_aggregate_live_time_series] Task count: {len(task_time_series_map)}, "
                        f"All time points (union): {len(all_time_points)}")
            
            # 如果是多个任务且使用交集，记录日志
            if len(task_time_series_map) > 1:
                intersection_size = len(set.intersection(*time_point_sets)) if time_point_sets else 0
                if intersection_size < len(all_time_points):
                    logger.debug(f"[_aggregate_live_time_series] Using union strategy: {len(all_time_points)} points "
                               f"(intersection would be {intersection_size} points)")

        # 汇总所有时间点的车辆数（使用插值处理缺失值）
        aggregated_data = {}
        for time_point in all_time_points:
            total_running = 0
            for task_id, task_data in task_time_series_map.items():
                if time_point in task_data:
                    # 任务在该时间点有数据，直接使用
                    total_running += task_data[time_point]
                else:
                    # 任务在该时间点没有数据，使用最近邻插值（取小于等于该时间点的最大值）
                    # 如果该任务还没有任何数据，使用0
                    available_times = [t for t in task_data.keys() if t <= time_point]
                    if available_times:
                        nearest_time = max(available_times)
                        total_running += task_data[nearest_time]
                    # 如果没有可用数据，该任务在该时间点的贡献为0（不累加）
            
            aggregated_data[time_point] = total_running

        # 转换为数组格式
        logger.debug(f"[_aggregate_live_time_series] Total data points: {len(aggregated_data)}")

        if not aggregated_data:
            logger.debug(f"[_aggregate_live_time_series] No aggregated data found, returning empty")
            return {
                'time_points': [],
                'total_running': [],
                'task_count': len(data_source_tasks),
                'last_update': datetime.now().isoformat(),
                'data_source': 'cache_empty'
            }

        sorted_times = sorted(aggregated_data.keys())
        time_points = sorted_times
        total_running = [aggregated_data[t] for t in sorted_times]

        logger.debug(f"[_aggregate_live_time_series] Returning {len(time_points)} time points from incremental cache")
        logger.info(
            f"[_aggregate_live_time_series] Summary: Aggregated {len(data_source_tasks)} tasks, "
            f"{len(time_points)} time points, "
            f"time range: {time_points[0]}-{time_points[-1]}s, "
            f"data source: live_curve_cache.json (per-task files)"
        )

        return {
            'time_points': time_points,
            'total_running': total_running,
            'task_count': len(data_source_tasks),
            'last_update': datetime.now().isoformat(),
            'data_source': 'incremental_cache'  # 标记使用了增量缓存
        }

    def _calculate_batch_remaining_time(self, tasks: List[Dict[str, Any]]) -> Optional[int]:
        """
        计算批次剩余时间（基于已完成任务的实际耗时）

        Args:
            tasks: 任务列表（已注入live_status）

        Returns:
            Optional[int]: 预计剩余秒数，无法计算则返回None
        """
        from datetime import datetime

        # 计算已完成任务的平均耗时
        completed_tasks = [t for t in tasks if t.get('status') == 'completed']
        if completed_tasks:
            total_duration = 0
            count = 0
            for task in completed_tasks:
                if 'started_at' in task and 'completed_at' in task:
                    try:
                        started = datetime.fromisoformat(task['started_at'])
                        completed = datetime.fromisoformat(task['completed_at'])
                        duration = (completed - started).total_seconds()
                        total_duration += duration
                        count += 1
                    except Exception:
                        pass
            avg_duration = total_duration / count if count > 0 else 300.0  # 默认5分钟
        else:
            avg_duration = 300.0  # 无已完成任务时，使用默认值

        # 计算运行中任务的剩余时间（使用live_status）
        running_remaining = 0
        running_tasks = [t for t in tasks if t.get('status') == 'running']
        for task in running_tasks:
            live_status = task.get('live_status', {})
            task_remaining = live_status.get('estimated_remaining_seconds')
            if task_remaining is not None:
                running_remaining += task_remaining
            else:
                # 无法估算，使用平均值
                running_remaining += avg_duration

        # 待执行任务数 * 平均耗时
        pending_tasks = [t for t in tasks if t.get('status') == 'pending']
        pending_remaining = len(pending_tasks) * avg_duration

        # 总剩余时间 = 运行中任务剩余时间 + 待执行任务时间
        # 注意：这里假设任务是串行的；如果并行，需要除以并发数
        total_remaining = running_remaining + pending_remaining

        return int(total_remaining) if total_remaining > 0 else None

    def get_batch_progress(self, case_id: str, batch_id: str) -> Dict[str, Any]:
        """
        获取批次进度（增强版，包含实时监控数据）

        Args:
            case_id: 案例ID
            batch_id: 批次ID

        Returns:
            Dict: 批次进度数据（包含live_status和estimated_remaining_seconds）

        Raises:
            FileNotFoundError: 批次不存在
        """
        try:
            progress_data = self.scheduler.get_batch_progress(case_id, batch_id)

            # 🚀 性能优化：加载批次配置（包含缓存的end_time）
            # 避免在progress轮询时重复从磁盘提取end_time
            batch_dir = Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / batch_id
            batch_metadata_path = batch_dir / "batch_metadata.json"
            cached_end_times = {}  # {task_id: end_time}
            needs_metadata_update = False

            if batch_metadata_path.exists():
                try:
                    with open(batch_metadata_path, "r", encoding="utf-8") as f:
                        batch_metadata = json.load(f)
                        # 从metadata获取缓存的end_times(如果存在)
                        cached_end_times = batch_metadata.get("task_end_times", {})
                except Exception as e:
                    logger.debug(f"Failed to load task_end_times from metadata: {e}")
            else:
                batch_metadata = {}

            # 对每个任务添加live_status（运行中任务使用实时数据，已完成任务使用最后一步数据）
            for task_dict in progress_data["tasks"]:
                if task_dict.get('status') in ['running', 'completed']:
                    # 获取task_id作为缓存key
                    task_id = task_dict.get('task_id', 'unknown')

                    # 🚀 优化：优先使用缓存的end_time，避免磁盘I/O
                    task_total_steps = cached_end_times.get(task_id)

                    if task_total_steps is None:
                        # 缓存未命中，从磁盘提取(这只发生在第一次poll或metadata损坏时)
                        plan_id = task_dict.get('plan_id')
                        seed = task_dict.get('seed')

                        # 定位 simulation.sumocfg 文件
                        if plan_id and seed:
                            # 批量仿真：使用 plan_opti 路径
                            sumocfg_file = (
                                Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" /
                                batch_id / plan_id / f"sim_{seed}" / "simulation.sumocfg"
                            )
                        else:
                            # 单次仿真：使用标准路径
                            simulation_id = task_dict.get('simulation_id')
                            sumocfg_file = (
                                Path(self.cases_base_dir) / case_id / "simulations" / simulation_id / "simulation.sumocfg"
                            )

                        # 提取实际的 end_time，如果失败则使用默认值
                        extracted_end_time = self._extract_simulation_end_time(sumocfg_file)
                        task_total_steps = extracted_end_time if extracted_end_time is not None else 14400

                        if extracted_end_time is None:
                            logger.debug(f"Task {task_id}: Using default end_time 14400 seconds")

                        # 缓存到cached_end_times供后续保存到metadata
                        cached_end_times[task_id] = task_total_steps
                        needs_metadata_update = True
                    else:
                        logger.debug(f"Task {task_id}: Using cached end_time {task_total_steps} seconds")

                    live_status = self._get_simulation_live_status(
                        case_id=case_id,
                        batch_id=batch_id,
                        task=task_dict,
                        total_steps=task_total_steps  # 使用每个任务的实际仿真时长
                    )
                    task_dict['live_status'] = live_status

            # 计算批次剩余时间（使用增强算法）
            batch_remaining_seconds = self._calculate_batch_remaining_time(progress_data["tasks"])

            # 🚀 性能优化: 禁用progress轮询中的时序聚合
            # 【根本原因】: 对于已完成的12-15个task,每个都需要:
            # 1. 读取整个summary.xml (可能很大)
            # 2. XML解析所有step元素 (1.5小时仿真 = 5400+ step元素)
            # 3. 总耗时: 12 task × (读取+解析5400 step) = 20-30秒 ❌
            #
            # 【解决】: 时序数据仅在明确请求时计算(如results页面加载)
            # progress轮询只返回基本的进度信息,不计算复杂的时序聚合
            # 性能提升: 27秒 → <100ms (-99%)
            live_time_series = {
                'time_points': [],
                'total_running': [],
                'task_count': len(progress_data["tasks"]),
                'data_source': 'disabled_for_progress_optimization'
            }

            # 计算预计完成时间
            from datetime import datetime
            estimated_completion = None
            if batch_remaining_seconds is not None and batch_remaining_seconds > 0:
                estimated_time = datetime.now().timestamp() + batch_remaining_seconds
                estimated_completion = datetime.fromtimestamp(estimated_time).isoformat()

            # 🚀 优化：延迟写入task_end_times到metadata,避免重复磁盘I/O
            # 每个progress poll只需读一次metadata,而不是两次
            if needs_metadata_update and batch_metadata:
                try:
                    batch_metadata["task_end_times"] = cached_end_times
                    with open(batch_metadata_path, "w", encoding="utf-8") as f:
                        json.dump(batch_metadata, f, indent=2, ensure_ascii=False)
                    logger.debug(f"Cached {len(cached_end_times)} task end_times to batch_metadata.json")
                except Exception as e:
                    logger.warning(f"Failed to save task_end_times to metadata: {e}")

            # 提取batch配置信息（reuse已加载的batch_metadata)
            batch_config = {}
            if batch_metadata:
                batch_config = {
                    "num_seeds": batch_metadata.get("num_seeds", 3),
                    "base_seed": batch_metadata.get("base_seed", 66),
                    "simulation_duration": batch_metadata.get("simulation_duration"),
                    "output_config": batch_metadata.get("output_config", {}),
                }

            response = {
                **progress_data,
                "estimated_completion": estimated_completion,
                "estimated_remaining_seconds": batch_remaining_seconds,
                "live_time_series": live_time_series,
                **batch_config,  # 添加配置信息
            }

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

        # 读取案例元数据（用于获取案例的时间范围）
        case_dir = Path(self.cases_base_dir) / case_id
        case_metadata_path = case_dir / "metadata.json"
        case_info = {}

        if case_metadata_path.exists():
            try:
                with open(case_metadata_path, "r", encoding="utf-8") as f:
                    case_info = json.load(f)
            except:
                logger.debug(f"Failed to load case metadata for {case_id}")
                case_info = {}

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
            "case_id": case_id,
            "status": progress_data["status"],
            "plan_results": plan_results,
            "created_at": metadata.get("created_at"),
            "completed_at": metadata.get("completed_at"),

            # 仿真配置信息（从batch_metadata.json读取）
            "num_seeds": metadata.get("num_seeds", 3),
            "base_seed": metadata.get("base_seed", 66),
            "output_level": metadata.get("output_level", "standard"),
            "simulation_duration": metadata.get("simulation_duration"),
            "duration_seconds": metadata.get("duration_seconds"),
            "output_config": metadata.get("output_config", {}),  # 详细输出配置 (tripinfo, edgedata, netstate等)

            # 案例信息（从case metadata.json读取）
            "case_info": {
                "case_name": case_info.get("case_name", case_id),
                "case_id": case_id,
                "time_range": case_info.get("time_range", {}),  # {start: "...", end: "..."}
                "description": case_info.get("description", ""),
            },

            # Phase 2: 添加指标元数据配置 (中文标签、单位、改进方向)
            "metric_config": {
                "step": {
                    "label": "仿真步数",
                    "unit": "秒",
                    "direction": "verification",
                    "is_verification_metric": True,
                    "expected_value": 3600,
                    "description": "整个仿真运行的总时长 - 用于验证仿真是否完整执行到预定时长"
                },
                "loaded": {
                    "label": "已加载车数",
                    "unit": "辆",
                    "direction": "neutral",
                    "description": "被加载到网络中的总车数"
                },
                "inserted": {
                    "label": "已插入车数",
                    "unit": "辆",
                    "direction": "higher",
                    "description": "成功插入到网络的车数"
                },
                "ended": {
                    "label": "已完成车数",
                    "unit": "辆",
                    "direction": "higher",
                    "description": "完成行程、离开网络的车数（通行效率指标）"
                },
                "running": {
                    "label": "当前运行车数",
                    "unit": "辆",
                    "direction": "lower",
                    "description": "仿真结束时仍在网络中的车数"
                },
                "waiting": {
                    "label": "等待车数",
                    "unit": "辆",
                    "direction": "lower",
                    "description": "因信号灯、拥堵等原因停止等待的车数"
                },
                "teleports": {
                    "label": "传送次数",
                    "unit": "次",
                    "direction": "lower",
                    "description": "SUMO进行的传送操作次数（拥堵严重程度指标）"
                },
                "collisions": {
                    "label": "碰撞次数",
                    "unit": "次",
                    "direction": "lower",
                    "description": "仿真中发生的车辆碰撞事件数"
                },
                "avgSpeed": {
                    "label": "平均速度",
                    "unit": "m/s",
                    "direction": "higher",
                    "description": "所有已完成车的平均行驶速度（核心性能指标）"
                }
            }
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
        解析summary.xml文件提取指标 (Phase 1: 扩展为提取完整的9个指标)

        提取的指标:
        - step: 仿真步数 (秒)
        - loaded: 已加载车数 (辆)
        - inserted: 已插入车数 (辆)
        - ended: 已完成车数 (辆) ⭐ 核心
        - running: 当前运行车数 (辆)
        - waiting: 等待车数 (辆) ⭐ 核心
        - teleports: 传送次数 (次) ⭐ 拥堵指标
        - collisions: 碰撞次数 (次)
        - avgSpeed: 平均速度 (m/s) ⭐ 核心

        Args:
            file_path: summary.xml文件路径

        Returns:
            Dict: 提取的9个指标

        注意: 实际SUMO输出的summary.xml结构为:
            <summary>
                <step time="..." loaded="..." inserted="..." running="..."
                       waiting="..." ended="..." collisions="..." teleports="..."
                       meanSpeed="..." ... />
            </summary>
            所有指标都是<step>元素的属性，不是独立的<vehicleSummary>子元素
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # 获取所有step元素，取最后一个（最终统计）
            steps = root.findall("step")
            if not steps:
                logger.warning(f"No step elements found in {file_path}")
                return {}

            # 取最后一步（仿真结束时的统计数据）
            last_step = steps[-1]

            # 直接从<step>元素属性提取所有9个指标 ✅
            # 注意: XML中使用"meanSpeed"，我们转换为"avgSpeed"
            metrics = {
                # 时间相关
                "step": float(last_step.get("time", 0)),

                # 车辆流相关
                "loaded": int(last_step.get("loaded", 0)),
                "inserted": int(last_step.get("inserted", 0)),
                "ended": int(last_step.get("ended", 0)),
                "running": int(last_step.get("running", 0)),

                # 拥堵相关
                "waiting": int(last_step.get("waiting", 0)),
                "teleports": int(last_step.get("teleports", 0)),
                "collisions": int(last_step.get("collisions", 0)),

                # 性能相关 (XML中是meanSpeed，转换为avgSpeed)
                "avgSpeed": float(last_step.get("meanSpeed", 0.0))
            }

            logger.debug(f"Extracted {len(metrics)} metrics from {file_path}")
            return metrics

        except Exception as e:
            logger.warning(f"Failed to parse summary.xml {file_path}: {e}")
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

        注意：只取消任务，不删除目录。目录保留以便之后重新启动。

        Args:
            case_id: 案例ID
            batch_id: 批次ID

        Returns:
            Dict: 取消响应数据，包含cancelled_count和killed_count

        Raises:
            FileNotFoundError: 批次不存在
            ValueError: 批次状态不允许取消
        """
        logger.info(f"Cancelling batch {batch_id}")

        try:
            result = self.scheduler.cancel_batch(case_id, batch_id)

            # 更新批次索引
            try:
                self._update_batches_index_on_status_change(case_id, batch_id, "cancelled")
            except Exception as e:
                logger.warning(f"Failed to update batches index: {e}")

            logger.info(f"Batch {batch_id} cancelled: {result.get('cancelled_count')} tasks, {result.get('killed_count')} processes")

            return result

        except FileNotFoundError as e:
            raise FileNotFoundError(f"批次不存在: {batch_id}") from e
        except ValueError as e:
            raise ValueError(str(e)) from e

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

        # 删除批次目录，重试3次以处理文件锁定问题
        import shutil
        import time

        max_retries = 3
        for attempt in range(max_retries):
            try:
                shutil.rmtree(batch_dir)
                response = {"batch_id": batch_id, "deleted": True, "deleted_at": datetime.now().isoformat()}
                logger.info(f"Batch {batch_id} deleted")
                return response
            except PermissionError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Permission denied deleting batch {batch_id}, retrying ({attempt + 1}/{max_retries}): {e}")
                    time.sleep(0.5)  # 等待0.5秒后重试
                else:
                    # 最后一次尝试失败，返回警告但认为删除成功
                    logger.warning(f"Failed to delete batch directory after {max_retries} retries: {e}")
                    # 更新批次索引以标记为已删除
                    try:
                        self._update_batches_index_on_delete(case_id, batch_id)
                    except Exception:
                        pass
                    response = {
                        "batch_id": batch_id,
                        "deleted": True,
                        "deleted_at": datetime.now().isoformat(),
                        "warning": "目录删除失败，但批次已标记为已删除"
                    }
                    logger.info(f"Batch {batch_id} marked as deleted (directory not fully removed)")
                    return response
            except Exception as e:
                logger.error(f"Error deleting batch {batch_id}: {e}", exc_info=True)
                raise

        # 不应到达这里
        raise RuntimeError(f"无法删除批次 {batch_id}")

    def _get_batches_index_path(self, case_id: str) -> Path:
        """获取批次索引文件路径"""
        return Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / "batches_index.json"

    def _load_batches_index(self, case_id: str) -> Dict[str, Any]:
        """加载批次索引文件，如不存在则返回空索引"""
        index_path = self._get_batches_index_path(case_id)
        if not index_path.exists():
            return {"batches": [], "last_updated": datetime.now().isoformat()}

        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load batches index: {e}, returning empty index")
            return {"batches": [], "last_updated": datetime.now().isoformat()}

    def _save_batches_index(self, case_id: str, index: Dict[str, Any]) -> None:
        """保存批次索引文件"""
        index_path = self._get_batches_index_path(case_id)
        index_path.parent.mkdir(parents=True, exist_ok=True)

        index["last_updated"] = datetime.now().isoformat()
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def _update_batches_index_on_create(self, case_id: str, batch_metadata: Dict[str, Any]) -> None:
        """批次创建时更新索引"""
        index = self._load_batches_index(case_id)

        # 检查是否已存在
        batch_id = batch_metadata.get("batch_id")
        existing = next((b for b in index["batches"] if b.get("batch_id") == batch_id), None)
        if not existing:
            batch_summary = {
                "batch_id": batch_id,
                "case_id": case_id,
                "plan_ids": batch_metadata.get("plan_ids", []),
                "plan_count": len(batch_metadata.get("plan_ids", [])),
                "total_tasks": batch_metadata.get("total_tasks", 0),
                "num_seeds": batch_metadata.get("num_seeds", 1),
                "base_seed": batch_metadata.get("base_seed", 66),
                "max_concurrent": batch_metadata.get("max_concurrent", 1),
                "status": batch_metadata.get("status", "pending"),
                "created_at": batch_metadata.get("created_at", datetime.now().isoformat()),
                "simulation_duration": batch_metadata.get("simulation_duration"),
                "output_config": batch_metadata.get("output_config", {}),
            }
            index["batches"].append(batch_summary)
            self._save_batches_index(case_id, index)
            logger.debug(f"Updated batches index for case {case_id} on batch creation")

    async def _on_batch_completed(self, case_id: str, batch_id: str) -> None:
        """
        批次完成时的回调函数

        Args:
            case_id: 案例ID
            batch_id: 批次ID
        """
        try:
            # 加载批次元数据
            batch_dir = Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / batch_id
            metadata_file = batch_dir / "batch_metadata.json"

            if not metadata_file.exists():
                logger.warning(f"Batch metadata not found for {batch_id}")
                return

            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 获取批次进度数据，统计已完成的任务
            progress_data = self.scheduler.get_batch_progress(case_id, batch_id)
            total_tasks = len(progress_data.get("tasks", []))
            completed_tasks = sum(
                1 for task in progress_data.get("tasks", [])
                if task.get("status") == "completed"
            )
            success_rate = (completed_tasks / total_tasks) if total_tasks > 0 else 0.0

            # 更新元数据
            metadata['status'] = 'completed'
            metadata['completed_at'] = datetime.now().isoformat()
            metadata['success_rate'] = round(success_rate, 4)

            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 更新批次索引
            self._update_batches_index_on_status_change(
                case_id=case_id,
                batch_id=batch_id,
                status='completed',
                metadata=metadata
            )

            logger.debug(
                f"Batch {batch_id} completed: {completed_tasks}/{total_tasks} tasks "
                f"({success_rate*100:.1f}% success rate)"
            )

        except Exception as e:
            logger.error(f"Error in batch completion callback for {batch_id}: {e}")

    def _update_batches_index_on_status_change(self, case_id: str, batch_id: str, status: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """批次状态变更时更新索引"""
        index = self._load_batches_index(case_id)

        for batch in index["batches"]:
            if batch.get("batch_id") == batch_id:
                batch["status"] = status
                if status == "running" and "started_at" not in batch:
                    batch["started_at"] = datetime.now().isoformat()
                elif status == "completed":
                    batch["completed_at"] = datetime.now().isoformat()
                    if "started_at" in batch and "completed_at" in batch:
                        start_time = datetime.fromisoformat(batch["started_at"])
                        end_time = datetime.fromisoformat(batch["completed_at"])
                        batch["duration_seconds"] = int((end_time - start_time).total_seconds())

                    if metadata:
                        batch["success_rate"] = metadata.get("success_rate", 0.0)
                        batch["completed_tasks"] = metadata.get("completed_tasks", 0)
                        batch["failed_tasks"] = metadata.get("failed_tasks", 0)
                break

        self._save_batches_index(case_id, index)
        logger.debug(f"Updated batches index for batch {batch_id} on status change to {status}")

    def _update_batches_index_on_delete(self, case_id: str, batch_id: str) -> None:
        """批次删除时更新索引"""
        index = self._load_batches_index(case_id)
        index["batches"] = [b for b in index["batches"] if b.get("batch_id") != batch_id]
        self._save_batches_index(case_id, index)
        logger.debug(f"Updated batches index for case {case_id} on batch deletion")

    def list_batches(self, case_id: str, status: Optional[str] = None, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """
        列表查询批次

        Args:
            case_id: 案例ID
            status: 筛选状态（可选）
            page: 页码（从1开始）
            limit: 每页数量

        Returns:
            Dict: 批次列表和分页信息
        """
        index = self._load_batches_index(case_id)
        batches = index.get("batches", [])

        # 按状态筛选
        if status:
            batches = [b for b in batches if b.get("status") == status]

        # 按创建时间逆序排序
        batches = sorted(batches, key=lambda b: b.get("created_at", ""), reverse=True)

        # 分页
        total = len(batches)
        start = (page - 1) * limit
        end = start + limit
        paginated_batches = batches[start:end]

        return {
            "batches": paginated_batches,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0,
        }

    def get_batch_detail(self, case_id: str, batch_id: str) -> Dict[str, Any]:
        """
        获取批次详细信息

        Args:
            case_id: 案例ID
            batch_id: 批次ID

        Returns:
            Dict: 批次详细信息

        Raises:
            FileNotFoundError: 批次不存在
        """
        batch_dir = Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / batch_id

        if not batch_dir.exists():
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        # 加载批次元数据
        metadata_file = batch_dir / "batch_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                batch_metadata = json.load(f)
        else:
            batch_metadata = {"batch_id": batch_id, "case_id": case_id}

        # 获取任务列表（从batch_progress.json）
        progress_file = batch_dir / "batch_progress.json"
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                tasks = progress_data.get("tasks", [])
        else:
            tasks = []

        # 计算摘要统计
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.get("status") == "completed")
        failed_tasks = sum(1 for t in tasks if t.get("status") == "failed")
        cancelled_tasks = sum(1 for t in tasks if t.get("status") == "cancelled")

        # 计算平均任务时长
        completed = [t for t in tasks if t.get("status") == "completed" and t.get("duration_seconds")]
        avg_task_duration = (
            sum(t.get("duration_seconds", 0) for t in completed) // len(completed)
            if completed else None
        )

        return {
            "batch_id": batch_id,
            "case_id": case_id,
            "plan_ids": batch_metadata.get("plan_ids", []),
            "num_seeds": batch_metadata.get("num_seeds", 1),
            "base_seed": batch_metadata.get("base_seed", 66),
            "max_concurrent": batch_metadata.get("max_concurrent", 1),
            "status": batch_metadata.get("status", "pending"),
            "created_at": batch_metadata.get("created_at"),
            "started_at": batch_metadata.get("started_at"),
            "completed_at": batch_metadata.get("completed_at"),
            "duration_seconds": batch_metadata.get("duration_seconds"),
            "tasks": tasks,
            "summary": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "cancelled_tasks": cancelled_tasks,
                "success_rate": completed_tasks / total_tasks if total_tasks > 0 else 0.0,
                "avg_task_duration_seconds": avg_task_duration,
            }
        }

    def get_case_duration(self, case_id: str) -> Dict[str, Any]:
        """
        从case元数据中读取仿真时长 (Revision 3: 新增)

        从cases/{case_id}/metadata.json中读取time_range信息，
        计算仿真时长（从start到end）

        Args:
            case_id: 案例ID

        Returns:
            Dict: {
                "use_default": True,
                "start_time": "2025/09/01 08:00:00",
                "end_time": "2025/09/01 09:00:00",
                "duration_hours": 1,
                "duration_minutes": 0,
                "total_minutes": 60,
                "display_text": "1小时0分钟 (08:00 - 09:00)"
            }

        Raises:
            FileNotFoundError: 案例不存在或元数据文件不存在
            ValueError: 时间解析失败
        """
        try:
            case_dir = Path(self.cases_base_dir) / case_id
            metadata_file = case_dir / "metadata.json"

            if not metadata_file.exists():
                logger.warning(f"Metadata file not found: {metadata_file}")
                raise FileNotFoundError(f"案例元数据不存在: {case_id}")

            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            # 从metadata中提取time_range
            time_range = metadata.get("time_range", {})
            start_time_str = time_range.get("start")
            end_time_str = time_range.get("end")

            if not start_time_str or not end_time_str:
                logger.warning(f"No time_range in metadata for {case_id}")
                raise ValueError(f"案例元数据中缺少时间范围信息")

            # 解析时间
            from datetime import datetime
            try:
                start_time = datetime.strptime(start_time_str, "%Y/%m/%d %H:%M:%S")
                end_time = datetime.strptime(end_time_str, "%Y/%m/%d %H:%M:%S")
            except ValueError as e:
                logger.error(f"Failed to parse time range: {e}")
                raise ValueError(f"时间格式解析失败: {str(e)}")

            # 计算时长
            duration = end_time - start_time
            total_seconds = int(duration.total_seconds())
            total_minutes = total_seconds // 60
            hours = total_minutes // 60
            minutes = total_minutes % 60

            # 提取时间部分用于显示
            start_time_display = start_time.strftime("%H:%M")
            end_time_display = end_time.strftime("%H:%M")

            result = {
                "use_default": True,
                "start_time": start_time_str,
                "end_time": end_time_str,
                "duration_hours": hours,
                "duration_minutes": minutes,
                "total_minutes": total_minutes,
                "display_text": f"{hours}小时{minutes}分钟 ({start_time_display} - {end_time_display})"
            }

            logger.info(f"Case duration for {case_id}: {result['display_text']}")

            return result

        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting case duration: {e}", exc_info=True)
            raise ValueError(f"获取案例时长失败: {str(e)}")

    def list_vehicle_templates(self) -> Dict[str, Any]:
        """
        列表查询可用的车辆模板文件 (Revision 2: 新增)

        扫描templates目录下的vehicle_types*.json文件

        Returns:
            Dict: {
                "templates": [
                    {
                        "filename": "vehicle_types.json",
                        "display_name": "默认车辆参数",
                        "path": "templates/config_templates/vehicle_templates/vehicle_types.json"
                    },
                    ...
                ]
            }

        Raises:
            FileNotFoundError: 模板目录不存在
        """
        try:
            # 获取项目根目录（api/services/batch_optimization_service.py向上2层）
            project_root = Path(__file__).parent.parent.parent
            template_dir = project_root / "templates" / "config_templates" / "vehicle_templates"

            if not template_dir.exists():
                logger.warning(f"Template directory not found: {template_dir}")
                return {
                    "templates": [
                        {
                            "filename": "vehicle_types.json",
                            "display_name": "默认车辆参数",
                            "path": "templates/config_templates/vehicle_templates/vehicle_types.json"
                        }
                    ],
                    "total": 1
                }

            templates = []

            # 扫描所有vehicle_types*.json文件
            for json_file in sorted(template_dir.glob("vehicle_types*.json")):
                filename = json_file.name
                relative_path = str(json_file.relative_to(Path.cwd())).replace("\\", "/")

                # 显示名称直接使用文件名（不做多余的转换）
                display_name = filename

                templates.append({
                    "filename": filename,
                    "display_name": display_name,
                    "path": relative_path
                })

            logger.info(f"Found {len(templates)} vehicle template files")

            return {
                "templates": templates,
                "total": len(templates)
            }

        except Exception as e:
            logger.error(f"Error listing vehicle templates: {e}", exc_info=True)
            # 返回默认模板
            return {
                "templates": [
                    {
                        "filename": "vehicle_types.json",
                        "display_name": "默认车辆参数",
                        "path": "templates/config_templates/vehicle_templates/vehicle_types.json"
                    }
                ],
                "total": 1
            }

    def delete_batch_with_archive(self, case_id: str, batch_id: str, archive: bool = False) -> Dict[str, Any]:
        """
        删除或归档批次

        Args:
            case_id: 案例ID
            batch_id: 批次ID
            archive: True=归档（保留元数据），False=完全删除

        Returns:
            Dict: 删除/归档结果

        Raises:
            FileNotFoundError: 批次不存在
            ValueError: 批次正在运行
        """
        batch_dir = Path(self.cases_base_dir) / case_id / "simulations" / "plan_opti" / batch_id

        if not batch_dir.exists():
            raise FileNotFoundError(f"批次不存在: {batch_id}")

        # 检查批次状态
        metadata_file = batch_dir / "batch_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                if metadata.get("status") == "running":
                    raise ValueError("无法删除运行中的批次，请先取消批次")

        import shutil

        if archive:
            # 归档：删除大文件，保留元数据
            for plan_dir in batch_dir.glob("**/sim_*"):
                if plan_dir.is_dir():
                    # 保留 simulation_metadata.json 和 progress.json
                    for item in plan_dir.iterdir():
                        if item.name not in ["simulation_metadata.json", "progress.json", "batch_metadata.json"]:
                            if item.is_dir():
                                shutil.rmtree(item)
                            else:
                                item.unlink()

            # 更新元数据中的状态
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                metadata["status"] = "archived"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)

            response = {"batch_id": batch_id, "archived": True, "archived_at": datetime.now().isoformat()}
        else:
            # 完全删除
            shutil.rmtree(batch_dir)
            response = {"batch_id": batch_id, "deleted": True, "deleted_at": datetime.now().isoformat()}

        # 更新索引
        self._update_batches_index_on_delete(case_id, batch_id)

        logger.info(f"Batch {batch_id} {'archived' if archive else 'deleted'}")
        return response


# 单例服务实例
batch_optimization_service = BatchOptimizationService()


# 导出服务函数（用于路由层调用）
def create_batch_service(
    case_id: str,
    plan_ids: List[str],
    num_seeds: int = 3,
    base_seed: int = 66,
    output_level: str = "standard",
    simulation_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """创建批量仿真批次服务函数 (Phase 3: 支持output_level)"""
    return batch_optimization_service.create_batch(
        case_id=case_id,
        plan_ids=plan_ids,
        num_seeds=num_seeds,
        base_seed=base_seed,
        output_level=output_level,
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


def list_batches_service(case_id: str, status: Optional[str] = None, page: int = 1, limit: int = 20) -> Dict[str, Any]:
    """列表查询批次服务函数"""
    return batch_optimization_service.list_batches(case_id, status, page, limit)


def get_batch_detail_service(case_id: str, batch_id: str) -> Dict[str, Any]:
    """获取批次详细信息服务函数"""
    return batch_optimization_service.get_batch_detail(case_id, batch_id)


def delete_batch_with_archive_service(case_id: str, batch_id: str, archive: bool = False) -> Dict[str, Any]:
    """删除或归档批次服务函数"""
    return batch_optimization_service.delete_batch_with_archive(case_id, batch_id, archive)
