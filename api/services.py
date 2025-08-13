"""
OD数据处理与仿真系统 - 业务逻辑服务
"""

import os
import json
import shutil
from datetime import datetime
import threading
from typing import List, Optional, Dict, Any
from pathlib import Path
import asyncio

from api.models import *
from api.utils import *
import pandas as pd
import numpy as np

# ==================== 数据处理服务 ====================

async def process_od_data_service(request: TimeRangeRequest) -> Dict[str, Any]:
    """
    OD数据处理服务
    """
    try:
        from shared.data_processors.od_processor import ODProcessor
        from accuracy_analysis.utils import get_table_names_from_date
        from datetime import datetime as _dt
        
        # 创建OD处理器
        od_processor = ODProcessor()
        
        # 若未显式提供表名，则根据开始时间推断
        inferred_table_name = request.table_name
        if not inferred_table_name:
            try:
                start_dt = _dt.strptime(request.start_time, "%Y/%m/%d %H:%M:%S")
                table_names = get_table_names_from_date(start_dt)
                inferred_table_name = table_names.get("od_table")
            except Exception:
                inferred_table_name = None
        if not inferred_table_name:
            raise Exception("未提供有效的表名，且自动推断失败。请在请求中设置 table_name 或检查时间格式以便自动推断。")

        # 生成case_id与输出目录（cases结构）
        case_id = f"case_{_dt.now().strftime('%Y%m%d_%H%M%S')}"
        case_dir = Path("cases") / case_id
        (case_dir / "config").mkdir(parents=True, exist_ok=True)
        (case_dir / "simulation").mkdir(parents=True, exist_ok=True)
        (case_dir / "analysis" / "accuracy").mkdir(parents=True, exist_ok=True)

        # 构建请求参数
        request_params = {
            "start_time": request.start_time,
            "end_time": request.end_time,
            "interval_minutes": request.interval_minutes,
            "taz_file": request.taz_file,
            "net_file": request.net_file,
            "schemas_name": request.schemas_name,
            "table_name": inferred_table_name,
            "output_dir": str(case_dir / "config")
        }
        
        # 获取数据库连接
        db_connection = open_db_connection()
        
        # 处理OD数据
        result = od_processor.process_od_data(db_connection, request_params)
        
        if result["success"]:
            # 复制TAZ文件到case/config，保持文件名
            try:
                if request.taz_file and os.path.exists(request.taz_file):
                    shutil.copy2(request.taz_file, case_dir / "config" / Path(request.taz_file).name)
            except Exception:
                pass

            # 默认不复制网络文件；如需自包含可在后续需求中增加开关
            copied_network_path = None
 
            # 生成并保存sumocfg（写入真实时间注释）
            try:
                from api.utils import generate_sumocfg, save_sumocfg
                # 计算相对路径（相对于sumocfg所在目录）
                sumocfg_path = Path(os.path.abspath(result.get("sumocfg_file")))
                cfg_dir = sumocfg_path.parent
                route_abs = Path(os.path.abspath(result.get("route_file")))
                if copied_network_path:
                    net_abs = Path(os.path.abspath(str(copied_network_path)))
                else:
                    net_abs = Path(os.path.abspath(request.net_file)) if request.net_file else None
                # TAZ附加文件：优先使用复制到config下的同名文件
                add_abs = None
                if request.taz_file:
                    add_candidate = (case_dir / "config" / Path(request.taz_file).name)
                    add_abs = Path(os.path.abspath(add_candidate)) if add_candidate.exists() else Path(os.path.abspath(request.taz_file))
                    # 方案B：不使用output-prefix，直接将TAZ中 file="e1/" 改为 file="../simulation/e1/"
                    try:
                        taz_target = add_candidate
                        if taz_target.exists():
                            content = taz_target.read_text(encoding="utf-8")
                            if "file=\"../simulation/e1/" not in content:
                                content = content.replace("file=\"e1/", "file=\"../simulation/e1/")
                                taz_target.write_text(content, encoding="utf-8")
                    except Exception:
                        pass
                # 尝试相对路径，跨盘符失败则使用绝对POSIX路径
                try:
                    route_rel = Path(os.path.relpath(route_abs, cfg_dir)).as_posix()
                except ValueError:
                    route_rel = route_abs.as_posix()
                if net_abs:
                    try:
                        net_rel = Path(os.path.relpath(net_abs, cfg_dir)).as_posix()
                    except ValueError:
                        net_rel = net_abs.as_posix()
                else:
                    net_rel = ""
                if add_abs:
                    try:
                        add_rel = Path(os.path.relpath(add_abs, cfg_dir)).as_posix()
                    except ValueError:
                        add_rel = add_abs.as_posix()
                else:
                    add_rel = None

                # 根据前端复选框构造输出开关
                output_options = {
                    "summary": bool(getattr(request, "output_summary", True)),
                    "tripinfo": bool(getattr(request, "output_tripinfo", True)),
                    "vehroute": bool(getattr(request, "output_vehroute", False)),
                    "netstate": bool(getattr(request, "output_netstate", False)),
                    "fcd": bool(getattr(request, "output_fcd", False)),
                    "emission": bool(getattr(request, "output_emission", False)),
                }

                # 统一在 cases/{case_id}/simulation 下产出文件
                # 在 sumocfg 中将输出相对路径写为 ../simulation/*.xml
                cfg_content = generate_sumocfg(
                    route_file=route_rel,
                    net_file=net_rel,
                    start_time=request.start_time,
                    end_time=request.end_time,
                    additional_file=add_rel,
                    output_prefix=None,
                    summary_output="../simulation/summary.xml",
                    tripinfo_output=("../simulation/tripinfo.xml" if output_options["tripinfo"] else None),
                    vehroute_output=("../simulation/vehroute.xml" if output_options["vehroute"] else None),
                    netstate_output=("../simulation/netstate.xml" if output_options["netstate"] else None),
                    fcd_output=("../simulation/fcd.xml" if output_options["fcd"] else None),
                    emission_output=("../simulation/emission.xml" if output_options["emission"] else None),
                )
                # 在XML声明之后插入真实时间注释，避免破坏XML规范
                marker = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
                insert_comment = f"{marker}\n<!-- real_start={request.start_time}, real_end={request.end_time} -->"
                if marker in cfg_content:
                    cfg_content = cfg_content.replace(marker, insert_comment, 1)
                else:
                    # 兜底：如果没有XML声明，则添加到最前一行
                    cfg_content = f"<!-- real_start={request.start_time}, real_end={request.end_time} -->\n" + cfg_content
                save_sumocfg(cfg_content, os.path.abspath(result.get("sumocfg_file")))
            except Exception as _e:
                # 不阻断主流程，留日志即可
                print(f"写入sumocfg失败: {_e}")

            # 写入/更新metadata.json
            try:
                # 辅助：转为相对于项目根目录的POSIX相对路径
                def to_posix_rel(path_str: str) -> str:
                    if not path_str:
                        return path_str
                    try:
                        abs_p = Path(os.path.abspath(path_str))
                        rel = abs_p.relative_to(Path.cwd())
                        return rel.as_posix()
                    except Exception:
                        try:
                            return Path(os.path.relpath(path_str, Path.cwd())).as_posix()
                        except Exception:
                            return Path(path_str).as_posix()
                # 简单模板版本识别
                taz_file_name = Path(request.taz_file).name if request.taz_file else None
                network_file_name = Path(request.net_file).name if request.net_file else None
                def _detect_version(name: str) -> str:
                    if not name:
                        return "unknown"
                    low = name.lower()
                    if "taz_5" in low:
                        return "TAZ_5"
                    if "v6" in low:
                        return "v6"
                    if "v5" in low:
                        return "v5"
                    return "unknown"
                metadata = {
                    "case_id": case_id,
                    "case_name": request.case_name or case_id,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "time_range": {"start": request.start_time, "end": request.end_time},
                    "config": {
                        "interval_minutes": request.interval_minutes,
                        "schemas_name": request.schemas_name,
                    },
                    "templates": {
                        "taz_version": _detect_version(taz_file_name),
                        "network_version": _detect_version(network_file_name),
                        "taz_file_name": taz_file_name,
                        "network_file_name": network_file_name
                    },
                    "status": CaseStatus.PROCESSING.value,
                    "description": request.description,
                    "files": {
                        "od_file": to_posix_rel(result.get("od_file")),
                        "routes_file": to_posix_rel(result.get("route_file")),
                        "config_file": to_posix_rel(result.get("sumocfg_file")),
                        "taz_file": to_posix_rel(str((case_dir / "config" / Path(request.taz_file).name))) if request.taz_file else None,
                        "network_file": to_posix_rel(str(copied_network_path)) if copied_network_path else (to_posix_rel(request.net_file) if request.net_file else None)
                    },
                    "statistics": {
                        "total_records": result.get("total_records"),
                        "od_pairs": result.get("od_pairs")
                    },
                    "last_step": "od_processed"
                }
                with open(case_dir / "metadata.json", "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            except Exception as _e:
                print(f"写入metadata.json失败: {_e}")
            # 确保仿真输出目录结构健全（特别是 e1）
            try:
                (case_dir / "simulation" / "e1").mkdir(parents=True, exist_ok=True)
            except Exception:
                pass

            return {
                "start_time": request.start_time,
                "end_time": request.end_time,
                "interval_minutes": request.interval_minutes,
                "processed_at": datetime.now().isoformat(),
                "status": "completed",
                "case_id": case_id,
                "run_folder": (case_dir / "config").as_posix(),
                "od_file": to_posix_rel(result.get("od_file")),
                "route_file": to_posix_rel(result.get("route_file")),
                "sumocfg_file": to_posix_rel(result.get("sumocfg_file")),
                "total_records": result.get("total_records"),
                "od_pairs": result.get("od_pairs")
            }
        else:
            raise Exception(result.get("error", "OD数据处理失败"))
            
    except Exception as e:
        raise Exception(f"OD数据处理失败: {str(e)}")
    finally:
        try:
            if 'db_connection' in locals() and db_connection:
                db_connection.close()
        except Exception:
            pass

async def run_simulation_service(request: SimulationRequest) -> Dict[str, Any]:
    """
    仿真运行服务
    """
    try:
        from shared.data_processors.simulation_processor import SimulationProcessor
        
        # 创建仿真处理器
        sim_processor = SimulationProcessor()

        # 自动探测并设置 SUMO 可执行文件（Windows 优先 sumo.exe）
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
            # PATH 中查找
            which_sumo = _shutil.which("sumo.exe") or _shutil.which("sumo")
            if which_sumo:
                candidates.append(which_sumo)
            # 常见安装路径（兜底）
            candidates.extend([
                r"C:\\Program Files (x86)\\Eclipse\\Sumo\\bin\\sumo.exe",
                r"C:\\Program Files\\Eclipse\\Sumo\\bin\\sumo.exe",
            ])
            picked = next((p for p in candidates if p and os.path.exists(p)), None)
            if picked:
                sim_processor.set_sumo_binary(picked)
            else:
                # 若找不到，不立即失败，后续运行会抛出更直观的错误，但这里给出提示以便定位
                print("警告: 未能自动定位SUMO，可设置环境变量 SUMO_BIN 或 SUMO_HOME，或将 sumo 加入 PATH。")
        except Exception:
            pass
        
        # 构建请求参数
        # run_folder 可能是案例根目录（cases/case_xxx），也可能是cases/{case_id}/simulation或cases/{case_id}/config
        input_run_folder = request.run_folder.replace('\\', '/')
        base_name = os.path.basename(input_run_folder.rstrip('/'))
        if base_name in ("simulation", "config"):
            case_root = os.path.dirname(input_run_folder.rstrip('/'))
        else:
            case_root = input_run_folder

        # 默认sumocfg取cases/{case_id}/config/simulation.sumocfg
        default_cfg = os.path.join(case_root, "config", "simulation.sumocfg")
        cfg_file = (request.config_file or default_cfg).replace('\\', '/')
        # 如果误传了simulation/config路径，纠正为config路径
        cfg_file = cfg_file.replace('/simulation/config/', '/config/').replace('\\simulation\\config\\', '\\config\\').replace('\\simulation/config\\', '\\config\\')
 
        # 仿真前更新metadata状态为simulating
        try:
            case_dir = Path(case_root)
            meta_file = case_dir / "metadata.json"
            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                _sim_started_at = datetime.now().isoformat()
                meta["status"] = CaseStatus.SIMULATING.value
                meta["updated_at"] = _sim_started_at
                meta["simulation_started_at"] = _sim_started_at
                meta["last_step"] = "simulation_start"
                with open(meta_file, "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
        except Exception as _e:
            print(f"更新metadata为simulating失败: {_e}")
        request_params = {
            "run_folder": os.path.join(case_root, "simulation"),  # 仿真输出目录
            "gui": request.gui,
            "mesoscopic": request.simulation_type == SimulationType.MESOSCOPIC,
            "config_file": cfg_file,
            "expected_duration": request.expected_duration # 新增：预期仿真时长
        }
        
        # 先写入初始progress.json，避免前端第一次轮询读到旧结果
        try:
            prog_path = Path(request_params["run_folder"]) / "progress.json"
            prog_path.parent.mkdir(parents=True, exist_ok=True)
            with open(prog_path, "w", encoding="utf-8") as f:
                json.dump({
                    "status": "running",
                    "percent": 0,
                    "message": "仿真启动中",
                    "updated_at": datetime.now().isoformat(),
                    "pid": None
                }, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        # 后台线程运行仿真
        def _run_and_finalize():
            try:
                result = sim_processor.process_simulation_request(request_params)
                # 仿真完成后更新metadata
                if result.get("success"):
                    try:
                        case_dir = Path(case_root)
                        meta_file = case_dir / "metadata.json"
                        if meta_file.exists():
                            with open(meta_file, "r", encoding="utf-8") as f:
                                meta = json.load(f)
                            meta["status"] = CaseStatus.COMPLETED.value
                            # 从simulation_result读取结束时间，兜底用当前时间
                            _ended_at = None
                            try:
                                _ended_at = (result.get("simulation_result") or {}).get("end_time")
                            except Exception:
                                _ended_at = None
                            if not _ended_at:
                                _ended_at = datetime.now().isoformat()
                            meta["updated_at"] = _ended_at
                            meta["simulation_ended_at"] = _ended_at
                            meta["last_step"] = "simulation"
                            meta.setdefault("files", {})["config_file"] = cfg_file
                            with open(meta_file, "w", encoding="utf-8") as f:
                                json.dump(meta, f, ensure_ascii=False, indent=2)
                    except Exception as _e:
                        print(f"更新metadata为completed失败: {_e}")
            except Exception as _e:
                # 失败时写入失败状态（SimulationProcessor内部也会写入failed，这里兜底）
                try:
                    # 写progress.json
                    with open(Path(request_params["run_folder"]) / "progress.json", "w", encoding="utf-8") as f:
                        json.dump({
                            "status": "failed",
                            "percent": 0,
                            "message": str(_e),
                            "updated_at": datetime.now().isoformat(),
                            "pid": None
                        }, f, ensure_ascii=False, indent=2)
                    # 写metadata为failed并记录结束时间
                    case_dir = Path(case_root)
                    meta_file = case_dir / "metadata.json"
                    if meta_file.exists():
                        with open(meta_file, "r", encoding="utf-8") as mf:
                            meta = json.load(mf)
                        meta["status"] = CaseStatus.FAILED.value
                        _ended_at = datetime.now().isoformat()
                        meta["updated_at"] = _ended_at
                        meta["simulation_ended_at"] = _ended_at
                        meta["last_step"] = "simulation_failed"
                        with open(meta_file, "w", encoding="utf-8") as mf:
                            json.dump(meta, mf, ensure_ascii=False, indent=2)
                except Exception:
                    pass

        threading.Thread(target=_run_and_finalize, daemon=True).start()

        # 立即返回“已启动”，由前端轮询progress.json获取真实进度
        return {
            "run_folder": request_params["run_folder"],
            "gui": request.gui,
            "mesoscopic": request.simulation_type == SimulationType.MESOSCOPIC,
            "simulation_type": request.simulation_type.value,
            "started_at": datetime.now().isoformat(),
            "status": "started"
        }
            
    except Exception as e:
        raise Exception(f"仿真运行失败: {str(e)}")

async def get_simulation_progress_service(case_id: str) -> Dict[str, Any]:
    """
    读取仿真进度（progress.json）
    """
    try:
        case_dir = Path("cases") / case_id
        prog_file = case_dir / "simulation" / "progress.json"
        if not prog_file.exists():
            return {"status": "unknown", "percent": 0, "message": "暂无进度"}
        with open(prog_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        return {"status": "error", "percent": 0, "message": str(e)}

async def analyze_accuracy_service(request: AccuracyAnalysisRequest) -> Dict[str, Any]:
    """
    精度/机理分析服务（analysis_type 决定具体分析）
    """
    try:
        from shared.analysis_tools.accuracy_analyzer import AccuracyAnalyzer
        from accuracy_analysis.flow_analysis import TrafficFlowAnalyzer

        # 解析目录：请求传入的是结果目录 cases/{case_id}/analysis/accuracy
        result_folder = Path(request.result_folder).as_posix()
        case_root = Path(request.result_folder).resolve().parent.parent  # cases/{case_id}
        simulation_folder = (case_root / "simulation").as_posix()

        # 输出目录固定到案例的 analysis/{accuracy|mechanism|performance}
        charts_dir = (case_root / "analysis" / "accuracy" / "charts").as_posix()
        reports_dir = (case_root / "analysis" / "accuracy" / "reports").as_posix()

        # 若为机理分析（TRAFFIC_FLOW），走专用分支
        if request.analysis_type and request.analysis_type.value == "traffic_flow":
            # 机理分析（mechanism）：
            # - 输入：cases/{case_id}/simulation 下的 tripinfo/vehroute、.rou.xml、.od.xml
            # - 输出：cases/{case_id}/analysis/mechanism/accuracy_results_时间戳/ 下的 CSV
            # 说明：与精度分析（accuracy）分目录，避免产物混淆
            mech_base = (Path(simulation_folder).parent / "analysis" / "mechanism").as_posix()
            analyzer = TrafficFlowAnalyzer(
                run_folder=simulation_folder,
                output_base_folder=mech_base
            )
            tr_result = analyzer.analyze()

            # 构造CSV可访问URL（通过 /cases 静态挂载）
            case_id = case_root.name
            out_dir = Path(tr_result.get("output_folder", ""))
            csv_urls: list[str] = []
            csv_files = tr_result.get("csv_files") or {}
            for _k, p in csv_files.items():
                if not p:
                    continue
                fname = Path(p).name
                csv_urls.append(f"/cases/{case_id}/analysis/mechanism/{out_dir.name}/{fname}")

            return {
                "result_folder": out_dir.as_posix(),
                "analysis_type": request.analysis_type.value,
                "status": "completed",
                "metrics": {},
                "chart_files": tr_result.get("chart_files", []),
                "report_file": tr_result.get("report_file") or "",
                "report_url": (f"/cases/{case_id}/analysis/mechanism/{out_dir.name}/{Path(tr_result.get('report_file')).name}" if tr_result.get('report_file') else None),
                "chart_urls": [f"/cases/{case_id}/analysis/mechanism/{out_dir.name}/{Path(p).name}" for p in (tr_result.get("chart_files") or []) if p],
                "csv_urls": csv_urls,
                "analysis_time": datetime.now().isoformat(),
            }

        # 否则：精度分析分支
        # 优先使用新版分析器（accuracy_analysis.AccuracyAnalyzer），加载真实观测数据并按门架×时间对齐
        # 输出目录将使用 cases/{case_id}/analysis/accuracy/accuracy_results_yyyyMMdd_HHmmss
        use_new_analyzer = True

        # 运行前环境自检：统计可用仿真数据文件
        try:
            sim_path = Path(simulation_folder)
            e1_dirs = [p for p in [sim_path / 'e1', sim_path / 'e1_detectors'] if p.exists() and p.is_dir()]
            try:
                e1_dirs.extend([p for p in sim_path.iterdir() if p.is_dir() and p.name.lower().startswith('e1') and p not in e1_dirs])
            except Exception:
                pass
            e1_count = 0
            for d in e1_dirs:
                e1_count += sum(1 for _ in d.rglob('*.xml'))
            gantry_dir = sim_path / 'gantry_data'
            gantry_count = sum(1 for _ in gantry_dir.glob('*.csv')) if gantry_dir.exists() else 0
            summary_exists = (sim_path / 'summary.xml').exists()
            debug_msg = (
                f"[Accuracy] sim='{simulation_folder}', e1_xml={e1_count}, gantry_csv={gantry_count}, summary={summary_exists}"
            )
            print(debug_msg)
            if e1_count == 0 and gantry_count == 0:
                raise Exception("没有找到可分析的仿真数据（E1或门架）。请确认仿真已生成 e1/*.xml 或 gantry_data/*.csv 后再试。")
        except Exception as _precheck_err:
            raise Exception(str(_precheck_err))

        result = None
        if use_new_analyzer:
            try:
                from accuracy_analysis.analyzer import AccuracyAnalyzer as NewAccuracyAnalyzer
                # run_folder 取 cases/{case_id}/simulation 的父目录
                run_folder = Path(simulation_folder).parent.as_posix()
                # 运行新版分析器（内部从数据库加载门架观测数据，并与E1合并）
                new_analyzer = NewAccuracyAnalyzer(run_folder=run_folder, output_base_folder=(Path(simulation_folder).parent / "analysis" / "accuracy").as_posix())
                new_result = new_analyzer.analyze_accuracy()
                if new_result.get("success"):
                    # 适配返回给前端的字段
                    report_files = new_result.get("report_files", {})
                    report_file = report_files.get("html_report") or ""
                    # 附加导出的对比CSV路径（detailed_records.csv 中包含 sim_flow/obs_flow/gantry_id/interval_start）
                    exported_csvs = {
                        "accuracy_results": report_files.get("overall_results"),
                        "gantry_accuracy_analysis": report_files.get("gantry_analysis"),
                        "time_accuracy_analysis": report_files.get("time_analysis"),
                        "detailed_records": report_files.get("detailed_records")
                    }
                    result = {
                        "analysis_type": request.analysis_type.value,
                        "simulation_folder": simulation_folder,
                        "metrics": new_result.get("accuracy_summary", {}).get("overall_metrics", {}),
                        "chart_files": [v for k, v in report_files.items() if k != "html_report"],
                        "report_file": report_file,
                        "analysis_time": datetime.now().isoformat(),
                        "exported_csvs": exported_csvs,
                    }
                else:
                    raise Exception(new_result.get("error") or "新版精度分析失败")
            except Exception as _e:
                # 回退旧分析器（不理想但不中断）
                print(f"新版分析器失败，回退旧版: {_e}")
                use_new_analyzer = False

        if not use_new_analyzer:
            # 旧版分析器路径（注意：旧版此前用了模拟观测数据，不再使用）
            analyzer = AccuracyAnalyzer()
            analyzer.set_output_dirs(charts_dir, reports_dir)
            # 从数据库读取真实观测数据的旧管道尚未在旧版中实现，这里直接报错提醒
            raise Exception("当前分析通道仅支持新版分析器以加载真实观测数据，请确保数据库连接配置正确，并在 cases/{case_id}/simulation 生成 E1 后重试。")

        if "error" not in result:
            # 构造对外可访问URL（通过 /cases 静态挂载）
            case_id = case_root.name
            report_path = Path(result.get("report_file") or "")
            # 统一定位到时间戳结果目录（新版分析器）
            report_url = None
            if report_path and report_path.name:
                report_url = f"/cases/{case_id}/analysis/accuracy/{report_path.parent.name}/{report_path.name}"
            charts: list[str] = []
            csv_urls: list[str] = []
            # 结果输出目录：从 report_file 或 任意chart/CSV 推断
            out_dir = report_path.parent
            # 对旧/新两类返回统一处理：
            for p in (result.get("chart_files", []) or []):
                path = Path(p)
                name = path.name
                suffix = path.suffix.lower()
                if suffix in (".png", ".jpg", ".jpeg", ".gif"):
                    charts.append(f"/cases/{case_id}/analysis/accuracy/charts/{name}")
                elif suffix == ".csv":
                    # CSV 位于输出目录根，而非 charts
                    csv_urls.append(f"/cases/{case_id}/analysis/accuracy/{out_dir.name}/{name}")
            # 若后端提供了 exported_csvs（新版分析器），补充其URL
            exported = result.get("exported_csvs") or {}
            for name, fullpath in exported.items():
                if not fullpath:
                    continue
                fname = Path(fullpath).name
                csv_urls.append(f"/cases/{case_id}/analysis/accuracy/{Path(fullpath).parent.name}/{fname}")

            return {
                "result_folder": result_folder,
                "analysis_type": request.analysis_type.value,
                "started_at": datetime.now().isoformat(),
                "status": "completed",
                "metrics": result.get("metrics", {}),
                "chart_files": result.get("chart_files", []),
                "report_file": result.get("report_file", ""),
                "report_url": report_url,
                "chart_urls": charts,
                "csv_urls": csv_urls,
                "analysis_time": result.get("analysis_time"),
                # 透传增强信息（阶段A：效率与数据源、对齐策略）
                "source_stats": result.get("source_stats"),
                "alignment": result.get("alignment"),
                "efficiency": result.get("efficiency")
            }
        else:
            raise Exception(result.get("error", "精度分析失败"))
            
    except Exception as e:
        raise Exception(f"精度分析失败: {str(e)}")

# ==================== 案例管理服务 ====================

async def create_case_service(request: CaseCreationRequest) -> Dict[str, Any]:
    """
    创建案例服务
    """
    try:
        # 生成案例ID
        case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建案例目录结构
        case_dir = Path("cases") / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        (case_dir / "config").mkdir(exist_ok=True)
        (case_dir / "simulation").mkdir(exist_ok=True)
        # 预创建 e1 目录，用于保存 SUMO 仿真后的 E1 检测器输出
        (case_dir / "simulation" / "e1").mkdir(parents=True, exist_ok=True)
        (case_dir / "analysis").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy" / "results").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy" / "charts").mkdir(exist_ok=True)
        (case_dir / "analysis" / "accuracy" / "reports").mkdir(exist_ok=True)
        
        # 创建元数据
        metadata = {
            "case_id": case_id,
            "case_name": request.case_name or case_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "time_range": request.time_range,
            "config": request.config,
            "status": CaseStatus.CREATED.value,
            "description": request.description,
            "statistics": {},
            "files": {}
        }
        
        # 保存元数据
        with open(case_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return {
            "case_id": case_id,
            "case_dir": str(case_dir),
            "metadata": metadata
        }
    except Exception as e:
        raise Exception(f"案例创建失败: {str(e)}")

async def list_cases_service(
    page: int = 1,
    page_size: int = 10,
    status: Optional[CaseStatus] = None,
    search: Optional[str] = None
) -> CaseListResponse:
    """
    列出案例服务
    """
    try:
        cases = []
        cases_dir = Path("cases")
        
        if not cases_dir.exists():
            return CaseListResponse(cases=[], total_count=0, page=page, page_size=page_size)
        
        # 获取所有案例目录
        case_dirs = [d for d in cases_dir.iterdir() if d.is_dir() and d.name.startswith("case_")]
        
        # 过滤和排序
        filtered_cases = []
        for case_dir in case_dirs:
            metadata_file = case_dir / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                
                # 状态过滤
                if status and metadata.get("status") != status.value:
                    continue
                
                # 搜索过滤
                if search:
                    case_name = metadata.get("case_name", "")
                    description = metadata.get("description", "")
                    if search.lower() not in case_name.lower() and search.lower() not in description.lower():
                        continue
                
                filtered_cases.append(metadata)
        
        # 按创建时间排序
        filtered_cases.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 分页
        total_count = len(filtered_cases)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_cases = filtered_cases[start_idx:end_idx]
        
        # 转换为CaseMetadata对象
        case_metadata_list = []
        for case_data in page_cases:
            case_metadata = CaseMetadata(**case_data)
            case_metadata_list.append(case_metadata)
        
        return CaseListResponse(
            cases=case_metadata_list,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise Exception(f"获取案例列表失败: {str(e)}")

async def get_case_service(case_id: str) -> CaseMetadata:
    """
    获取案例详情服务
    """
    try:
        case_dir = Path("cases") / case_id
        metadata_file = case_dir / "metadata.json"
        
        if not metadata_file.exists():
            raise Exception(f"案例 {case_id} 不存在")
        
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        return CaseMetadata(**metadata)
    except Exception as e:
        raise Exception(f"获取案例详情失败: {str(e)}")

async def delete_case_service(case_id: str) -> Dict[str, Any]:
    """
    删除案例服务
    """
    try:
        case_dir = Path("cases") / case_id
        
        if not case_dir.exists():
            raise Exception(f"案例 {case_id} 不存在")
        
        # 删除案例目录
        shutil.rmtree(case_dir)
        
        return {
            "case_id": case_id,
            "deleted_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise Exception(f"删除案例失败: {str(e)}")

async def clone_case_service(case_id: str, request: CaseCloneRequest) -> Dict[str, Any]:
    """
    克隆案例服务
    """
    try:
        source_case_dir = Path("cases") / case_id
        if not source_case_dir.exists():
            raise Exception(f"源案例 {case_id} 不存在")
        
        # 生成新案例ID
        new_case_id = f"case_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        new_case_dir = Path("cases") / new_case_id
        
        # 复制案例目录
        shutil.copytree(source_case_dir, new_case_dir)
        
        # 更新元数据
        metadata_file = new_case_dir / "metadata.json"
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        metadata.update({
            "case_id": new_case_id,
            "case_name": request.new_case_name or f"{metadata.get('case_name', '')}_copy",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "description": request.new_description or f"克隆自 {case_id}",
            "status": CaseStatus.CREATED.value
        })
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return {
            "original_case_id": case_id,
            "new_case_id": new_case_id,
            "new_case_dir": str(new_case_dir),
            "cloned_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise Exception(f"克隆案例失败: {str(e)}")

# ==================== 文件管理服务 ====================

async def get_folders_service(prefix: str) -> List[FolderInfo]:
    """
    获取文件夹列表服务
    """
    try:
        folders = []
        base_dir = Path(".")
        
        # 查找匹配前缀的文件夹
        for item in base_dir.iterdir():
            if item.is_dir() and item.name.startswith(prefix):
                folder_info = FolderInfo(
                    name=item.name,
                    path=str(item),
                    created_at=datetime.fromtimestamp(item.stat().st_ctime),
                    size=get_folder_size(item),
                    file_count=count_files(item)
                )
                folders.append(folder_info)
        
        return folders
    except Exception as e:
        raise Exception(f"获取文件夹列表失败: {str(e)}")

async def get_accuracy_analysis_status_service(result_folder: str) -> AnalysisStatus:
    """
    获取精度分析状态服务
    """
    try:
        # 这里应该检查实际的分析状态
        # 暂时返回模拟数据
        status = AnalysisStatus(
            result_folder=result_folder,
            status="completed",
            progress=100.0,
            message="分析完成",
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        return status
    except Exception as e:
        raise Exception(f"获取分析状态失败: {str(e)}")

# ==================== 模板管理服务 ====================

async def get_taz_templates_service() -> List[TemplateInfo]:
    """
    获取TAZ模板列表服务
    """
    try:
        templates = []
        taz_dir = Path("templates/taz_files")
        config_file = taz_dir / "taz_templates.json"
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            for template_id, template_data in config.get("taz_templates", {}).items():
                template = TemplateInfo(
                    name=template_data["name"],
                    description=template_data["description"],
                    file_path=str(taz_dir / template_data["file_path"]),
                    version=template_data["version"],
                    created_date=template_data["created_date"],
                    status=template_data["validation_status"]
                )
                templates.append(template)
        
        return templates
    except Exception as e:
        raise Exception(f"获取TAZ模板失败: {str(e)}")

async def get_network_templates_service() -> List[TemplateInfo]:
    """
    获取网络模板列表服务
    """
    try:
        templates = []
        network_dir = Path("templates/network_files")
        config_file = network_dir / "network_configs.json"
        
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            for template_id, template_data in config.get("network_templates", {}).items():
                template = TemplateInfo(
                    name=template_data["name"],
                    description=template_data["description"],
                    file_path=str(network_dir / template_data["file_path"]),
                    version=template_data["version"],
                    created_date=template_data["created_date"],
                    status=template_data["status"]
                )
                templates.append(template)
        
        return templates
    except Exception as e:
        raise Exception(f"获取网络模板失败: {str(e)}")

async def get_simulation_templates_service() -> List[TemplateInfo]:
    """
    获取仿真配置模板列表服务
    """
    try:
        templates = []
        sim_dir = Path("templates/config_templates/simulation_templates")
        
        template_files = {
            "default.sumocfg": "默认仿真配置",
            "mesoscopic.sumocfg": "中观仿真配置",
            "microscopic.sumocfg": "微观仿真配置"
        }
        
        for filename, description in template_files.items():
            file_path = sim_dir / filename
            if file_path.exists():
                template = TemplateInfo(
                    name=filename,
                    description=description,
                    file_path=str(file_path),
                    version="1.0",
                    created_date="2025-01-08",
                    status="available"
                )
                templates.append(template)
        
        return templates
    except Exception as e:
        raise Exception(f"获取仿真模板失败: {str(e)}")

# ==================== 工具服务 ====================

async def validate_taz_file_service(file_path: str) -> Dict[str, Any]:
    """
    验证TAZ文件服务
    """
    try:
        # 这里应该调用TAZ验证工具
        # 暂时返回模拟数据
        result = {
            "file_path": file_path,
            "is_valid": True,
            "validation_time": datetime.now().isoformat(),
            "issues": []
        }
        return result
    except Exception as e:
        raise Exception(f"TAZ文件验证失败: {str(e)}")

async def fix_taz_file_service(file_path: str) -> Dict[str, Any]:
    """
    修复TAZ文件服务
    """
    try:
        # 这里应该调用TAZ修复工具
        # 暂时返回模拟数据
        result = {
            "file_path": file_path,
            "fixed": True,
            "fix_time": datetime.now().isoformat(),
            "changes": []
        }
        return result
    except Exception as e:
        raise Exception(f"TAZ文件修复失败: {str(e)}")

async def compare_taz_files_service(file1: str, file2: str) -> Dict[str, Any]:
    """
    比较TAZ文件服务
    """
    try:
        # 这里应该调用TAZ比较工具
        # 暂时返回模拟数据
        result = {
            "file1": file1,
            "file2": file2,
            "comparison_time": datetime.now().isoformat(),
            "differences": [],
            "similarities": []
        }
        return result
    except Exception as e:
        raise Exception(f"TAZ文件比较失败: {str(e)}")

# ==================== 辅助函数 ====================

def get_folder_size(folder_path: Path) -> int:
    """获取文件夹大小"""
    total_size = 0
    try:
        for item in folder_path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
    except:
        pass
    return total_size

def count_files(folder_path: Path) -> int:
    """统计文件夹中的文件数量"""
    file_count = 0
    try:
        for item in folder_path.rglob("*"):
            if item.is_file():
                file_count += 1
    except:
        pass
    return file_count 

# ==================== 历史结果回看服务 ====================

async def list_analysis_results_service(case_id: str, analysis_type: Optional[str] = "accuracy") -> Dict[str, Any]:
    """
    按类型列出指定案例下的历史分析结果（accuracy | mechanism | performance）。
    - accuracy：返回报告HTML、标准CSV、charts
    - mechanism/performance：返回目录下所有CSV与charts
    """
    at = (analysis_type or "accuracy").lower()
    if at not in ("accuracy", "mechanism", "performance"):
        at = "accuracy"
    base_dir = Path("cases") / case_id / "analysis" / at
    if not base_dir.exists():
        raise Exception(f"案例{at}目录不存在")
    items: list[dict[str, Any]] = []
    for d in base_dir.iterdir():
        if d.is_dir() and d.name.startswith("accuracy_results_"):
            record: Dict[str, Any] = {
                "folder": d.name,
                "created_at": datetime.fromtimestamp(d.stat().st_ctime).isoformat(),
                "report_html": None,
                "csv_files": [],
                "chart_files": []
            }
            if at == "accuracy":
                html_path = d / "accuracy_report.html"
                if html_path.exists():
                    record["report_html"] = f"/cases/{case_id}/analysis/{at}/{d.name}/accuracy_report.html"
                for csv_name in [
                    "accuracy_results.csv",
                    "gantry_accuracy_analysis.csv",
                    "time_accuracy_analysis.csv",
                    "detailed_records.csv",
                    "anomaly_analysis.csv",
                ]:
                    p = d / csv_name
                    if p.exists():
                        record["csv_files"].append(f"/cases/{case_id}/analysis/{at}/{d.name}/{csv_name}")
                charts_dir = d / "charts"
                if charts_dir.exists():
                    for p in charts_dir.glob("*.png"):
                        record["chart_files"].append(f"/cases/{case_id}/analysis/{at}/{d.name}/charts/{p.name}")
            else:
                for p in d.glob("*.csv"):
                    record["csv_files"].append(f"/cases/{case_id}/analysis/{at}/{d.name}/{p.name}")
                charts_dir = d / "charts"
                if charts_dir.exists():
                    for p in charts_dir.glob("*.png"):
                        record["chart_files"].append(f"/cases/{case_id}/analysis/{at}/{d.name}/charts/{p.name}")
            items.append(record)
    items.sort(key=lambda x: x["created_at"], reverse=True)
    return {"case_id": case_id, "analysis_type": at, "results": items}