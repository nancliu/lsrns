"""
性能分析服务
专门处理性能分析相关的业务逻辑
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from .base_metadata_service import BaseMetadataService
from shared.analysis_tools.performance_analysis import PerformanceAnalyzer

logger = logging.getLogger(__name__)


class PerformanceAnalysisService(BaseMetadataService):
    """性能分析服务类"""
    
    async def analyze_performance(self, case_id: str, simulation_ids: List[str]) -> Dict[str, Any]:
        """
        执行性能分析
        
        Args:
            case_id: 案例ID
            simulation_ids: 仿真ID列表
            
        Returns:
            分析结果字典
        """
        try:
            logger.info(f"开始性能分析: case_id={case_id}, simulation_ids={simulation_ids}")
            
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
            base_dir, analysis_dir = self.prepare_analysis_dirs(case_root, "performance")
            
            # 执行性能分析的核心逻辑
            analysis_results = await self._run_performance_analysis(case_root, simulation_folders, simulation_ids, analysis_dir)
            
            # 更新元数据（仅分析分支：analysis/<batch>/metadata.json 与 analysis/analysis_index.json）
            self.update_metadata_for_analysis(case_root, simulation_ids, "performance", analysis_results, base_dir)
            
            logger.info(f"性能分析完成: {analysis_dir}")
            
            return {
                "success": True,
                "message": "性能分析完成",
                "data": {
                    "analysis_id": analysis_dir.name,
                    "case_id": str(case_root.name),
                    "simulation_ids": simulation_ids,
                    "analysis_type": "performance",
                    "chart_files": analysis_results.get("chart_files", []),
                    "report_file": analysis_results.get("report_file", ""),
                    "csv_files": analysis_results.get("csv_files", {}),
                    "performance_metrics": analysis_results.get("performance_metrics", {}),
                    "efficiency_score": analysis_results.get("efficiency_score", 0),
                    "analysis_summary": analysis_results.get("analysis_summary", {})
                }
            }
            
        except Exception as e:
            logger.error(f"性能分析执行失败: {e}")
            return {
                "success": False,
                "message": f"性能分析执行失败: {str(e)}",
                "data": {"error": str(e)}
            }
    
    async def list_analysis_results(self, case_id: str, analysis_type: str = "performance") -> Dict[str, Any]:
        """
        获取性能分析结果列表
        
        Args:
            case_id: 案例ID
            analysis_type: 分析类型 (默认performance)
            
        Returns:
            分析结果列表字典
        """
        try:
            logger.info(f"获取性能分析结果列表: case_id={case_id}, analysis_type={analysis_type}")
            
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
            
            logger.info(f"获取到 {len(results)} 个性能分析结果")
            
            return {
                "case_id": case_id,
                "analysis_type": analysis_type,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"获取性能分析结果列表失败: {e}")
            raise
    
    async def _run_performance_analysis(self, case_root: Path, simulation_folders: List[Path], 
                                      simulation_ids: List[str], analysis_dir: Path) -> Dict[str, Any]:
        """执行性能分析的核心逻辑"""
        # 1. 执行性能分析（使用shared层分析器）
        analyzer = PerformanceAnalyzer()
        charts_dir = analysis_dir / "charts"
        reports_dir = analysis_dir
        
        analyzer.set_output_dirs(str(charts_dir), str(reports_dir))
        
        # 2. 执行性能分析
        analysis_results = analyzer.analyze_performance(case_root, simulation_folders, simulation_ids)
        
        if not analysis_results:
            raise Exception("性能分析执行失败")
        
        return analysis_results
