"""
EdgeData 分析模块
专门处理 SUMO edgeData 输出结果的分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import logging
import json
import xml.etree.ElementTree as ET
from datetime import datetime

logger = logging.getLogger(__name__)


class EdgeDataAnalysis:
    """EdgeData 分析器类"""
    
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
        
        logger.info(f"EdgeData分析输出目录设置完成 - 图表={charts_dir}, 报告={reports_dir}")
    
    def analyze_edgedata(self, simulation_folders: List[Path], 
                        simulation_ids: List[str]) -> Dict[str, Any]:
        """
        执行 EdgeData 分析
        
        Args:
            simulation_folders: 仿真目录列表
            simulation_ids: 仿真ID列表
            
        Returns:
            分析结果字典
        """
        try:
            logger.info(f"开始EdgeData分析，仿真数量: {len(simulation_folders)}")
            start_time = datetime.now()
            
            # 1. 解析 EdgeData 数据
            edgedata_summary = self._parse_edgedata_files(simulation_folders, simulation_ids)
            
            # 2. 执行流量分析
            flow_analysis = self._analyze_traffic_flow(edgedata_summary)
            
            # 3. 执行速度分析
            speed_analysis = self._analyze_traffic_speed(edgedata_summary)
            
            # 4. 执行密度分析
            density_analysis = self._analyze_traffic_density(edgedata_summary)
            
            # 5. 执行时间序列分析
            temporal_analysis = self._analyze_temporal_patterns(edgedata_summary)
            
            # 6. 生成分析图表
            chart_files = self._generate_edgedata_charts(
                edgedata_summary, flow_analysis, speed_analysis, 
                density_analysis, temporal_analysis
            )
            
            # 7. 生成分析报告
            report_file = self._generate_edgedata_report(
                flow_analysis, speed_analysis, density_analysis, 
                temporal_analysis, chart_files
            )
            
            # 8. 导出分析结果CSV
            csv_files = self._export_analysis_csvs(edgedata_summary, flow_analysis, speed_analysis, density_analysis, temporal_analysis)
            
            # 计算分析耗时
            analysis_duration = (datetime.now() - start_time).total_seconds()
            
            results = {
                "analysis_type": "edgedata",
                "simulation_ids": simulation_ids,
                "edgedata_summary": edgedata_summary,
                "flow_analysis": flow_analysis,
                "speed_analysis": speed_analysis,
                "density_analysis": density_analysis,
                "temporal_analysis": temporal_analysis,
                "chart_files": chart_files,
                "report_file": report_file,
                "csv_files": csv_files,
                "analysis_time": datetime.now().isoformat(),
                "analysis_duration_seconds": analysis_duration
            }
            
            self.analysis_results = results
            logger.info(f"EdgeData分析完成，耗时: {analysis_duration:.2f}秒")
            return results
            
        except Exception as e:
            logger.error(f"EdgeData分析失败: {e}")
            return {}
    
    def _parse_edgedata_files(self, simulation_folders: List[Path], 
                             simulation_ids: List[str]) -> Dict[str, Any]:
        """解析 EdgeData XML 文件"""
        try:
            all_edgedata = []
            file_summary = {}
            
            for i, sim_folder in enumerate(simulation_folders):
                sim_id = simulation_ids[i]
                
                # 查找 edgedata.xml 文件，优先查找 edgedata 子目录
                edgedata_file = None
                possible_paths = [
                    sim_folder / "edgedata" / "edgedata.xml",  # 新路径：edgedata 子目录
                    sim_folder / "edgedata.xml"  # 旧路径：仿真根目录
                ]
                
                for path in possible_paths:
                    if path.exists():
                        edgedata_file = path
                        break
                
                if not edgedata_file:
                    logger.warning(f"EdgeData文件不存在，已尝试路径: {[str(p) for p in possible_paths]}")
                    continue
                
                # 解析 XML 文件
                try:
                    tree = ET.parse(edgedata_file)
                    root = tree.getroot()
                    
                    simulation_data = []
                    
                    for interval in root.findall("interval"):
                        begin_time = float(interval.get("begin", 0))
                        end_time = float(interval.get("end", 0))
                        
                        for edge in interval.findall("edge"):
                            edge_data = {
                                "simulation_id": sim_id,
                                "edge_id": edge.get("id"),
                                "begin_time": begin_time,
                                "end_time": end_time,
                                "interval_duration": end_time - begin_time,
                                "entered": int(edge.get("entered", 0)),
                                "left": int(edge.get("left", 0)),
                                "speed": float(edge.get("speed", 0)),
                                "traveltime": float(edge.get("traveltime", 0)),
                                "density": float(edge.get("density", 0)),
                                "occupancy": float(edge.get("occupancy", 0)),
                                "waitingTime": float(edge.get("waitingTime", 0))
                            }
                            simulation_data.append(edge_data)
                    
                    all_edgedata.extend(simulation_data)
                    file_summary[sim_id] = {
                        "file_path": str(edgedata_file),
                        "records_count": len(simulation_data),
                        "edge_count": len(set(row["edge_id"] for row in simulation_data)),
                        "time_intervals": len(set(row["begin_time"] for row in simulation_data))
                    }
                    
                    logger.info(f"解析EdgeData完成: {sim_id}, 记录数: {len(simulation_data)}")
                    
                except ET.ParseError as e:
                    logger.error(f"EdgeData XML解析失败: {edgedata_file}, 错误: {e}")
                    continue
            
            # 转换为 DataFrame
            if all_edgedata:
                df = pd.DataFrame(all_edgedata)
                
                # 计算派生指标
                df["flow_rate"] = df["entered"] / (df["interval_duration"] / 3600)  # 车辆/小时
                df["congestion_index"] = df["waitingTime"] / df["interval_duration"]  # 拥堵指数
                
                return {
                    "data": df,
                    "file_summary": file_summary,
                    "total_records": len(df),
                    "edge_count": df["edge_id"].nunique(),
                    "simulation_count": len(simulation_ids),
                    "time_range": {
                        "min_time": df["begin_time"].min(),
                        "max_time": df["end_time"].max()
                    }
                }
            else:
                return {
                    "data": pd.DataFrame(),
                    "file_summary": file_summary,
                    "total_records": 0,
                    "edge_count": 0,
                    "simulation_count": len(simulation_ids),
                    "time_range": {}
                }
                
        except Exception as e:
            logger.error(f"EdgeData文件解析失败: {e}")
            return {"data": pd.DataFrame(), "file_summary": {}}
    
    def _analyze_traffic_flow(self, edgedata_summary: Dict[str, Any]) -> Dict[str, Any]:
        """分析交通流量"""
        try:
            df = edgedata_summary.get("data")
            if df.empty:
                return {}
            
            flow_stats = {
                "overall_stats": {
                    "total_vehicles_entered": df["entered"].sum(),
                    "total_vehicles_left": df["left"].sum(),
                    "avg_flow_rate": df["flow_rate"].mean(),
                    "max_flow_rate": df["flow_rate"].max(),
                    "min_flow_rate": df["flow_rate"].min(),
                    "std_flow_rate": df["flow_rate"].std()
                },
                "edge_level_stats": df.groupby("edge_id").agg({
                    "entered": ["sum", "mean", "max"],
                    "left": ["sum", "mean", "max"],
                    "flow_rate": ["mean", "max", "std"]
                }).round(2).to_dict(),
                "time_level_stats": df.groupby("begin_time").agg({
                    "entered": "sum",
                    "left": "sum",
                    "flow_rate": "mean"
                }).round(2).to_dict()
            }
            
            # 识别高流量路段
            edge_flow_summary = df.groupby("edge_id")["flow_rate"].mean().sort_values(ascending=False)
            flow_stats["top_flow_edges"] = edge_flow_summary.head(10).to_dict()
            
            return flow_stats
            
        except Exception as e:
            logger.error(f"交通流量分析失败: {e}")
            return {}
    
    def _analyze_traffic_speed(self, edgedata_summary: Dict[str, Any]) -> Dict[str, Any]:
        """分析交通速度"""
        try:
            df = edgedata_summary.get("data")
            if df.empty:
                return {}
            
            speed_stats = {
                "overall_stats": {
                    "avg_speed": df["speed"].mean(),
                    "max_speed": df["speed"].max(),
                    "min_speed": df["speed"].min(),
                    "std_speed": df["speed"].std(),
                    "median_speed": df["speed"].median()
                },
                "edge_level_stats": df.groupby("edge_id").agg({
                    "speed": ["mean", "max", "min", "std"],
                    "traveltime": ["mean", "max", "min"]
                }).round(2).to_dict(),
                "time_level_stats": df.groupby("begin_time").agg({
                    "speed": ["mean", "std"],
                    "traveltime": "mean"
                }).round(2).to_dict()
            }
            
            # 识别低速路段（可能的拥堵路段）
            edge_speed_summary = df.groupby("edge_id")["speed"].mean().sort_values()
            speed_stats["low_speed_edges"] = edge_speed_summary.head(10).to_dict()
            
            return speed_stats
            
        except Exception as e:
            logger.error(f"交通速度分析失败: {e}")
            return {}
    
    def _analyze_traffic_density(self, edgedata_summary: Dict[str, Any]) -> Dict[str, Any]:
        """分析交通密度"""
        try:
            df = edgedata_summary.get("data")
            if df.empty:
                return {}
            
            density_stats = {
                "overall_stats": {
                    "avg_density": df["density"].mean(),
                    "max_density": df["density"].max(),
                    "min_density": df["density"].min(),
                    "std_density": df["density"].std(),
                    "avg_occupancy": df["occupancy"].mean(),
                    "max_occupancy": df["occupancy"].max()
                },
                "edge_level_stats": df.groupby("edge_id").agg({
                    "density": ["mean", "max", "std"],
                    "occupancy": ["mean", "max", "std"]
                }).round(2).to_dict(),
                "congestion_analysis": {
                    "avg_congestion_index": df["congestion_index"].mean(),
                    "max_congestion_index": df["congestion_index"].max(),
                    "high_congestion_threshold": df["congestion_index"].quantile(0.8)
                }
            }
            
            # 识别高密度路段
            edge_density_summary = df.groupby("edge_id")["density"].mean().sort_values(ascending=False)
            density_stats["high_density_edges"] = edge_density_summary.head(10).to_dict()
            
            return density_stats
            
        except Exception as e:
            logger.error(f"交通密度分析失败: {e}")
            return {}
    
    def _analyze_temporal_patterns(self, edgedata_summary: Dict[str, Any]) -> Dict[str, Any]:
        """分析时间模式"""
        try:
            df = edgedata_summary.get("data")
            if df.empty:
                return {}
            
            # 按时间间隔分析
            temporal_stats = df.groupby("begin_time").agg({
                "entered": "sum",
                "speed": "mean",
                "density": "mean",
                "flow_rate": "mean",
                "congestion_index": "mean"
            }).round(2)
            
            # 识别峰值时段
            peak_flow_time = temporal_stats["flow_rate"].idxmax()
            peak_congestion_time = temporal_stats["congestion_index"].idxmax()
            
            return {
                "temporal_stats": temporal_stats.to_dict(),
                "peak_analysis": {
                    "peak_flow_time": peak_flow_time,
                    "peak_flow_value": temporal_stats.loc[peak_flow_time, "flow_rate"],
                    "peak_congestion_time": peak_congestion_time,
                    "peak_congestion_value": temporal_stats.loc[peak_congestion_time, "congestion_index"]
                },
                "time_series_summary": {
                    "total_time_intervals": len(temporal_stats),
                    "time_resolution": df["interval_duration"].iloc[0] if len(df) > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"时间模式分析失败: {e}")
            return {}
    
    def _generate_edgedata_charts(self, edgedata_summary: Dict[str, Any],
                                 flow_analysis: Dict[str, Any],
                                 speed_analysis: Dict[str, Any],
                                 density_analysis: Dict[str, Any],
                                 temporal_analysis: Dict[str, Any]) -> List[str]:
        """生成 EdgeData 分析图表"""
        try:
            df = edgedata_summary.get("data")
            if df.empty:
                return []
            
            chart_files = []
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 1. 流量时间序列图
            if "temporal_stats" in temporal_analysis:
                fig, ax = plt.subplots(figsize=(12, 6))
                temporal_data = pd.DataFrame(temporal_analysis["temporal_stats"])
                ax.plot(temporal_data.index, temporal_data["flow_rate"], 
                       marker='o', linewidth=2, markersize=4)
                ax.set_xlabel("时间 (秒)")
                ax.set_ylabel("平均流量 (车辆/小时)")
                ax.set_title("交通流量时间序列")
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                
                chart_file = self.charts_dir / "flow_time_series.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
            
            # 2. 速度分布直方图
            if not df["speed"].empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.hist(df["speed"], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
                ax.set_xlabel("速度 (m/s)")
                ax.set_ylabel("频次")
                ax.set_title("速度分布直方图")
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                
                chart_file = self.charts_dir / "speed_distribution.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
            
            # 3. 密度-速度散点图
            if not df[["density", "speed"]].empty:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.scatter(df["density"], df["speed"], alpha=0.5, s=20)
                ax.set_xlabel("密度 (车辆/km)")
                ax.set_ylabel("速度 (m/s)")
                ax.set_title("密度-速度关系")
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                
                chart_file = self.charts_dir / "density_speed_scatter.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
            
            # 4. 拥堵指数热力图
            if "temporal_stats" in temporal_analysis and not df["congestion_index"].empty:
                fig, ax = plt.subplots(figsize=(12, 6))
                temporal_data = pd.DataFrame(temporal_analysis["temporal_stats"])
                ax.plot(temporal_data.index, temporal_data["congestion_index"], 
                       color='red', linewidth=2, marker='s', markersize=4)
                ax.set_xlabel("时间 (秒)")
                ax.set_ylabel("拥堵指数")
                ax.set_title("拥堵指数时间变化")
                ax.grid(True, alpha=0.3)
                plt.tight_layout()
                
                chart_file = self.charts_dir / "congestion_index_time.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(str(chart_file))
                
            logger.info(f"EdgeData图表生成完成，共生成 {len(chart_files)} 个图表")
            return chart_files
            
        except Exception as e:
            logger.error(f"EdgeData图表生成失败: {e}")
            return []
    
    def _generate_edgedata_report(self, flow_analysis: Dict[str, Any],
                                 speed_analysis: Dict[str, Any],
                                 density_analysis: Dict[str, Any],
                                 temporal_analysis: Dict[str, Any],
                                 chart_files: List[str]) -> str:
        """生成 EdgeData 分析报告"""
        try:
            report_content = []
            report_content.append("# EdgeData 交通流分析报告")
            report_content.append(f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report_content.append("\n" + "="*50)
            
            # 1. 流量分析部分
            if flow_analysis and "overall_stats" in flow_analysis:
                report_content.append("\n## 1. 交通流量分析")
                stats = flow_analysis["overall_stats"]
                report_content.append(f"\n### 总体统计")
                report_content.append(f"- 总进入车辆数: {stats.get('total_vehicles_entered', 0):,}")
                report_content.append(f"- 总离开车辆数: {stats.get('total_vehicles_left', 0):,}")
                report_content.append(f"- 平均流量: {stats.get('avg_flow_rate', 0):.2f} 车辆/小时")
                report_content.append(f"- 最大流量: {stats.get('max_flow_rate', 0):.2f} 车辆/小时")
                
                if "top_flow_edges" in flow_analysis:
                    report_content.append(f"\n### 高流量路段 (Top 5)")
                    for i, (edge_id, flow) in enumerate(list(flow_analysis["top_flow_edges"].items())[:5], 1):
                        report_content.append(f"{i}. 路段 {edge_id}: {flow:.2f} 车辆/小时")
            
            # 2. 速度分析部分
            if speed_analysis and "overall_stats" in speed_analysis:
                report_content.append("\n## 2. 交通速度分析")
                stats = speed_analysis["overall_stats"]
                report_content.append(f"\n### 总体统计")
                report_content.append(f"- 平均速度: {stats.get('avg_speed', 0):.2f} m/s")
                report_content.append(f"- 最大速度: {stats.get('max_speed', 0):.2f} m/s")
                report_content.append(f"- 最小速度: {stats.get('min_speed', 0):.2f} m/s")
                report_content.append(f"- 速度标准差: {stats.get('std_speed', 0):.2f} m/s")
                
                if "low_speed_edges" in speed_analysis:
                    report_content.append(f"\n### 低速路段 (Top 5)")
                    for i, (edge_id, speed) in enumerate(list(speed_analysis["low_speed_edges"].items())[:5], 1):
                        report_content.append(f"{i}. 路段 {edge_id}: {speed:.2f} m/s")
            
            # 3. 密度分析部分
            if density_analysis and "overall_stats" in density_analysis:
                report_content.append("\n## 3. 交通密度分析")
                stats = density_analysis["overall_stats"]
                report_content.append(f"\n### 总体统计")
                report_content.append(f"- 平均密度: {stats.get('avg_density', 0):.2f} 车辆/km")
                report_content.append(f"- 最大密度: {stats.get('max_density', 0):.2f} 车辆/km")
                report_content.append(f"- 平均占用率: {stats.get('avg_occupancy', 0):.4f}")
                
                if "congestion_analysis" in density_analysis:
                    cong_stats = density_analysis["congestion_analysis"]
                    report_content.append(f"\n### 拥堵分析")
                    report_content.append(f"- 平均拥堵指数: {cong_stats.get('avg_congestion_index', 0):.4f}")
                    report_content.append(f"- 最大拥堵指数: {cong_stats.get('max_congestion_index', 0):.4f}")
            
            # 4. 时间模式分析
            if temporal_analysis and "peak_analysis" in temporal_analysis:
                report_content.append("\n## 4. 时间模式分析")
                peak_stats = temporal_analysis["peak_analysis"]
                report_content.append(f"\n### 峰值分析")
                report_content.append(f"- 流量峰值时间: {peak_stats.get('peak_flow_time', 0)} 秒")
                report_content.append(f"- 流量峰值: {peak_stats.get('peak_flow_value', 0):.2f} 车辆/小时")
                report_content.append(f"- 拥堵峰值时间: {peak_stats.get('peak_congestion_time', 0)} 秒")
                report_content.append(f"- 拥堵峰值: {peak_stats.get('peak_congestion_value', 0):.4f}")
            
            # 5. 图表列表
            if chart_files:
                report_content.append("\n## 5. 分析图表")
                for chart_file in chart_files:
                    chart_name = Path(chart_file).name
                    report_content.append(f"- {chart_name}")
            
            report_content.append(f"\n\n报告生成完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 保存报告
            report_file = self.reports_dir / "edgedata_analysis_report.md"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_content))
            
            logger.info(f"EdgeData分析报告已生成: {report_file}")
            return str(report_file)
            
        except Exception as e:
            logger.error(f"EdgeData分析报告生成失败: {e}")
            return ""
    
    def _export_analysis_csvs(self, edgedata_summary: Dict[str, Any],
                             flow_analysis: Dict[str, Any],
                             speed_analysis: Dict[str, Any],
                             density_analysis: Dict[str, Any],
                             temporal_analysis: Dict[str, Any]) -> List[str]:
        """导出分析结果到 CSV 文件"""
        try:
            csv_files = []
            
            # 1. 导出原始数据
            df = edgedata_summary.get("data")
            if not df.empty:
                raw_data_file = self.reports_dir / "edgedata_raw_data.csv"
                df.to_csv(raw_data_file, index=False, encoding='utf-8')
                csv_files.append(str(raw_data_file))
            
            # 2. 导出时间序列数据
            if "temporal_stats" in temporal_analysis:
                temporal_df = pd.DataFrame(temporal_analysis["temporal_stats"])
                temporal_file = self.reports_dir / "edgedata_temporal_stats.csv"
                temporal_df.to_csv(temporal_file, encoding='utf-8')
                csv_files.append(str(temporal_file))
            
            # 3. 导出路段流量统计
            if "top_flow_edges" in flow_analysis:
                flow_df = pd.DataFrame(list(flow_analysis["top_flow_edges"].items()), 
                                     columns=["edge_id", "avg_flow_rate"])
                flow_file = self.reports_dir / "edgedata_edge_flow_stats.csv"
                flow_df.to_csv(flow_file, index=False, encoding='utf-8')
                csv_files.append(str(flow_file))
            
            # 4. 导出路段速度统计
            if "low_speed_edges" in speed_analysis:
                speed_df = pd.DataFrame(list(speed_analysis["low_speed_edges"].items()), 
                                      columns=["edge_id", "avg_speed"])
                speed_file = self.reports_dir / "edgedata_edge_speed_stats.csv"
                speed_df.to_csv(speed_file, index=False, encoding='utf-8')
                csv_files.append(str(speed_file))
            
            logger.info(f"EdgeData CSV文件导出完成，共导出 {len(csv_files)} 个文件")
            return csv_files
            
        except Exception as e:
            logger.error(f"EdgeData CSV导出失败: {e}")
            return []
