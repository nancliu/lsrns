"""
机理分析服务
专门处理机理分析相关的业务逻辑
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from .base_metadata_service import BaseMetadataService
from shared.analysis_tools.mechanism_analysis import MechanismAnalysis
from shared.data_processors.e1_processor import E1DataProcessor

logger = logging.getLogger(__name__)


class MechanismAnalysisService(BaseMetadataService):
    """机理分析服务类"""
    
    async def analyze_mechanism(self, case_id: str, simulation_ids: List[str]) -> Dict[str, Any]:
        """
        执行机理分析
        
        Args:
            case_id: 案例ID
            simulation_ids: 仿真ID列表
            
        Returns:
            分析结果字典
        """
        try:
            logger.info(f"开始机理分析: case_id={case_id}, simulation_ids={simulation_ids}")
            
            # 获取案例根目录
            case_root = self.cases_dir / case_id
            if not case_root.exists():
                raise Exception(f"案例不存在: {case_id}")
            
            # 获取仿真文件夹
            simulation_folders = []
            for sim_id in simulation_ids:
                sim_dir = case_root / "simulations" / sim_id
                if sim_dir.exists():
                    simulation_folders.append(sim_dir)
                else:
                    logger.warning(f"仿真目录不存在: {sim_dir}")
            
            if not simulation_folders:
                raise Exception("选择的仿真结果目录不存在")
            
            # 准备分析目录
            # 说明：结果分析流程仅维护 analysis 分支元数据（批次与索引），
            # 不创建/不更新 案例级 metadata.json，且不更新仿真分支元数据。
            base_dir, analysis_dir = self.prepare_analysis_dirs(case_root, "mechanism")
            
            # 执行机理分析的核心逻辑
            analysis_results = await self._run_mechanism_analysis(simulation_folders, analysis_dir)
            
            # 更新元数据（仅分析分支：analysis/<batch>/metadata.json 与 analysis/analysis_index.json）
            self.update_metadata_for_analysis(case_root, simulation_ids, "mechanism", analysis_results, base_dir)
            
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
                "data": {"error": str(e)}
            }
    
    async def list_analysis_results(self, case_id: str, analysis_type: str = "mechanism") -> Dict[str, Any]:
        """
        获取机理分析结果列表
        
        Args:
            case_id: 案例ID
            analysis_type: 分析类型 (默认mechanism)
            
        Returns:
            分析结果列表字典
        """
        try:
            logger.info(f"获取机理分析结果列表: case_id={case_id}, analysis_type={analysis_type}")
            
            case_dir = self.cases_dir / case_id
            if not case_dir.exists():
                raise Exception(f"案例不存在: {case_id}")
            
            # 检查分析索引文件
            analysis_index_file = case_dir / "analysis" / "analysis_index.json"
            if not analysis_index_file.exists():
                logger.info(f"分析索引文件不存在: {analysis_index_file}")
                return {
                    "case_id": case_id,
                    "analysis_type": analysis_type,
                    "results": []
                }
            
            # 读取分析索引
            import json
            with open(analysis_index_file, 'r', encoding='utf-8') as f:
                analysis_index = json.load(f)
            
            results = []
            
            # 检查分析索引结构
            if "analyses" in analysis_index:
                # 新的结构：使用analyses数组
                analyses_list = analysis_index["analyses"]
                for analysis_info in analyses_list:
                    batch_id = analysis_info.get("analysis_batch_id", "")
                    analysis_types = analysis_info.get("analysis_types", {})
                    
                    # 检查analysis_types字段，它可能是字典或数组
                    if isinstance(analysis_types, dict):
                        # 如果是字典，检查是否包含指定的分析类型
                        if analysis_type in analysis_types:
                            # 检查分析类型目录
                            analysis_type_dir = case_dir / "analysis" / batch_id / analysis_type
                            if analysis_type_dir.exists():
                                # 检查元数据文件
                                metadata_file = analysis_type_dir / "metadata.json"
                                if metadata_file.exists():
                                    try:
                                        with open(metadata_file, 'r', encoding='utf-8') as f:
                                            metadata = json.load(f)
                                        
                                        # 构建结果信息
                                        result_info = {
                                            "folder": f"{batch_id}/{analysis_type}",
                                            "created_at": metadata.get("created_at", ""),
                                            "completed_at": metadata.get("completed_at", ""),
                                            "status": metadata.get("status", "unknown"),
                                            "analysis_id": metadata.get("analysis_id", ""),
                                            "case_id": metadata.get("case_id", case_id),
                                            "analysis_type": analysis_type
                                        }
                                        
                                        # 添加文件信息
                                        results_data = metadata.get("results", {})
                                        if results_data:
                                            result_info["report_html"] = results_data.get("report_file", "")
                                            result_info["chart_files"] = results_data.get("chart_files", [])
                                            result_info["csv_files"] = results_data.get("csv_files", [])
                                        
                                        results.append(result_info)
                                        
                                    except Exception as e:
                                        logger.warning(f"读取分析元数据失败 {metadata_file}: {e}")
                                        continue
                    elif isinstance(analysis_types, list):
                        # 如果是数组，检查是否包含指定的分析类型
                        if analysis_type in analysis_types:
                            # 检查分析类型目录
                            analysis_type_dir = case_dir / "analysis" / batch_id / analysis_type
                            if analysis_type_dir.exists():
                                # 检查元数据文件
                                metadata_file = analysis_type_dir / "metadata.json"
                                if metadata_file.exists():
                                    try:
                                        with open(metadata_file, 'r', encoding='utf-8') as f:
                                            metadata = json.load(f)
                                        
                                        # 构建结果信息
                                        result_info = {
                                            "folder": f"{batch_id}/{analysis_type}",
                                            "created_at": metadata.get("created_at", ""),
                                            "completed_at": metadata.get("completed_at", ""),
                                            "status": metadata.get("status", "unknown"),
                                            "analysis_id": metadata.get("analysis_id", ""),
                                            "case_id": metadata.get("case_id", case_id),
                                            "analysis_type": analysis_type
                                        }
                                        
                                        # 添加文件信息
                                        results_data = metadata.get("results", {})
                                        if results_data:
                                            result_info["report_html"] = results_data.get("report_file", "")
                                            result_info["chart_files"] = results_data.get("chart_files", [])
                                            result_info["csv_files"] = results_data.get("csv_files", [])
                                        
                                        results.append(result_info)
                                        
                                    except Exception as e:
                                        logger.warning(f"读取分析元数据失败 {metadata_file}: {e}")
                                        continue
            else:
                # 旧的结构：直接遍历键值对
                for batch_id, batch_info in analysis_index.items():
                    # 检查analysis_types字段，它可能是字典或数组
                    analysis_types = batch_info.get("analysis_types", {})
                    if isinstance(analysis_types, dict):
                        # 如果是字典，检查是否包含指定的分析类型
                        if analysis_type in analysis_types:
                            # 检查分析类型目录
                            analysis_type_dir = case_dir / "analysis" / batch_id / analysis_type
                            if analysis_type_dir.exists():
                                # 检查元数据文件
                                metadata_file = analysis_type_dir / "metadata.json"
                                if metadata_file.exists():
                                    try:
                                        with open(metadata_file, 'r', encoding='utf-8') as f:
                                            metadata = json.load(f)
                                        
                                        # 构建结果信息
                                        result_info = {
                                            "folder": f"{batch_id}/{analysis_type}",
                                            "created_at": metadata.get("created_at", ""),
                                            "completed_at": metadata.get("completed_at", ""),
                                            "status": metadata.get("status", "unknown"),
                                            "analysis_id": metadata.get("analysis_id", ""),
                                            "case_id": metadata.get("case_id", case_id),
                                            "analysis_type": analysis_type
                                        }
                                        
                                        # 添加文件信息
                                        results_data = metadata.get("results", {})
                                        if results_data:
                                            result_info["report_html"] = results_data.get("report_file", "")
                                            result_info["chart_files"] = results_data.get("chart_files", [])
                                            result_info["csv_files"] = results_data.get("csv_files", [])
                                        
                                        results.append(result_info)
                                        
                                    except Exception as e:
                                        logger.warning(f"读取分析元数据失败 {metadata_file}: {e}")
                                        continue
                    elif isinstance(analysis_types, list):
                        # 如果是数组，检查是否包含指定的分析类型
                        if analysis_type in analysis_types:
                            # 检查分析类型目录
                            analysis_type_dir = case_dir / "analysis" / batch_id / analysis_type
                            if analysis_type_dir.exists():
                                # 检查元数据文件
                                metadata_file = analysis_type_dir / "metadata.json"
                                if metadata_file.exists():
                                    try:
                                        with open(metadata_file, 'r', encoding='utf-8') as f:
                                            metadata = json.load(f)
                                        
                                        # 构建结果信息
                                        result_info = {
                                            "folder": f"{batch_id}/{analysis_type}",
                                            "created_at": metadata.get("created_at", ""),
                                            "completed_at": metadata.get("completed_at", ""),
                                            "status": metadata.get("status", "unknown"),
                                            "analysis_id": metadata.get("analysis_id", ""),
                                            "case_id": metadata.get("case_id", case_id),
                                            "analysis_type": analysis_type
                                        }
                                        
                                        # 添加文件信息
                                        results_data = metadata.get("results", {})
                                        if results_data:
                                            result_info["report_html"] = results_data.get("report_file", "")
                                            result_info["chart_files"] = results_data.get("chart_files", [])
                                            result_info["csv_files"] = results_data.get("csv_files", [])
                                        
                                        results.append(result_info)
                                        
                                    except Exception as e:
                                        logger.warning(f"读取分析元数据失败 {metadata_file}: {e}")
                                        continue
            
            # 按创建时间排序（最新的在前）
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            logger.info(f"获取到 {len(results)} 个机理分析结果")
            
            return {
                "case_id": case_id,
                "analysis_type": analysis_type,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"获取机理分析结果列表失败: {e}")
            raise
    
    async def _run_mechanism_analysis(self, simulation_folders: List[Path], analysis_dir: Path) -> Dict[str, Any]:
        """执行机理分析的核心逻辑"""
        # 1. 获取仿真数据
        simulation_data = self._get_simulation_data_for_mechanism(simulation_folders)
        if simulation_data.empty:
            raise Exception("无法获取有效的仿真数据进行机理分析")
        
        # 2. 执行机理分析（使用shared层分析器）
        analyzer = MechanismAnalysis()
        charts_dir = analysis_dir / "charts"
        reports_dir = analysis_dir
        
        analyzer.set_output_dirs(str(charts_dir), str(reports_dir))
        
        # 3. 执行机理分析
        analysis_results = analyzer.analyze_mechanism(simulation_data)
        
        if not analysis_results:
            raise Exception("机理分析执行失败")
        
        return analysis_results
    
    def _get_simulation_data_for_mechanism(self, simulation_folders: List[Path]):
        """获取用于机理分析的仿真数据"""
        try:
            all_data = []
            
            for sim_folder in simulation_folders:
                # 1. 加载E1检测器数据
                e1_dir = sim_folder / "e1"
                if e1_dir.exists():
                    processor = E1DataProcessor()
                    e1_data = processor.load_e1_data(e1_dir)
                    if not e1_data.empty:
                        e1_data['simulation_id'] = sim_folder.name
                        all_data.append(e1_data)
                
                # 2. 加载summary.xml数据
                summary_file = sim_folder / "summary.xml"
                if summary_file.exists():
                    summary_data = self._parse_summary_xml(summary_file)
                    if not summary_data.empty:
                        summary_data['simulation_id'] = sim_folder.name
                        all_data.append(summary_data)
            
            if not all_data:
                return type('EmptyDataFrame', (), {'empty': True})()
            
            # 合并所有数据
            import pandas as pd
            combined_data = pd.concat(all_data, ignore_index=True)
            logger.info(f"成功加载机理分析数据: {len(combined_data)} 条记录")
            
            return combined_data
            
        except Exception as e:
            logger.error(f"获取机理分析数据失败: {e}")
            return type('EmptyDataFrame', (), {'empty': True})()
    
    def _parse_summary_xml(self, summary_file: Path):
        """解析summary.xml文件"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(summary_file)
            root = tree.getroot()
            
            data = []
            for step in root.findall(".//step"):
                record = {
                    "time": float(step.get("time")),
                    "loaded": int(step.get("loaded", 0)),
                    "inserted": int(step.get("inserted", 0)),
                    "running": int(step.get("running", 0)),
                    "waiting": int(step.get("waiting", 0)),
                    "ended": int(step.get("ended", 0))
                }
                data.append(record)
            
            if not data:
                # 如果没有step数据，尝试获取总体统计
                for child in root:
                    if child.tag in ['step', 'vehicle', 'person', 'edge', 'lane']:
                        for item in child:
                            if item.tag in ['loaded', 'inserted', 'running', 'waiting', 'ended']:
                                data.append({
                                    "time": 0,
                                    item.tag: int(item.text) if item.text else 0,
                                    "loaded": 0, "inserted": 0, "running": 0, "waiting": 0, "ended": 0
                                })
                            elif item.tag == 'time':
                                data.append({
                                    "time": int(item.text) if item.text else 0,
                                    "loaded": 0, "inserted": 0, "running": 0, "waiting": 0, "ended": 0
                                })
            
            import pandas as pd
            df = pd.DataFrame(data)
            
            if not df.empty:
                # 填充缺失值
                for col in ['loaded', 'inserted', 'running', 'waiting', 'ended']:
                    if col not in df.columns:
                        df[col] = 0
                    else:
                        df[col] = df[col].fillna(0)
                
                logger.info(f"成功解析summary.xml: {len(df)} 条记录")
            
            return df
            
        except Exception as e:
            logger.error(f"解析summary.xml失败: {e}")
            import pandas as pd
            return pd.DataFrame()
