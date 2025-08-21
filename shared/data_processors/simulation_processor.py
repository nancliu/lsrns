"""
仿真处理器
迁移自原有的仿真运行逻辑
"""

import os
import subprocess
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import xml.etree.ElementTree as ET
from collections import deque
from queue import Queue, Empty
import threading
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimulationProcessor:
    """仿真处理器类"""
    
    def __init__(self):
        self.sumo_binary = "sumo"  # 默认SUMO二进制文件路径
        
    def set_sumo_binary(self, binary_path: str):
        """
        设置SUMO二进制文件路径
        
        Args:
            binary_path: SUMO二进制文件路径
        """
        self.sumo_binary = binary_path
        logger.info(f"设置SUMO二进制文件路径: {binary_path}")
    
    # NOTE: 仅旧版脚本使用。API 主流程已统一使用 api.utils.generate_sumocfg。
    # 为避免维护冲突，本方法保留签名但不再实现，直接抛出说明性异常。
    def generate_sumocfg(self, *args, **kwargs) -> str:
        raise RuntimeError(
            "generate_sumocfg is deprecated here. Use api.utils.generate_sumocfg in API pipeline."
        )
    
    def run_simulation(self, config_file: str, gui: bool = False, 
                      mesoscopic: bool = False,
                      run_folder: Optional[str] = None,
                      progress_path: Optional[str] = None,
                      expected_duration: Optional[int] = None) -> Dict[str, Any]:
        """
        运行仿真
        
        Args:
            config_file: 配置文件路径
            gui: 是否启用GUI
            mesoscopic: 是否使用中观仿真
            run_folder: 仿真输出目录，用于放置summary.xml与进度文件
            progress_path: 进度文件路径（progress.json）
            expected_duration: 预期仿真时长（秒），用于估算百分比
            
        Returns:
            仿真结果
        """
        try:
            logger.info(f"开始运行仿真: {config_file}")
            
            # 根据是否GUI选择可执行文件
            binary = "sumo-gui" if gui else self.sumo_binary
            if mesoscopic:
                cmd = [binary, "--mesosim"]
            else:
                cmd = [binary]
            
            if not gui:
                # 为了跟踪进度，保留必要输出，仍关闭警告
                cmd.append("--no-warnings")

            # 以sumocfg目录作为工作目录，确保相对路径解析一致（替代 -C）
            norm_cfg = config_file.replace('\\','/')
            config_dir = os.path.dirname(norm_cfg) or '.'
            cfg_arg = os.path.basename(norm_cfg) or "simulation.sumocfg"

            # 添加 -c 和配置文件名（相对于cwd）
            cmd.extend(["-c", cfg_arg])

            # GUI 模式下自动开始
            if gui:
                cmd.append("--start")

            logger.info(f"执行命令: {' '.join(cmd)}")
            logger.info(f"工作目录: {config_dir}")
            
            # 启动前清理旧的 summary.xml，避免读取上一次结果导致百分比飙升
            try:
                if run_folder:
                    old_summary = os.path.join(run_folder, "summary.xml")
                    if os.path.exists(old_summary):
                        os.remove(old_summary)
            except Exception:
                pass

            # 运行仿真
            start_time = datetime.now()
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=config_dir
            )

            # 异步读取stdout，避免主循环阻塞在readline
            stdout_queue: Queue[str] = Queue(maxsize=1000)
            def _drain_stdout(p: subprocess.Popen):
                try:
                    if not p.stdout:
                        return
                    for line in p.stdout:
                        try:
                            stdout_queue.put_nowait(line.rstrip("\n"))
                        except Exception:
                            pass
                except Exception:
                    pass

            reader_thread = threading.Thread(target=_drain_stdout, args=(proc,), daemon=True)
            reader_thread.start()

            def write_progress(status: str, percent: int, message: str = "", extra: Optional[Dict[str, Any]] = None):
                if not progress_path:
                    return
                try:
                    payload = {
                        "status": status,
                        "percent": max(0, min(100, int(percent))),
                        "message": message[-500:] if message else "",
                        "updated_at": datetime.now().isoformat(),
                        "pid": proc.pid if proc and proc.poll() is None else None
                    }
                    if extra:
                        payload.update(extra)
                    os.makedirs(os.path.dirname(progress_path), exist_ok=True)
                    with open(progress_path, "w", encoding="utf-8") as f:
                        json.dump(payload, f, ensure_ascii=False, indent=2)
                except Exception as _e:
                    logger.debug(f"写入进度失败: {_e}")

            def get_sim_time_from_summary() -> Optional[float]:
                try:
                    # 修复路径解析问题：优先检查运行目录下的summary.xml
                    candidates = []
                    if run_folder:
                        candidates.append(os.path.join(run_folder, "summary.xml"))
                    
                    # 回退路径：从config目录到simulation目录
                    cfg_dir = config_dir
                    candidates.append(os.path.normpath(os.path.join(cfg_dir, "../../simulation/summary.xml")))
                    
                    # 额外回退路径：从config目录到simulations/sim_xxx目录
                    candidates.append(os.path.normpath(os.path.join(cfg_dir, "../../simulations/*/summary.xml")))
 
                    def _mtime_ok(path: str) -> bool:
                        try:
                            return os.path.getmtime(path) > start_time.timestamp()
                        except Exception:
                            return True

                    def _tail_parse_time(path: str) -> Optional[float]:
                        try:
                            # 读取文件末尾一段文本，避免未写完导致XML整体解析失败
                            with open(path, 'rb') as f:
                                f.seek(0, os.SEEK_END)
                                size = f.tell()
                                read_len = min(200_000, size)
                                f.seek(size - read_len if size >= read_len else 0)
                                tail = f.read().decode('utf-8', errors='ignore')
                            # 匹配所有step，取最后一个中的time/end/begin
                            matches = list(re.finditer(r"<step[^>]*?(?:time|end|begin)=\"([0-9.]+)\"", tail))
                            if matches:
                                val = float(matches[-1].group(1))
                                return val
                            return None
                        except Exception:
                            return None

                    for sf in candidates:
                        if os.path.exists(sf):
                            if not _mtime_ok(sf):
                                continue
                            # 先尝试完整XML解析
                            try:
                                tree = ET.parse(sf)
                                root = tree.getroot()
                                steps = list(root.findall('.//step'))
                                if steps:
                                    last = steps[-1]
                                    t = last.get('time') or last.get('end') or last.get('begin')
                                    if t is not None:
                                        return float(t)
                            except Exception:
                                # 忽略，回退到tail解析
                                pass
                            # 回退：尾部正则解析
                            t2 = _tail_parse_time(sf)
                            if t2 is not None:
                                return t2
                    return None
                except Exception:
                    return None

            def get_expected_duration_from_summary_header() -> Optional[int]:
                try:
                    # 修复路径解析问题：优先检查运行目录下的summary.xml
                    candidates = []
                    if run_folder:
                        candidates.append(os.path.join(run_folder, "summary.xml"))
                    
                    # 回退路径：从config目录到simulation目录
                    cfg_dir = config_dir
                    candidates.append(os.path.normpath(os.path.join(cfg_dir, "../../simulation/summary.xml")))
                    
                    # 额外回退路径：从config目录到simulations/sim_xxx目录
                    candidates.append(os.path.normpath(os.path.join(cfg_dir, "../../simulations/*/summary.xml")))
                    
                    for sf in candidates:
                        if os.path.exists(sf):
                            try:
                                if os.path.getmtime(sf) <= start_time.timestamp():
                                    continue
                            except Exception:
                                pass
                            text = ''
                            with open(sf, 'r', encoding='utf-8') as f:
                                # 只读前几KB即可
                                text = f.read(4096)
                            m = re.search(r"<time>\s*<begin\s+value=\"([0-9.]+)\"\s*/>\s*<end\s+value=\"([0-9.]+)\"\s*/>\s*</time>", text, re.DOTALL)
                            if m:
                                begin_v = float(m.group(1))
                                end_v = float(m.group(2))
                                total = int(max(0, end_v - begin_v))
                                if total > 0:
                                    return total
                    return None
                except Exception:
                    return None

            last_lines = deque(maxlen=200)
            
            last_percent = 0
            last_write_ts = 0.0
            write_progress("running", 0, "仿真启动中")

            last_line = ""
            while True:
                # 尝试无阻塞获取stdout中的新行
                drained_any = False
                try:
                    while True:
                        line_item = stdout_queue.get_nowait()
                        drained_any = True
                        if line_item:
                            last_line = line_item.strip()
                            try:
                                last_lines.append(last_line)
                            except Exception:
                                pass
                except Empty:
                    pass

                # 若未获得expected_duration，尝试从summary.xml头部注释解析
                if (expected_duration is None) or (isinstance(expected_duration, int) and expected_duration <= 0):
                    try:
                        parsed_total = get_expected_duration_from_summary_header()
                        if parsed_total and parsed_total > 0:
                            expected_duration = parsed_total
                    except Exception:
                        pass

                # 子进程已结束且无更多输出，跳出
                if proc.poll() is not None and not drained_any and stdout_queue.empty():
                    break

                # 估算百分比（仅基于 summary.xml）
                percent = last_percent
                sim_time = get_sim_time_from_summary()
                if expected_duration and expected_duration > 0 and sim_time is not None:
                    percent = int(min(99, (sim_time / expected_duration) * 100))
 
                # 组织更直观的message
                try:
                    if expected_duration and expected_duration > 0:
                        if sim_time is not None:
                            msg_out = f"t={int(sim_time)}s/{int(expected_duration)}s"
                        else:
                            msg_out = f"t=?/{int(expected_duration)}s（waiting summary）"
                    else:
                        msg_out = "waiting summary"
                except Exception:
                    msg_out = "waiting summary"

                now_ts = time.time()
                if percent != last_percent or (now_ts - last_write_ts) >= 10.0:
                    write_progress("running", percent, msg_out)
                    last_percent = percent
                    last_write_ts = now_ts

                time.sleep(0.5)

            end_time = datetime.now()
            return_code = proc.returncode

            if return_code == 0:
                logger.info("仿真运行成功")
                write_progress("completed", 100, "仿真完成")
                return {
                    "success": True,
                    "config_file": config_file,
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "duration": (end_time - start_time).total_seconds(),
                    "stdout": None,
                    "stderr": None
                }
            else:
                tail = "\n".join(list(last_lines)[-50:])
                logger.error("仿真运行失败\n" + tail)
                write_progress("failed", last_percent, "仿真失败", {"return_code": return_code, "last_lines": tail})
                return {
                    "success": False,
                    "config_file": config_file,
                    "error": "SUMO返回非零状态码",
                    "return_code": return_code,
                    "last_lines": tail
                }
                
        except subprocess.TimeoutExpired:
            logger.error("仿真运行超时")
            return {
                "success": False,
                "config_file": config_file,
                "error": "仿真运行超时"
            }
        except Exception as e:
            logger.error(f"仿真运行异常: {e}")
            return {
                "success": False,
                "config_file": config_file,
                "error": str(e)
            }
    
    def collect_simulation_results(self, run_folder: str) -> Dict[str, Any]:
        """
        收集仿真结果
        
        Args:
            run_folder: 运行文件夹路径
            
        Returns:
            仿真结果信息
        """
        try:
            run_path = Path(run_folder)
            
            if not run_path.exists():
                return {
                    "success": False,
                    "error": f"运行文件夹不存在: {run_folder}"
                }
            
            # 收集结果文件
            result_files = {}
            
            # 查找常见的输出文件
            output_patterns = {
                "summary": "summary.xml",
                "tripinfo": "tripinfo.xml",
                "vehroute": "vehroute.xml",
                "fcd": "fcd.xml",
                "netstate": "netstate.xml",
                "emission": "emission.xml"
            }
            
            for file_type, filename in output_patterns.items():
                file_path = run_path / filename
                if file_path.exists():
                    result_files[file_type] = {
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    }
            
            # 查找E1检测器输出
            e1_folder = run_path / "e1_detectors"
            if e1_folder.exists():
                e1_files = list(e1_folder.glob("*.xml"))
                result_files["e1_detectors"] = {
                    "folder": str(e1_folder),
                    "file_count": len(e1_files),
                    "files": [str(f) for f in e1_files]
                }
            
            # 查找门架数据
            gantry_folder = run_path / "gantry_data"
            if gantry_folder.exists():
                gantry_files = list(gantry_folder.glob("*.csv"))
                result_files["gantry_data"] = {
                    "folder": str(gantry_folder),
                    "file_count": len(gantry_files),
                    "files": [str(f) for f in gantry_files]
                }
            
            # 统计文件夹信息
            total_files = len(list(run_path.rglob("*")))
            total_size = sum(f.stat().st_size for f in run_path.rglob("*") if f.is_file())
            
            return {
                "success": True,
                "run_folder": run_folder,
                "result_files": result_files,
                "statistics": {
                    "total_files": total_files,
                    "total_size_bytes": total_size,
                    "total_size_mb": total_size / (1024 * 1024)
                }
            }
            
        except Exception as e:
            logger.error(f"收集仿真结果失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def monitor_simulation_status(self, run_folder: str) -> Dict[str, Any]:
        """
        监控仿真状态
        
        Args:
            run_folder: 运行文件夹路径
            
        Returns:
            仿真状态信息
        """
        try:
            run_path = Path(run_folder)
            
            if not run_path.exists():
                return {
                    "status": "not_found",
                    "message": f"运行文件夹不存在: {run_folder}"
                }
            
            # 检查是否有正在运行的仿真进程
            # 这里可以扩展为检查实际的SUMO进程
            summary_file = run_path / "summary.xml"
            
            if summary_file.exists():
                # 检查summary.xml是否完整
                try:
                    tree = ET.parse(summary_file)
                    root = tree.getroot()
                    
                    # 检查是否有完整的仿真结果
                    if root.find(".//step") is not None:
                        return {
                            "status": "completed",
                            "message": "仿真已完成",
                            "summary_file": str(summary_file)
                        }
                    else:
                        return {
                            "status": "incomplete",
                            "message": "仿真结果不完整"
                        }
                except ET.ParseError:
                    return {
                        "status": "error",
                        "message": "仿真结果文件损坏"
                    }
            else:
                return {
                    "status": "running",
                    "message": "仿真正在运行中"
                }
                
        except Exception as e:
            logger.error(f"监控仿真状态失败: {e}")
            return {
                "status": "error",
                "message": f"监控失败: {str(e)}"
            }
    
    def process_simulation_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理仿真请求
        
        Args:
            request: 仿真请求参数
            
        Returns:
            仿真结果
        """
        try:
            # 提取请求参数
            run_folder = request.get("run_folder")
            gui = request.get("gui", False)
            mesoscopic = request.get("mesoscopic", False)
            config_file = request.get("config_file")
            
            if not config_file:
                # 如果没有提供配置文件，尝试在run_folder中查找
                if run_folder:
                    config_file = os.path.join(run_folder, "simulation.sumocfg")
                else:
                    raise Exception("未提供配置文件路径")
            
            # 标准化路径分隔符
            config_file = config_file.replace('\\', '/')
            run_folder = run_folder.replace('\\', '/') if run_folder else run_folder

            # 确保输出目录存在
            if run_folder and not os.path.exists(run_folder):
                os.makedirs(run_folder, exist_ok=True)

            # 读取metadata获取预期仿真时长
            expected_duration = None
            case_dir = Path(run_folder).parent if run_folder else None
            meta_file = case_dir / "metadata.json" if case_dir else None
            if meta_file and meta_file.exists():
                try:
                    with open(meta_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    start_str = meta.get("time_range", {}).get("start")
                    end_str = meta.get("time_range", {}).get("end")
                    if start_str and end_str:
                        start_dt = datetime.strptime(start_str, "%Y/%m/%d %H:%M:%S")
                        end_dt = datetime.strptime(end_str, "%Y/%m/%d %H:%M:%S")
                        expected_duration = int((end_dt - start_dt).total_seconds())
                except Exception:
                    expected_duration = None

            # 回退到请求中的expected_duration
            if expected_duration is None:
                expected_duration = request.get("expected_duration")

            progress_path = os.path.join(run_folder, "progress.json") if run_folder else None

            simulation_result = self.run_simulation(
                config_file, gui, mesoscopic,
                run_folder=run_folder,
                progress_path=progress_path,
                expected_duration=expected_duration
            )
            
            if simulation_result["success"]:
                # 收集仿真结果
                results = self.collect_simulation_results(run_folder)
                
                return {
                    "success": True,
                    "run_folder": run_folder,
                    "gui": gui,
                    "mesoscopic": mesoscopic,
                    "config_file": config_file,
                    "simulation_result": simulation_result,
                    "results": results
                }
            else:
                return simulation_result
                
        except Exception as e:
            logger.error(f"处理仿真请求失败: {e}")
            return {
                "success": False,
                "error": str(e)
            } 