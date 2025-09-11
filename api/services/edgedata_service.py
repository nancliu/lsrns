"""
EdgeData 分析服务
专门处理 EdgeData 分析相关的业务逻辑
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

from .base_metadata_service import BaseMetadataService
from shared.analysis_tools.edgedata_analysis import EdgeDataAnalysis

logger = logging.getLogger(__name__)


class EdgeDataAnalysisService(BaseMetadataService):
    """EdgeData 分析服务类"""
    
    async def analyze_edgedata(self, case_id: str, simulation_ids: List[str]) -> Dict[str, Any]:
        """
        执行 EdgeData 分析
        
        Args:
            case_id: 案例ID
            simulation_ids: 仿真ID列表
            
        Returns:
            分析结果字典
        """
        try:
            logger.info(f"开始EdgeData分析: case_id={case_id}, simulation_ids={simulation_ids}")
            
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
            
            # 验证 EdgeData 文件存在性
            edgedata_available = False
            for sim_dir in simulation_folders:
                # 检查多个可能的路径
                possible_edgedata_paths = [
                    sim_dir / "edgedata" / "edgedata.xml",  # 新路径：edgedata 子目录
                    sim_dir / "edgedata.xml"  # 旧路径：仿真根目录
                ]
                
                for edgedata_path in possible_edgedata_paths:
                    if edgedata_path.exists():
                        edgedata_available = True
                        break
                
                if edgedata_available:
                    break
            
            if not edgedata_available:
                raise Exception("选择的仿真结果中未找到 edgedata.xml 文件，请确保仿真时启用了 EdgeData 输出")
            
            # 准备分析目录
            # 说明：结果分析流程仅维护 analysis 分支元数据（批次与索引），
            # 不创建/不更新 案例级 metadata.json，且不更新仿真分支元数据。
            base_dir, analysis_dir = self.prepare_analysis_dirs(case_root, "edgedata")
            
            # 执行 EdgeData 分析的核心逻辑
            analysis_results = await self._run_edgedata_analysis(
                case_root, simulation_folders, analysis_dir, simulation_ids
            )
            
            # 更新分析元数据
            self.update_metadata_for_analysis(case_root, simulation_ids, "edgedata", analysis_results, base_dir)
            
            logger.info("EdgeData分析完成")
            return analysis_results
            
        except Exception as e:
            logger.error(f"EdgeData分析失败: {e}")
            raise
    
    async def list_analysis_results(self, case_id: str, analysis_type: str = "edgedata") -> Dict[str, Any]:
        """
        列出 EdgeData 分析结果
        
        Args:
            case_id: 案例ID
            analysis_type: 分析类型，默认为 "edgedata"
            
        Returns:
            分析结果列表
        """
        try:
            logger.info(f"获取EdgeData分析结果列表: case_id={case_id}")
            
            case_dir = self.cases_dir / case_id
            if not case_dir.exists():
                raise Exception(f"案例不存在: {case_id}")
            
            analysis_index_file = case_dir / "analysis" / "analysis_index.json"
            if not analysis_index_file.exists():
                return {"analyses": []}
            
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
                                try:
                                    # 读取分析类型元数据
                                    metadata_file = analysis_type_dir / "metadata.json"
                                    if metadata_file.exists():
                                        with open(metadata_file, 'r', encoding='utf-8') as f:
                                            analysis_metadata = json.load(f)
                                        results.append({
                                            "analysis_batch_id": batch_id,
                                            "analysis_type": analysis_type,
                                            "metadata": analysis_metadata,
                                            "analysis_info": analysis_info
                                        })
                                except Exception as e:
                                    logger.warning(f"读取分析元数据失败: {e}")
                                    continue
                    elif isinstance(analysis_types, list):
                        # 如果是数组，检查是否包含指定的分析类型
                        if analysis_type in analysis_types:
                            analysis_type_dir = case_dir / "analysis" / batch_id / analysis_type
                            if analysis_type_dir.exists():
                                try:
                                    metadata_file = analysis_type_dir / "metadata.json"
                                    if metadata_file.exists():
                                        with open(metadata_file, 'r', encoding='utf-8') as f:
                                            analysis_metadata = json.load(f)
                                        results.append({
                                            "analysis_batch_id": batch_id,
                                            "analysis_type": analysis_type,
                                            "metadata": analysis_metadata,
                                            "analysis_info": analysis_info
                                        })
                                except Exception as e:
                                    logger.warning(f"读取分析元数据失败: {e}")
                                    continue
            
            # 按创建时间倒序排列
            results.sort(key=lambda x: x["metadata"].get("created_at", ""), reverse=True)
            
            return {"analyses": results}
            
        except Exception as e:
            logger.error(f"获取EdgeData分析结果列表失败: {e}")
            raise
    
    async def get_analysis_detail(self, case_id: str, analysis_batch_id: str, 
                                analysis_type: str = "edgedata") -> Dict[str, Any]:
        """
        获取 EdgeData 分析详情
        
        Args:
            case_id: 案例ID
            analysis_batch_id: 分析批次ID
            analysis_type: 分析类型，默认为 "edgedata"
            
        Returns:
            分析详情字典
        """
        try:
            logger.info(f"获取EdgeData分析详情: case_id={case_id}, batch_id={analysis_batch_id}")
            
            case_dir = self.cases_dir / case_id
            analysis_dir = case_dir / "analysis" / analysis_batch_id / analysis_type
            
            if not analysis_dir.exists():
                raise Exception(f"分析结果不存在: {analysis_dir}")
            
            # 读取分析元数据
            metadata_file = analysis_dir / "metadata.json"
            if not metadata_file.exists():
                raise Exception(f"分析元数据文件不存在: {metadata_file}")
            
            import json
            with open(metadata_file, 'r', encoding='utf-8') as f:
                analysis_metadata = json.load(f)
            
            # 列出分析结果文件
            chart_files = []
            csv_files = []
            report_files = []
            
            # 扫描图表目录
            charts_dir = analysis_dir / "charts"
            if charts_dir.exists():
                for chart_file in charts_dir.glob("*.png"):
                    chart_files.append(str(chart_file.relative_to(case_dir)))
                for chart_file in charts_dir.glob("*.jpg"):
                    chart_files.append(str(chart_file.relative_to(case_dir)))
            
            # 扫描CSV文件
            for csv_file in analysis_dir.glob("*.csv"):
                csv_files.append(str(csv_file.relative_to(case_dir)))
            
            # 扫描报告文件
            for report_file in analysis_dir.glob("*.md"):
                report_files.append(str(report_file.relative_to(case_dir)))
            for report_file in analysis_dir.glob("*.html"):
                report_files.append(str(report_file.relative_to(case_dir)))
            
            return {
                "analysis_metadata": analysis_metadata,
                "result_files": {
                    "charts": chart_files,
                    "csvs": csv_files,
                    "reports": report_files
                },
                "analysis_directory": str(analysis_dir.relative_to(case_dir))
            }
            
        except Exception as e:
            logger.error(f"获取EdgeData分析详情失败: {e}")
            raise
    
    async def _run_edgedata_analysis(self, case_root: Path, simulation_folders: List[Path], 
                                   analysis_dir: Path, simulation_ids: List[str]) -> Dict[str, Any]:
        """执行 EdgeData 分析的核心逻辑"""
        try:
            # 创建 EdgeData 分析专用目录
            edgedata_dir = analysis_dir / "edgedata"
            from shared.utilities.file_utils import ensure_directory
            ensure_directory(edgedata_dir)
            
            # 执行 EdgeData 分析（使用shared层分析器）
            analyzer = EdgeDataAnalysis()
            charts_dir = edgedata_dir / "charts"
            reports_dir = edgedata_dir
            
            analyzer.set_output_dirs(str(charts_dir), str(reports_dir))
            analysis_results = analyzer.analyze_edgedata(simulation_folders, simulation_ids)
            
            # 构建完整的分析结果（用于元数据更新）
            complete_results = {
                **analysis_results,
                "analysis_id": analysis_dir.parent.name,
                "case_id": case_root.name,
                "simulation_ids": simulation_ids,
                "analysis_directory": str(edgedata_dir.relative_to(case_root)),
                "charts_directory": str(charts_dir.relative_to(case_root)),
                "reports_directory": str(reports_dir.relative_to(case_root))
            }
            
            return complete_results
            
        except Exception as e:
            logger.error(f"EdgeData分析核心逻辑执行失败: {e}")
            raise


# 创建服务实例
edgedata_analysis_service = EdgeDataAnalysisService()


# 导出服务函数 (保持向后兼容)
async def analyze_edgedata_service(case_id: str, simulation_ids: List[str]) -> Dict[str, Any]:
    """EdgeData 分析服务函数"""
    return await edgedata_analysis_service.analyze_edgedata(case_id, simulation_ids)


async def list_edgedata_analysis_results_service(case_id: str) -> Dict[str, Any]:
    """列出 EdgeData 分析结果服务函数"""
    return await edgedata_analysis_service.list_analysis_results(case_id, "edgedata")


async def get_edgedata_analysis_detail_service(case_id: str, analysis_batch_id: str) -> Dict[str, Any]:
    """获取 EdgeData 分析详情服务函数"""
    return await edgedata_analysis_service.get_analysis_detail(case_id, analysis_batch_id, "edgedata")
