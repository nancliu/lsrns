"""
性能分析模块
专门处理仿真性能分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import json
from datetime import datetime
import os

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """性能分析器类"""
    
    def __init__(self):
        self.analysis_results = {}
        self.charts_dir = None
        self.reports_dir = None
        
    def set_output_dirs(self, charts_dir: str, reports_dir: str):
        """设置输出目录"""
        self.charts_dir = Path(charts_dir)
        self.reports_dir = Path(reports_dir)
        
        # 创建目录
        self.charts_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"设置输出目录: 图表={charts_dir}, 报告={reports_dir}")
    
    def analyze_performance(self, case_root: Path, simulation_folders: List[Path], 
                           simulation_ids: List[str]) -> Dict[str, Any]:
        """
        执行性能分析
        
        Args:
            case_root: 案例根目录
            simulation_folders: 仿真文件夹列表
            simulation_ids: 仿真ID列表
            
        Returns:
            性能分析结果字典
        """
        try:
            logger.info("开始性能分析...")
            start_time = datetime.now()
            
            # 1. 分析仿真运行性能
            simulation_performance = self._analyze_simulation_performance(simulation_folders)
            
            # 2. 分析数据处理性能
            data_processing_performance = self._analyze_data_processing_performance(simulation_folders)
            
            # 3. 分析输出结果性能
            output_performance = self._analyze_output_performance(case_root, simulation_folders)
            
            # 4. 计算总体性能指标
            overall_performance = self._calculate_overall_performance(
                simulation_performance, data_processing_performance, output_performance
            )
            
            # 5. 生成性能分析图表
            chart_files = self._generate_performance_charts(
                simulation_performance, data_processing_performance, output_performance
            )
            
            # 6. 生成分析报告
            report_file = self._generate_performance_report(
                simulation_performance, data_processing_performance, 
                output_performance, overall_performance, chart_files
            )
            
            # 7. 导出分析结果CSV
            csv_files = self._export_performance_csvs(
                simulation_performance, data_processing_performance, output_performance
            )
            
            # 计算分析耗时
            analysis_duration = (datetime.now() - start_time).total_seconds()
            
            results = {
                "analysis_type": "performance",
                "simulation_ids": simulation_ids,
                "simulation_performance": simulation_performance,
                "data_processing_performance": data_processing_performance,
                "output_performance": output_performance,
                "overall_performance": overall_performance,
                "chart_files": chart_files,
                "report_file": report_file,
                "csv_files": csv_files,
                "analysis_time": datetime.now().isoformat(),
                "analysis_duration_seconds": analysis_duration
            }
            
            self.analysis_results = results
            logger.info(f"性能分析完成，耗时: {analysis_duration:.2f}秒")
            return results
            
        except Exception as e:
            logger.error(f"性能分析失败: {e}")
            return {}
    
    def _analyze_simulation_performance(self, simulation_folders: List[Path]) -> Dict[str, Any]:
        """分析仿真运行性能"""
        try:
            performance_data = {
                "total_simulations": len(simulation_folders),
                "simulation_details": [],
                "summary_stats": {}
            }
            
            all_summary_data = []
            
            for sim_folder in simulation_folders:
                sim_id = sim_folder.name
                summary_file = sim_folder / "summary.xml"
                
                sim_data = {
                    "simulation_id": sim_id,
                    "folder_path": str(sim_folder),
                    "summary_exists": summary_file.exists()
                }
                
                if summary_file.exists():
                    # 解析summary.xml
                    summary_data = self._parse_summary_xml(summary_file)
                    if not summary_data.empty:
                        summary_data['simulation_id'] = sim_id
                        all_summary_data.append(summary_data)
                        
                        # 添加到仿真详情
                        sim_data.update({
                            "steps": summary_data.get('steps', 0).iloc[0] if 'steps' in summary_data.columns else 0,
                            "loaded_total": summary_data.get('loaded_total', 0).iloc[0] if 'loaded_total' in summary_data.columns else 0,
                            "inserted_total": summary_data.get('inserted_total', 0).iloc[0] if 'inserted_total' in summary_data.columns else 0,
                            "running_max": summary_data.get('running_max', 0).iloc[0] if 'running_max' in summary_data.columns else 0,
                            "waiting_max": summary_data.get('waiting_max', 0).iloc[0] if 'waiting_max' in summary_data.columns else 0,
                            "ended_total": summary_data.get('ended_total', 0).iloc[0] if 'ended_total' in summary_data.columns else 0
                        })
                
                performance_data["simulation_details"].append(sim_data)
            
            # 计算汇总统计
            if all_summary_data:
                combined_summary = pd.concat(all_summary_data, ignore_index=True)
                performance_data["summary_stats"] = {
                    "total_steps": combined_summary.get('steps', pd.Series([0])).sum(),
                    "total_loaded": combined_summary.get('loaded_total', pd.Series([0])).sum(),
                    "total_inserted": combined_summary.get('inserted_total', pd.Series([0])).sum(),
                    "max_running": combined_summary.get('running_max', pd.Series([0])).max(),
                    "max_waiting": combined_summary.get('waiting_max', pd.Series([0])).max(),
                    "total_ended": combined_summary.get('ended_total', pd.Series([0])).sum()
                }
            
            return performance_data
            
        except Exception as e:
            logger.error(f"仿真性能分析失败: {e}")
            return {}
    
    def _analyze_data_processing_performance(self, simulation_folders: List[Path]) -> Dict[str, Any]:
        """分析数据处理性能"""
        try:
            processing_data = {
                "total_e1_files": 0,
                "total_e1_records": 0,
                "e1_file_sizes": [],
                "simulation_data_details": []
            }
            
            for sim_folder in simulation_folders:
                sim_id = sim_folder.name
                e1_dir = sim_folder / "e1"
                
                sim_data_detail = {
                    "simulation_id": sim_id,
                    "e1_files_count": 0,
                    "e1_records_count": 0,
                    "e1_total_size_bytes": 0
                }
                
                if e1_dir.exists():
                    # 统计E1文件
                    e1_files = list(e1_dir.glob("*.xml"))
                    sim_data_detail["e1_files_count"] = len(e1_files)
                    processing_data["total_e1_files"] += len(e1_files)
                    
                    # 统计文件大小和记录数
                    for e1_file in e1_files:
                        file_size = e1_file.stat().st_size
                        sim_data_detail["e1_total_size_bytes"] += file_size
                        processing_data["e1_file_sizes"].append(file_size)
                        
                        # 尝试统计记录数（简化实现）
                        try:
                            with open(e1_file, 'r', encoding='utf-8') as f:
                                content = f.read()
                                # 简单统计<interval>标签数量作为记录数
                                record_count = content.count('<interval')
                                sim_data_detail["e1_records_count"] += record_count
                                processing_data["total_e1_records"] += record_count
                        except Exception:
                            pass
                
                processing_data["simulation_data_details"].append(sim_data_detail)
            
            # 计算文件大小统计
            if processing_data["e1_file_sizes"]:
                processing_data["e1_size_stats"] = {
                    "total_size_bytes": sum(processing_data["e1_file_sizes"]),
                    "average_size_bytes": np.mean(processing_data["e1_file_sizes"]),
                    "min_size_bytes": min(processing_data["e1_file_sizes"]),
                    "max_size_bytes": max(processing_data["e1_file_sizes"])
                }
            
            return processing_data
            
        except Exception as e:
            logger.error(f"数据处理性能分析失败: {e}")
            return {}
    
    def _analyze_output_performance(self, case_root: Path, simulation_folders: List[Path]) -> Dict[str, Any]:
        """分析输出结果性能"""
        try:
            output_data = {
                "analysis_outputs": [],
                "total_charts": 0,
                "total_csv_files": 0,
                "total_output_size_bytes": 0
            }
            
            # 检查分析输出目录
            analysis_dir = case_root / "analysis"
            if analysis_dir.exists():
                for analysis_folder in analysis_dir.iterdir():
                    if analysis_folder.is_dir() and analysis_folder.name.startswith("ana_"):
                        analysis_output = {
                            "analysis_id": analysis_folder.name,
                            "charts_count": 0,
                            "csv_count": 0,
                            "total_size_bytes": 0
                        }
                        
                        # 统计图表文件
                        charts_dir = analysis_folder / "charts"
                        if charts_dir.exists():
                            chart_files = list(charts_dir.glob("*.png")) + list(charts_dir.glob("*.jpg"))
                            analysis_output["charts_count"] = len(chart_files)
                            output_data["total_charts"] += len(chart_files)
                            
                            for chart_file in chart_files:
                                analysis_output["total_size_bytes"] += chart_file.stat().st_size
                                output_data["total_output_size_bytes"] += chart_file.stat().st_size
                        
                        # 统计CSV文件
                        csv_files = list(analysis_folder.glob("*.csv"))
                        analysis_output["csv_count"] = len(csv_files)
                        output_data["total_csv_files"] += len(csv_files)
                        
                        for csv_file in csv_files:
                            analysis_output["total_size_bytes"] += csv_file.stat().st_size
                            output_data["total_output_size_bytes"] += csv_file.stat().st_size
                        
                        # 统计报告文件
                        report_files = list(analysis_folder.glob("*.html")) + list(analysis_folder.glob("*.md"))
                        for report_file in report_files:
                            analysis_output["total_size_bytes"] += report_file.stat().st_size
                            output_data["total_output_size_bytes"] += report_file.stat().st_size
                        
                        output_data["analysis_outputs"].append(analysis_output)
            
            return output_data
            
        except Exception as e:
            logger.error(f"输出结果性能分析失败: {e}")
            return {}
    
    def _calculate_overall_performance(self, simulation_perf: Dict, data_perf: Dict, output_perf: Dict) -> Dict[str, Any]:
        """计算总体性能指标"""
        try:
            overall = {
                "efficiency_score": 0.0,
                "data_processing_efficiency": 0.0,
                "output_efficiency": 0.0,
                "performance_summary": {}
            }
            
            # 计算数据处理效率（基于文件数量和记录数）
            if data_perf.get("total_e1_files", 0) > 0:
                records_per_file = data_perf.get("total_e1_records", 0) / data_perf.get("total_e1_files", 1)
                overall["data_processing_efficiency"] = min(records_per_file / 100, 1.0)  # 标准化到0-1
            
            # 计算输出效率（基于图表和CSV数量）
            total_outputs = output_perf.get("total_charts", 0) + output_perf.get("total_csv_files", 0)
            if total_outputs > 0:
                overall["output_efficiency"] = min(total_outputs / 20, 1.0)  # 标准化到0-1
            
            # 综合效率评分
            overall["efficiency_score"] = (overall["data_processing_efficiency"] + overall["output_efficiency"]) / 2
            
            # 性能摘要
            overall["performance_summary"] = {
                "total_simulations": simulation_perf.get("total_simulations", 0),
                "total_data_files": data_perf.get("total_e1_files", 0),
                "total_data_records": data_perf.get("total_e1_records", 0),
                "total_outputs": total_outputs,
                "efficiency_level": self._get_efficiency_level(overall["efficiency_score"])
            }
            
            return overall
            
        except Exception as e:
            logger.error(f"总体性能计算失败: {e}")
            return {}
    
    def _get_efficiency_level(self, score: float) -> str:
        """获取效率等级"""
        if score >= 0.8:
            return "优秀"
        elif score >= 0.6:
            return "良好"
        elif score >= 0.4:
            return "一般"
        else:
            return "待改进"
    
    def _parse_summary_xml(self, summary_file: Path) -> pd.DataFrame:
        """解析summary.xml文件"""
        try:
            import xml.etree.ElementTree as ET
            
            tree = ET.parse(summary_file)
            root = tree.getroot()
            
            data = {}
            
            # 提取基础统计信息
            for child in root:
                if child.tag in ['step', 'vehicle', 'person', 'edge', 'lane']:
                    for item in child:
                        if item.tag in ['loaded', 'inserted', 'running', 'waiting', 'ended']:
                            data[item.tag] = int(item.text) if item.text else 0
                        elif item.tag == 'time':
                            data['steps'] = int(item.text) if item.text else 0
            
            return pd.DataFrame([data])
            
        except Exception as e:
            logger.error(f"解析summary.xml失败: {e}")
            return pd.DataFrame()
    
    def _generate_performance_charts(self, simulation_perf: Dict, data_perf: Dict, output_perf: Dict) -> List[str]:
        """生成性能分析图表"""
        try:
            chart_files = []
            
            # 1. 仿真性能对比图
            if simulation_perf.get("simulation_details"):
                self._create_simulation_comparison_chart(simulation_perf)
                chart_files.append("simulation_performance_comparison.png")
            
            # 2. 数据处理性能图
            if data_perf.get("e1_file_sizes"):
                self._create_data_processing_chart(data_perf)
                chart_files.append("data_processing_performance.png")
            
            # 3. 输出结果统计图
            if output_perf.get("analysis_outputs"):
                self._create_output_performance_chart(output_perf)
                chart_files.append("output_performance.png")
            
            return chart_files
            
        except Exception as e:
            logger.error(f"生成性能图表失败: {e}")
            return []
    
    def _create_simulation_comparison_chart(self, simulation_perf: Dict):
        """创建仿真性能对比图"""
        try:
            details = simulation_perf["simulation_details"]
            if not details:
                return
            
            # 提取数据
            sim_ids = [d["simulation_id"] for d in details]
            loaded_counts = [d.get("loaded_total", 0) for d in details]
            ended_counts = [d.get("ended_total", 0) for d in details]
            
            # 创建图表
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # 车辆数量对比
            x = np.arange(len(sim_ids))
            width = 0.35
            
            ax1.bar(x - width/2, loaded_counts, width, label='加载车辆', alpha=0.8)
            ax1.bar(x + width/2, ended_counts, width, label='结束车辆', alpha=0.8)
            ax1.set_xlabel('仿真ID')
            ax1.set_ylabel('车辆数量')
            ax1.set_title('仿真车辆数量对比')
            ax1.set_xticks(x)
            ax1.set_xticklabels(sim_ids, rotation=45)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 效率对比
            efficiency = [ended/loaded if loaded > 0 else 0 for loaded, ended in zip(loaded_counts, ended_counts)]
            ax2.bar(sim_ids, efficiency, alpha=0.8, color='green')
            ax2.set_xlabel('仿真ID')
            ax2.set_ylabel('完成率')
            ax2.set_title('仿真完成效率')
            ax2.set_xticklabels(sim_ids, rotation=45)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            chart_path = self.charts_dir / "simulation_performance_comparison.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"仿真性能对比图已保存: {chart_path}")
            
        except Exception as e:
            logger.error(f"创建仿真性能对比图失败: {e}")
    
    def _create_data_processing_chart(self, data_perf: Dict):
        """创建数据处理性能图"""
        try:
            if not data_perf.get("e1_file_sizes"):
                return
            
            file_sizes = data_perf["e1_file_sizes"]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # 文件大小分布
            ax1.hist(file_sizes, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
            ax1.set_xlabel('文件大小 (字节)')
            ax1.set_ylabel('文件数量')
            ax1.set_title('E1文件大小分布')
            ax1.grid(True, alpha=0.3)
            
            # 文件大小统计
            size_stats = data_perf.get("e1_size_stats", {})
            if size_stats:
                categories = ['总大小', '平均大小', '最大大小']
                values = [
                    size_stats.get("total_size_bytes", 0) / 1024,  # KB
                    size_stats.get("average_size_bytes", 0) / 1024,  # KB
                    size_stats.get("max_size_bytes", 0) / 1024  # KB
                ]
                
                ax2.bar(categories, values, alpha=0.8, color='lightcoral')
                ax2.set_ylabel('大小 (KB)')
                ax2.set_title('E1文件大小统计')
                ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            chart_path = self.charts_dir / "data_processing_performance.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"数据处理性能图已保存: {chart_path}")
            
        except Exception as e:
            logger.error(f"创建数据处理性能图失败: {e}")
    
    def _create_output_performance_chart(self, output_perf: Dict):
        """创建输出结果性能图"""
        try:
            outputs = output_perf.get("analysis_outputs", [])
            if not outputs:
                return
            
            # 提取数据
            analysis_ids = [o["analysis_id"] for o in outputs]
            chart_counts = [o["charts_count"] for o in outputs]
            csv_counts = [o["csv_count"] for o in outputs]
            total_sizes = [o["total_size_bytes"] / 1024 for o in outputs]  # KB
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # 输出数量对比
            x = np.arange(len(analysis_ids))
            width = 0.35
            
            ax1.bar(x - width/2, chart_counts, width, label='图表数量', alpha=0.8)
            ax1.bar(x + width/2, csv_counts, width, label='CSV数量', alpha=0.8)
            ax1.set_xlabel('分析ID')
            ax1.set_ylabel('文件数量')
            ax1.set_title('分析输出文件数量')
            ax1.set_xticks(x)
            ax1.set_xticklabels(analysis_ids, rotation=45)
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 输出大小
            ax2.bar(analysis_ids, total_sizes, alpha=0.8, color='lightgreen')
            ax2.set_xlabel('分析ID')
            ax2.set_ylabel('总大小 (KB)')
            ax2.set_title('分析输出总大小')
            ax2.set_xticklabels(analysis_ids, rotation=45)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            chart_path = self.charts_dir / "output_performance.png"
            plt.savefig(chart_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"输出结果性能图已保存: {chart_path}")
            
        except Exception as e:
            logger.error(f"创建输出结果性能图失败: {e}")
    
    def _generate_performance_report(self, simulation_perf: Dict, data_perf: Dict, 
                                   output_perf: Dict, overall_perf: Dict, chart_files: List[str]) -> str:
        """生成性能分析报告"""
        try:
            report_content = f"""
