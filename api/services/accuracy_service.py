"""
精度分析服务
专门处理精度分析相关的业务逻辑
"""

import logging
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional

from .base_metadata_service import BaseMetadataService
from shared.analysis_tools.accuracy_analysis import AccuracyAnalysis
from shared.data_processors.gantry_processor import GantryDataProcessor
from shared.data_processors.e1_processor import E1DataProcessor

logger = logging.getLogger(__name__)


class AccuracyAnalysisService(BaseMetadataService):
    """精度分析服务类"""
    
    async def analyze_accuracy(self, case_id: str, simulation_id: str) -> Dict[str, Any]:
        """
        执行精度分析
        
        Args:
            case_id: 案例ID
            simulation_id: 仿真ID
            
        Returns:
            分析结果字典
        """
        try:
            logger.info(f"开始精度分析: case_id={case_id}, simulation_id={simulation_id}")
            
            # 获取案例和仿真目录
            case_dir = self.cases_dir / case_id
            simulation_dir = case_dir / "simulations" / simulation_id
            
            if not case_dir.exists():
                raise Exception(f"案例不存在: {case_id}")
            if not simulation_dir.exists():
                raise Exception(f"仿真目录不存在: {simulation_id}")
            
            # 准备分析目录
            # 说明：结果分析流程仅维护 analysis 分支元数据（批次与索引），
            # 不创建/不更新 案例级 metadata.json，且不更新仿真分支元数据。
            base_dir, analysis_dir = self.prepare_analysis_dirs(case_dir, "accuracy")
            
            # 执行精度分析的核心逻辑
            analysis_results = await self._run_accuracy_analysis(case_dir, simulation_dir, analysis_dir)
            
            # 更新元数据（仅分析分支：analysis/<batch>/accuracy/metadata.json 与 analysis/analysis_index.json）
            self.update_metadata_for_analysis(case_dir, [simulation_id], "accuracy", analysis_results, base_dir)
            
            logger.info(f"精度分析完成: {analysis_dir}")
            
            return {
                "success": True,
                "message": "精度分析完成",
                "data": {
                    "analysis_id": analysis_dir.name,
                    "case_id": case_id,
                    "simulation_id": simulation_id,
                    "analysis_type": "accuracy",
                    "output_folder": str(analysis_dir),
                    "chart_files": analysis_results.get("results", {}).get("chart_files", []),
                    "report_file": analysis_results.get("results", {}).get("report_file", ""),
                    "csv_files": analysis_results.get("results", {}).get("csv_files", []),
                    "accuracy_metrics": analysis_results.get("results", {}).get("accuracy_metrics", {}),
                    "data_summary": analysis_results.get("results", {}).get("data_summary", {}),
                    "analysis_metadata": analysis_results.get("analysis_metadata", {})
                }
            }
            
        except Exception as e:
            logger.error(f"精度分析执行失败: {e}")
            return {
                "success": False,
                "message": f"精度分析执行失败: {str(e)}",
                "data": {"error": str(e)}
            }
    
    async def list_analysis_results(self, case_id: str, analysis_type: str = "accuracy") -> Dict[str, Any]:
        """
        获取分析结果列表
        
        Args:
            case_id: 案例ID
            analysis_type: 分析类型 (accuracy/mechanism/performance)
            
        Returns:
            分析结果列表字典
        """
        try:
            logger.info(f"获取分析结果列表: case_id={case_id}, analysis_type={analysis_type}")
            
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
                                            result_info["accuracy_metrics"] = results_data.get("accuracy_metrics", {})
                                            result_info["data_summary"] = results_data.get("data_summary", {})
                                        
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
                                            result_info["accuracy_metrics"] = results_data.get("accuracy_metrics", {})
                                            result_info["data_summary"] = results_data.get("data_summary", {})
                                        
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
                                            result_info["accuracy_metrics"] = results_data.get("accuracy_metrics", {})
                                            result_info["data_summary"] = results_data.get("data_summary", {})
                                        
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
                                            result_info["accuracy_metrics"] = results_data.get("accuracy_metrics", {})
                                            result_info["data_summary"] = results_data.get("data_summary", {})
                                        
                                        results.append(result_info)
                                        
                                    except Exception as e:
                                        logger.warning(f"读取分析元数据失败 {metadata_file}: {e}")
                                        continue
            
            # 按创建时间排序（最新的在前）
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            
            logger.info(f"获取到 {len(results)} 个分析结果")
            
            return {
                "case_id": case_id,
                "analysis_type": analysis_type,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"获取分析结果列表失败: {e}")
            raise
    
    async def get_case_analysis_history(self, case_id: str) -> Dict[str, Any]:
        """
        获取案例的分析历史
        
        Args:
            case_id: 案例ID
            
        Returns:
            分析历史字典
        """
        try:
            logger.info(f"获取案例分析历史: case_id={case_id}")
            
            # 获取所有分析类型的结果
            accuracy_results = await self.list_analysis_results(case_id, "accuracy")
            mechanism_results = await self.list_analysis_results(case_id, "mechanism")
            performance_results = await self.list_analysis_results(case_id, "performance")
            
            return {
                "case_id": case_id,
                "accuracy": accuracy_results,
                "mechanism": mechanism_results,
                "performance": performance_results
            }
            
        except Exception as e:
            logger.error(f"获取案例分析历史失败: {e}")
            raise
    
    async def get_analysis_simulation_mapping(self, case_id: str, analysis_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取分析和仿真的对应关系
        
        Args:
            case_id: 案例ID
            analysis_id: 分析ID（可选）
            
        Returns:
            对应关系字典
        """
        try:
            logger.info(f"获取分析仿真对应关系: case_id={case_id}, analysis_id={analysis_id}")
            
            case_dir = self.cases_dir / case_id
            if not case_dir.exists():
                raise Exception(f"案例不存在: {case_id}")
            
            # 检查分析索引文件
            analysis_index_file = case_dir / "analysis" / "analysis_index.json"
            if not analysis_index_file.exists():
                return {
                    "case_id": case_id,
                    "mappings": []
                }
            
            # 读取分析索引
            with open(analysis_index_file, 'r', encoding='utf-8') as f:
                analysis_index = json.load(f)
            
            mappings = []
            
            # 检查分析索引结构
            if "analyses" in analysis_index:
                # 新的结构：使用analyses数组
                analyses_list = analysis_index["analyses"]
                for analysis_info in analyses_list:
                    batch_id = analysis_info.get("analysis_batch_id", "")
                    if analysis_id and batch_id != analysis_id:
                        continue
                    
                    mapping_info = {
                        "analysis_id": batch_id,
                        "created_at": analysis_info.get("created_at", ""),
                        "simulation_ids": analysis_info.get("simulation_ids", []),
                        "analysis_types": analysis_info.get("analysis_types", {}),
                        "status": analysis_info.get("status", "unknown")
                    }
                    
                    mappings.append(mapping_info)
            else:
                # 旧的结构：直接遍历键值对
                for batch_id, batch_info in analysis_index.items():
                    if analysis_id and batch_id != analysis_id:
                        continue
                    
                    mapping_info = {
                        "analysis_id": batch_id,
                        "created_at": batch_info.get("created_at", ""),
                        "simulation_ids": batch_info.get("simulation_ids", []),
                        "analysis_types": batch_info.get("analysis_types", []),
                        "status": batch_info.get("status", "unknown")
                    }
                    
                    mappings.append(mapping_info)
            
            return {
                "case_id": case_id,
                "mappings": mappings
            }
            
        except Exception as e:
            logger.error(f"获取分析仿真对应关系失败: {e}")
            raise
    
    async def _run_accuracy_analysis(self, case_dir: Path, simulation_dir: Path, analysis_dir: Path) -> Dict[str, Any]:
        """执行精度分析的核心逻辑"""
        # 1. 解析门架数据
        gantry_data = self._resolve_gantry_data(case_dir)
        
        # 2. 解析E1检测器数据
        e1_data = self._resolve_e1_data(simulation_dir)
        
        # 3. 创建精度分析专用目录 - 调用shared层功能
        accuracy_dir = analysis_dir / "accuracy"
        from shared.utilities.file_utils import ensure_directory
        ensure_directory(accuracy_dir)
        
        # 4. 执行数据对齐和导出
        alignment_results = self._run_alignment_and_exports(gantry_data, e1_data, accuracy_dir)
        
        # 5. 执行精度分析（使用shared层分析器）
        analyzer = AccuracyAnalysis()
        charts_dir = accuracy_dir / "charts"
        reports_dir = accuracy_dir
        
        analyzer.set_output_dirs(str(charts_dir), str(reports_dir))
        analysis_results = analyzer.analyze_accuracy(alignment_results['aligned_data'])
        
        # 5. 构建完整的分析结果（用于元数据更新）
        complete_results = {
            "analysis_id": analysis_dir.name,
            "analysis_type": "accuracy",
            "status": "completed",
            "created_at": pd.Timestamp.now().isoformat(),
            "completed_at": pd.Timestamp.now().isoformat(),
            
            # 分析结果
            "results": {
                "chart_files": analysis_results.get("chart_files", []),
                "report_file": analysis_results.get("report_file", ""),
                "csv_files": alignment_results.get("csv_exports", []),
                "accuracy_metrics": analysis_results.get("basic_metrics", {}),
                "data_summary": {
                    "gantry_data": {
                        "total_records": len(gantry_data),
                        "unique_gantries": gantry_data['gantry_id'].nunique() if 'gantry_id' in gantry_data.columns else 0
                    },
                    "e1_data": {
                        "total_records": len(e1_data),
                        "unique_detectors": e1_data['gantry_id'].nunique() if 'gantry_id' in e1_data.columns else 0
                    },
                    "aligned_data": {
                        "total_records": len(alignment_results.get('aligned_data', pd.DataFrame())),
                        "unique_gantries": alignment_results.get('aligned_data', pd.DataFrame())['gantry_id'].nunique() if not alignment_results.get('aligned_data', pd.DataFrame()).empty and 'gantry_id' in alignment_results.get('aligned_data', pd.DataFrame()).columns else 0
                    }
                }
            },
            
            # 分析元数据
            "analysis_metadata": {
                "analysis_tool": "accuracy_analyzer",
                "analysis_version": "1.0.0",
                "analysis_parameters": {
                    "data_alignment": "gantry_id + time_key",
                    "precision_metrics": ["MAE", "MSE", "RMSE", "MAPE", "GEH", "correlation"]
                },
                "analysis_workflow": [
                    "门架数据加载",
                    "E1数据加载", 
                    "数据对齐",
                    "精度指标计算",
                    "图表生成",
                    "报告生成"
                ]
            }
        }
        
        return complete_results
    
    def _resolve_gantry_data(self, case_dir: Path):
        """解析门架数据 - 调用shared层模块"""
        try:
            # 从案例元数据中获取时间范围
            metadata_file = case_dir / "metadata.json"
            if not metadata_file.exists():
                raise Exception("案例元数据文件不存在")
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            time_range = metadata.get("time_range", {})
            start_time = time_range.get("start")
            end_time = time_range.get("end")
            
            if not start_time or not end_time:
                raise Exception("案例元数据中缺少时间范围信息")
            
            # 调用shared层的门架数据管理功能
            from shared.utilities.file_utils import DirectoryManager
            
            # 确保门架数据可用（如果不存在会自动从数据库加载）
            gantry_dir = DirectoryManager.ensure_gantry_data_available(case_dir, start_time, end_time)
            
            # 使用shared层的门架数据处理器加载数据
            from shared.data_processors.gantry_processor import GantryDataProcessor
            
            processor = GantryDataProcessor()
            gantry_data = processor.load_gantry_data(gantry_dir)
            
            if gantry_data.empty:
                raise Exception("门架数据为空")
            
            logger.info(f"成功加载门架数据: {len(gantry_data)} 条记录")
            return gantry_data
            
        except Exception as e:
            logger.error(f"解析门架数据失败: {e}")
            raise
    
    def _resolve_e1_data(self, simulation_dir: Path):
        """解析E1检测器数据"""
        try:
            e1_dir = simulation_dir / "e1"
            if not e1_dir.exists():
                raise Exception("E1检测器数据目录不存在")
            
            processor = E1DataProcessor()
            e1_data = processor.load_e1_data(e1_dir)
            
            if e1_data.empty:
                raise Exception("E1检测器数据为空")
            
            logger.info(f"成功加载E1检测器数据: {len(e1_data)} 条记录")
            return e1_data
            
        except Exception as e:
            logger.error(f"解析E1检测器数据失败: {e}")
            raise
    
    def _run_alignment_and_exports(self, gantry_data, e1_data, analysis_dir: Path) -> Dict[str, Any]:
        """执行数据对齐和导出 - 调用shared层模块"""
        try:
            # 使用shared层的门架数据处理器进行数据对齐
            from shared.data_processors.gantry_processor import GantryDataProcessor
            
            processor = GantryDataProcessor()
            
            # 执行数据对齐
            alignment_results = processor.process_for_accuracy_analysis(gantry_data, e1_data)
            
            # 导出分析用的CSV文件
            csv_exports = processor.export_analysis_csvs(analysis_dir)
            
            # 获取对齐后的数据
            aligned_data = processor.get_aligned_data()
            
            if aligned_data.empty:
                raise Exception("数据对齐失败，无法获取对齐后的数据")
            
            logger.info(f"数据对齐完成: {len(aligned_data)} 条记录")
            
            return {
                "aligned_data": aligned_data,
                "csv_exports": list(csv_exports.values()) if csv_exports else []
            }
            
        except Exception as e:
            logger.error(f"数据对齐和导出失败: {e}")
            raise
