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
        """生成 EdgeData 分析报告（HTML，内嵌图表链接与样式）"""
        try:
            # 计算相对路径，保证报告中图片能显示
            rel_charts = []
            for cf in chart_files:
                try:
                    rel = Path(cf).relative_to(self.reports_dir)
                except Exception:
                    # 退化：若无法相对，则仅取文件名并放在 charts/ 前缀下
                    rel = Path("charts") / Path(cf).name
                rel_charts.append(rel.as_posix())

            # 提取核心统计
            def _fmt_float(v, digits=2):
                try:
                    return f"{float(v):.{digits}f}"
                except Exception:
                    return str(v)

            flow = flow_analysis.get("overall_stats", {}) if flow_analysis else {}
            speed = speed_analysis.get("overall_stats", {}) if speed_analysis else {}
            density = density_analysis.get("overall_stats", {}) if density_analysis else {}
            peak = (temporal_analysis or {}).get("peak_analysis", {})

            # HTML 模板
            html = f"""
<!DOCTYPE html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>EdgeData 交通流分析报告</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', 'Microsoft YaHei', sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }}
    .container {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    .header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }}
    .title {{ font-size: 24px; font-weight: 700; color: #f8fafc; }}
    .subtitle {{ color: #94a3b8; font-size: 14px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }}
    .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 12px; padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.2); }}
    .card h3 {{ margin: 0 0 8px; font-size: 16px; color: #f1f5f9; }}
    .metric {{ display: flex; align-items: baseline; gap: 6px; margin: 6px 0; }}
    .metric .label {{ color: #94a3b8; font-size: 13px; }}
    .metric .value {{ color: #e5e7eb; font-weight: 600; }}
    .section {{ margin-top: 24px; }}
    .section h2 {{ font-size: 18px; margin: 0 0 12px; color: #f8fafc; }}
    .img-wrap {{ background: #0b1220; border: 1px solid #1f2937; border-radius: 12px; padding: 12px; margin-bottom: 16px; text-align: center; }}
    img {{ max-width: 100%; height: auto; border-radius: 8px; }}
    table {{ width: 100%; border-collapse: collapse; border: 1px solid #1f2937; border-radius: 8px; overflow: hidden; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #1f2937; }}
    th {{ background: #0b1220; color: #cbd5e1; text-align: left; }}
    tr:nth-child(even) td {{ background: #0b1220; }}
    .footer {{ margin-top: 24px; color: #64748b; font-size: 12px; text-align: right; }}
    a {{ color: #60a5fa; text-decoration: none; }}
  </style>
  <script>
    // 轻量交互：折叠/展开
    function toggle(id) {{
      var el = document.getElementById(id);
      if (!el) return;
      el.style.display = (el.style.display === 'none') ? 'block' : 'none';
    }}
  </script>
  </head>
<body>
  <div class=\"container\">
    <div class=\"header\">
      <div class=\"title\">EdgeData 交通流分析报告</div>
      <div class=\"subtitle\">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    </div>

    <div class=\"grid\">
      <div class=\"card\">
        <h3>流量概览</h3>
        <div class=\"metric\"><span class=\"label\">平均流量</span><span class=\"value\">{_fmt_float(flow.get('avg_flow_rate', 0))} 车辆/小时</span></div>
        <div class=\"metric\"><span class=\"label\">最大流量</span><span class=\"value\">{_fmt_float(flow.get('max_flow_rate', 0))} 车辆/小时</span></div>
        <div class=\"metric\"><span class=\"label\">总进入车辆</span><span class=\"value\">{flow.get('total_vehicles_entered', 0):,}</span></div>
      </div>
      <div class=\"card\">
        <h3>速度概览</h3>
        <div class=\"metric\"><span class=\"label\">平均速度</span><span class=\"value\">{_fmt_float(speed.get('avg_speed', 0))} m/s</span></div>
        <div class=\"metric\"><span class=\"label\">最大速度</span><span class=\"value\">{_fmt_float(speed.get('max_speed', 0))} m/s</span></div>
        <div class=\"metric\"><span class=\"label\">最小速度</span><span class=\"value\">{_fmt_float(speed.get('min_speed', 0))} m/s</span></div>
      </div>
      <div class=\"card\">
        <h3>密度与拥堵</h3>
        <div class=\"metric\"><span class=\"label\">平均密度</span><span class=\"value\">{_fmt_float(density.get('avg_density', 0))} 车辆/km</span></div>
        <div class=\"metric\"><span class=\"label\">平均占用率</span><span class=\"value\">{_fmt_float(density.get('avg_occupancy', 0), 4)}</span></div>
      </div>
      <div class=\"card\">
        <h3>峰值时段</h3>
        <div class=\"metric\"><span class=\"label\">流量峰值时间</span><span class=\"value\">{peak.get('peak_flow_time', '-')}</span></div>
        <div class=\"metric\"><span class=\"label\">拥堵峰值时间</span><span class=\"value\">{peak.get('peak_congestion_time', '-')}</span></div>
      </div>
    </div>

    <div class=\"section\">
      <h2>图表</h2>
      {''.join([f'<div class=\"img-wrap\"><img alt=\"chart\" src=\"{src}\" /></div>' for src in rel_charts])}
    </div>

    <div class=\"section\">
      <h2 onclick=\"toggle('tables')\" style=\"cursor:pointer\">统计明细（点击折叠）</h2>
      <div id=\"tables\"> 
        <div class=\"card\">
          <h3>低速路段（Top 10）</h3>
          <table>
            <thead><tr><th>edge_id</th><th>avg_speed</th></tr></thead>
            <tbody>
            {''.join([f"<tr><td>{eid}</td><td>{_fmt_float(val)}</td></tr>" for eid, val in (list((speed_analysis or {}).get('low_speed_edges', {}).items())[:10])])}
            </tbody>
          </table>
        </div>
        <div class=\"card\">
          <h3>高流量路段（Top 10）</h3>
          <table>
            <thead><tr><th>edge_id</th><th>avg_flow_rate</th></tr></thead>
            <tbody>
            {''.join([f"<tr><td>{eid}</td><td>{_fmt_float(val)}</td></tr>" for eid, val in (list((flow_analysis or {}).get('top_flow_edges', {}).items())[:10])])}
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div class=\"section\">
      <h2>导出文件</h2>
      <div class=\"card\">
        <p>CSV 导出文件位于本目录，或 charts 子目录中的图表。</p>
        <ul>
          <li><a href=\"edgedata_raw_data.csv\">edgedata_raw_data.csv</a></li>
          <li><a href=\"edgedata_temporal_stats.csv\">edgedata_temporal_stats.csv</a></li>
          <li><a href=\"edgedata_edge_flow_stats.csv\">edgedata_edge_flow_stats.csv</a></li>
          <li><a href=\"edgedata_edge_speed_stats.csv\">edgedata_edge_speed_stats.csv</a></li>
        </ul>
      </div>
    </div>

    <div class=\"footer\">OD生成脚本 · EdgeData 报告</div>
  </div>
</body>
</html>
"""

            # 保存 HTML 报告
            report_file = self.reports_dir / "edgedata_analysis_report.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(html)

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