# 性能分析报告

## 报告概览
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **分析类型**: 性能分析
- **仿真数量**: {simulation_perf.get('total_simulations', 0)}
- **总体效率评分**: {overall_perf.get('efficiency_score', 0):.2f} ({overall_perf.get('performance_summary', {}).get('efficiency_level', 'N/A')})

## 仿真运行性能

### 仿真统计摘要
- **总仿真步数**: {overall_perf.get('performance_summary', {}).get('total_steps', 'N/A')}
- **总加载车辆**: {overall_perf.get('performance_summary', {}).get('total_loaded', 'N/A')}
- **总插入车辆**: {overall_perf.get('performance_summary', {}).get('total_inserted', 'N/A')}
- **最大运行车辆**: {overall_perf.get('performance_summary', {}).get('max_running', 'N/A')}
- **最大等待车辆**: {overall_perf.get('performance_summary', {}).get('max_waiting', 'N/A')}
- **总结束车辆**: {overall_perf.get('performance_summary', {}).get('total_ended', 'N/A')}

### 仿真详情
"""
            
            # 添加仿真详情
            for sim_detail in simulation_perf.get("simulation_details", []):
                report_content += f"""
**仿真 {sim_detail.get('simulation_id', 'N/A')}**:
- 仿真步数: {sim_detail.get('steps', 'N/A')}
- 加载车辆: {sim_detail.get('loaded_total', 'N/A')}
- 插入车辆: {sim_detail.get('inserted_total', 'N/A')}
- 最大运行: {sim_detail.get('running_max', 'N/A')}
- 最大等待: {sim_detail.get('waiting_max', 'N/A')}
- 结束车辆: {sim_detail.get('ended_total', 'N/A')}
"""
            
            report_content += f"""
