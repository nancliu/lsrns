"""
仿真运行服务 - 负责仿真运行和进度管理相关业务逻辑
"""

import os
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from ..models import SimulationRequest, SimulationType, CaseStatus
from .base_service import BaseService, MetadataManager, DirectoryManager


class SimulationService(BaseService):
    """仿真运行服务类"""
    
    async def run_simulation(self, request: SimulationRequest) -> Dict[str, Any]:
        """
        运行仿真的主要业务逻辑
        """
        try:
            # 导入仿真处理器
            from shared.data_processors.simulation_processor import SimulationProcessor
            
            # 创建仿真处理器并设置SUMO环境
            sim_processor = SimulationProcessor()
            self._setup_sumo_environment(sim_processor)
            
            # 验证案例并创建仿真目录
            case_path = self._validate_case(request.case_id)
            simulation_id, simulation_folder = self._create_simulation_structure(case_path, request)
            
            # 生成配置文件
            cfg_file = self._generate_simulation_config(case_path, simulation_folder, request)
            
            # 创建并保存仿真元数据
            sim_metadata = self._create_simulation_metadata(request, simulation_id, simulation_folder, cfg_file)
            MetadataManager.save_simulation_metadata(simulation_folder, sim_metadata)
            
            # 更新案例状态和索引
            self._update_case_status(case_path, CaseStatus.SIMULATING)
            MetadataManager.update_simulations_index(case_path, simulation_id, sim_metadata)
            
            # 准备仿真参数
            request_params = self._build_simulation_params(request, simulation_folder, cfg_file)
            
            # 初始化进度文件
            self._init_progress_file(simulation_folder)
            
            # 后台运行仿真
            self._start_background_simulation(sim_processor, request_params, case_path, 
                                            simulation_id, simulation_folder)
            
            return self._build_simulation_response(request, simulation_id, request_params)
            
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
        """创建仿真目录结构"""
        # 生成仿真ID
        sim_type_short = "micro" if request.simulation_type.value == "microscopic" else "meso"
        simulation_id = f"sim_{datetime.now().strftime('%m%d_%H%M%S')}_{sim_type_short}"
        
        # 创建仿真目录
        simulation_folder = DirectoryManager.create_simulation_structure(case_path, simulation_id)
        
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

        return {
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
    
    def _start_background_simulation(self, sim_processor, request_params: Dict[str, Any], 
                                   case_path: Path, simulation_id: str, simulation_folder: Path) -> None:
        """在后台线程启动仿真"""
        def _run_and_finalize():
            try:
                result = sim_processor.process_simulation_request(request_params)
                if result.get("success"):
                    self._handle_simulation_success(case_path, simulation_id, simulation_folder)
                else:
                    self._handle_simulation_failure(case_path, simulation_id, simulation_folder, "仿真执行失败")
            except Exception as e:
                self._handle_simulation_failure(case_path, simulation_id, simulation_folder, str(e))
        
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
            
            # 更新案例状态
            self._update_case_completion_status(case_path, ended_at, "completed")
            
        except Exception as e:
            print(f"处理仿真成功状态失败: {e}")
    
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
    
    async def get_simulation_progress(self, case_id: str) -> Dict[str, Any]:
        """获取仿真进度"""
        try:
            case_dir = Path("cases") / case_id
            simulations_dir = case_dir / "simulations"
            
            if not simulations_dir.exists():
                return {"status": "unknown", "percent": 0, "message": "暂无进度"}
            
            # 查找最新的仿真目录
            latest_sim_dir = self._find_latest_simulation(simulations_dir)
            
            if not latest_sim_dir:
                return {"status": "unknown", "percent": 0, "message": "暂无进度"}
            
            # 读取进度文件
            prog_file = latest_sim_dir / "progress.json"
            if not prog_file.exists():
                return {"status": "unknown", "percent": 0, "message": "暂无进度"}
            
            with open(prog_file, "r", encoding="utf-8") as f:
                return json.load(f)
                
        except Exception as e:
            return {"status": "error", "percent": 0, "message": str(e)}
    
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
