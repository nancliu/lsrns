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
    
    def generate_sumocfg(self, route_file: str, net_file: str, start_time: str, 
                         end_time: str, additional_file: str = None, 
                         output_file: str = "simulation.sumocfg",
                         output_options: Dict[str, bool] = None,
                         enable_mesoscopic: bool = False) -> str:
        """
        生成SUMO配置文件
        
        Args:
            route_file: 路由文件路径
            net_file: 网络文件路径
            start_time: 开始时间
            end_time: 结束时间
            additional_file: 附加文件路径（如TAZ文件）
            output_file: 输出配置文件路径
            output_options: 输出选项
            enable_mesoscopic: 是否启用中观仿真
            
        Returns:
            生成的配置文件路径
        """
        logger.info(f"开始生成SUMO配置文件: {output_file}")
        
        # 计算仿真时长
        start_dt = datetime.strptime(start_time, "%Y/%m/%d %H:%M:%S")
        end_dt = datetime.strptime(end_time, "%Y/%m/%d %H:%M:%S")
        duration = int((end_dt - start_dt).total_seconds())
        
        # 将路径标准化为POSIX（不改变是否相对，仅分隔符）
        route_val = (route_file or "").replace('\\', '/')
        net_val = (net_file or "").replace('\\', '/')
        add_val = (additional_file or "").replace('\\', '/') if additional_file else None
        
        # 创建XML根元素
        root = ET.Element("configuration")
        
        # 输入部分
        input_elem = ET.SubElement(root, "input")
        
        # 网络文件
        net_elem = ET.SubElement(input_elem, "net-file")
        net_elem.set("value", net_val)
        
        # 路由文件
        route_elem = ET.SubElement(input_elem, "route-files")
        route_elem.set("value", route_val)
        
        # 附加文件（如TAZ文件）
        if additional_file:
            additional_elem = ET.SubElement(input_elem, "additional-files")
            additional_elem.set("value", add_val)
        
        # 时间设置
        time_elem = ET.SubElement(root, "time")
        begin_elem = ET.SubElement(time_elem, "begin")
        begin_elem.set("value", "0")
        end_elem = ET.SubElement(time_elem, "end")
        end_elem.set("value", str(duration))
        
        # 处理设置
        processing_elem = ET.SubElement(root, "processing")
        ignore_route_elem = ET.SubElement(processing_elem, "ignore-route-errors")
        ignore_route_elem.set("value", "true")
        collision_elem = ET.SubElement(processing_elem, "collision.action")
        collision_elem.set("value", "warn")
        
        # 报告设置
        report_elem = ET.SubElement(root, "report")
        verbose_elem = ET.SubElement(report_elem, "verbose")
        verbose_elem.set("value", "true")
        no_step_log_elem = ET.SubElement(report_elem, "no-step-log")
        no_step_log_elem.set("value", "true")
        
        # 输出选项
        if output_options:
            for option_name, enabled in output_options.items():
                if enabled:
                    option_elem = ET.SubElement(report_elem, option_name)
                    option_elem.set("value", "true")
        
        # GUI设置（如果启用）
        if not enable_mesoscopic:
            gui_elem = ET.SubElement(root, "gui_only")
            gui_settings_elem = ET.SubElement(gui_elem, "gui-settings-file")
            gui_settings_elem.set("value", "gui-settings.cfg")
        
        # 写入文件
        tree = ET.ElementTree(root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"SUMO配置文件生成完成: {output_file}")
        return output_file
    
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
                    # 从sumocfg中已写入的summary_output相对路径推导：<config_dir>/../../simulation/summary.xml
                    # 这里仍兼容优先读取运行目录下的summary.xml
                    candidates = []
                    if run_folder:
                        candidates.append(os.path.join(run_folder, "summary.xml"))
                    # 回退：config_dir/../../simulation/summary.xml
                    cfg_dir = config_dir
                    candidates.append(os.path.normpath(os.path.join(cfg_dir, "../../simulation/summary.xml")))
                    for sf in candidates:
                        if os.path.exists(sf):
                            tree = ET.parse(sf)
                            root = tree.getroot()
                            steps = list(root.findall('.//step'))
                            if steps:
                                last = steps[-1]
                                t = last.get('time') or last.get('end') or last.get('begin')
                                if t is not None:
                                    return float(t)
                    return None
                except Exception:
                    return None

            last_lines = deque(maxlen=200)
            
            last_percent = 0
            write_progress("running", 0, "仿真启动中")

            last_line = ""
            while True:
                line = proc.stdout.readline() if proc.stdout else ""
                if line:
                    last_line = line.strip()
                    try:
                        last_lines.append(last_line)
                    except Exception:
                        pass
                if line == "" and proc.poll() is not None:
                    break

                # 估算百分比
                percent = last_percent
                sim_time = get_sim_time_from_summary()
                if expected_duration and expected_duration > 0:
                    if sim_time is not None:
                        percent = int(sim_time / expected_duration * 100)
                    else:
                        # 基于耗时的保守估算，最多到95%
                        elapsed = (datetime.now() - start_time).total_seconds()
                        percent = min(95, int(elapsed / expected_duration * 100))
                else:
                    # 无法估算，保持已有百分比
                    percent = max(percent, 10 if last_percent == 0 else last_percent)

                if percent != last_percent or (int(time.time()) % 3 == 0):
                    write_progress("running", percent, last_line)
                    last_percent = percent

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