## 数据处理性能

### 数据统计
- **E1文件总数**: {data_perf.get('total_e1_files', 0)}
- **有效记录总数**: {data_perf.get('total_e1_records', 0)}
- **数据处理效率**: {overall_perf.get('data_processing_efficiency', 0):.2f}

### 文件大小统计
"""
            
            if data_perf.get("e1_size_stats"):
                size_stats = data_perf["e1_size_stats"]
                report_content += f"""
- **总大小**: {size_stats.get('total_size_bytes', 0) / 1024 / 1024:.2f} MB
- **平均大小**: {size_stats.get('average_size_bytes', 0) / 1024:.2f} KB
- **最小大小**: {size_stats.get('min_size_bytes', 0) / 1024:.2f} KB
- **最大大小**: {size_stats.get('max_size_bytes', 0) / 1024:.2f} KB
"""
            
            report_content += f"""
## 输出结果性能

### 输出统计
- **图表总数**: {output_perf.get('total_charts', 0)}
- **CSV文件总数**: {output_perf.get('total_csv_files', 0)}
- **输出总大小**: {output_perf.get('total_output_size_bytes', 0) / 1024 / 1024:.2f} MB
- **输出效率**: {overall_perf.get('output_efficiency', 0):.2f}

## 性能图表

### 已生成图表
"""
            
            for chart_file in chart_files:
                report_content += f"- {chart_file}\n"
            
            report_content += f"""
