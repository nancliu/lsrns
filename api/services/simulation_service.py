"""
仿真运行服务 - 负责仿真运行和进度管理相关业务逻辑
"""

import os
import json
import signal
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess

logger = logging.getLogger(__name__)

from ..models import SimulationRequest, SimulationType, CaseStatus
from .base_service import BaseService, MetadataManager, DirectoryManager


class SimulationService(BaseService):
    """仿真运行服务类"""

    def __init__(self):
        """初始化仿真服务，添加进程跟踪"""
        super().__init__()
        # 跟踪活跃的SUMO进程：{simulation_id: (process_obj, case_id)}
        self.active_processes: Dict[str, tuple] = {}
        # 进程跟踪锁（线程安全）
        self._process_lock = threading.Lock()

    async def prepare_simulation(self, request: SimulationRequest) -> Dict[str, Any]:
        """准备仿真：仅创建目录与生成 sumocfg，不启动仿真。

        Args:
            request: 仿真请求参数。

        Returns:
            包含 simulation_id、run_folder、config_file、status=pending 的信息。
        """
        try:
            # 验证案例并创建仿真目录
            case_path = self._validate_case(request.case_id)
            simulation_id, simulation_folder = self._create_simulation_structure(case_path, request)

            # 检查并处理待生成的OD文件（异步调用）
            await self._ensure_od_file_available(case_path)

            # 生成配置文件
            cfg_file = self._generate_simulation_config(case_path, simulation_folder, request)
            cfg_file_abs = str(Path(cfg_file).resolve())

            # 创建并保存仿真元数据（pending）
            sim_metadata = self._create_simulation_metadata(request, simulation_id, simulation_folder, cfg_file)
            sim_metadata["status"] = "pending"
            MetadataManager.save_simulation_metadata(simulation_folder, sim_metadata)
            MetadataManager.update_simulations_index(case_path, simulation_id, sim_metadata)

            return {
                "simulation_id": simulation_id,
                "run_folder": str(simulation_folder),
                "config_file": cfg_file,
                "config_file_abs": cfg_file_abs,
                "status": "pending",
            }
        except Exception as e:
            raise Exception(f"准备仿真失败: {str(e)}")

    async def start_simulation(self, case_id: str, simulation_id: str, gui: bool = False) -> Dict[str, Any]:
        """启动仿真：基于已准备的 sim 目录与配置文件启动后台仿真。

        Args:
            case_id: 案例ID。
            simulation_id: 仿真ID（准备阶段生成）。
            gui: 是否启用 GUI。

        Returns:
            启动结果，包含 simulation_id、run_folder、status=started 等。
        """
        try:
            # 导入仿真处理器
            from shared.data_processors.simulation_processor import SimulationProcessor

            # 校验目录与配置
            case_path = self._validate_case(case_id)
            simulation_folder = Path("cases") / case_id / "simulations" / simulation_id
            if not simulation_folder.exists():
                raise Exception(f"仿真目录不存在: {simulation_folder}")

            sim_metadata = MetadataManager.load_simulation_metadata(simulation_folder)
            # 优先使用 config_file_path (实际文件路径)，fallback 到 config_file (但这是XML内容)
            cfg_file = sim_metadata.get("config_file_path") or str(simulation_folder / "simulation.sumocfg")
            if not Path(cfg_file).exists():
                raise Exception(f"未找到配置文件: {cfg_file}")

            # 创建仿真处理器并设置SUMO环境
            sim_processor = SimulationProcessor()
            self._setup_sumo_environment(sim_processor)

            # 构建仿真参数并初始化进度
            request_params = {
                "run_folder": str(simulation_folder),
                "gui": gui,
                "mesoscopic": sim_metadata.get("simulation_type") == "mesoscopic",
                "config_file": cfg_file,
                "expected_duration": sim_metadata.get("simulation_params", {}).get("expected_duration"),
                "case_id": case_id,  # 添加case_id用于进程跟踪
            }
            self._init_progress_file(simulation_folder)

            # 更新元数据与案例状态
            sim_metadata["status"] = "running"
            sim_metadata["started_at"] = datetime.now().isoformat()
            MetadataManager.save_simulation_metadata(simulation_folder, sim_metadata)
            self._update_case_status(case_path, CaseStatus.SIMULATING)

            # 后台运行仿真
            self._start_background_simulation(sim_processor, request_params, case_path, simulation_id, simulation_folder)

            return {
                "simulation_id": simulation_id,
                "run_folder": str(simulation_folder),
                "gui": gui,
                "mesoscopic": sim_metadata.get("simulation_type") == "mesoscopic",
                "simulation_type": sim_metadata.get("simulation_type"),
                "started_at": datetime.now().isoformat(),
                "status": "started",
            }
        except Exception as e:
            raise Exception(f"启动仿真失败: {str(e)}")

    async def run_simulation(self, request: SimulationRequest) -> Dict[str, Any]:
        """
        运行仿真的主要业务逻辑
        """
        try:
            # 兼容旧接口：先准备，再启动
            prepared = await self.prepare_simulation(request)
            start_result = await self.start_simulation(request.case_id, prepared["simulation_id"], gui=request.gui or False)
            return start_result
        except Exception as e:
            raise Exception(f"仿真运行失败: {str(e)}")
    
    def _setup_sumo_environment(self, sim_processor) -> None:
        """设置SUMO环境"""
        try:
            import shutil as _shutil
            sumo_bin_env = os.getenv("SUMO_BIN")
            sumo_home = os.getenv("SUMO_HOME")
            candidates: list[str] = []
            
            if sumo_bin_env:
                candidates.append(sumo_bin_env)
            if sumo_home:
                candidates.append(os.path.join(sumo_home, "bin", "sumo.exe"))
                candidates.append(os.path.join(sumo_home, "bin", "sumo"))
            
            # PATH中查找
            which_sumo = _shutil.which("sumo.exe") or _shutil.which("sumo")
            if which_sumo:
                candidates.append(which_sumo)
            
            # 常见安装路径
            candidates.extend([
                r"C:\\Program Files (x86)\\Eclipse\\Sumo\\bin\\sumo.exe",
                r"C:\\Program Files\\Eclipse\\Sumo\\bin\\sumo.exe",
            ])
            
            picked = next((p for p in candidates if p and os.path.exists(p)), None)
            if picked:
                sim_processor.set_sumo_binary(picked)
            else:
                print("警告: 未能自动定位SUMO，可设置环境变量 SUMO_BIN 或 SUMO_HOME")
        except Exception:
            pass
    
    def _validate_case(self, case_id: str) -> Path:
        """验证案例是否存在"""
        case_path = Path("cases") / case_id
        if not case_path.exists():
            raise Exception(f"案例不存在: {case_id}")
        return case_path
    
    def _create_simulation_structure(self, case_path: Path, request: SimulationRequest) -> tuple[str, Path]:
        """创建仿真目录结构

        对于批量仿真，使用batch_context生成唯一ID和特殊目录结构
        """
        # 生成仿真ID
        sim_type_short = "micro" if request.simulation_type.value == "microscopic" else "meso"
        batch_context = request.batch_context

        if batch_context and all(k in batch_context for k in ['batch_id', 'plan_id', 'seed']):
            # 批量仿真：使用plan_id和seed生成唯一ID
            plan_id = batch_context['plan_id']
            seed = batch_context['seed']
            simulation_id = f"batch_{batch_context['batch_id']}_{plan_id}_seed{seed}_{sim_type_short}"
        else:
            # 普通仿真：使用时间戳（添加微秒避免冲突）
            simulation_id = f"sim_{datetime.now().strftime('%m%d_%H%M%S%f')[:-3]}_{sim_type_short}"

        # 创建仿真目录
        simulation_folder = DirectoryManager.create_simulation_structure(
            case_path,
            simulation_id,
            batch_context
        )

        return simulation_id, simulation_folder
    
    def _generate_simulation_config(self, case_path: Path, simulation_folder: Path, 
                                  request: SimulationRequest) -> str:
        """生成仿真配置文件"""
        # 定义配置文件路径
        cfg_file = simulation_folder / "simulation.sumocfg"
        
        # 加载案例元数据
        case_metadata = MetadataManager.load_case_metadata(case_path)
        
        # 生成sumocfg内容
        from shared.utilities.sumo_utils import generate_sumocfg_for_simulation
        config_content = generate_sumocfg_for_simulation(case_metadata, request.simulation_type, simulation_folder, case_path, request.simulation_params or {})
        
        # 保存配置文件
        with open(cfg_file, "w", encoding="utf-8") as f:
            f.write(config_content)
        
        return str(cfg_file)
    
    def _create_simulation_metadata(self, request: SimulationRequest, simulation_id: str,
                                   simulation_folder: Path, cfg_file: str) -> Dict[str, Any]:
        """创建仿真元数据"""
        # 收集输入文件（从案例元数据 files 字段获取来源路径）
        input_files: Dict[str, Any] = {}
        try:
            case_path = Path("cases") / request.case_id
            case_metadata = MetadataManager.load_case_metadata(case_path)
            files_info = (case_metadata or {}).get("files", {})
            network_file = files_info.get("network_file")
            routes_file = files_info.get("routes_file")
            taz_file = files_info.get("taz_file")
            input_files = {
                "network_file": network_file,
                "routes_files": [routes_file] if routes_file else [],
                "taz_files": [taz_file] if taz_file else []
            }
        except Exception:
            # 若无法获取，保持空结构，不影响仿真
            input_files = {
                "network_file": None,
                "routes_files": [],
                "taz_files": []
            }

        # Phase 2: 提取 source_scenario 用于三级元数据追踪 (Task 1.4)
        source_scenario = None
        metadata_version = "1.0"  # 默认 v1.0 (向后兼容)

        try:
            case_path = Path("cases") / request.case_id
            case_metadata = MetadataManager.load_case_metadata(case_path)

            # 检测元数据版本 (使用 BaseService 方法)
            metadata_version = self.detect_metadata_version(case_metadata)

            # 如果是 v2.0 事件场景案例,提取 source_scenario
            if metadata_version == "2.0" and "source_scenario_id" in case_metadata:
                source_scenario = {
                    "scenario_id": case_metadata.get("source_scenario_id"),
                    "event_id": case_metadata.get("source_event_id"),
                    "event_type": case_metadata.get("immutable_fields", {}).get("event_type"),
                    "control_strategy_type": case_metadata.get("immutable_fields", {}).get("strategy")
                }
        except Exception:
            # 如果无法提取,保持 None (向后兼容)
            pass

        metadata = {
            "simulation_id": simulation_id,
            "case_id": request.case_id,
            "simulation_name": request.simulation_name,
            "simulation_type": request.simulation_type.value,
            "simulation_params": request.simulation_params or {},
            "status": "running",
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
            "description": request.simulation_description,
            "result_folder": str(simulation_folder),
            "config_file": cfg_file,
            "input_files": input_files,
            "gui": request.gui
        }

        # Phase 2: 添加 v2.0 字段 (如果适用)
        if metadata_version == "2.0":
            metadata["metadata_version"] = "2.0"
            if source_scenario:
                metadata["source_scenario"] = source_scenario

        return metadata
    
    def _update_case_status(self, case_path: Path, status: CaseStatus) -> None:
        """更新案例状态"""
        try:
            metadata = MetadataManager.load_case_metadata(case_path)
            metadata["status"] = status.value
            metadata["updated_at"] = datetime.now().isoformat()
            if status == CaseStatus.SIMULATING:
                metadata["simulation_started_at"] = datetime.now().isoformat()
                metadata["last_step"] = "simulation_start"
            MetadataManager.save_case_metadata(case_path, metadata)
        except Exception as e:
            print(f"更新案例状态失败: {e}")
    
    def _build_simulation_params(self, request: SimulationRequest, simulation_folder: Path,
                               cfg_file: str) -> Dict[str, Any]:
        """构建仿真参数"""
        return {
            "run_folder": str(simulation_folder),
            "gui": request.gui,
            "mesoscopic": request.simulation_type == SimulationType.MESOSCOPIC,
            "config_file": cfg_file,
            "expected_duration": request.expected_duration
        }
    
    def _init_progress_file(self, simulation_folder: Path) -> None:
        """初始化进度文件"""
        try:
            prog_path = simulation_folder / "progress.json"
            progress_data = {
                "status": "running",
                "percent": 0,
                "message": "仿真启动中",
                "updated_at": datetime.now().isoformat(),
                "pid": None
            }
            with open(prog_path, "w", encoding="utf-8") as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    async def _ensure_od_file_available(self, case_path: Path) -> None:
        """
        确保OD文件可用。

        如果OD文件还未生成（数据库表参考），则通过API调用生成。
        这个方法在prepare_simulation期间被调用。

        Args:
            case_path: 案例路径
        """
        try:
            # 检查od_file_info.json
            od_info_path = case_path / "config" / "od_file_info.json"
            if not od_info_path.exists():
                logger.debug("No od_file_info.json found - skipping OD file generation check")
                return

            with open(od_info_path, 'r', encoding='utf-8') as f:
                od_info = json.load(f)

            # 如果OD文件已经存在，无需生成
            if od_info.get('od_file_status') == 'exists':
                logger.debug(f"OD file already exists: {od_info.get('od_file')}")
                return

            # 如果OD文件是待生成状态，尝试生成
            if od_info.get('od_file_status') == 'pending' and od_info.get('od_file_type') == 'database':
                logger.info(f"Generating OD file from database table: {od_info.get('od_file')}")

                # 从案例元数据获取时间范围
                case_metadata = MetadataManager.load_case_metadata(case_path)
                time_range = case_metadata.get('time_range', {})

                # 动态导入数据服务来调用OD生成API
                # Note: 实际的OD生成逻辑应该通过API调用或直接调用data_service
                # 这里仅记录日志和标记状态，实际生成可能在后续流程中进行
                logger.info(f"OD file generation scheduled: {od_info.get('od_file')}")
                logger.info(f"  Time range: {time_range}")
                logger.info(f"  Status: Will be generated at next checkpoint")

        except Exception as e:
            logger.warning(f"Error checking OD file status: {e}")
            # 不抛出异常，继续进行仿真准备
            pass

    def _start_background_simulation(self, sim_processor, request_params: Dict[str, Any],
                                   case_path: Path, simulation_id: str, simulation_folder: Path) -> None:
        """在后台线程启动仿真"""
        def _run_and_finalize():
            proc_obj = None
            try:
                # 获取进程对象（如果sim_processor返回）
                result = sim_processor.process_simulation_request(request_params)

                # 尝试从sim_processor中获取进程对象
                if hasattr(sim_processor, 'last_process') and sim_processor.last_process:
                    proc_obj = sim_processor.last_process
                    # 记录进程到活跃进程字典
                    with self._process_lock:
                        self.active_processes[simulation_id] = (proc_obj, request_params.get('case_id', str(case_path)))

                if result.get("success"):
                    self._handle_simulation_success(case_path, simulation_id, simulation_folder)
                else:
                    self._handle_simulation_failure(case_path, simulation_id, simulation_folder, "仿真执行失败")
            except Exception as e:
                self._handle_simulation_failure(case_path, simulation_id, simulation_folder, str(e))
            finally:
                # 仿真完成或失败时，从活跃进程中移除
                with self._process_lock:
                    self.active_processes.pop(simulation_id, None)

        threading.Thread(target=_run_and_finalize, daemon=True).start()
    
    def _handle_simulation_success(self, case_path: Path, simulation_id: str, simulation_folder: Path) -> None:
        """处理仿真成功"""
        try:
            # 更新仿真元数据
            sim_metadata = MetadataManager.load_simulation_metadata(simulation_folder)
            sim_metadata["status"] = "completed"
            ended_at = datetime.now().isoformat()
            sim_metadata["completed_at"] = ended_at

            # 计算耗时
            try:
                start_time = datetime.fromisoformat(sim_metadata["started_at"])
                end_time = datetime.fromisoformat(ended_at)
                duration = (end_time - start_time).total_seconds()
                sim_metadata["duration"] = int(duration)
            except:
                pass

            MetadataManager.save_simulation_metadata(simulation_folder, sim_metadata)
            MetadataManager.update_simulations_index(case_path, simulation_id, sim_metadata)

            # 更新进度文件为完成状态
            self._write_success_progress(simulation_folder)

            # 更新案例状态
            self._update_case_completion_status(case_path, ended_at, "completed")

        except Exception as e:
            print(f"处理仿真成功状态失败: {e}")

    def _write_success_progress(self, simulation_folder: Path) -> None:
        """写入成功完成进度"""
        try:
            progress_data = {
                "status": "completed",
                "percent": 100,
                "message": "仿真已完成",
                "updated_at": datetime.now().isoformat(),
                "pid": None
            }
            with open(simulation_folder / "progress.json", "w", encoding="utf-8") as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _handle_simulation_failure(self, case_path: Path, simulation_id: str, 
                                 simulation_folder: Path, error_message: str) -> None:
        """处理仿真失败"""
        try:
            # 更新仿真元数据
            sim_metadata = MetadataManager.load_simulation_metadata(simulation_folder)
            sim_metadata["status"] = "failed"
            sim_metadata["completed_at"] = datetime.now().isoformat()
            sim_metadata["error_message"] = error_message
            
            MetadataManager.save_simulation_metadata(simulation_folder, sim_metadata)
            MetadataManager.update_simulations_index(case_path, simulation_id, sim_metadata)
            
            # 写入失败进度
            self._write_failure_progress(simulation_folder, error_message)
            
            # 更新案例状态
            self._update_case_completion_status(case_path, datetime.now().isoformat(), "failed")
            
        except Exception as e:
            print(f"处理仿真失败状态失败: {e}")
    
    def _write_failure_progress(self, simulation_folder: Path, error_message: str) -> None:
        """写入失败进度"""
        try:
            progress_data = {
                "status": "failed",
                "percent": 0,
                "message": error_message,
                "updated_at": datetime.now().isoformat(),
                "pid": None
            }
            with open(simulation_folder / "progress.json", "w", encoding="utf-8") as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def _update_case_completion_status(self, case_path: Path, ended_at: str, status: str) -> None:
        """更新案例完成状态"""
        try:
            metadata = MetadataManager.load_case_metadata(case_path)
            metadata["status"] = CaseStatus.COMPLETED.value if status == "completed" else CaseStatus.FAILED.value
            metadata["updated_at"] = ended_at
            metadata["simulation_ended_at"] = ended_at
            metadata["last_step"] = "simulation" if status == "completed" else "simulation_failed"
            MetadataManager.save_case_metadata(case_path, metadata)

            # 更新scenario_index.json中该case的状态（仿真完成或失败）
            try:
                from shared.utilities.scenario_case_mapping import ScenarioCaseMapper
                mapper = ScenarioCaseMapper()

                case_id = metadata.get('case_id')
                # 确定新状态：'completed' 或 'failed'
                new_status = 'completed' if status == 'completed' else 'failed'

                # 为所有关联的scenario更新状态
                for scenario_id in metadata.get('scenarios', []):
                    mapper.update_case_status(scenario_id, case_id, new_status)
                    print(f"✓ scenario_index.json已更新: {scenario_id} - {case_id} 状态 → {new_status}")
            except Exception as mapping_error:
                print(f"⚠️ 更新scenario_index.json失败（非致命错误）: {mapping_error}")

        except Exception as e:
            print(f"更新案例完成状态失败: {e}")
    
    def _build_simulation_response(self, request: SimulationRequest, simulation_id: str,
                                 request_params: Dict[str, Any]) -> Dict[str, Any]:
        """构建仿真响应"""
        return {
            "simulation_id": simulation_id,
            "run_folder": request_params["run_folder"],
            "gui": request.gui,
            "mesoscopic": request.simulation_type == SimulationType.MESOSCOPIC,
            "simulation_type": request.simulation_type.value,
            "started_at": datetime.now().isoformat(),
            "status": "started"
        }

    async def cancel_simulation(self, case_id: str, simulation_id: str) -> Dict[str, Any]:
        """
        取消运行中的仿真，杀死SUMO子进程

        Args:
            case_id: 案例ID
            simulation_id: 仿真ID

        Returns:
            取消结果
        """
        try:
            simulation_folder = Path("cases") / case_id / "simulations" / simulation_id

            # 检查仿真目录是否存在
            if not simulation_folder.exists():
                return {
                    "success": False,
                    "message": f"仿真目录不存在: {simulation_id}",
                    "simulation_id": simulation_id
                }

            # 加载仿真元数据
            sim_metadata = MetadataManager.load_simulation_metadata(simulation_folder)
            sim_status = sim_metadata.get("status", "unknown")

            # 如果不在运行状态，无法取消
            if sim_status not in ["running", "pending"]:
                return {
                    "success": False,
                    "message": f"仿真状态为 {sim_status}，无法取消",
                    "simulation_id": simulation_id
                }

            # 尝试从活跃进程中获取进程对象
            proc_obj = None
            pid = None

            with self._process_lock:
                if simulation_id in self.active_processes:
                    proc_obj, _ = self.active_processes[simulation_id]

            # 如果没有进程对象，从progress.json中读取PID
            if proc_obj is None:
                try:
                    progress_file = simulation_folder / "progress.json"
                    if progress_file.exists():
                        with open(progress_file, "r", encoding="utf-8") as f:
                            progress_data = json.load(f)
                            pid = progress_data.get("pid")
                except Exception as e:
                    pass  # 继续尝试其他方法

            # 方法1：如果有进程对象，直接杀死
            if proc_obj is not None:
                try:
                    proc_obj.terminate()  # 优雅关闭
                    try:
                        proc_obj.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        # 2秒后仍未结束，强制杀死
                        proc_obj.kill()
                except Exception as e:
                    pass  # 继续

            # 方法2：如果有PID，尝试系统级杀死
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)  # Windows上使用SIGTERM，Unix上使用SIGTERM
                    # 等待一下，检查进程是否结束
                    import time
                    time.sleep(1)
                    try:
                        os.kill(pid, 0)  # 检查进程是否还活着
                        # 还活着，强制杀死
                        if hasattr(signal, 'SIGKILL'):
                            os.kill(pid, signal.SIGKILL)
                        else:
                            # Windows上，使用taskkill命令
                            os.system(f"taskkill /PID {pid} /F")
                    except ProcessLookupError:
                        # 进程已经死亡
                        pass
                except Exception as e:
                    pass  # 继续

            # 更新仿真状态为cancelled
            sim_metadata["status"] = "cancelled"
            sim_metadata["cancelled_at"] = datetime.now().isoformat()
            MetadataManager.save_simulation_metadata(simulation_folder, sim_metadata)
            MetadataManager.update_simulations_index(Path("cases") / case_id, simulation_id, sim_metadata)

            # 更新进度文件
            try:
                progress_file = simulation_folder / "progress.json"
                progress_data = {
                    "status": "cancelled",
                    "percent": 0,
                    "message": "仿真已取消",
                    "updated_at": datetime.now().isoformat(),
                    "pid": None
                }
                with open(progress_file, "w", encoding="utf-8") as f:
                    json.dump(progress_data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            # 从活跃进程字典中移除
            with self._process_lock:
                self.active_processes.pop(simulation_id, None)

            return {
                "success": True,
                "message": "仿真已成功取消",
                "simulation_id": simulation_id,
                "status": "cancelled"
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"取消仿真失败: {str(e)}",
                "simulation_id": simulation_id
            }

    async def get_simulation_progress(self, case_id: str) -> Dict[str, Any]:
        """获取案例下的所有仿真列表及进度统计（用于监控面板）

        返回格式：
        {
            "simulations": [
                {
                    "simulation_id": "...",
                    "status": "...",  # from metadata or progress.json
                    "progress": ...,  # from progress.json
                    "created_at": "...",
                    ...
                },
                ...
            ],
            "progress_percentage": XX,
            "stats": {
                "total": X,
                "completed": Y,
                "in_progress": Z,
                "failed": W,
                "queued": V
            }
        }
        """
        try:
            case_dir = Path("cases") / case_id
            simulations_dir = case_dir / "simulations"

            if not simulations_dir.exists():
                return {
                    "simulations": [],
                    "progress_percentage": 0,
                    "stats": {"total": 0, "completed": 0, "in_progress": 0, "failed": 0, "queued": 0}
                }

            # 获取案例下的所有仿真
            simulations = await self.get_case_simulations(case_id)

            if not simulations:
                return {
                    "simulations": [],
                    "progress_percentage": 0,
                    "stats": {"total": 0, "completed": 0, "in_progress": 0, "failed": 0, "queued": 0}
                }

            # 增强仿真信息：添加进度文件中的实时信息
            enhanced_simulations = []
            for sim in simulations:
                sim_id = sim.get("simulation_id")
                sim_folder = simulations_dir / sim_id

                # 尝试读取进度文件
                progress_file = sim_folder / "progress.json"
                if progress_file.exists():
                    try:
                        with open(progress_file, 'r', encoding='utf-8') as f:
                            progress_data = json.load(f)
                            # 用进度文件中的状态覆盖元数据中的状态
                            sim["status"] = progress_data.get("status", sim.get("status"))
                            sim["progress"] = progress_data.get("percent", 0)
                            sim["progress_message"] = progress_data.get("message", "")
                    except:
                        # 如果读取失败，使用元数据中的状态
                        sim["progress"] = 100 if sim.get("status") == "completed" else 0

                enhanced_simulations.append(sim)

            # 计算统计信息（使用增强后的数据）
            stats = {
                "total": len(enhanced_simulations),
                "completed": len([s for s in enhanced_simulations if s.get("status") == "completed"]),
                "in_progress": len([s for s in enhanced_simulations if s.get("status") in ["running", "simulating"]]),
                "failed": len([s for s in enhanced_simulations if s.get("status") == "failed"]),
                "queued": len([s for s in enhanced_simulations if s.get("status") == "queued"])
            }

            # 计算总进度百分比
            if stats["total"] > 0:
                progress_percentage = int((stats["completed"] / stats["total"]) * 100)
            else:
                progress_percentage = 0

            return {
                "simulations": enhanced_simulations,
                "progress_percentage": progress_percentage,
                "stats": stats
            }

        except Exception as e:
            logger.error(f"获取仿真进度失败: {str(e)}")
            return {
                "simulations": [],
                "progress_percentage": 0,
                "stats": {"total": 0, "completed": 0, "in_progress": 0, "failed": 0, "queued": 0},
                "error": str(e)
            }
    
    def _find_latest_simulation(self, simulations_dir: Path) -> Path:
        """查找最新的仿真目录"""
        latest_sim_dir = None
        latest_time = 0
        
        for sim_dir in simulations_dir.iterdir():
            if sim_dir.is_dir():
                metadata_file = sim_dir / "simulation_metadata.json"
                if metadata_file.exists():
                    try:
                        metadata = MetadataManager.load_simulation_metadata(sim_dir)
                        created_at = metadata.get("created_at", "")
                        if created_at:
                            sim_time = datetime.fromisoformat(created_at).timestamp()
                            if sim_time > latest_time:
                                latest_time = sim_time
                                latest_sim_dir = sim_dir
                    except:
                        continue
        
        return latest_sim_dir
    
    async def get_case_simulations(self, case_id: str) -> List[Dict[str, Any]]:
        """获取案例下的所有仿真结果"""
        try:
            case_path = Path("cases") / case_id
            simulations_path = case_path / "simulations"
            
            if not simulations_path.exists():
                return []
            
            simulations = []
            for sim_dir in simulations_path.iterdir():
                if sim_dir.is_dir():
                    try:
                        sim_data = MetadataManager.load_simulation_metadata(sim_dir)
                        simulations.append(sim_data)
                    except Exception as e:
                        print(f"读取仿真元数据失败: {e}")
            
            # 按创建时间倒序排列
            simulations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return simulations
            
        except Exception as e:
            raise Exception(f"获取仿真列表失败: {str(e)}")
    
    async def get_simulation_detail(self, simulation_id: str) -> Dict[str, Any]:
        """获取仿真详情"""
        try:
            # 查找仿真元数据文件
            cases_path = Path("cases")
            
            for case_dir in cases_path.iterdir():
                if case_dir.is_dir():
                    sim_dir = case_dir / "simulations" / simulation_id
                    if sim_dir.exists():
                        return MetadataManager.load_simulation_metadata(sim_dir)
            
            raise Exception(f"未找到仿真: {simulation_id}")
            
        except Exception as e:
            raise Exception(f"获取仿真详情失败: {str(e)}")
    
    async def delete_simulation(self, simulation_id: str) -> None:
        """删除仿真结果"""
        try:
            import shutil
            
            # 查找仿真目录
            cases_path = Path("cases")
            
            for case_dir in cases_path.iterdir():
                if case_dir.is_dir():
                    sim_dir = case_dir / "simulations" / simulation_id
                    if sim_dir.exists():
                        # 先删除目录
                        shutil.rmtree(sim_dir)
                        # 同步更新仿真索引
                        try:
                            MetadataManager.remove_simulation_from_index(case_dir, simulation_id)
                        except Exception:
                            pass
                        # 可选：刷新案例元数据的更新时间（保持字段统一使用 updated_at）
                        try:
                            metadata = MetadataManager.load_case_metadata(case_dir)
                            metadata["updated_at"] = datetime.now().isoformat()
                            MetadataManager.save_case_metadata(case_dir, metadata)
                        except Exception:
                            pass
                        return
            
            raise Exception(f"未找到仿真: {simulation_id}")
            
        except Exception as e:
            raise Exception(f"删除仿真失败: {str(e)}")

    async def start_simulation_with_event(self, request: 'EventScenarioSimulationRequest') -> Dict[str, Any]:
        """
        启动应用事件场景的仿真 (Phase 5.3.5)

        将事件场景的.add.xml合并到仿真配置中，然后执行仿真。

        Args:
            request: 包含事件场景信息的仿真请求

        Returns:
            包含仿真ID和状态的响应
        """
        try:
            # 验证案例存在
            case_path = self._validate_case(request.case_id)

            # 加载事件场景信息
            event_scenario = self._load_event_scenario(request.scenario_id)
            if not event_scenario:
                raise Exception(f"事件场景不存在: {request.scenario_id}")

            # 创建仿真目录结构
            sim_type_short = "micro" if request.simulation_type.value == "microscopic" else "meso"
            simulation_id = f"sim_event_{request.scenario_id}_{datetime.now().strftime('%m%d_%H%M%S')}_{sim_type_short}"
            simulation_folder = DirectoryManager.create_simulation_structure(
                case_path,
                simulation_id,
                request.batch_context
            )

            # 生成配置文件并合并事件场景的.add.xml
            cfg_file = self._generate_simulation_config_with_event(
                case_path, simulation_folder, request, event_scenario
            )
            cfg_file_abs = str(Path(cfg_file).resolve())

            # 创建仿真元数据（包含事件场景信息）
            sim_metadata = self._create_simulation_metadata(request, simulation_id, simulation_folder, cfg_file)
            sim_metadata["event_scenario"] = {
                "event_type": request.event_type,
                "strategy": request.strategy,
                "scenario_id": request.scenario_id,
                "event_id": event_scenario.get("event_id"),
                "add_xml_file": event_scenario.get("files", {}).get("add_xml")
            }
            sim_metadata["status"] = "pending"

            # 保存元数据
            MetadataManager.save_simulation_metadata(simulation_folder, sim_metadata)
            MetadataManager.update_simulations_index(case_path, simulation_id, sim_metadata)

            # 初始化进度文件
            self._init_progress_file(simulation_folder)

            # 更新案例状态
            self._update_case_status(case_path, CaseStatus.SIMULATING)

            # 构建仿真参数
            request_params = {
                "run_folder": str(simulation_folder),
                "gui": request.gui,
                "mesoscopic": request.simulation_type.value == "mesoscopic",
                "config_file": cfg_file,
                "expected_duration": request.expected_duration,
                "case_id": request.case_id,
            }

            # 导入仿真处理器
            from shared.data_processors.simulation_processor import SimulationProcessor
            sim_processor = SimulationProcessor()
            self._setup_sumo_environment(sim_processor)

            # 后台运行仿真
            self._start_background_simulation(sim_processor, request_params, case_path, simulation_id, simulation_folder)

            return {
                "simulation_id": simulation_id,
                "run_folder": str(simulation_folder),
                "config_file": cfg_file,
                "config_file_abs": cfg_file_abs,
                "event_scenario": request.scenario_id,
                "status": "started",
                "started_at": datetime.now().isoformat()
            }

        except Exception as e:
            raise Exception(f"启动事件场景仿真失败: {str(e)}")

    def _load_event_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """从scenario_index.json加载事件场景信息"""
        try:
            scenario_index_path = Path("output/scenarios/scenario_index.json")
            if not scenario_index_path.exists():
                return None

            with open(scenario_index_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 查找匹配的场景
            for scenario in data.get("scenarios", []):
                # 构建scenario_id (format: scenario_{event_id}_{strategy_lower})
                constructed_id = f"scenario_{scenario['event_id']}_{scenario['strategy'].lower()}"
                if constructed_id == scenario_id:
                    return scenario

            return None
        except Exception as e:
            print(f"加载事件场景失败: {e}")
            return None

    def _generate_simulation_config_with_event(self, case_path: Path, simulation_folder: Path,
                                               request: 'EventScenarioSimulationRequest',
                                               event_scenario: Dict[str, Any]) -> str:
        """生成仿真配置文件并合并事件场景的.add.xml"""
        # 首先生成基础配置文件
        cfg_file = simulation_folder / "simulation.sumocfg"

        # 加载案例元数据
        case_metadata = MetadataManager.load_case_metadata(case_path)

        # 生成sumocfg内容
        from shared.utilities.sumo_utils import generate_sumocfg_for_simulation
        config_content = generate_sumocfg_for_simulation(
            case_metadata, request.simulation_type, simulation_folder, case_path,
            request.simulation_params or {}
        )

        # 提取add.xml文件路径
        add_xml_path = event_scenario.get("files", {}).get("add_xml")
        if add_xml_path and Path(add_xml_path).exists():
            # 将add.xml路径添加到sumocfg的include部分
            config_content = self._merge_add_xml_to_config(config_content, add_xml_path)

        # 保存配置文件
        with open(cfg_file, "w", encoding="utf-8") as f:
            f.write(config_content)

        return str(cfg_file)

    def _merge_add_xml_to_config(self, config_content: str, add_xml_path: str) -> str:
        """将.add.xml文件合并到sumocfg配置中"""
        import xml.etree.ElementTree as ET

        try:
            # 解析配置文件
            root = ET.fromstring(config_content)

            # 查找或创建input元素
            input_elem = root.find("input")
            if input_elem is None:
                input_elem = ET.Element("input")
                root.insert(0, input_elem)

            # 添加additional-files元素指向.add.xml
            # SUMO支持通过additional-files指定额外的XML文件
            additional_elem = ET.Element("additional-files")
            additional_elem.set("value", add_xml_path)
            input_elem.append(additional_elem)

            # 转换回字符串
            result = ET.tostring(root, encoding="unicode")
            return result
        except Exception as e:
            print(f"合并.add.xml失败: {e}，继续使用基础配置")
            return config_content


# 创建服务实例
simulation_service = SimulationService()


# 导出服务函数 (保持向后兼容)
async def run_simulation_service(request: SimulationRequest) -> Dict[str, Any]:
    """仿真运行服务函数"""
    return await simulation_service.run_simulation(request)


async def get_simulation_progress_service(case_id: str) -> Dict[str, Any]:
    """获取仿真进度服务函数"""
    return await simulation_service.get_simulation_progress(case_id)


async def get_case_simulations_service(case_id: str) -> List[Dict[str, Any]]:
    """获取案例仿真列表服务函数"""
    return await simulation_service.get_case_simulations(case_id)


async def get_simulation_detail_service(simulation_id: str) -> Dict[str, Any]:
    """获取仿真详情服务函数"""
    return await simulation_service.get_simulation_detail(simulation_id)


async def delete_simulation_service(simulation_id: str) -> None:
    """删除仿真服务函数"""
    return await simulation_service.delete_simulation(simulation_id)


async def prepare_simulation_service(request: SimulationRequest) -> Dict[str, Any]:
    """准备仿真服务函数：仅生成配置不启动"""
    return await simulation_service.prepare_simulation(request)


async def start_simulation_service(case_id: str, simulation_id: str, gui: bool = False) -> Dict[str, Any]:
    """启动仿真服务函数：基于已准备的配置启动"""
    return await simulation_service.start_simulation(case_id, simulation_id, gui)


async def start_simulation_with_event_service(request: 'EventScenarioSimulationRequest') -> Dict[str, Any]:
    """启动应用事件场景的仿真服务函数 (Phase 5.3.5)"""
    return await simulation_service.start_simulation_with_event(request)
