"""
分析服务 - 负责各种分析功能的业务逻辑
"""

import json
from datetime import datetime
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional

from ..models import AccuracyAnalysisRequest
from .base_service import BaseService, MetadataManager


logger = logging.getLogger(__name__)


class AnalysisService(BaseService):
    """分析服务类"""
    
    async def analyze_accuracy(self, request: AccuracyAnalysisRequest) -> Dict[str, Any]:
        """执行精度分析"""
        try:
            case_id = request.case_id
            simulation_ids = request.simulation_ids
            
            if not simulation_ids:
                raise Exception("请选择至少一个仿真结果")
            
            # 获取案例信息
            case_dir = self.cases_dir / case_id
            if not case_dir.exists():
                raise Exception(f"案例 {case_id} 不存在")
            
            # 获取第一个仿真结果进行分析（简化处理）
            simulation_id = simulation_ids[0]
            simulation_dir = case_dir / "simulations" / simulation_id
            if not simulation_dir.exists():
                raise Exception(f"仿真结果 {simulation_id} 不存在")
            
            # 准备分析目录
            analysis_dir = self._prepare_analysis_dirs(case_dir)
            
            # 解析门架数据
            gantry_data = self._resolve_gantry_data(case_dir, simulation_dir)
            
            # 解析E1检测器数据
            e1_data = self._resolve_e1_data(simulation_dir)
            
            # 执行数据对齐和导出
            alignment_results = self._run_alignment_and_exports(gantry_data, e1_data, analysis_dir)
            
            # 执行精度分析（直接使用 shared 分析器）
            from shared.analysis_tools.accuracy_analysis import AccuracyAnalysis
            analyzer = AccuracyAnalysis()
            charts_dir = analysis_dir / "charts"
            reports_dir = analysis_dir
            analyzer.set_output_dirs(str(charts_dir), str(reports_dir))
            analysis_results = analyzer.analyze_accuracy(alignment_results['aligned_data'])
            
            # 构建响应
            return self._build_analysis_response(
                case_id, simulation_id, analysis_dir, 
                alignment_results, analysis_results
            )
                
        except Exception as e:
            raise Exception(f"精度分析失败: {str(e)}")

    def _prepare_analysis_dirs(self, case_dir: Path) -> Path:
        """准备分析目录结构"""
        analysis_dir = case_dir / "analysis" / f"ana_{datetime.now().strftime('%m%d_%H%M%S')}" / "accuracy"
        analysis_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"创建分析目录: {analysis_dir}")
        return analysis_dir

    def _resolve_gantry_data(self, case_dir: Path, simulation_dir: Path) -> pd.DataFrame:
        """解析门架数据：优先使用现有数据，否则从数据库加载"""
        logger.info("检查门架数据状态...")
        
        # 尝试从现有门架数据文件夹加载
        gantry_data = None
        gantry_folders = list(case_dir.glob("gantry_*"))
        
        if gantry_folders:
            # 使用最新的门架数据文件夹
            gantry_folder = max(gantry_folders, key=lambda x: x.stat().st_mtime)
            logger.info(f"门架数据文件夹: {gantry_folder}")
            
            gantry_file = gantry_folder / "gantry_data_raw.csv"
            if gantry_file.exists():
                try:
                    gantry_data = pd.read_csv(gantry_file)
                    logger.info(f"找到现有门架数据: {gantry_file}")
                    logger.info(f"数据记录数: {len(gantry_data)}")
                    if 'gantry_id' in gantry_data.columns:
                        logger.info(f"门架数量: {gantry_data['gantry_id'].nunique()}")
                    if 'start_time' in gantry_data.columns:
                        time_range = gantry_data['start_time'].agg(['min', 'max'])
                        logger.info(f"数据时间: {time_range['min']} - {time_range['max']}")
                except Exception as e:
                    logger.warning(f"读取现有门架数据失败: {e}")
        
        # 如果没有现有数据，尝试从数据库加载
        if gantry_data is None or gantry_data.empty:
            logger.info("尝试从数据库加载门架数据...")
            try:
                from shared.data_access.gantry_loader import GantryDataLoader
                
                # 从仿真元数据获取时间范围
                metadata_file = simulation_dir / "simulation_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        
                    # 解析时间范围
                    start_time_str = metadata.get('start_time', '2025-08-04T09:00:00')
                    end_time_str = metadata.get('end_time', '2025-08-04T09:15:00')
                    
                    start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    
                    # 使用门架数据加载方法
                    loader = GantryDataLoader()
                    try:
                        # 加载门架原始数据
                        raw_data = loader.load_gantry_data(start_time, end_time)
                        if not raw_data.empty:
                            # 保存到门架数据文件夹
                            gantry_folder = case_dir / f"gantry_{start_time.strftime('%Y%m%d_%H%M%S')}_{end_time.strftime('%Y%m%d_%H%M%S')}"
                            gantry_folder.mkdir(exist_ok=True)
                            
                            # 保存原始格式数据
                            raw_file = gantry_folder / "gantry_data_raw.csv"
                            raw_data.to_csv(raw_file, index=False, encoding="utf-8-sig")
                            logger.info(f"保存门架原始数据: {raw_file}")

                            # 设置供后续处理使用
                            gantry_data = raw_data
                            
                            logger.info("门架数据准备完成，开始精度分析...")
                        else:
                            raise Exception("无法从数据库加载门架数据")
                    finally:
                        loader.close()
                else:
                    raise Exception("无法找到仿真元数据文件")
            except Exception as e:
                raise Exception(f"门架数据获取失败: {str(e)}")
        
        if gantry_data is None or gantry_data.empty:
            raise Exception("精度分析需要门架数据，但无法获取到有效的门架数据。")
        
        return gantry_data

    def _resolve_e1_data(self, simulation_dir: Path) -> pd.DataFrame:
        """解析E1检测器数据"""
        e1_data = pd.DataFrame()
        try:
            # 从仿真结果的e1目录加载XML文件
            e1_dir = simulation_dir / "e1"
            if e1_dir.exists():
                from shared.data_processors.e1_processor import E1DataProcessor
                
                # 从仿真元数据获取仿真开始时间
                metadata_file = simulation_dir / "simulation_metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    start_time_str = metadata.get('start_time', '2025-08-04T09:00:00')
                    simulation_start = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    
                    # 使用E1数据处理器
                    e1_processor = E1DataProcessor()
                    e1_data = e1_processor.load_from_directory(e1_dir, simulation_start)
                    
                    logger.info(f"成功加载E1检测器数据: {len(e1_data)} 条记录，{e1_data['gantry_id'].nunique() if not e1_data.empty else 0} 个门架")
                else:
                    raise Exception("无法找到仿真元数据文件")
            else:
                raise Exception("未找到E1检测器数据目录")
        except Exception as e:
            raise Exception(f"E1数据加载失败: {e}")
        
        return e1_data

    def _run_alignment_and_exports(self, gantry_data: pd.DataFrame, e1_data: pd.DataFrame, analysis_dir: Path) -> Dict[str, Any]:
        """执行数据对齐和导出"""
        from shared.data_processors.gantry_processor import GantryDataProcessor
        
        # 处理门架数据，生成待比较的CSV文件
        gantry_processor = GantryDataProcessor()
        
        # 处理门架数据
        processed_data = gantry_processor.process_for_accuracy_analysis(gantry_data, e1_data)
        
        if not processed_data:
            raise Exception("门架数据处理失败")
        
        # 导出比较用的CSV文件
        csv_exports = gantry_processor.export_analysis_csvs(analysis_dir)
        
        # 获取对齐后的数据
        aligned_data = gantry_processor.get_aligned_data()
        
        if aligned_data.empty:
            raise Exception("无法获取对齐后的数据进行分析")
        
        return {
            'aligned_data': aligned_data,
            'csv_exports': csv_exports,
            'data_summary': gantry_processor.get_data_summary(),
            'alignment_metadata': gantry_processor.get_alignment_metadata()
        }

    

    def _build_analysis_response(self, case_id: str, simulation_id: str, analysis_dir: Path, 
                                alignment_results: Dict[str, Any], analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """构建分析响应"""
        return {
            "success": True,
            "message": "精度分析完成",
            "data": {
                "analysis_id": analysis_dir.name,
                "case_id": case_id,
                "simulation_id": simulation_id,
                "metrics": analysis_results.get("basic_metrics", {}),
                "chart_files": analysis_results.get("chart_files", []),
                "report_file": analysis_results.get("report_file", ""),
                "exported_csvs": alignment_results.get("csv_exports", []),
                "analysis_time": analysis_results.get("analysis_time", ""),
                "data_summary": alignment_results.get("data_summary", {}),
                "alignment_metadata": alignment_results.get("alignment_metadata", {})
            }
        }

    async def _run_accuracy_analysis(self, case_root: Path, simulation_folders: List[Path], 
                                   simulation_ids: List[str], result_folder_name: str) -> Dict[str, Any]:
        """运行精度分析（统一复用私有方法）"""
        try:
            # 1) 准备分析目录
            analysis_dir = self._prepare_analysis_dirs(case_root)

            # 2) 解析仿真目录（优先使用传入的 simulation_folders，其次使用 simulation_ids 推导）
            if simulation_folders and len(simulation_folders) > 0:
                simulation_dir = simulation_folders[0]
            else:
                if not simulation_ids:
                    raise Exception("缺少仿真ID")
                simulation_dir = case_root / "simulations" / simulation_ids[0]
            if not simulation_dir.exists():
                raise Exception(f"仿真结果目录不存在: {simulation_dir}")

            # 3) 加载数据（复用私有方法）
            gantry_df = self._resolve_gantry_data(case_root, simulation_dir)
            e1_df = self._resolve_e1_data(simulation_dir)

            # 4) 对齐与导出（复用私有方法）
            alignment_results = self._run_alignment_and_exports(gantry_df, e1_df, analysis_dir)

            # 5) 精度分析（直接使用 shared 分析器）
            from shared.analysis_tools.accuracy_analysis import AccuracyAnalysis
            analyzer = AccuracyAnalysis()
            charts_dir = analysis_dir / "charts"
            reports_dir = analysis_dir
            analyzer.set_output_dirs(str(charts_dir), str(reports_dir))
            analysis_results = analyzer.analyze_accuracy(alignment_results['aligned_data'])

            # 6) 构建统一返回
            return {
                "success": True,
                "message": "精度分析完成",
                "data": {
                    "analysis_id": analysis_dir.name,
                    "case_id": str(case_root.name),
                    "simulation_ids": simulation_ids,
                    "metrics": analysis_results.get("basic_metrics", {}),
                    "chart_files": analysis_results.get("chart_files", []),
                    "report_file": analysis_results.get("report_file", ""),
                    "exported_csvs": alignment_results.get("csv_exports", []),
                    "analysis_time": analysis_results.get("analysis_time", ""),
                    "data_summary": alignment_results.get("data_summary", {}),
                    "alignment_metadata": alignment_results.get("alignment_metadata", {})
                }
            }

        except Exception as e:
            logger.error(f"精度分析执行失败: {e}")
            return {
                "success": False,
                "message": f"精度分析执行失败: {str(e)}",
                "data": {
                    "analysis_id": analysis_dir.name if 'analysis_dir' in locals() else None,
                    "error": str(e)
                }
            }

    async def _run_mechanism_analysis(self, case_root: Path, simulation_folders: List[Path], 
                                    simulation_ids: List[str], result_folder_name: str) -> Dict[str, Any]:
        """运行机理分析（交通流机理分析）"""
        try:
            logger.info("开始运行机理分析...")
            
            # 1) 准备分析目录
            analysis_dir = case_root / "analysis" / f"ana_{datetime.now().strftime('%m%d_%H%M%S')}" / "mechanism"
            analysis_dir.mkdir(parents=True, exist_ok=True)
            
            # 2) 获取仿真数据
            simulation_data = self._get_simulation_data_for_mechanism(simulation_folders)
            if simulation_data.empty:
                raise Exception("无法获取有效的仿真数据进行机理分析")
            
            # 3) 执行机理分析
            from shared.analysis_tools.mechanism_analysis import MechanismAnalysis
            analyzer = MechanismAnalysis()
            
            charts_dir = analysis_dir / "charts"
            reports_dir = analysis_dir
            
            analyzer.set_output_dirs(str(charts_dir), str(reports_dir))
            
            # 执行机理分析
            analysis_results = analyzer.analyze_mechanism(simulation_data)
            
            if not analysis_results:
                raise Exception("机理分析执行失败")
            
            # 4) 保存分析元数据
            metadata = {
                "analysis_type": "mechanism",
                "simulation_ids": simulation_ids,
                "simulation_folders": [str(f) for f in simulation_folders],
                "created_at": datetime.now().isoformat(),
                "status": "completed",
                "output_folder": str(analysis_dir),
                "report_file": analysis_results.get("report_file", ""),
                "chart_files": analysis_results.get("chart_files", []),
                "csv_files": analysis_results.get("csv_files", {})
            }
            
            metadata_file = analysis_dir / "analysis_metadata.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 5) 更新分析索引
            self._update_analysis_index(case_root, analysis_dir.name, metadata)
            
            logger.info(f"机理分析完成: {analysis_dir}")
            
            return {
                "success": True,
                "message": "机理分析完成",
                "data": {
                    "analysis_id": analysis_dir.name,
                    "case_id": str(case_root.name),
                    "simulation_ids": simulation_ids,
                    "analysis_type": "mechanism",
                    "chart_files": analysis_results.get("chart_files", []),
                    "report_file": analysis_results.get("report_file", ""),
                    "csv_files": analysis_results.get("csv_files", {}),
                    "analysis_time": analysis_results.get("analysis_time", ""),
                    "flow_density_analysis": analysis_results.get("flow_density_analysis", {}),
                    "speed_flow_analysis": analysis_results.get("speed_flow_analysis", {}),
                    "traffic_state_analysis": analysis_results.get("traffic_state_analysis", {}),
                    "residual_analysis": analysis_results.get("residual_analysis", {})
                }
            }
            
        except Exception as e:
            logger.error(f"机理分析执行失败: {e}")
            return {
                "success": False,
                "message": f"机理分析执行失败: {str(e)}",
                "data": {
                    "analysis_id": analysis_dir.name if 'analysis_dir' in locals() else None,
                    "error": str(e)
                }
            }
    
    def _update_analysis_index(self, case_root: Path, analysis_id: str, metadata: Dict[str, Any]):
        """更新分析索引"""
        try:
            index_file = case_root / "analysis" / "analysis_index.json"
            
            if index_file.exists():
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
            else:
                index_data = {"analyses": [], "updated_at": None}
            
            # 添加新的分析记录
            analysis_record = {
                "analysis_id": analysis_id,
                "analysis_type": metadata.get("analysis_type"),
                "simulation_ids": metadata.get("simulation_ids", []),
                "simulation_folders": metadata.get("simulation_folders", []),
                "created_at": metadata.get("created_at"),
                "status": metadata.get("status"),
                "output_folder": metadata.get("output_folder"),
                "report_file": metadata.get("report_file"),
                "chart_files": metadata.get("chart_files", []),
                "csv_files": metadata.get("csv_files", {})
            }
            
            # 检查是否已存在
            existing_index = -1
            for i, analysis in enumerate(index_data["analyses"]):
                if analysis.get("analysis_id") == analysis_id:
                    existing_index = i
                    break
            
            if existing_index >= 0:
                # 更新现有记录
                index_data["analyses"][existing_index] = analysis_record
            else:
                # 添加新记录
                index_data["analyses"].append(analysis_record)
            
            # 更新时间戳
            index_data["updated_at"] = datetime.now().isoformat()
            
            # 保存索引文件
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"分析索引已更新: {analysis_id}")
            
        except Exception as e:
            logger.error(f"更新分析索引失败: {e}")
    
    def _get_simulation_data_for_mechanism(self, simulation_folders: List[Path]) -> pd.DataFrame:
        """获取用于机理分析的仿真数据"""
        try:
            all_data = []
            
            for sim_folder in simulation_folders:
                # 1. 加载E1检测器数据
                e1_dir = sim_folder / "e1"
                if e1_dir.exists():
                    from shared.data_processors.e1_processor import E1DataProcessor
                    
                    # 从仿真元数据获取仿真开始时间
                    metadata_file = sim_folder / "simulation_metadata.json"
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        start_time_str = metadata.get('start_time', '2025-08-04T09:00:00')
                        simulation_start = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                        
                        # 使用E1数据处理器
                        e1_processor = E1DataProcessor()
                        e1_data = e1_processor.load_from_directory(e1_dir, simulation_start)
                        
                        if not e1_data.empty:
                            # 添加仿真标识
                            e1_data['simulation_id'] = sim_folder.name
                            e1_data['simulation_folder'] = str(sim_folder)
                            all_data.append(e1_data)
                            
                            logger.info(f"加载E1数据: {sim_folder.name}, {len(e1_data)} 条记录")
                
                # 2. 加载summary.xml数据（如果存在）
                summary_file = sim_folder / "summary.xml"
                if summary_file.exists():
                    from shared.analysis_tools.accuracy_analyzer import AccuracyAnalyzer
                    analyzer = AccuracyAnalyzer()
                    summary_data = analyzer._parse_summary_xml(summary_file)
                    
                    if not summary_data.empty:
                        # 添加仿真标识
                        summary_data['simulation_id'] = sim_folder.name
                        summary_data['simulation_folder'] = str(sim_folder)
                        all_data.append(summary_data)
                        
                        logger.info(f"加载summary数据: {sim_folder.name}, {len(summary_data)} 条记录")
            
            if not all_data:
                logger.warning("未找到任何仿真数据")
                return pd.DataFrame()
            
            # 合并所有数据
            combined_data = pd.concat(all_data, ignore_index=True)
            
            # 数据预处理
            if 'flow' in combined_data.columns:
                combined_data['flow'] = pd.to_numeric(combined_data['flow'], errors='coerce')
            if 'speed' in combined_data.columns:
                combined_data['speed'] = pd.to_numeric(combined_data['speed'], errors='coerce')
            if 'occupancy' in combined_data.columns:
                combined_data['occupancy'] = pd.to_numeric(combined_data['occupancy'], errors='coerce')
            
            # 计算密度（如果不存在）
            if 'density' not in combined_data.columns and 'flow' in combined_data.columns and 'speed' in combined_data.columns:
                # 使用基本关系：密度 = 流量 / 速度（简化计算）
                combined_data['density'] = combined_data['flow'] / (combined_data['speed'] + 1e-6)  # 避免除零
            
            # 过滤无效数据
            combined_data = combined_data.dropna(subset=['flow', 'speed'])
            
            logger.info(f"机理分析数据准备完成: {len(combined_data)} 条记录")
            return combined_data
            
        except Exception as e:
            logger.error(f"获取机理分析数据失败: {e}")
            return pd.DataFrame()

    async def _run_performance_analysis(self, case_root: Path, simulation_folders: List[Path], 
                                      simulation_ids: List[str], result_folder_name: str) -> Dict[str, Any]:
        """运行性能分析"""
        # 暂时返回占位实现
        return {
            "analysis_type": "performance", 
            "simulation_ids": simulation_ids,
            "status": "completed",
            "message": "性能分析功能待实现",
            "analysis_time": datetime.now().isoformat()
        }
    
    async def get_case_analysis_history(self, case_id: str) -> Dict[str, Any]:
        """获取案例的分析历史记录"""
        try:
            case_root = self.cases_dir / case_id
            analysis_index_file = case_root / "analysis" / "analysis_index.json"
            
            if not analysis_index_file.exists():
                return {
                    "case_id": case_id,
                    "analyses": [],
                    "total_count": 0
                }
            
            with open(analysis_index_file, 'r', encoding='utf-8') as f:
                import json
                analysis_index = json.load(f)
            
            return {
                "case_id": case_id,
                "analyses": analysis_index.get("analyses", []),
                "total_count": len(analysis_index.get("analyses", [])),
                "last_updated": analysis_index.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"获取分析历史失败: {e}")
            return {
                "case_id": case_id,
                "analyses": [],
                "total_count": 0,
                "error": str(e)
            }
    
    async def get_analysis_simulation_mapping(self, case_id: str, 
                                            analysis_id: str = None) -> Dict[str, Any]:
        """获取分析和仿真的对应关系"""
        try:
            case_root = self.cases_dir / case_id
            
            if analysis_id:
                # 获取特定分析的对应关系
                analysis_metadata_file = case_root / "analysis" / analysis_id / "analysis_metadata.json"
                
                if not analysis_metadata_file.exists():
                    return {
                        "error": f"分析 {analysis_id} 的元数据不存在"
                    }
                
                with open(analysis_metadata_file, 'r', encoding='utf-8') as f:
                    import json
                    analysis_metadata = json.load(f)
                
                return {
                    "analysis_id": analysis_id,
                    "analysis_type": analysis_metadata.get("analysis_type"),
                    "simulation_ids": analysis_metadata.get("simulation_ids", []),
                    "simulation_folders": analysis_metadata.get("simulation_folders", []),
                    "created_at": analysis_metadata.get("created_at"),
                    "status": analysis_metadata.get("status"),
                    "output_folder": analysis_metadata.get("output_folder"),
                    "report_file": analysis_metadata.get("report_file")
                }
            else:
                # 获取所有分析的对应关系
                analysis_history = await self.get_case_analysis_history(case_id)
                
                mappings = []
                for analysis in analysis_history.get("analyses", []):
                    mapping = {
                        "analysis_id": analysis.get("analysis_id"),
                        "analysis_type": analysis.get("analysis_type"),
                        "simulation_ids": analysis.get("simulation_ids", []),
                        "simulation_folders": analysis.get("simulation_folders", []),
                        "created_at": analysis.get("created_at"),
                        "status": analysis.get("status"),
                        "output_folder": analysis.get("output_folder")
                    }
                    mappings.append(mapping)
                
                return {
                    "case_id": case_id,
                    "total_analyses": len(mappings),
                    "mappings": mappings
                }
                
        except Exception as e:
            return {
                "error": f"获取对应关系失败: {str(e)}"
            }
    
    async def list_analysis_results(self, case_id: str, 
                                  analysis_type: Optional[str] = "accuracy") -> Dict[str, Any]:
        """列出指定案例下的历史分析结果"""
        try:
            at = (analysis_type or "accuracy").lower()
            if at not in ("accuracy", "mechanism", "performance"):
                at = "accuracy"
            
            base_dir = self.cases_dir / case_id / "analysis" / at
            if not base_dir.exists():
                # 如果目录不存在，创建它并返回空结果
                base_dir.mkdir(parents=True, exist_ok=True)
                return {"case_id": case_id, "analysis_type": at, "results": []}
            
            items: List[Dict[str, Any]] = []
            for d in base_dir.iterdir():
                if d.is_dir() and (d.name.startswith("ana_") or d.name.startswith("accuracy_results_")):
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
                                record["chart_files"].append(f"/cases/{case_id}/analysis/{at}/{d.name}/accuracy/charts/{p.name}")
                    else:
                        for p in d.glob("*.csv"):
                            record["csv_files"].append(f"/cases/{case_id}/analysis/{at}/{d.name}/{p.name}")
                        charts_dir = d / "charts"
                        if charts_dir.exists():
                            for p in charts_dir.glob("*.png"):
                                record["chart_files"].append(f"/cases/{case_id}/analysis/{at}/{d.name}/accuracy/charts/{p.name}")
                    
                    items.append(record)
            
            items.sort(key=lambda x: x["created_at"], reverse=True)
            return {"case_id": case_id, "analysis_type": at, "results": items}
            
        except Exception as e:
            raise Exception(f"获取分析结果列表失败: {str(e)}")
    
# 创建服务实例
analysis_service = AnalysisService()


# 导出服务函数 (保持向后兼容)
async def analyze_accuracy_service(request: AccuracyAnalysisRequest) -> Dict[str, Any]:
    """精度分析服务函数"""
    return await analysis_service.analyze_accuracy(request)


async def get_case_analysis_history(case_id: str) -> Dict[str, Any]:
    """获取分析历史服务函数"""
    return await analysis_service.get_case_analysis_history(case_id)


async def get_analysis_simulation_mapping(case_id: str, analysis_id: str = None) -> Dict[str, Any]:
    """获取分析映射服务函数"""
    return await analysis_service.get_analysis_simulation_mapping(case_id, analysis_id)


async def list_analysis_results_service(case_id: str, analysis_type: Optional[str] = "accuracy") -> Dict[str, Any]:
    """列出分析结果服务函数"""
    return await analysis_service.list_analysis_results(case_id, analysis_type)