## 性能优化建议

### 当前状态评估
- **效率等级**: {overall_perf.get('performance_summary', {}).get('efficiency_level', 'N/A')}
- **综合评分**: {overall_perf.get('efficiency_score', 0):.2f}/1.0

### 改进建议
"""
            
            efficiency_score = overall_perf.get('efficiency_score', 0)
            if efficiency_score < 0.4:
                report_content += """
- 数据文件处理效率较低，建议优化E1数据解析
- 输出文件生成效率待提升，建议批量处理
- 仿真运行效率需要进一步优化
"""
            elif efficiency_score < 0.6:
                report_content += """
- 数据处理效率一般，建议优化文件读取方式
- 输出生成效率有提升空间，建议并行处理
"""
            else:
                report_content += """
- 系统运行效率良好，继续保持
- 可考虑进一步优化细节处理流程
"""
            
            report_content += f"""
---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
            
            # 保存报告
            report_path = self.reports_dir / "performance_analysis_report.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            logger.info(f"性能分析报告已保存: {report_path}")
            return str(report_path)
            
        except Exception as e:
            logger.error(f"生成性能分析报告失败: {e}")
            return ""
    
    def _export_performance_csvs(self, simulation_perf: Dict, data_perf: Dict, output_perf: Dict) -> Dict[str, str]:
        """导出性能分析结果CSV"""
        try:
            csv_files = {}
            
            # 1. 仿真性能数据
            if simulation_perf.get("simulation_details"):
                sim_df = pd.DataFrame(simulation_perf["simulation_details"])
                sim_csv_path = self.reports_dir / "simulation_performance.csv"
                sim_df.to_csv(sim_csv_path, index=False, encoding='utf-8')
                csv_files["simulation_performance"] = str(sim_csv_path)
            
            # 2. 数据处理性能数据
            if data_perf.get("simulation_data_details"):
                data_df = pd.DataFrame(data_perf["simulation_data_details"])
                data_csv_path = self.reports_dir / "data_processing_performance.csv"
                data_df.to_csv(data_csv_path, index=False, encoding='utf-8')
                csv_files["data_processing_performance"] = str(data_csv_path)
            
            # 3. 输出结果性能数据
            if output_perf.get("analysis_outputs"):
                output_df = pd.DataFrame(output_perf["analysis_outputs"])
                output_csv_path = self.reports_dir / "output_performance.csv"
                output_df.to_csv(output_csv_path, index=False, encoding='utf-8')
                csv_files["output_performance"] = str(output_csv_path)
            
            logger.info(f"性能分析CSV文件已导出: {len(csv_files)} 个文件")
            return csv_files
            
        except Exception as e:
            logger.error(f"导出性能分析CSV失败: {e}")
            return {}
